# AgentProf 协作手册

> 给两个人看的操作指南，尽量不依赖 git 高级知识。  
> 遇到任何操作，把命令复制粘贴就能用。不确定时先问 CC。

---

## 1. 仓库结构一眼看懂

```text
agentprof/               核心包（两人共同维护，改动需知会对方）
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

## 2. 分支命名约定

| 分支名 | 用途 | 谁创建 |
| --- | --- | --- |
| `main` | 稳定版，只接 PR | 自动 |
| `dev` | 日常汇合点 | 已创建 |
| `feat/NO1xes-<名字>` | 你的功能开发 | 你 |
| `feat/collab-<名字>` | 对方的功能开发 | 对方 |
| `exp/NO1xes-<名字>` | 你的完整实验/不同设计 | 你 |
| `exp/collab-<名字>` | 对方的完整实验/不同设计 | 对方 |
| `baseline/<名字>` | 基线搭建 | 任意 |

---

## 3. 日常操作命令（傻瓜版）

### 每天开始工作前

```bash
# 切换到自己的分支，拉取最新内容
git checkout feat/NO1xes-xxx   # 换成你的分支名
git pull origin dev             # 把 dev 最新内容拉到本地（不是 merge，只是看看）
```

### 创建一个新功能分支

```bash
git checkout dev
git pull
git checkout -b feat/NO1xes-resource-health
```

这三步的意思：先切到 dev，确保是最新的，然后从 dev 创建新分支。

### 保存进度（提交）

```bash
git add <修改的文件>          # 或者 git add . 加入所有改动
git commit -m "简短说明做了什么"
git push origin feat/NO1xes-xxx
```

### 把自己的工作合入 dev

```bash
# 在 GitHub 上开一个 PR：feat/NO1xes-xxx → dev
# 对方看一眼，approve，然后 merge
# 合并后本地同步：
git checkout dev
git pull
```

### 把 dev 合入 main（里程碑完成时）

```bash
# 在 GitHub 上开 PR：dev → main
# 两人都 approve，merge
```

---

## 4. 对比实验操作

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

## 5. 切换后端

```bash
# .env 中修改：
AGENTPROF_BACKEND=langchain    # 观测层后端
AGENTPROF_PLANNER=llm          # planner 后端

# 临时覆盖（不改 .env）：
AGENTPROF_PLANNER=rule python -m agentprof.runner ...
```

---

## 6. 对方有完整的不同设计怎么办

对方在 `exp/collab-xxx` 分支上有一套完全不同的实现，想跑对比实验：

```bash
# 步骤 1：在本地同时检出对方分支（不影响你的工作）
git fetch origin
git checkout exp/collab-xxx

# 步骤 2：跑对方的实现
python -m agentprof.runner --config ...

# 步骤 3：切回自己的分支
git checkout feat/NO1xes-xxx

# 不需要 merge，两套代码可以独立运行
```

如果要把对方的某个文件合入你的分支（cherry-pick 单个文件）：

```bash
# 只把对方分支的某一个文件复制到你的工作区
git checkout exp/collab-xxx -- agentprof/analysis/breakdown.py
# 然后正常 commit
```

---

## 7. 回退到某个历史版本

```bash
# 查看最近的提交历史
git log --oneline -20

# 回退到某个 commit（只是查看，不修改任何东西）
git checkout <commit-hash>

# 回到当前分支
git checkout feat/NO1xes-xxx

# 如果想把某个文件回退到之前的版本
git checkout <commit-hash> -- agentprof/analysis/timeline.py
git commit -m "revert timeline.py to <commit-hash>"
```

---

## 8. 设计分歧怎么记录

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

## 9. 常见问题

**Q: push 失败，说 "rejected non-fast-forward"**

```bash
git pull --rebase origin feat/NO1xes-xxx
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
