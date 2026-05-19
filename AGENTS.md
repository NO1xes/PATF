# AgentProf Coding Rules — v0.4

## Project Goal

Build a methodology-driven profiling controller for agent systems under workload.

**Current stage: profiling only. No optimization.**

## Architecture (v0.4)

```text
Target Agent    = LangChain/LangGraph ReAct single agent
LLM Backend     = vLLM OpenAI-compatible server (Qwen3-30B-A3B)
AgentProf       = LLM planner + deterministic tools + validator
```

These three components must remain separate. Do NOT merge AgentProf logic into the Target Agent.

## Core Design Principle

```text
LLM planner   → decides WHAT to observe (ObservationPlan)
Python tools  → decides HOW to collect, compute, validate, write
Validator     → enforces constraints (no optimization, no budget overrun)
```

## Forbidden — NEVER implement or call

```python
FORBIDDEN_ACTIONS = {
    "change_concurrency", "change_arrival_rate", "toggle_cache",
    "set_timeout", "set_quota", "apply_patch",
    "modify_prompt", "modify_planner",
}
```

- Do NOT implement `select_next_layer` — use `plan_observation` returning `ObservationPlan`
- Do NOT put raw metrics into `ExecutionModel` — it is a correlation graph with data refs only
- Do NOT hardcode tool decomposition phases — capability is described in `ObserverCapability`
- Do NOT let Python rules alone decide the next observer — LLM planner must generate the plan
- Do NOT delete files under `profiles/`
- Do NOT commit `.env`, API keys, model weights, large logs

## Required

- After any code change: update `CHANGELOG.md`
- After any task status change: update `PROJECT_STATUS.md`
- Every new experiment run must generate `profiles/<run_id>/metadata.yaml`
- All output to `profiles/<run_id>/`: events.jsonl, timeline.csv, breakdown.json,
  resource_snapshot.csv, resource_health.json, execution_model.json,
  observation_plans.jsonl, evidence.jsonl, known_unknowns.md, report.md
- All paths must be configurable via `configs/` or `.env`

## Module Responsibilities

| Module | Responsibility |
| --- | --- |
| `agentprof/schema/` | Data structures (AgentEvent, SpanRecord, ObservationPlan, EvidenceRecord) |
| `agentprof/model/` | ExecutionModel (correlation graph), ObserverRegistry |
| `agentprof/observers/` | Collect raw data, emit AgentEvents |
| `agentprof/analysis/` | Deterministic computation: timeline, breakdown, resource_health, questions |
| `agentprof/planner/` | LLM-based ObservationPlan generation |
| `agentprof/tools/` | Deterministic tools callable by controller |
| `agentprof/validator.py` | Enforce forbidden actions and budget |
| `agentprof/executor.py` | Execute approved ObservationPlan |
| `agentprof/report/` | Write report.md and summary.json |
| `agentprof/controller.py` | Orchestrate the full profiling loop |

## Checklist Before Any PR to main

1. Is Target Agent / LLM Backend / AgentProf still separate?
2. Does `profiling_spec.yaml` have `forbidden_actions`?
3. Is there an `ObserverRegistry`?
4. Does next-step selection produce `ObservationPlan` (not a layer name)?
5. Does `validator.py` check forbidden actions?
6. Does LLM planner generate the plan (not just write the report)?
7. Does `ExecutionModel` contain only nodes/edges/data_refs (no raw metrics)?
8. Does `resource_snapshot` run at baseline (not deferred)?
9. Does `report.md` include evidence and known_unknowns?
10. Are there zero forbidden optimization actions implemented?
