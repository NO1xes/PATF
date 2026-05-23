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
| **Shared workload** | `targets/`, `configs/`, `controller.py`, `executor.py`, `report/` | PR to `dev`, one approve required |

---

## 3. Branch Strategy

Based on **GitHub Flow** (simplified trunk-based development):

```
main      ← stable, tagged releases; accepts PRs from dev only
dev       ← daily integration; accepts PRs from feat/ and baseline/
│
├── feat/NO1xes-<name>      Lead contributor feature branches
├── feat/collab-<name>      Second contributor feature branches
├── exp/NO1xes-<name>       Lead's experimental / alternative design branches
├── exp/collab-<name>       Second contributor's experimental branches
└── baseline/<name>         Baseline construction branches
```

### Branch lifecycle

1. Branch from `dev` (not `main`)
2. Push freely; no review required on your own `feat/` branch
3. Open PR to `dev` when ready; one approve required
4. `exp/` branches: no PR required to `dev`; used for running comparison experiments
5. `main` accepts PRs from `dev` only; both contributors approve; milestone-level only

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
4. **The lead contributor makes the final call** on which goes to `dev`
5. The non-selected implementation stays on its `exp/` branch permanently — it may be
   revived if the decision is revisited

This ensures no work is lost and all design reasoning is recorded.

---

## 7. Pre-merge Checklist

Before opening a PR from `feat/` to `dev`:

- [ ] `pytest tests/test_schema.py tests/test_storage.py tests/test_validator.py tests/test_analysis.py` passes
- [ ] No imports from frozen modules have changed signatures
- [ ] If a frozen module was changed: ADR written and both contributors agreed
- [ ] `CHANGELOG.md` updated
- [ ] `PROJECT_STATUS.md` updated if a milestone item is done
- [ ] New observer/planner backend: factory in `__init__.py` updated, `backends.yaml` comment updated

Before opening a PR from `dev` to `main`:

- [ ] All of the above
- [ ] Milestone smoke test passes (see `PROJECT_STATUS.md`)
- [ ] Both contributors approve the PR

---

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
