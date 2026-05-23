# agentprof/

The core profiling controller Python package. Profiles agent systems under workload — does not optimize.

## Package layout

```text
agentprof/
  schema/         FROZEN — data structures (AgentEvent, SpanRecord, ObservationPlan, EvidenceRecord)
  model/          FROZEN — ExecutionModel (correlation graph), ObserverRegistry
  validator.py    FROZEN — forbidden action enforcement
  storage.py      FROZEN — read/write events.jsonl
  state.py        FROZEN — ProfilingState (shared mutable state across one run)
  observers/
    base.py       FROZEN — BaseObserver ABC
    __init__.py   Factory: get_observer(), get_all_baseline_observers()
    backends/
      langchain/  LangChain observer implementations (Milestone 1, implemented)
  planner/
    base.py       FROZEN — BasePlanner ABC
    __init__.py   Factory: get_planner()
    backends/
      llm/        LLM-based planner (Milestone 3, stub)
      rule/       Rule-based planner — ablation baseline b (Milestone 2, stub)
  analysis/       Deterministic computation: timeline, breakdown, resource_health, questions
  tools/          Deterministic tools callable by controller
  executor.py     Execute approved ObservationPlan (Milestone 3, stub)
  report/         Write report.md and summary.json (Milestone 4, stub)
  controller.py   Orchestrate the full profiling loop (Milestone 3, stub)
```

## Ownership tiers

| Tier | Modules | Rule |
| --- | --- | --- |
| FROZEN | `schema/`, `model/`, `validator.py`, `storage.py`, `state.py`, `observers/base.py`, `planner/base.py` | Interface changes require both contributors + ADR |
| Interface-stable | `observers/__init__.py`, `planner/__init__.py` | Signatures fixed; add backends freely |
| Contributor-owned | `observers/backends/`, `planner/backends/` | Owner decides; other reviews |
| Shared | `analysis/`, `tools/`, `executor.py`, `report/`, `controller.py` | PR to `dev`; one approve required |

## Backend switching

```bash
AGENTPROF_BACKEND=langchain   # observer backend
AGENTPROF_PLANNER=llm         # planner: llm | rule
```

## Module implementation status

See `PROJECT_STATUS.md` for the full table. Summary:

- Milestone 0–1: schema, model, validator, storage, state, observers (langchain), analysis (timeline, breakdown) — **implemented**
- Milestone 2: resource_health, questions, run_workload_tool, rule_planner — **stub**
- Milestone 3+: executor, controller, llm_planner, report — **stub**
