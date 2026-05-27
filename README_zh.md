# AgentProf（中文说明）

基于方法论的 LLM Agent 系统性能剖析框架。

当前架构：v0.1 — LLM planner + 确定性工具 + 验证器
工作分支：`dev`（两位贡献者的日常分支）

> 英文版：[README.md](README.md)

---

## 这是什么

AgentProf 是一个**外部剖析控制器**，通过观察目标 Agent 系统（Target Agent + LLM Backend + Tools）的运行过程，生成结构化性能报告。采用 Gregg 的 Drill-Down Latency Analysis 方法论。

**AgentProf 只做剖析，不做优化。**

---

## 系统架构

```text
工作负载任务
      ↓
目标 Agent（LangChain/LangGraph ReAct）
      ↓ LLM 调用              ↓ 工具调用
vLLM 服务（Qwen3-30B-A3B）   slow/cpu/flaky 工具
      │                          │
      └──── AgentProf 通过 callbacks / wrappers / 客户端计时进行外部观测
                  ↓
            events.jsonl（规范化事件日志）
                  ↓
         analysis/（时序分析、耗时分解、资源健康、诊断问题）
                  ↓
         planner/（LLM 生成 ObservationPlan）
                  ↓
         validator → executor
                  ↓
         report.md + known_unknowns.md
```

三个组件严格分离：

| 组件 | 说明 | 位置 |
| --- | --- | --- |
| 目标 Agent | 被剖析的 Agent | `targets/langchain_react_agent/` |
| LLM Backend | vLLM 服务（仅 GPU 服务器） | `scripts/start_vllm.sh` |
| AgentProf | 外部剖析控制器 | `agentprof/` |

---

## 快速开始

```bash
# 1. 克隆仓库，切换到工作分支
git clone git@github.com:NO1xes/PATF.git      # SSH（个人机）
# 或: git clone https://github.com/NO1xes/PATF.git  # 共享服务器 HTTPS
cd PATF
git checkout dev

# 2. 创建 conda 环境（Python 3.11）
conda create -n agentprof python=3.11 -y
conda activate agentprof
pip install -e ".[dev]"
# 国内网络加镜像：pip install -e ".[dev]" -i https://pypi.tuna.tsinghua.edu.cn/simple

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env：填写 VLLM_BASE_URL、VLLM_MODEL、AGENTPROF_MACHINE 等
# 共享服务器还需填写 GITHUB_USER/GITHUB_PAT，并用 scripts/git_push_with_env_pat.sh 推送

# 4. 安装 pre-commit hook（一次性，推荐）
bash scripts/install_hooks.sh

# 5. 验证环境（无需 GPU）
pytest tests/ -x -q   # 应有 70 个测试通过

# 6. 运行受控工作负载（需要在 .env 中配置 LLM 端点）
bash scripts/run_controlled_workload.sh

# 7. 查看报告
cat profiles/<run_id>/report.md
```

---

## 必读文件顺序

新成员按以下顺序阅读：

1. 本文件（README_zh.md）— 项目概览
2. [AGENTS.md](AGENTS.md) — 硬性约束，CC 和人都必读
3. [PROJECT_STATUS.md](PROJECT_STATUS.md) — 当前进度、阻塞项、下一步
4. [COLLAB.md](COLLAB.md) — 协作工作流、分支命令、实验操作（中文）
5. [docs/design/onboarding.md](docs/design/onboarding.md) — 模块地图、文档维护规则
6. [docs/design/collaboration.md](docs/design/collaboration.md) — 正式协作规范（英文，CC 使用）

---

## 目录结构

```text
agentprof/                核心剖析控制器（Python 包）
  schema/                 冻结 — 数据结构定义
  model/                  冻结 — 执行模型、观察器注册表
  validator.py            冻结 — 禁止行为执行
  storage.py              冻结 — 事件读写
  state.py                冻结 — ProfilingState
  observers/              观察器（接口冻结，实现可替换）
  planner/                规划器（接口冻结，实现可替换）
  analysis/               确定性计算：时序、耗时分解、资源健康
  executor.py             执行已批准的 ObservationPlan
  report/                 生成 report.md 和 summary.json
  controller.py           协调完整的剖析流程

targets/                  目标 Agent（被剖析对象，非 AgentProf 代码）
configs/                  所有配置文件
baselines/                对比基线（Langfuse、OpenTelemetry、规则基线）
experiments/              实验管理（ADR、对比实验、结果存档）
scripts/                  启动和工具脚本
docs/                     设计文档、周报、会议记录
profiles/                 实验运行输出（大文件，不进 git）
```

---

## 当前里程碑

- [x] Milestone 0：仓库骨架 + v0.4 架构重构
- [x] Milestone 1：观察器 + 分析模块（38 个测试，无需 LLM/GPU）
- [x] Milestone 2：resource_health、questions、run_workload、端到端 smoke test
- [x] Milestone 3：LLM Planner + 完整控制器循环 — smoke test 通过（nusa100，2026-05-23）
- [x] Milestone 4：多程序聚合 + 报告质量（70 个测试）
- [ ] Milestone 5：真实基准子集（BFCL V3；adapter 已实现，demo run 待完成）

---

## 协作说明

本项目为双人贡献者科研项目。完整工作流见 [COLLAB.md](COLLAB.md)。

| 角色 | GitHub 账号 | 职责 |
| --- | --- | --- |
| maintainer | NO1xes | 仓库所有者，审批 PR，管理 main 分支 |
| contributor | zcmmy | 开发功能、基线、实验 |

- 日常在 `dev` 分支工作，向 `dev` 开 PR
- `feat/NO1xes-<名字>` 和 `feat/collab-<名字>` 用于功能开发分支
- `exp/<名字>` 用于实验/备选设计分支
- 设计分歧：在 `experiments/designs/` 写 ADR 记录

---

## 版本历史

| 版本 | 日期 | 内容 |
| --- | --- | --- |
| v0.1.1 | 2026-05-23 | 添加 MIT LICENSE，开源准备 |
| v0.1.0 | 2026-05-23 | Milestone 0–3 完成；LLM+rule planner smoke test 通过；协作工作流完备 |

完整变更记录见 [CHANGELOG.md](CHANGELOG.md)。

---

## 机器配置

| machine_id | 角色 | GPU | 配置文件 |
| --- | --- | --- | --- |
| local_pc_win11 | 开发 + API 实验 | 无 | `configs/machines/local_pc_win11.yaml` |
| nusa100 | LangChain 测试，vLLM 后端 | 5× A100-SXM4-80GB | `configs/machines/nusa100.yaml` |

各机器详细搭建步骤见 [ENVIRONMENT.md](ENVIRONMENT.md)。

## 许可证

MIT License — 见 [LICENSE](LICENSE)。
