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
      llm/        LLM-based planner (Milestone 3, implemented)
      rule/       Rule-based planner — ablation baseline b (Milestone 2, implemented)
  analysis/       Deterministic computation: timeline, breakdown, resource_health, questions
  tools/          Profiling tools callable by LLM (v2) or controller (legacy)
                  system_metrics.py       L1 — psutil + nvidia-smi hardware tools
                  llm_serving_metrics.py   L2 — vLLM Prometheus query tools
                  tool_execution_metrics.py L3 — span/event inspection tools
                  agent_semantic_metrics.py L4 — agent loop trace tools
  adapters/       External benchmark adapters (BFCL implemented)
  executor.py     Legacy executor (v0.4)
  report/         Write report.md and summary.json (Milestone 4)
  controller.py   Legacy linear pipeline (v0.4)
  controller_v2.py ReAct tool-calling loop (v2)
```

## Ownership tiers

| Tier | Modules | Rule |
| --- | --- | --- |
| FROZEN | `schema/`, `model/`, `validator.py`, `storage.py`, `state.py`, `observers/base.py`, `planner/base.py` | Interface changes require both contributors + ADR |
| Interface-stable | `observers/__init__.py`, `planner/__init__.py` | Signatures fixed; add backends freely |
| Contributor-owned | `observers/backends/`, `planner/backends/` | Owner decides; other reviews |
| Shared | `analysis/`, `tools/`, `executor.py`, `report/`, `controller.py` | PR to `dev`; affected contributor should review integration diffs when practical |

## Backend switching

```bash
AGENTPROF_BACKEND=langchain   # observer backend
AGENTPROF_PLANNER=llm         # planner: llm | rule
```

## Module implementation status

See `PROJECT_STATUS.md` for the full table. Summary (as of 2026-05-23):

- Milestone 0–4: all planned modules **implemented** — schema, model, validator, storage, state,
  observers (langchain), analysis (timeline, breakdown, resource_health, questions),
  rule_planner, llm_planner, executor, controller, report
- 90 tests passing; Tier 0 ReAct profiling session PASSED (DeepSeek v4-pro, 5 tool calls)
- Milestone 4: multi-program aggregation and report quality implemented
- Milestone 5: BFCL workload adapter implemented
- **v2: ReAct tool-calling loop with 11 tools across 4 tiers (L1 Hardware → L4 Agent Semantic)**
