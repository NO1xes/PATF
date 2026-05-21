# AgentProf Design — v0.4

> 本文档描述 v0.4 架构的设计意图和调用链。  
> 代码是最终实现；stub 处以本文档为准。

---

## 1. 设计原则

AgentProf 是一个**外部 profiling controller**，不修改被观测系统。

三个核心原则：

1. **Profiling only, no optimization**：禁止任何修改系统配置的动作
2. **Methodology-driven**：遵循 Gregg Drill-Down Latency Analysis，先高层分解，再按问题下钻
3. **LLM planner + deterministic tools + validator**：LLM 决定"观测什么"，Python 决定"怎么采集/计算"，validator 防止越界

---

## 2. 三个系统对象

```text
┌─────────────────────────────────────────────────────────┐
│                    AgentProf Controller                  │
│  run_workload → analyze → plan → validate → execute →  │
│  repeat → report                                        │
└────────────────────┬────────────────────────────────────┘
                     │ callbacks / wrappers / client timing
         ┌───────────▼──────────────────────────────┐
         │           Target Agent System             │
         │  LangChain/LangGraph ReAct Agent          │
         │       ↓ LLM calls      ↓ tool calls       │
         │  vLLM (Qwen3-30B-A3B)  slow/cpu/flaky     │
         └──────────────────────────────────────────┘
```

| 对象 | 职责 | 目录 |
| --- | --- | --- |
| Target Agent | 被 profile 的 agent，接收 workload task，调用 LLM 和 tools | `targets/langchain_react_agent/` |
| LLM Backend | vLLM OpenAI-compatible server，GPU 服务器上运行 | `scripts/start_vllm.sh` |
| AgentProf | 外部 profiling controller，观测、分析、规划、报告 | `agentprof/` |

**Target Agent 不 import agentprof**。AgentProf 通过 callback/wrapper 从外部挂载。

---

## 3. 四个执行层

| 层 | 执行对象 | 默认 Observer |
| --- | --- | --- |
| Agent Semantic | run, step, llm_call, tool_call, retry, wait | `semantic_langchain` |
| LLM Serving | request, queue, prefill, decode, TTFT, TPOT | `llm_client_timing` |
| Tool Execution | function, subprocess, error, duration | `tool_events` |
| Hardware/Resource | CPU, memory, GPU, disk, network | `resource_snapshot` |

跨层关联通过 `trace_id → span_id → parent_span_id` 链实现（OpenTelemetry 模型）。

---

## 4. 核心数据结构

### AgentEvent（`schema/events.py`）

所有 observer 的输出统一格式。字段：

```python
event_id, trace_id, program_id, span_id, parent_span_id,
layer, event_type, name, ts, attrs, source_observer, raw_ref
```

`ts` 是 Unix 秒（float），`attrs` 是灵活字段（tool_name、duration_ms、token_usage 等）。

### SpanRecord（`schema/spans.py`）

由 start/end AgentEvent 配对合并得到。timeline 和 breakdown 操作 SpanRecord，不操作原始 event。

```python
trace_id, program_id, span_id, parent_span_id,
span_kind,  # AGENT | LLM | TOOL | WAIT | UNKNOWN
name, start_ts, end_ts, duration_ms, attrs, children, error, is_retry
```

### ObservationPlan（`schema/observations.py`）

LLM planner 的输出，validator 的输入。

```python
plan_id, question_id,
observers,          # list[str]，从 registry 中选
scope,              # {program_id, span_id, time_window_start, time_window_end}
mode,               # same_run | replay_if_deterministic | query_existing
rationale,          # LLM 必须给出理由
expected_evidence,  # list[str]
budget,
approved, rejection_reason
```

### ExecutionModel（`model/execution_model.py`）

跨层 correlation graph。**只存节点、边和数据引用，不存原始 metrics**。

```python
nodes: dict[node_id → {type, layer, attrs}]
edges: list[{src, dst, kind, attrs}]
data_refs: dict[name → file_path]
# 例：{"events": "profiles/run_001/events.jsonl",
#      "resource_snapshot": "profiles/run_001/resource_snapshot.csv"}
```

节点类型：`system_run`, `program_run`, `span`, `llm_request`, `tool_call`, `process`, `resource_entity`

边类型：`parent_child`, `span_maps_to_request`, `tool_maps_to_pid`, `span_overlaps_resource_window`

### ProfilingState（`state.py`）

一次 profiling campaign 的完整状态，贯穿整个 controller 循环。

```python
run_id, workload_name, spec,
observer_registry,      # ObserverRegistry
execution_model,        # ExecutionModel
enabled_observers,      # set[str]
events_path,            # str | None
timeline_path,          # str | None
breakdown,              # dict | None
resource_health,        # dict | None
diagnostic_questions,   # list[dict]
observation_plans,      # list[ObservationPlan]
evidence,               # list[EvidenceRecord]
known_unknowns,         # list[str]
action_log,             # list[dict]  — 审计用
budget_used,            # dict
iteration               # int
```

---

## 5. 完整调用链（MVP run）

```text
controller.run_profiling(spec, target, observers, workload)
  │
  ├─ 1. load_spec()                    → state.spec
  ├─ 2. ObserverRegistry.from_yaml()   → state.observer_registry
  ├─ 3. build_initial_execution_model()→ state.execution_model
  │
  ├─ 4. tools/run_workload_tool.run_workload()
  │       激活 baseline observers:
  │         semantic_langchain (LangChain callback)
  │         llm_client_timing  (monkey-patch OpenAI client)
  │         tool_events        (wrap tool functions)
  │         resource_snapshot  (psutil background thread)
  │       运行 target agent tasks
  │       → profiles/<run_id>/events.jsonl
  │       → profiles/<run_id>/resource_snapshot.csv
  │
  ├─ 5. analysis/timeline.build_timeline()
  │       → list[SpanRecord] + timeline.csv
  │
  ├─ 6. analysis/breakdown.compute_breakdown()
  │       → breakdown.json
  │         {total_ms, llm_ms, tool_ms, wait_retry_ms, unknown_ms,
  │          llm_pct, tool_pct, ..., dominant_component}
  │
  ├─ 7. analysis/resource_health.compute_resource_health()
  │       → resource_health.json
  │         {cpu_util_pct, memory_util_pct, symptoms, notes}
  │
  ├─ 8. analysis/questions.generate_questions()
  │       → state.diagnostic_questions
  │         [{question_id, priority, text, source, candidate_observers}]
  │
  ├─ 9. planner/llm_planner.plan_observation()   ← LLM 决策
  │       输入: spec + breakdown + resource_health + registry + questions + known_unknowns
  │       → ObservationPlan
  │
  ├─ 10. validator.validate(plan, registry, budget)
  │        → approved=True / False + reason
  │
  ├─ 11. executor.execute(plan)   (若 approved)
  │        → observer outputs → state.evidence updated
  │
  ├─ 12. 若 iteration < max_iterations 且有新问题 → 回到步骤 9
  │
  └─ 13. report/markdown_report.write_markdown_report()
          report/summary_json.write_summary_json()
          → profiles/<run_id>/report.md
          → profiles/<run_id>/summary.json
          → profiles/<run_id>/known_unknowns.md
```

---

## 6. Observer 设计原则

- 每个 observer 继承 `BaseObserver`，实现 `attach()`, `detach()`, `flush()`
- `flush()` 返回 buffer 中的 `list[AgentEvent]` 并清空 buffer
- Observer 不做分析，只做采集和格式转换
- Tool decomposition 由 observer capability 描述，不硬编码阶段

### Baseline observers（每次 run 都激活）

| Observer | 层 | 成本 | 实现方式 |
| --- | --- | --- | --- |
| `semantic_langchain` | agent_semantic | low | LangChain `BaseCallbackHandler` |
| `llm_client_timing` | llm_serving | low | monkey-patch `client.chat.completions.create` |
| `tool_events` | tool_execution | low | `wrap_tool(fn)` 包装函数 |
| `resource_snapshot` | hardware_resource | low | psutil 后台采样线程，1s 间隔 |

### 按需 observers（由 ObservationPlan 触发）

| Observer | 层 | 触发条件 |
| --- | --- | --- |
| `vllm_metrics` | llm_serving | LLM time 主导 + 本地 vLLM 可用 |
| `tool_process` | tool_execution | tool time 主导 + 需要 pid 级别归因 |

---

## 7. Validator 约束

`validator.py` 是代码层面的最后防线，与 `configs/profiling_spec.yaml` 的 `forbidden_actions` 保持一致。

当前禁止的 action（任何出现在 ObservationPlan.observers 中的名字）：

```python
FORBIDDEN_ACTIONS = {
    "change_concurrency", "change_arrival_rate", "toggle_cache",
    "set_timeout", "set_quota", "apply_patch",
    "modify_prompt", "modify_planner",
}
```

Validator 还检查：observer 是否在 registry 中、budget 是否超限。

---

## 8. 本机（local_pc_win11）的特殊说明

- **无 GPU**：不能运行 vLLM，`vllm_metrics` observer 不可用
- **可调用远程 API**：`VLLM_BASE_URL` 指向远程 vLLM 服务器或 OpenAI API
- **resource_snapshot**：可以运行（psutil 不需要 GPU），但 GPU 字段为 null
- **Milestone 1 可以在本机完成**：observers、analysis、storage 都不依赖 GPU
- **Milestone 3 的 LLM planner**：可以调用远程 API（OpenAI 或远程 vLLM）

---

## 9. 报告格式（10 个必须章节）

```text
1. Profiling Scope
2. Workload
3. Enabled Observers
4. Initial Baseline
5. Timeline / Breakdown
6. Resource Health Snapshot
7. Observation Plans
8. Evidence
9. Known Unknowns
10. Suggested Next Observation  ← 注意：不是优化建议
```

第 10 项只建议"下一步观察什么"，不建议"如何优化"。
