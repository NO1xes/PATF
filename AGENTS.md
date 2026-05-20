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

## Shared Server Resource Constraints

When working on a shared GPU/CPU server, ALL of the following limits apply.
Violating them affects other users and may result in job termination.

### Hard limits (enforce before running anything)

| Resource | Limit | How to enforce |
| --- | --- | --- |
| CPU cores | ≤ 1/8 of total | `taskset`, `os.cpu_count()//8`, or `cpuset` in Docker |
| RAM | ≤ 1/8 of total | `ulimit -v`, cgroup `memory.limit_in_bytes`, or Docker `--memory` |
| GPU memory | ≤ 1/8 of total per GPU | `CUDA_VISIBLE_DEVICES` + `--gpu-memory-utilization` in vLLM |
| GPU count | ≤ 1 GPU unless explicitly allocated | set `CUDA_VISIBLE_DEVICES=<single id>` |
| Disk (work dir) | ≤ 20 GB under assigned `$AGENTPROF_WORK_DIR` | check with `du -sh` before large writes |
| Network ports | only ports assigned to your user/job | check with sysadmin; do not bind 0.0.0.0 |
| Process count | no fork bombs; max 32 child processes | use `ulimit -u` |
| Wall time | respect job scheduler limits (SLURM/PBS) | always submit via scheduler, never run directly on login node |

### Development workflow tiers

**Tier 1 — local unit tests (no GPU, no LLM)**
Use conda env `agentprof`. No resource constraints needed.
Covers: test_schema, test_storage, test_validator, test_analysis.

**Tier 2 — integration tests with LLM API (no GPU locally)**
Use conda env `agentprof` + remote vLLM API endpoint.
Enforce CPU/RAM limits via `ulimit` before running.
Covers: test_tools, single-task end-to-end smoke test.

**Tier 3 — full workload experiments (GPU server)**
Must use Docker or SLURM job with explicit resource limits.
Never run Tier 3 workloads directly in a login shell.

```bash
# Example: Docker run with 1/8 resource limits (adjust totals for your server)
docker run --rm \
  --cpus="4" \
  --memory="16g" \
  --gpus '"device=0"' \
  -e CUDA_VISIBLE_DEVICES=0 \
  -v $AGENTPROF_WORK_DIR:/workspace \
  agentprof:latest \
  python -m agentprof.controller --config configs/profiling_spec.yaml
```

### What NOT to do on a shared server

- Do NOT run `pip install` or `conda install` in the base environment — use your own env
- Do NOT write output outside `$AGENTPROF_WORK_DIR`
- Do NOT start vLLM on a port already in use
- Do NOT leave zombie processes — always call `observer.detach()` and clean up
- Do NOT run `pytest` without `-x` flag on shared login nodes (use job scheduler)

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
10. Are zero forbidden optimization actions implemented?

## New Machine / New CC Agent Onboarding

See `docs/design/onboarding.md` for full setup steps.
Quick start prompt for a new CC session is at the bottom of that file.

