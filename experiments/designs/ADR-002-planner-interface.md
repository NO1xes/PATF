# ADR-002: Planner Interface Design

- **Date**: 2026-05-21
- **Status**: Accepted
- **Deciders**: NO1xes (lead)

## Context

AgentProf's core research question requires comparing an LLM-based planner against
a deterministic rule-based planner (ablation study). This requires both to be
interchangeable at runtime without code changes.

## Decision

Adopt the same **Interface + Backend** pattern as ADR-001 for the planner:

- `agentprof/planner/base.py` — `BasePlanner` ABC with `plan_observation(state)` method
- `agentprof/planner/backends/llm/` — LLM-based planner (default, Milestone 3)
- `agentprof/planner/backends/rule/` — Rule-based planner (ablation baseline b, Milestone 2)
- `agentprof/planner/__init__.py` — `get_planner(backend)` factory, reads `AGENTPROF_PLANNER`

## Switching between planners

```bash
# Use LLM planner (default)
AGENTPROF_PLANNER=llm python -m agentprof.runner ...

# Use rule-based planner for ablation
AGENTPROF_PLANNER=rule python -m agentprof.runner ...
```

## Consequences

- `llm_planner.py`, `prompts.py`, `context_builder.py` moved to `backends/llm/`
- `rule_planner.py` stub created in `backends/rule/`
- Ablation experiment can be run by changing one env var
- `baselines/rule_based_profiler/` provides a standalone version for comparison scripts
