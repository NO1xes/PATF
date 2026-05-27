# AgentProf Collaboration Guide

> This document defines the collaboration workflow, code ownership model,
> branch strategy, and experiment management conventions for the AgentProf project.
> It is intended for both human contributors and coding agents (CC).

---

## 1. Repository Structure Overview

```text
AgentProf/
├── agentprof/               Core package — shared ownership, interface-stable
│   ├── schema/              FROZEN — changes require both contributors to agree
│   ├── model/               FROZEN
│   ├── validator.py         FROZEN
│   ├── storage.py           FROZEN
│   ├── observers/
│   │   ├── base.py          FROZEN interface
│   │   ├── backends/        Implementations — each contributor may own a backend
│   │   │   ├── langchain/   Current default
│   │   │   └── <future>/    Add new backends here
│   │   └── __init__.py      Factory — stable API, backend-agnostic
│   ├── planner/
│   │   ├── base.py          FROZEN interface
│   │   ├── backends/
│   │   │   ├── llm/         Default planner (Milestone 3)
│   │   │   └── rule/        Ablation baseline b (Milestone 2)
│   │   └── __init__.py      Factory
│   ├── analysis/            Shared — function signatures frozen, algorithms swappable
│   ├── executor.py          Shared
│   ├── controller.py        Shared
│   └── state.py             FROZEN
├── targets/                 Target agents (shared)
├── baselines/               Comparison baselines (contributor can own independently)
├── experiments/
│   ├── designs/             Architecture Decision Records (ADRs)
│   └── comparisons/         Per-experiment configs, results, conclusions
├── configs/
│   └── backends.yaml        Backend selection config
├── COLLAB.md                Simplified Chinese collaboration guide (this file's sibling)
└── docs/design/
    └── collaboration.md     This file
```

---

## 2. Ownership Tiers

| Tier | Modules | Change Policy |
| --- | --- | --- |
| **Frozen** | `schema/`, `model/`, `validator.py`, `storage.py`, `state.py`, all `base.py` files | Both contributors must agree; record in ADR |
| **Interface-stable** | `observers/__init__.py`, `planner/__init__.py`, `analysis/` function signatures | Agree on signature before implementation; document in ADR if changed |
| **Contributor-owned** | `backends/<name>/`, `baselines/<name>/`, `experiments/` | Owner decides; other contributor reviews but does not block |
| **Shared workload** | `targets/`, `configs/`, `controller.py`, `executor.py`, `report/` | PR to `dev`; maintainer may self-merge, but affected contributor should review integration diffs when practical |

---

## 3. Branch Strategy

Based on **GitHub Flow** (simplified trunk-based development):

```
main      ← stable; accepts PRs from dev only; maintainer (NO1xes) approves
dev       ← daily integration; accepts PRs from feat/ and baseline/; maintainer may self-merge when branch protection permits
│
├── feat/NO1xes-<name>      Maintainer feature branches
├── feat/collab-<name>      Contributor feature branches
├── exp/NO1xes-<name>       Maintainer's experimental / alternative design branches
├── exp/collab-<name>       Contributor's experimental branches
└── baseline/<name>         Baseline construction branches
```

### Roles

| Role | GitHub account | Responsibilities |
| --- | --- | --- |
| **maintainer** | NO1xes | Repository owner; manages Branch Protection; final approve on dev→main PRs |
| **contributor** | zcmmy | Develops features, baselines, experiments; PRs reviewed and merged by maintainer |

These roles only affect PR approval and `main` merge rights. Code architecture and module ownership are defined in Section 2 above — both contributors share ownership of core modules equally.

### Branch lifecycle

1. Branch from `dev` (not `main`)
2. Push freely; no review required on your own `feat/` branch
3. Open PR to `dev` when ready; maintainer may self-merge when branch protection permits, but contributor PRs and integration PRs should still be reviewed by the affected contributor when practical
4. `exp/` branches: no PR required to `dev`; used for running comparison experiments
5. `main` accepts PRs from `dev` only; both contributors approve; milestone-level only

### Sequential PRs and conflict handling

When two feature branches are developed in parallel, merge them to `dev` one at a
time. The second branch should rebase onto the updated `dev` before opening or
updating its PR:

```bash
git fetch origin
git rebase origin/dev
```

Git can identify textual conflicts, but it cannot decide the research meaning of
combined changes. Conflict resolution is therefore a manual or coding-agent-assisted
semantic merge:

- `CHANGELOG.md`: keep both contributors' entries; order by date or topic.
- `TODO.md`: keep both new tasks and completed checkboxes.
- `PROJECT_STATUS.md`: update to the latest factual status, test count, and blockers.
- `EXPERIMENTS.md`: keep one row per profiling run; never overwrite another run.
- Code files: verify that both edits belong to the same abstraction before combining.

If a PR integrates files or experiment records produced by the other contributor,
the maintainer can still merge it when repository permissions allow, but should
show the affected contributor the integration diff first.

### Commit messages

```
<type>(<scope>): <short summary>

Types: feat, fix, refactor, docs, test, chore, exp
Scope: observers, planner, analysis, baselines, experiments, configs

Examples:
  feat(observers): implement DeepAgent semantic observer
  exp(planner): compare LLM vs rule planner on slow_001
  docs(collab): add branch strategy section
```

---

## 4. Experiment Management

### Running a comparison experiment

Each experiment lives in `experiments/comparisons/expXXX-<name>/`:

```
expXXX-<name>/
  README.md          Hypothesis, setup, how to reproduce, conclusion
  config_A.yaml      Configuration for variant A
  config_B.yaml      Configuration for variant B (or more)
  results/           Copied outputs: breakdown_A.json, report_A.md, ...
```

Switching between implementations is one environment variable:

```bash
AGENTPROF_BACKEND=langchain  AGENTPROF_PLANNER=llm   python -m agentprof.runner ...
AGENTPROF_BACKEND=langchain  AGENTPROF_PLANNER=rule  python -m agentprof.runner ...
```

### Ablation study convention

For ablation experiments (isolating one component):

- Keep all config identical except the one variable being tested
- Run both variants on the same workload and same machine
- Record `run_id_A` and `run_id_B` in the experiment README
- Copy `breakdown.json`, `report.md`, `resource_health.json` to `results/`

### Design decisions (ADR)

Any significant design choice — especially contested ones — must have an ADR in
`experiments/designs/ADR-NNN-<topic>.md`. See `ADR-001` and `ADR-002` for format.

An ADR is required when:
- A frozen module's interface changes
- A new backend is added or removed
- Two contributors disagree on approach and reach a resolution
- A baseline is added or deprecated

---

## 5. Adding a New Backend

### Observer backend

1. Create `agentprof/observers/backends/<name>/`
2. Implement the four observer classes inheriting `BaseObserver`:
   - `<Name>SemanticObserver`
   - `<Name>LLMTimingObserver`
   - `<Name>ToolEventsObserver`
   - `<Name>ResourceSnapshotObserver`
3. Add a branch in `agentprof/observers/__init__.py` → `get_observer()` and `get_all_baseline_observers()`
4. Add `<name>` to `configs/backends.yaml` comment
5. Write an ADR explaining the motivation
6. Add tests in `tests/backends/<name>/`

### Planner backend

1. Create `agentprof/planner/backends/<name>/`
2. Implement `BasePlanner` subclass
3. Add a branch in `agentprof/planner/__init__.py` → `get_planner()`
4. Write an ADR

---

## 6. Resolving Disagreements

When two contributors have conflicting implementations:

1. **Both implementations stay on their respective `exp/` branches** — neither is deleted
2. **Write a comparison experiment** (`experiments/comparisons/expXXX/`) running both
3. **Write an ADR** documenting both options, the comparison results, and the decision
4. **The maintainer (NO1xes) makes the final call** on which goes to `dev`
5. The non-selected implementation stays on its `exp/` branch permanently — it may be
   revived if the decision is revisited

This ensures no work is lost and all design reasoning is recorded.

---

## 7. Modifying Workflow and Process Files

Changes to workflow, process, and collaboration files (`AGENTS.md`, `COLLAB.md`,
`docs/design/collaboration.md`, `docs/design/onboarding.md`) are **high-impact**:
they affect how both contributors and their coding agents behave on every future task.
Mistakes here propagate silently.

### Which files count as workflow files

| File | Why it's high-impact |
| --- | --- |
| `AGENTS.md` | Hard rules read by CC on every session; wrong rules cause systematic errors |
| `COLLAB.md` | Chinese operations guide; both contributors follow it daily |
| `docs/design/collaboration.md` | Formal spec; defines PR rules, ownership tiers, roles |
| `docs/design/onboarding.md` | Read by new contributors and CC at session start |

### Rules

1. **Discuss before changing** — state the problem and proposed change explicitly before editing. For CC-initiated changes, CC must describe the intent and get explicit approval.
2. **One logical change per commit** — do not bundle workflow changes with feature code changes.
3. **Record in CHANGELOG.md** — use type `docs` and mention which rule changed and why.
4. **Write an ADR if the change is contested or significant** — e.g. changing ownership tiers, branch strategy, or role definitions.
5. **Both contributors should read the diff** before it merges to `dev`.

### What does NOT require this process

- Fixing a factual error (stale module status, wrong filename)
- Updating trigger tables to add a newly-discovered file
- Typo / formatting fixes

These can be committed directly with a `docs:` commit message, no prior discussion needed.

---

## 8. Pre-merge Checklist

Before opening a PR from `feat/` to `dev`:

- [ ] `pytest tests/ -x -q` passes locally (68 tests, no GPU needed)
- [ ] GitHub Actions CI is green on the PR page
- [ ] No imports from frozen modules have changed signatures
- [ ] If a frozen module was changed: ADR written and both contributors agreed
- [ ] `CHANGELOG.md` updated
- [ ] `README.md` milestone list updated if a milestone completed
- [ ] `agentprof/README.md` status summary updated if module status changed
- [ ] `PROJECT_STATUS.md` updated if a module status changed
- [ ] `TODO.md` checked off if a task completed
- [ ] `EXPERIMENTS.md` updated if a `run_profiling()` run was executed
- [ ] New observer/planner backend: factory in `__init__.py` updated

Before opening a PR from `dev` to `main`:

- [ ] All of the above
- [ ] Milestone smoke test passes (see `PROJECT_STATUS.md`)
- [ ] Both contributors approve the PR
- [ ] No private paths, credentials, or machine-specific info in any committed file

## 8. For Coding Agents (CC)

When a CC is given a task on this repository:

1. Read `AGENTS.md` first (hard constraints, forbidden actions)
2. Read `PROJECT_STATUS.md` (current state, which modules are stubs)
3. Check which ownership tier the target module is in (Section 2 above)
4. For **frozen** modules: do not change interfaces without explicit instruction
5. For **contributor-owned** backends: implement freely within `BaseObserver` / `BasePlanner` contract
6. After completing a task: update `PROJECT_STATUS.md` and `CHANGELOG.md`
7. Do not open PRs to `main` directly; target `dev` or the assigned feature branch
8. On shared servers: follow resource constraints in `AGENTS.md` Section "Shared Server Resource Constraints"

---

## 9. Versioning and Tags

### Version number format

`vMAJOR.MINOR.PATCH` — [Semantic Versioning](https://semver.org/):

| Part | When to increment |
| --- | --- |
| MAJOR | Incompatible architecture change (e.g. replacing the controller loop) |
| MINOR | New milestone completed; new feature merged to main |
| PATCH | Bug fix or documentation-only change merged to main |

Current series: `v0.x.y` (pre-release research prototype — MAJOR stays 0 until stable).

### Tag rules

- **Every merge to `main` gets a tag.** No untagged main commits.
- Tag at the merge commit: `git tag -a v0.x.y -m "short description"` then `git push origin v0.x.y`
- Tag name must match the version entry in `README_zh.md` version history table.
- Annotated tags only (`-a`); no lightweight tags.

### What to do when merging to main

```bash
git checkout main
git merge dev --no-ff -m "chore: merge dev → main — vX.Y.Z description"
git tag -a vX.Y.Z -m "vX.Y.Z: short milestone description"
git push origin main
git push origin vX.Y.Z
git checkout dev
```

Then update `README_zh.md` version history table and commit to dev.

### Chinese README (README_zh.md)

- `README_zh.md` is the authoritative Chinese overview for both contributors.
- **Required update**: every time `main` is updated (PR merged), update the version
  history table in `README_zh.md` before or at the merge commit.
- Other sections (milestone list, machine table, architecture): update when the
  corresponding section in `README.md` changes.
- Plain content sync is fine to do in the same commit as the merge.
