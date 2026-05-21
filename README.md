# AgentProf

A methodology-driven profiling controller for agent systems under workload.

Current architecture: v0.4 — LLM planner + deterministic tools + validator
Current branch: `refactor/v0.4-architecture` (pending merge to main)

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
# 1. Clone
git clone git@github.com:NO1xes/AgentProf.git
cd AgentProf

# 2. Create conda environment (Python 3.11 recommended)
conda create -n agentprof python=3.11 -y
conda activate agentprof
pip install -e ".[dev]" -i https://pypi.tuna.tsinghua.edu.cn/simple  # China mainland

# 3. Copy and fill environment variables
cp .env.example .env
# Edit .env: set VLLM_BASE_URL to your vLLM server or remote API endpoint

# 4. Verify setup
bash scripts/verify_env.sh

# 5. Run controlled workload (requires LLM endpoint in .env)
bash scripts/run_controlled_workload.sh

# 6. View report
cat profiles/<run_id>/report.md
```

## Key Files to Read First

New to this repo? Read in this order:

1. This file (README.md) — overview
2. [AGENTS.md](AGENTS.md) — rules and constraints (especially if you're a coding agent)
3. [PROJECT_STATUS.md](PROJECT_STATUS.md) — what's done, what's next, what's blocked
4. [docs/design/onboarding.md](docs/design/onboarding.md) — full module map and maintenance guide
5. [TODO.md](TODO.md) — current task list by milestone

## Project Structure

```text
agentprof/          Core profiling controller (Python package)
  schema/           Data structures: AgentEvent, SpanRecord, ObservationPlan, EvidenceRecord
  model/            ExecutionModel (correlation graph), ObserverRegistry
  observers/        Collect raw data, emit AgentEvents
  analysis/         Deterministic computation: timeline, breakdown, resource_health, questions
  planner/          LLM-based ObservationPlan generation
  tools/            Deterministic tools callable by controller
  validator.py      Enforce forbidden actions and budget limits
  executor.py       Execute approved ObservationPlan
  storage.py        Read/write events.jsonl
  report/           Write report.md and summary.json
  controller.py     Orchestrate the full profiling loop
  state.py          ProfilingState — the mutable campaign state

targets/            Target agents (being profiled, not part of AgentProf)
configs/            All configuration files
scripts/            Startup and utility shell scripts
experiments/        Experiment index and archived reports
docs/               Design docs, weekly reports, meeting notes
profiles/           Per-run experiment outputs (large files not in git)
docker/             Containerization (future)
```

## Current Milestone

- [x] Milestone 0: Repository skeleton + v0.4 architecture refactor
- [ ] Milestone 1: Minimal event chain — observers + analysis → events.jsonl + breakdown
- [ ] Milestone 2: Timeline + Report
- [ ] Milestone 3: LLM Planner + full controller loop
- [ ] Milestone 4: Multi-program workload
- [ ] Milestone 5: Real benchmark subset (BFCL V3)

## Machines

| machine_id | Role | GPU | Config |
| --- | --- | --- | --- |
| local_pc_win11 | Dev + API experiments | None | `configs/machines/local_pc_win11.yaml` |
| (gpu_server) | vLLM backend | TBD | TBD |

See [ENVIRONMENT.md](ENVIRONMENT.md) for setup instructions per machine.
