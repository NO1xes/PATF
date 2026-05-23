# AgentProf 协作手册

> 给两位贡献者看的操作指南，尽量不依赖 git 高级知识。  
> 遇到任何操作，把命令复制粘贴就能用。不确定时先问各自的 CC。

**新人第一步（按顺序读）：**
1. [README.md](README.md) — 项目概览、架构图、Quick Start
2. [AGENTS.md](AGENTS.md) — 硬性约束（CC 和人都必读）
3. [ENVIRONMENT.md](ENVIRONMENT.md) — 本机环境搭建（conda、.env、机器配置）
4. 本文件（COLLAB.md）— 日常操作命令、分支约定、实验流程
5. [docs/design/onboarding.md](docs/design/onboarding.md) — 模块地图、文档维护规则
6. [PROJECT_STATUS.md](PROJECT_STATUS.md) — 当前进度和下一步任务

---

## 0. 两位贡献者的角色

| 角色标识 | GitHub 账号 | 职责 |
| --- | --- | --- |
| **maintainer**（维护者） | NO1xes | 仓库所有者；管理 Branch Protection；PR dev→main 最终审批 |
| **contributor**（协作者） | zcmmy | 开发功能、基线、实验；PR 经 maintainer approve 合入 dev |

这两个角色**只影响 PR 审批和 main 合并权限**，代码架构和模块分工见 `AGENTS.md`。

---

## 1. 分支总览（先看这里）

| 分支 | 性质 | 说明 |
| --- | --- | --- |
| `main` | **正式版本** | 稳定，只从 dev 合入，每次打 tag |
| `dev` | **日常开发** | 两人主要工作的汇合点 |
| `feat/` `exp/` `baseline/` | 功能/实验分支 | 从 dev 切出，PR 回 dev |
| `public` | **仓库门面（勿用于开发）** | GitHub 默认分支，展示用途；内容与本项目无关，**不要 checkout 到这里工作** |

> **一句话**：克隆仓库后立即 `git checkout dev`，所有开发工作都在 `dev` 及其子分支上进行。`public` 分支不参与任何开发流程，也不会合入 main。

---

## 2. 仓库结构一眼看懂

```text
agentprof/               核心包（两人共同维护，改动需知会另一位贡献者）
  schema/                数据结构 — 冻结，单人不得改动接口
  model/                 注册表/模型 — 冻结
  validator.py           约束执行 — 冻结
  storage.py             读写工具 — 冻结
  observers/
    base.py              接口 — 冻结
    backends/langchain/  当前实现（可换）
    __init__.py          工厂函数，换后端改这里
  planner/
    base.py              接口 — 冻结
    backends/llm/        默认 LLM planner
    backends/rule/       规则 baseline（消融用）
    __init__.py          工厂函数

baselines/               对比基线（独立，不影响主代码）
experiments/
  designs/               设计决策记录（ADR）
  comparisons/           对比实验配置和结果
```

**冻结 = 改动必须两人都同意，并写 ADR 记录原因。**

---

## 3. 分支命名约定

| 分支名 | 用途 | 谁创建 |
| --- | --- | --- |
| `main` | 稳定版，只接来自 dev 的 PR，maintainer 审批 | — |
| `dev` | 日常汇合点，接受 feat/ 和 baseline/ 的 PR | — |
| `feat/NO1xes-<名字>` | maintainer 的功能开发 | NO1xes |
| `feat/collab-<名字>` | contributor 的功能开发 | contributor |
| `exp/NO1xes-<名字>` | maintainer 的完整实验/不同设计 | NO1xes |
| `exp/collab-<名字>` | contributor 的完整实验/不同设计 | contributor |
| `baseline/<名字>` | 基线搭建 | 任意 |
| `public` | 仓库门面，**不参与开发流程** | NO1xes（只读） |

---

## 4. 日常操作命令（傻瓜版）

### 每天开始工作前

```bash
# 切换到自己的分支，同步 dev 最新内容
git checkout feat/<你的分支名>
git pull origin dev --rebase
```

### 创建一个新功能分支

```bash
git checkout dev
git pull
git checkout -b feat/NO1xes-resource-health   # maintainer 示例
git checkout -b feat/collab-langfuse-adapter  # contributor 示例
```

### 保存进度（提交）

```bash
git add <修改的文件>          # 或者 git add . 加入所有改动
git commit -m "简短说明做了什么"
git push origin feat/<你的分支名>
```

### 把自己的工作合入 dev

```bash
# 在 GitHub 上开一个 PR：feat/<你的分支名> → dev
# 另一方 approve，maintainer merge
# 合并后本地同步：
git checkout dev
git pull
```

### 把 dev 合入 main（里程碑完成时）

```bash
# 在 GitHub 上开 PR：dev → main
# 两人都 approve，maintainer merge
```

---

## 5. 对比实验操作

两套实现跑同一个 workload 的步骤：

```bash
# 步骤 1：确保两套配置文件都在 experiments/comparisons/expXXX/
ls experiments/comparisons/exp001-llm-vs-rule/
# config_llm.yaml  config_rule.yaml

# 步骤 2：跑 A 配置
AGENTPROF_PLANNER=llm python -m agentprof.runner \
  --config experiments/comparisons/exp001-llm-vs-rule/config_llm.yaml

# 步骤 3：跑 B 配置
AGENTPROF_PLANNER=rule python -m agentprof.runner \
  --config experiments/comparisons/exp001-llm-vs-rule/config_rule.yaml

# 步骤 4：把结果拷贝到 comparisons 目录
cp profiles/<run_id_A>/breakdown.json experiments/comparisons/exp001-llm-vs-rule/results/breakdown_llm.json
cp profiles/<run_id_B>/breakdown.json experiments/comparisons/exp001-llm-vs-rule/results/breakdown_rule.json

# 步骤 5：写结论到 experiments/comparisons/exp001-llm-vs-rule/README.md
```

---

## 6. 切换后端

```bash
# .env 中修改：
AGENTPROF_BACKEND=langchain    # 观测层后端
AGENTPROF_PLANNER=llm          # planner 后端

# 临时覆盖（不改 .env）：
AGENTPROF_PLANNER=rule python -m agentprof.runner ...
```

---

## 7. 查看另一位贡献者的不同设计

另一位贡献者在 `exp/collab-xxx` 或 `exp/NO1xes-xxx` 分支上有一套完全不同的实现，想跑对比实验：

```bash
# 步骤 1：在本地检出另一方的分支（不影响自己的工作）
git fetch origin
git checkout exp/collab-xxx

# 步骤 2：跑另一方的实现
python -m agentprof.runner --config ...

# 步骤 3：切回自己的分支
git checkout feat/<你的分支名>

# 不需要 merge，两套代码可以独立运行
```

如果要把另一方的某个文件合入自己的分支（cherry-pick 单个文件）：

```bash
# 只把另一方分支的某一个文件复制到自己的工作区
git checkout exp/collab-xxx -- agentprof/analysis/breakdown.py
# 然后正常 commit
```

---

## 8. 回退到某个历史版本

```bash
# 查看最近的提交历史
git log --oneline -20

# 回退到某个 commit（只是查看，不修改任何东西）
git checkout <commit-hash>

# 回到当前分支
git checkout feat/<你的分支名>

# 如果想把某个文件回退到之前的版本
git checkout <commit-hash> -- agentprof/analysis/timeline.py
git commit -m "revert timeline.py to <commit-hash>"
```

---

## 9. 设计分歧怎么记录

当两人对某个设计有不同想法时：

1. 在 `experiments/designs/` 下创建 `ADR-00X-<主题>.md`
2. 用这个模板：

```markdown
# ADR-00X: <主题>

- Date: YYYY-MM-DD
- Status: Proposed / Accepted / Rejected / Superseded
- Deciders: <谁参与讨论>

## Context
<为什么需要做这个决定>

## Option A — <方案名>（谁提出）
**优点：** ...
**缺点：** ...

## Option B — <方案名>（谁提出）
**优点：** ...
**缺点：** ...

## Decision
<选了哪个，为什么>

## Reverting
<如果要撤回这个决定，需要做什么>
```

3. commit 这个文件，推到 `dev`

---

## 10. 常见问题

**Q: push 失败，说 "rejected non-fast-forward"**

```bash
git pull --rebase origin feat/<你的分支名>
git push
```

**Q: 误改了不该改的文件，想撤销**

```bash
git restore <文件名>   # 撤销未提交的修改
```

**Q: 提交了但想撤销最后一次 commit（还没 push）**

```bash
git reset HEAD~1   # 撤销 commit，保留文件改动
```

**Q: 不知道现在在哪个分支**

```bash
git status         # 第一行显示当前分支
git branch         # 列出所有本地分支，* 是当前分支
```

---

## 11. 修改工作流/流程文件的规定

`AGENTS.md`、`COLLAB.md`、`docs/design/collaboration.md`、`docs/design/onboarding.md` 这类文件是**高影响文件**——改错了会让两个人（和各自的 CC）在每次任务中都走错路，影响面远大于普通代码改动。

**改之前：先讨论**
- 说清楚要改什么、为什么改，得到另一方（或 maintainer）明确同意后再改。
- CC 发起的修改：CC 必须先描述意图，等确认后再执行。

**改之后：记录**
- `CHANGELOG.md` 追加一行，类型用 `docs`，写清楚改了哪条规则、原因是什么。
- 改动较大或有争议的：写一个 ADR（`experiments/designs/ADR-00X.md`）。

**不需要走这个流程的小改动：**
- 修正错误的文件名、过时的模块状态
- 补充之前遗漏的触发条件（纯补全）
- 错别字/格式修复

这类改动直接提交，commit 类型写 `docs:` 即可。

---

## 12. 自动化测试

### 本地 pre-commit hook（推荐每人安装一次）

```bash
bash scripts/install_hooks.sh
```

安装后，每次 `git commit` 涉及 `.py` 文件时，会自动跑 4 个核心 unit test（约 5 秒，无需 GPU）。失败则阻止提交。紧急情况可以绕过：`git commit --no-verify`。

### GitHub Actions（自动，无需操作）

每次向 `dev` 或 `main` push，或者开 PR 时，GitHub 会自动跑全部 63 个 unit test。可在 PR 页面看到结果。两人都不能 merge 一个 CI 红了的 PR（除非 Branch Protection 未开启）。

### 测试分层

| 层级 | 命令 | 条件 | 用途 |
| --- | --- | --- | --- |
| 快速核心 | `pytest tests/test_schema.py tests/test_storage.py tests/test_validator.py tests/test_analysis.py -x -q` | 无需 GPU | pre-commit hook 运行 |
| 全部单元 | `pytest tests/ -x -q` | 无需 GPU | CI / PR 前手动 |
| 端到端 | `AGENTPROF_PLANNER=rule python -m agentprof...` | 需要 vLLM | milestone smoke test |

---

## 13. 版本号与 Tag 规则

版本号格式：`vMAJOR.MINOR.PATCH`

| 部分 | 何时递增 |
| --- | --- |
| MAJOR | 不兼容的架构变更（目前保持 0） |
| MINOR | 新里程碑完成并合入 main |
| PATCH | bug 修复或纯文档变更合入 main |

**每次合入 main 都必须打 tag，流程如下：**

```bash
git checkout main
git merge dev --no-ff -m "chore: merge dev → main — vX.Y.Z 说明"
git tag -a vX.Y.Z -m "vX.Y.Z: 简短说明"
git push origin main
git push origin vX.Y.Z
git checkout dev
```

**中文 README（README_zh.md）：**
- 每次合入 main 时，必须更新其中的版本历史表。
- 其他章节（里程碑、机器表等）随英文 README.md 同步更新。
