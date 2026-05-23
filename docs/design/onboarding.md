# AgentProf Onboarding Guide

> 目标读者：新机器上的开发者、协作同学、Coding Agent（CC）。  
> 目标：读完此文件后，能独立理解仓库结构、接手任务、维护文档、给 CC 分配任务。

---

## 1. 先读哪些文件（顺序）

| 顺序 | 文件 | 目的 |
| --- | --- | --- |
| 1 | `README.md` | 项目概览、架构图、快速启动 |
| 2 | `AGENTS.md` | 硬性约束，CC 必读，人也应读 |
| 3 | `PROJECT_STATUS.md` | 当前进度、阻塞项、下一步 |
| 4 | 本文件 | 模块地图、维护方法、任务分配 |
| 5 | `TODO.md` | 当前任务列表，按 Milestone 组织 |
| 6 | `CHANGELOG.md` | 历史变更，了解来龙去脉 |
| 7 | `docs/design/agentprof_design.md` | 深入架构设计和调用链 |

其他文件按需查阅，不需要全部读完才能开始工作。

---

## 2. 文件权威性说明

不同文件的"权威性"不同，冲突时以权威性高的为准：

| 文件 | 权威性 | 说明 |
| --- | --- | --- |
| `AGENTS.md` | 最高 | 约束规则，任何代码不得违反 |
| `configs/profiling_spec.yaml` | 高 | 当前 profiling campaign 的契约，forbidden_actions 在此声明 |
| `agentprof/validator.py` | 高 | 代码层面的约束执行，与 profiling_spec 保持一致 |
| `PROJECT_STATUS.md` | 中（时效性强）| 反映当前状态，需要经常更新 |
| `TODO.md` | 中（时效性强）| 任务列表，完成后立即勾选 |
| `docs/design/agentprof_design.md` | 中（设计层）| 架构意图，代码是最终实现 |
| `CHANGELOG.md` | 低（历史记录）| 只追加，不修改历史 |

**重要**：设计文档描述意图，代码是实现。如两者冲突，先看代码是否是 stub（`raise NotImplementedError`），是 stub 则文档为准；是真实实现则代码为准，并更新文档。

---

## 3. 模块职责地图

### 3.1 数据流向（一次 MVP run）

```text
configs/ (spec + target + observers + backends + workload)
        ↓  controller.py 读取并初始化
agentprof/state.py  ← ProfilingState，贯穿全程

tools/run_workload_tool.py
        ↓  启动 Target Agent，激活 baseline observers
observers/__init__.py → get_all_baseline_observers(backend="langchain")
  backends/langchain/semantic_langchain.py   ← LangChain callback → AgentEvent
  backends/langchain/llm_client_timing.py    ← monkey-patch OpenAI client → AgentEvent
  backends/langchain/tool_events.py          ← wrap tool functions → AgentEvent
  backends/langchain/resource_snapshot.py    ← psutil sampling → AgentEvent
        ↓  所有 AgentEvent 写入
storage.py → profiles/<run_id>/events.jsonl
                           resource_snapshot.csv

analysis/
  timeline.py    ← events.jsonl → SpanRecords + timeline.csv
  breakdown.py   ← SpanRecords → breakdown.json (各层时间占比)
  resource_health.py ← resource_snapshot.csv → resource_health.json
  questions.py   ← breakdown + resource_health → diagnostic_questions

planner/__init__.py → get_planner(backend="llm"|"rule")
  backends/llm/context_builder.py ← state → prompt context
  backends/llm/llm_planner.py     ← LLM call → ObservationPlan
  [或] backends/rule/rule_planner.py ← 规则决策 → ObservationPlan (消融用)

validator.py   ← ObservationPlan → approved / rejected

executor.py    ← approved plan → run observer → update evidence

report/
  markdown_report.py → report.md
  summary_json.py    → summary.json
```

### 3.2 各模块实现状态

| 模块 | 状态 | Tier | Milestone |
| --- | --- | --- | --- |
| `schema/` (4 files) | 实现完成 | FROZEN | 0 |
| `model/execution_model.py` | 实现完成 | FROZEN | 0 |
| `model/observer_registry.py` | 实现完成 | FROZEN | 1 |
| `storage.py` | 实现完成 | FROZEN | 0 |
| `validator.py` | 实现完成 | FROZEN | 0 |
| `state.py` | 实现完成 | FROZEN | 0 |
| `observers/base.py` | 实现完成 | FROZEN | 0 |
| `planner/base.py` | 实现完成 | FROZEN | 1 |
| `observers/backends/langchain/semantic_langchain.py` | 实现完成（需 langchain_core） | Contributor-owned | 1 |
| `observers/backends/langchain/llm_client_timing.py` | 实现完成 | Contributor-owned | 1 |
| `observers/backends/langchain/tool_events.py` | 实现完成 | Contributor-owned | 1 |
| `observers/backends/langchain/resource_snapshot.py` | 实现完成（需 psutil） | Contributor-owned | 1 |
| `analysis/timeline.py` | 实现完成 | Shared | 1 |
| `analysis/breakdown.py` | 实现完成 | Shared | 1 |
| `analysis/resource_health.py` | stub | Shared | 2 |
| `analysis/questions.py` | stub | Shared | 2 |
| `tools/run_workload_tool.py` | stub | Shared | 2 |
| `targets/langchain_react_agent/agent.py` | stub (`run_task`) | Shared | 2 |
| `targets/langchain_react_agent/tools.py` | 实现完成（3 tools） | Shared | 0 |
| `tools/inspect_trace_tool.py` | stub | Shared | 2 |
| `tools/query_observer_tool.py` | stub | Shared | 2 |
| `tools/build_report_tool.py` | stub | Shared | 2 |
| `executor.py` | stub | Shared | 3 |
| `report/markdown_report.py` | stub | Shared | 4 |
| `report/summary_json.py` | stub | Shared | 4 |
| `planner/backends/llm/context_builder.py` | stub | Contributor-owned | 3 |
| `planner/backends/llm/llm_planner.py` | stub | Contributor-owned | 3 |
| `planner/backends/rule/rule_planner.py` | stub | Contributor-owned | 2 |
| `controller.py` | stub | Shared | 3 |
| `baselines/langfuse_adapter/` | stub | Contributor-owned | — |
| `baselines/rule_based_profiler/` | stub | Contributor-owned | — |

### 3.3 哪些东西由 LLM 决定，哪些由 Python 决定

| 决策 | 由谁做 | 文件 |
| --- | --- | --- |
| 下一步观测什么 (ObservationPlan) | LLM | `planner/backends/llm/llm_planner.py` |
| 是否越界 / 预算是否超 | Python | `validator.py` |
| 事件怎么采集 | Python | `observers/` |
| 时间怎么算 | Python | `analysis/` |
| 文件怎么写 | Python | `storage.py`, `report/` |
| 有哪些 observer 可用 | Python 注册 | `model/observer_registry.py` |
| 是否有优化动作 | Python 拦截 | `validator.py` + `AGENTS.md` |

---

## 4. 如何在新机器上接手

### 4.1 通用步骤（所有机器）

```bash
# 1. 克隆（共享服务器用 HTTPS+PAT，个人机用 SSH）
git clone https://<PAT>@github.com/NO1xes/AgentProf.git   # HTTPS+PAT（共享服务器）
# 或
git clone git@github.com:NO1xes/AgentProf.git              # SSH（个人机）

# 2. 切换到当前工作分支
git checkout dev

# 3. 阅读 ENVIRONMENT.md，找本机对应的机器配置
cat ENVIRONMENT.md

# 4. 创建 conda 环境
conda create -n agentprof python=3.11 -y
conda activate agentprof

# 5. 安装依赖
pip install -e ".[dev]"
# 中国大陆加镜像：pip install -e ".[dev]" -i https://pypi.tuna.tsinghua.edu.cn/simple

# 6. 复制并填写环境变量
cp .env.example .env
# 编辑 .env，至少填写：
#   VLLM_BASE_URL=http://<your-server>:8000/v1
#   VLLM_API_KEY=dummy   （本地 vLLM 不需要真实 key）
#   AGENTPROF_MACHINE=<machine_id>
#   GITHUB_PAT=<your-token>   （共享服务器需要，用于 git push/pull）

# 7. 验证环境
bash scripts/verify_env.sh

# 8. 读 PROJECT_STATUS.md 了解当前状态
cat PROJECT_STATUS.md
```

### 4.2 添加新机器

1. 复制 `configs/machines/local_pc_win11.yaml` 为 `configs/machines/<新机器ID>.yaml`
2. 按注释填写所有字段（OS、GPU、conda 路径、git auth 方法、网络环境）
3. 在 `ENVIRONMENT.md` 的机器表格中添加一行
4. 提交：`git add configs/machines/ ENVIRONMENT.md && git commit -m "chore: add machine config <machine_id>"`

### 4.3 git 认证说明

| 场景 | 方法 |
| --- | --- |
| 个人机，SSH key 已配好 | `git clone git@github.com:NO1xes/AgentProf.git` |
| 共享服务器，无 SSH key | 用 HTTPS + Personal Access Token（PAT）：`git clone https://<PAT>@github.com/NO1xes/AgentProf.git`，PAT 存入 `.env` 的 `GITHUB_PAT` 字段，不进 git |
| 共享服务器，git 身份 | 用 `git config --local`（不用 `--global`，避免污染其他用户） |

---

## 5. 如何维护关键文档

每次开发结束前，检查以下文件是否需要更新：

| 文件 | 触发更新的事件 | 谁维护 |
| --- | --- | --- |
| `CHANGELOG.md` | 任何代码改动，追加一行 | CC + 开发者 |
| `TODO.md` | 完成一个 TODO 项（勾选）、新增任务、milestone 状态变化 | CC + 开发者 |
| `PROJECT_STATUS.md` | 模块状态变化（stub→implemented）、遇到新阻塞、测试数变化 | CC + 开发者 |
| `EXPERIMENTS.md` | 每次跑实验，登记 run_id 和关键结论 | 开发者 |
| `docs/weekly/YYYY-MM-DD.md` | 每周组会前写一份 | 开发者 |
| `configs/machines/<id>.yaml` | 新增机器或机器的硬件/角色信息变化 | 开发者 |
| `ENVIRONMENT.md` | 新增机器、依赖版本变化 | 开发者 |

**较少更新（仅以下情形）：**

| 文件 | 更新时机 |
| --- | --- |
| `README.md` | 架构变化、新 milestone 完成、新机器加入 |
| `AGENTS.md` | 约束规则变化、新模块分工 |
| `docs/design/agentprof_design.md` | 设计意图变化 |
| `agentprof/README.md`、`targets/README.md` 等子目录 README | 该模块接口或角色变化 |

**`TODO.md` vs `PROJECT_STATUS.md` 分工：**
- `TODO.md`：按 Milestone 列任务条目，追踪"还有什么要做"，粒度为一个具体任务。
- `PROJECT_STATUS.md`：按模块列实现状态（stub / implemented / FROZEN），追踪"哪个文件在什么状态"，粒度为一个文件/模块。
- 两个文件均需维护，互不替代。

---

## 6. 如何给 Coding Agent (CC) 分配任务

### 6.1 任务格式模板

```text
你是 AgentProf 项目的 coding assistant。
请先读：README.md → AGENTS.md → PROJECT_STATUS.md → docs/design/onboarding.md

当前任务：<具体模块名>
文件：<具体文件路径>
输入：<该函数/模块的输入是什么>
输出：<该函数/模块的输出是什么，写到哪个文件>
约束：
  - 不要修改 controller.py（尚未到 Milestone 3）
  - 不要新增 forbidden actions
  - 不要硬编码路径（从 .env 或 configs/ 读取）
验收标准：
  - <运行什么命令>
  - <预期输出是什么>
  - 完成后更新 TODO.md（勾选对应项）和 CHANGELOG.md（追加一行）
```

### 6.2 当前可分配的 Milestone 1 任务（每个独立）

每个任务可以独立分配给一个 CC，互不依赖（都是 stub → 实现）：

**任务 A：`tool_events.py`**
- 文件：`agentprof/observers/tool_events.py`
- 实现 `wrap_tool(fn)` 方法
- 输出：包装后的函数，在调用前后向 `self._buffer` 追加 `AgentEvent`（tool_call_start/end/error）
- 测试：直接调用包装后的 `slow_tool`，打印 buffer 中的事件

**任务 B：`analysis/timeline.py`**
- 文件：`agentprof/analysis/timeline.py`
- 实现 `build_timeline(events_path, output_dir)`
- 输入：`events.jsonl`（一组 AgentEvent JSON 行）
- 输出：`list[SpanRecord]` + `timeline.csv`
- 测试：用 `tests/fixtures/sample_events.jsonl` 跑，验证 SpanRecord 数量和 duration_ms > 0

**任务 C：`analysis/breakdown.py`**
- 依赖任务 B 完成后
- 文件：`agentprof/analysis/breakdown.py`
- 实现 `compute_breakdown(spans)`
- 输出：breakdown dict，`total_ms > 0`，各层 `pct` 之和约等于 1

### 6.3 CC 不应自己决定的事

- 是否改变 profiling 方法论（这是你的研究决定）
- observer_registry 里加哪些 observer（需要你审核）
- 是否跳过 validator（绝对不允许）
- experiment 结论的解释（你的第一作者职责）

---

## 7. 分支和合并规则

| 分支 | 用途 |
| --- | --- |
| `main` | 稳定可跑版本，只接受经过审查的 PR |
| `dev` | 日常汇合点，所有 PR 的目标分支 |
| `feat/NO1xes-<name>` | NO1xes 的功能开发分支 |
| `feat/collab-<name>` | 协作者的功能开发分支 |
| `exp/<name>` | 完整实验/不同设计分支 |
| `fix/<name>` | bug 修复 |
| `agent/<task>` | CC 的临时分支 |

合并到 main 前必须满足：
1. `scripts/verify_env.sh` 通过
2. 对应 milestone 的 smoke test 通过（见 TODO.md）
3. `CHANGELOG.md` 已更新
4. `PROJECT_STATUS.md` 已更新

---

## 8. 实验输出规范

每次 profiling run 必须产生：

```text
profiles/<run_id>/
  metadata.yaml          # run_id, date, machine, git commit hash, config snapshot ref
  config_snapshot/       # 冻结的 4 个 yaml（profiling_spec, target_system, observers, workload）
  events.jsonl           # 原始 AgentEvent 流（可能很大，不进 git）
  timeline.csv           # 每个 span：start_ts, end_ts, duration_ms, layer, name
  breakdown.json         # 各层时间占比
  resource_snapshot.csv  # psutil 采样（可能很大，不进 git）
  resource_health.json   # USE health signals
  execution_model.json   # correlation graph（节点/边/data_refs）
  observation_plans.jsonl  # LLM 生成的 ObservationPlan 序列
  evidence.jsonl         # EvidenceRecord 序列
  known_unknowns.md      # 无法归因的内容
  report.md              # 最终报告
  logs/                  # 原始日志（不进 git）
```

大文件（events.jsonl、resource_snapshot.csv、logs/）不进 git。  
每次实验后把 `report.md` 和 `summary.json` 复制到 `experiments/reports/` 并更新 `EXPERIMENTS.md`。

---

## 9. 新机器 CC 启动提示词

在新机器上开启 Claude Code 会话后，将以下提示词粘贴给 CC，它将能独立接手工作：

```text
你是 AgentProf 项目的 coding assistant。这是一个方法论驱动的 agent 系统 profiling 控制器，
当前阶段：profiling only，不做优化。

请按以下顺序读取文件，建立完整上下文：
1. README.md                     — 项目概览和架构
2. AGENTS.md                     — 硬性约束、模块 ownership tier、共享服务器资源限制
3. PROJECT_STATUS.md             — 当前进度、模块实现状态、下一步任务
4. COLLAB.md                     — 协作流程、分支命名、对比实验操作（中文）
5. docs/design/onboarding.md     — 模块地图和维护规则（本文件）
6. docs/design/collaboration.md  — 正式协作规范（英文，含 CC 操作指引）

读完后，告诉我：
- 当前处于哪个 Milestone
- 哪些模块是 stub（待实现）
- 你被分配的任务属于哪个 ownership tier（FROZEN / Interface-stable / Contributor-owned / Shared）
- 你建议从哪个任务开始，理由是什么

操作约束：
- FROZEN 模块（schema/, model/, validator.py, storage.py, state.py, */base.py）：
  不得修改接口，除非明确被告知两人已达成一致
- observer/planner 实现放在对应的 backends/<name>/ 子目录，不要放在 observers/ 根目录
- 切换后端只改 .env 中的 AGENTPROF_BACKEND / AGENTPROF_PLANNER，不改代码
- 所有 PR 目标分支是 dev，不是 main
- 共享服务器（nusa100）：遵守 AGENTS.md "Shared Server Resource Constraints"，Tier 3 测试用 Docker/SLURM
- git 使用 --local config，不要修改 global git 配置
- 不要安装任何包到 base conda 环境
- 所有输出写入 $AGENTPROF_WORK_DIR（从 .env 读取）
- 完成任何任务后更新 PROJECT_STATUS.md 和 CHANGELOG.md
```
