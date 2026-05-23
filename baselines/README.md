# Baselines directory

This directory contains comparison baselines used in experiments and ablation studies.

## Structure

```
baselines/
  langfuse_adapter/         Adapter wrapping Langfuse output into AgentProf's AgentEvent format
  opentelemetry_adapter/    Adapter wrapping OpenTelemetry spans into AgentEvent format
  rule_based_profiler/      Standalone rule-based profiler (no LLM) for ablation
```

## Purpose

| Baseline | Type | Used in |
| --- | --- | --- |
| `langfuse_adapter` | External tool (baseline a) | Compare AgentProf output against Langfuse for same run |
| `opentelemetry_adapter` | External tool (baseline a) | Compare trace coverage and attribution quality |
| `rule_based_profiler` | Ablation (baseline b) | Verify LLM planner adds value over deterministic rules |

## Candidate selection

Baseline comparison is motivation-oriented, not a strict variable-control experiment.
The goal is to understand coverage, attribution style, reporting strengths/weaknesses,
and ideas AgentProf can learn from.

Initial candidate pool:

| Candidate | Why consider it | Likely comparison angle |
| --- | --- | --- |
| Langfuse | Open-source LLM observability with tracing, metrics, evals, prompt management, and OpenTelemetry integration | Trace coverage, latency/cost visibility, report ergonomics |
| Arize Phoenix / OpenInference | OpenTelemetry-based AI observability and broad framework instrumentation | OTel/OpenInference span schema vs AgentProf AgentEvent schema |
| AgentOps | Agent-focused monitoring, replay, cost tracking, and framework integrations | Agent-session view vs methodology-driven profiling report |
| AgentSight | eBPF/system-level AI agent observability | System boundary visibility vs in-process observer callbacks |
| AgentProf-named projects | Must be searched and filtered; many hits may mean "agent profile" rather than profiling | Include only if it profiles/observes LLM agent execution |

## How baselines relate to `agentprof/planner/backends/rule/`

`rule_based_profiler/` here is a **standalone** version that can run without the full AgentProf
controller — useful for quick comparison scripts.
`agentprof/planner/backends/rule/rule_planner.py` is the **integrated** version that plugs into
the controller via the factory interface. They share logic; the standalone version calls the
integrated one internally once it is implemented.

## Adding a new baseline

1. Create `baselines/<name>/`
2. Add `README.md` explaining: what it is, what data it produces, how to run it
3. Add an adapter that converts its output to `list[AgentEvent]` or `breakdown dict`
4. Add a comparison entry in `experiments/comparisons/`
5. Record the decision to add it in `experiments/designs/`
