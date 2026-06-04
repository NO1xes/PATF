# AgentProf Design — v2 (ReAct Tool-Calling Loop)

> 本文档描述 v2 架构：LLM-driven ReAct profiling agent + 四层可调用工具。
> v0.4 legacy 设计（线性 pipeline）参见文档末尾 [§10 附录](#10-附录-v04-legacy-设计)。

---

## 1. 设计原则

AgentProf 是一个**同环境外部 profiling agent**，不修改被观测系统，不控制工作负载。

核心原则：

1. **Profiling only, no optimization**：禁止任何修改系统配置的动作
2. **Methodology-driven**：遵循 coarse→fine drill-down，先便宜粗粒度扫描定位异常，再细粒度确认
3. **LLM ReAct agent + four-tier tools**：LLM 通过 function-calling 主动调用四层 profiling 工具，决定"观察什么、什么粒度、多久"
4. **Profiling 开销可量化**：AgentProf 与被观测系统同宿主机运行，自身资源消耗纳入 profiling 质量评估
5. **白盒可退化到黑盒**：Layer 1 工具仅依赖 psutil/nvidia-smi（黑盒可用），Layer 2-4 逐步引入白盒能力

---

## 2. 部署拓扑与系统对象

```text
宿主机（nusa100 / 单机）
  │
  ├── Docker / 裸进程: Target Agent System（已在运行，AgentProf 不控制）
  │     ├── Agent runtime (LangGraph ReAct / SWE-agent / ...)
  │     ├── Tools (code exec, browser, file I/O, ...)
  │     └── LLM calls ──────→  vLLM / 远程 API（DeepSeek / OpenAI）
  │
  └── 裸进程: AgentProf（同宿主机，Docker 外）
        ├── psutil → 监控宿主机 + Docker 进程
        ├── nvidia-smi → GPU 指标（如本地有 GPU server）
        ├── HTTP → vLLM Prometheus metrics
        ├── callbacks / monkey-patch → 白盒 observer（可选）
        └── HTTP API call → AgentProf 自己的 LLM（决策 profiling 策略）
```

| 对象 | 职责 | AgentProf 能控制？ |
| --- | --- | --- |
| Target Agent System | 被 profiling 的系统，独立运行 | ❌ 不能启动/停止/修改 |
| AgentProf LLM | profiling 决策大脑，通过 HTTP API 调用 | ✅ 唯一控制者 |
| Four-Tier Tools | AgentProf LLM 可调用的 profiling 工具 | ✅ LLM 决定何时调用、什么参数 |

---

## 3. 四层 Profiling 工具（粗→细）

AgentProf 的 LLM 有四层工具可用，层次含义：
- **越下层越便宜、越黑盒**，适合首次粗扫
- **越上层越细、越白盒**，需要更多权限和开销
- **两个目的**：(a) 定位问题 (b) 节省资源（不能全开细粒度）

| 层 | 名称 | 可访问性 | 工具（LLM 可调用） | 源码 |
| --- | --- | --- | --- | --- |
| **L1** | Hardware/System | 黑盒 ✅ | `get_system_overview()`, `get_process_tree()`, `get_gpu_metrics()`, `sample_resources()` | `tools/system_metrics.py` |
| **L2** | LLM Serving | 灰盒 | `get_vllm_metrics()`, `sample_vllm_metrics()` | `tools/llm_serving_metrics.py` |
| **L3** | Tool Execution | 白盒→黑盒退化 | `observe_tool_calls()`, `inspect_span()`, `query_events()` | `tools/tool_execution_metrics.py` |
| **L4** | Agent Semantic | 白盒 | `trace_agent_loop()`, `list_active_agents()` | `tools/agent_semantic_metrics.py` |

**子视角**：L1 的 `get_process_tree()` 提供进程级资源归属（psutil 原生支持），prompt 告知 LLM 有此能力。

---

## 4. ReAct Profiling Loop

```
AgentProf 启动
  │
  ├─ 加载配置（workload 描述 + target system 信息 + machine 信息）
  ├─ 构建 system prompt（四层层次 + 方法论 + 资源效率规则 + Hard Constraints）
  ├─ 构建 initial context（当前已知 + 可用工具列表）
  │
  └─ ReAct LOOP（最多 max_tool_calls 次）:
        │
        ├─ LLM 收到 messages（system + context + 历史 tool calls）
        ├─ LLM 决定: 调用某个 tool（带参数）OR 输出最终报告
        │
        ├─ 若 tool_call:
        │     ├─ AgentProf 执行 tool（如 get_system_overview()）
        │     ├─ 结果序列化为 JSON 注入 messages
        │     └─ 回到 LOOP 顶部
        │
        └─ 若 text response（无 tool_call）:
              → 即为 final report → 写入 report.md → 结束
```

**关键变化 vs v0.4**：
- ❌ 不再有硬编码 baseline（旧: 4 observer 全开）
- ❌ LLM 不再只"建议 observer"（旧: planner → validator → executor 查询已有数据）
- ✅ LLM 主动调用工具、决定粒度（`interval_sec`、`top_n`、`duration_sec`）
- ✅ 工具结果实时注入 context，LLM 基于新信息迭代决策

---

## 5. System Prompt 核心内容

`agentprof/planner/backends/llm/prompts_v2.py` — `PROFILING_AGENT_SYSTEM_PROMPT`

包含七个部分：
1. **身份**：你是 AgentProf，profiling agent，不是 target agent
2. **目标**：产出结构化 profiling report，定位瓶颈
3. **四层工具**：描述每层工具 + 何时使用 + 可调参数
4. **方法论**：先粗→定位异常→归因→时间剖析→决策
5. **资源效率规则**：不要一开始就细粒度；系统健康时快速结论；tool call 预算有限
6. **Hard Constraints**：不修改系统、不优化、只 profiling
7. **输出格式**：5 段结构化 report（System Health / Anomalies / Root Cause / Drill-Down Path / Recommendations）

---

## 6. 核心数据结构（不变，同 v0.4）

AgentEvent → SpanRecord → ObservationPlan → ExecutionModel → ProfilingState

详见 [§10 附录](#10-附录-v04-legacy-设计) 第 4 节。

---

## 7. Observer 角色变化

**v0.4**：Observer 硬编码全开（baseline run 4 个全激活）
**v2**：Observer 变为 LLM 按需调用的底层采集器

- L1 工具直接调用 psutil/nvidia-smi，不经过 observer（黑盒路径）
- L2 工具通过 HTTP 拉取 vLLM Prometheus metrics（灰盒路径）
- L3/L4 工具可选择性注入 observer（白盒路径），无 observer 时从事件流推断（黑盒退化）
- 现有 4 个 baseline observer 保留，供 L3/L4 工具调用

---

## 8. Validator 约束（不变，同 v0.4）

详见 [§10 附录](#10-附录-v04-legacy-设计) 第 7 节。Forbidden actions 不变。

---

## 9. 报告格式（5 段输出）

```text
1. System Health Summary — L1 工具结果（CPU/mem/disk/net/GPU 概览）
2. Anomalies Detected — 哪些指标异常，具体数值
3. Root Cause Attribution — 证据链：哪条工具调用揭示了什么
4. Drill-Down Path — 按时间顺序记录每个 tool call 的动机和发现
5. Recommendations for Next Iteration — 建议启用哪些上层工具深挖
```

---

## 10. 附录：v0.4 Legacy 设计

> 以下为 v0.4 线性 pipeline 设计，保留作为参考。旧代码在 `controller.py`（保留为 legacy）。
