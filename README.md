# AgentProf

A methodology-driven profiling controller for agent systems under workload.

Current architecture: v0.1 — LLM planner + deterministic tools + validator
Active branch: `dev` (working branch for both contributors)

## What This Is

AgentProf is an external profiling controller. It observes a running agent system
(Target Agent + LLM Backend + Tools) and produces structured profiling reports
following Gregg's Drill-Down Latency Analysis methodology.

**AgentProf profiles. It does NOT optimize.**

## Architecture

```text
workload task
      ↓
Target Agent (LangChain/LangGraph ReAct)
      ↓ LLM calls          ↓ tool calls
vLLM server (Qwen3-30B-A3B)   slow/cpu/flaky tools
      │                         │
      └──── AgentProf observes via callbacks / wrappers / client timing
                  ↓
            events.jsonl
                  ↓
         analysis/ (timeline, breakdown, resource_health, questions)
                  ↓
         planner/ (LLM generates ObservationPlan)
                  ↓
         validator → executor
                  ↓
         report.md + known_unknowns.md
```

The three components are strictly separate:

| Component | What it is | Where |
| --- | --- | --- |
| Target Agent | Agent being profiled | `targets/langchain_react_agent/` |
| LLM Backend | vLLM server (GPU server only) | `scripts/start_vllm.sh` |
| AgentProf | External profiling controller | `agentprof/` |

## Quick Start

```bash
# 1. Clone and switch to working branch
git clone git@github.com:NO1xes/PATF.git   # SSH
# or: git clone https://github.com/NO1xes/PATF.git  # HTTPS on shared servers
cd PATF
git checkout dev

# 2. Create conda environment (Python 3.11)
conda create -n agentprof python=3.11 -y
conda activate agentprof
pip install -e ".[dev]"
# China mainland: add -i https://pypi.tuna.tsinghua.edu.cn/simple

# 3. Copy and fill environment variables
cp .env.example .env
# Edit .env: set VLLM_BASE_URL, VLLM_MODEL, AGENTPROF_MACHINE, etc.
# On shared servers, also set GITHUB_USER/GITHUB_PAT and use scripts/git_push_with_env_pat.sh.

# 4. Install pre-commit hook (one-time, optional but recommended)
bash scripts/install_hooks.sh

# 5. Verify setup (no GPU needed)
pytest tests/ -x -q   # 70 tests should pass

# 6. Run controlled workload (requires LLM endpoint in .env)
bash scripts/run_controlled_workload.sh

# 7. View report
cat profiles/<run_id>/report.md
```

## Key Files to Read First

New to this repo? Read in this order:

1. This file (README.md) — overview
2. [AGENTS.md](AGENTS.md) — rules, constraints, ownership tiers, shared server limits
3. [PROJECT_STATUS.md](PROJECT_STATUS.md) — what's done, what's next, what's blocked
4. [COLLAB.md](COLLAB.md) — collaboration workflow, branch commands, experiment operations (Chinese)
5. [docs/design/onboarding.md](docs/design/onboarding.md) — full module map and maintenance guide
6. [docs/design/collaboration.md](docs/design/collaboration.md) — formal collaboration spec (English, for CC)

## Project Structure

```text
agentprof/                Core profiling controller (Python package)
  schema/                 FROZEN — AgentEvent, SpanRecord, ObservationPlan, EvidenceRecord
  model/                  FROZEN — ExecutionModel, ObserverRegistry
  validator.py            FROZEN — forbidden action enforcement
  storage.py              FROZEN — read/write events.jsonl
  state.py                FROZEN — ProfilingState
  observers/
    base.py               FROZEN — BaseObserver ABC
    backends/langchain/   Current observer implementations (LangChain)
    __init__.py           Factory: get_observer(), get_all_baseline_observers()
  planner/
    base.py               FROZEN — BasePlanner ABC
    backends/llm/         LLM-based planner (default, Milestone 3)
    backends/rule/        Rule-based planner (ablation baseline, Milestone 2)
    __init__.py           Factory: get_planner()
  analysis/               Deterministic computation: timeline, breakdown, resource_health, questions
  tools/                  Deterministic tools callable by controller
  adapters/               External benchmark adapters (BFCL workload conversion)
  executor.py             Execute approved ObservationPlan
  report/                 Write report.md and summary.json
  controller.py           Orchestrate the full profiling loop

targets/                  Target agents (profiled, not part of AgentProf)
  langchain_react_agent/  LangChain ReAct agent with slow/cpu/flaky tools

configs/                  All configuration files
  backends.yaml           Backend selection (observer_backend, planner_backend)
  profiling_spec.yaml     Profiling campaign spec + forbidden_actions
  observers.yaml          Observer capability registry
  machines/               Per-machine environment configs

baselines/                Comparison baselines for experiments
  langfuse_adapter/       Wrap Langfuse output → AgentEvent format
  opentelemetry_adapter/  Wrap OTel spans → AgentEvent format
  rule_based_profiler/    Standalone rule-based profiler (ablation)

experiments/              Experiment management
  designs/                Architecture Decision Records (ADRs)
  comparisons/            Per-experiment configs, results, conclusions
  reports/                Archived report.md and summary.json
  runs/                   Run metadata index

scripts/                  Startup and utility shell scripts
docs/                     Design docs, weekly reports, meeting notes
profiles/                 Per-run outputs (large files not in git)
docker/                   Containerization (future)
```

## Current Milestone

- [x] Milestone 0: Repository skeleton + v0.4 architecture refactor
- [x] Milestone 1: Observers + analysis implemented (38 tests, no LLM/GPU required)
- [x] Milestone 2: resource_health, questions, run_workload, end-to-end smoke test
- [x] Milestone 3: LLM Planner + full controller loop — smoke test PASSED (nusa100, 2026-05-23)
- [x] Milestone 4: Multi-program aggregation + report quality (70 tests)
- [ ] Milestone 5: Real benchmark subset (BFCL V3; adapter implemented, demo run pending)

## Collaboration

This is a two-contributor research project. See [COLLAB.md](COLLAB.md) for the full workflow.

Key points:

- Work on `dev` branch; open PRs to `dev`, not `main`
- `feat/NO1xes-<name>` and `feat/collab-<name>` for feature branches
- `exp/<name>` for experimental / alternative design branches
- `public` branch is the GitHub default (repo landing page only) — **do not use for development**
- Switching backends: set `AGENTPROF_BACKEND` / `AGENTPROF_PLANNER` in `.env`
- Design disagreements: write an ADR in `experiments/designs/`

## Machines

| machine_id | Role | GPU | Config |
| --- | --- | --- | --- |
| local_pc_win11 | Dev + API experiments | None | `configs/machines/local_pc_win11.yaml` |
| nusa100 | LangChain tests, vLLM backend | 5× A100-SXM4-80GB | `configs/machines/nusa100.yaml` |

See [ENVIRONMENT.md](ENVIRONMENT.md) for per-machine setup instructions.

## License

MIT License — see [LICENSE](LICENSE).
