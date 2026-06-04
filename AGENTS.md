# AgentProf Coding Rules — v2

## Project Goal

Build a methodology-driven profiling controller for agent systems under workload.

**Current stage: profiling only. No optimization.**

## Architecture (v2 — ReAct Tool-Calling Loop)

```text
Target Agent System = Docker/native processes (ALREADY RUNNING — AgentProf does not control)
LLM Backend         = vLLM or remote API (OpenAI-compatible)
AgentProf           = LLM ReAct agent + four-tier profiling tools
```

AgentProf observes the target system from the same host, outside Docker.
LLM calls profiling tools (L1→L4) in a coarse→fine drill-down pattern.

## Core Design Principle

```text
LLM (ReAct)   → decides WHAT to observe, at WHAT granularity, for HOW LONG
Python tools  → execute the observation (psutil, nvidia-smi, Prometheus, events)
System prompt → conveys 4-tier hierarchy, methodology, resource efficiency rules
Validator     → enforces constraints (forbidden actions, budget)
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
- Do NOT put PATs or other secrets in git remote URLs, shell history, docs, commits, or chat.
- On shared machines where SSH is unavailable, use `scripts/git_push_with_env_pat.sh`;
  it reads `GITHUB_USER`/`GITHUB_PAT` from `.env` without printing them.

## Required

After every code change, update these files before committing:

| File | When to update |
| --- | --- |
| `CHANGELOG.md` | Every code change — append one entry |
| `PROJECT_STATUS.md` | Module status changes (implemented / stub / frozen) |
| `TODO.md` | Task completed (check box), new task added, milestone status changes |
| `README.md` | Milestone completed or uncompleted; test count changes; new machine added |
| `agentprof/README.md` | Module implementation status changes (stub → implemented) |
| `EXPERIMENTS.md` | Every `run_profiling()` call that produces a report — add one row |

After every new experiment run:
- Add a row to `EXPERIMENTS.md` (run_id, date, machine, planner, workload, key finding)
- Optionally copy `report.md` + `summary.json` to `experiments/reports/`

Sub-directory `README.md` files (`targets/README.md`, `baselines/README.md`, etc.):
update when that directory's interface, role, or implementation status changes.

`AGENTS.md` itself: update only when constraints or module ownership changes.

- All output to `profiles/<run_id>/`: events.jsonl, timeline.csv, breakdown.json,
  resource_snapshot.csv, resource_health.json, report.md, summary.json
- All paths must be configurable via `configs/` or `.env`

## Module Responsibilities

| Module | Responsibility | Ownership tier |
| --- | --- | --- |
| `agentprof/schema/` | Data structures (AgentEvent, SpanRecord, ObservationPlan, EvidenceRecord) | FROZEN |
| `agentprof/model/` | ExecutionModel (correlation graph), ObserverRegistry | FROZEN |
| `agentprof/validator.py` | Enforce forbidden actions and budget | FROZEN |
| `agentprof/storage.py` | Read/write events.jsonl | FROZEN |
| `agentprof/state.py` | ProfilingState | FROZEN |
| `agentprof/observers/base.py` | BaseObserver ABC | FROZEN |
| `agentprof/observers/backends/<name>/` | Concrete observer implementations | Contributor-owned |
| `agentprof/observers/__init__.py` | Factory: `get_observer()`, `get_all_baseline_observers()` | Interface-stable |
| `agentprof/planner/base.py` | BasePlanner ABC | FROZEN |
| `agentprof/planner/backends/llm/` | LLM-based planner | Contributor-owned |
| `agentprof/planner/backends/rule/` | Rule-based planner (ablation) | Contributor-owned |
| `agentprof/planner/__init__.py` | Factory: `get_planner()` | Interface-stable |
| `agentprof/analysis/` | Deterministic computation: timeline, breakdown, resource_health, questions | Shared |
| `agentprof/tools/system_metrics.py` | L1 — psutil + nvidia-smi hardware tools | Shared |
| `agentprof/tools/llm_serving_metrics.py` | L2 — vLLM Prometheus query tools | Shared |
| `agentprof/tools/tool_execution_metrics.py` | L3 — span/event inspection tools | Shared |
| `agentprof/tools/agent_semantic_metrics.py` | L4 — agent loop trace tools | Shared |
| `agentprof/tools/run_workload_tool.py` | Legacy baseline runner | Shared |
| `agentprof/executor.py` | Legacy executor (v0.4) | Shared |
| `agentprof/report/` | Write report.md and summary.json | Shared |
| `agentprof/controller.py` | Legacy linear pipeline (v0.4) | Shared |
| `agentprof/controller_v2.py` | ReAct tool-calling loop (v2) | Shared |
| `baselines/` | Comparison baselines (Langfuse, OTel, rule-based) | Contributor-owned |
| `experiments/designs/` | Architecture Decision Records | Both contributors |
| `experiments/comparisons/` | Comparison experiment configs and results | Both contributors |

**Ownership tiers explained:**

- **FROZEN**: Interface changes require both contributors to agree + write an ADR
- **Interface-stable**: Function signatures fixed; add backends freely, don't break existing callers
- **Contributor-owned**: Owner decides; other contributor reviews but does not block
- **Shared**: PR to `dev`; one approve required

See `docs/design/collaboration.md` for full collaboration rules.

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
2. Does AgentProf NOT control/start/stop the target workload?
3. Are forbidden actions enforced (validator + system prompt)?
4. Does the system prompt convey the 4-tier tool hierarchy?
5. Are all tool parameters exposed to the LLM (granularity, scope, duration)?
6. Do L3/L4 tools gracefully degrade when events.jsonl is unavailable?
7. Are profiling overhead metrics recorded?
8. Does `report.md` include drill-down path evidence chain?
9. Are zero forbidden optimization actions implemented?
10. Does `docs/design/agentprof_design.md` reflect the current architecture?

## New Machine / New CC Agent Onboarding

See `docs/design/onboarding.md` for full setup steps.
Quick start prompt for a new CC session is at the bottom of that file.
