# AgentProf

A methodology-driven profiling controller for agent systems under workload.

**Current Stage: MVP-0 — Single Program Controlled Workload**

## What This Is

AgentProf is an external profiling controller that observes an agent system (Target Agent + LLM Backend + Tools) running under a given workload, and produces structured profiling reports following Gregg's Drill-Down Latency Analysis methodology.

AgentProf profiles. It does NOT optimize.

## Architecture

```
User workload
    ↓
Target Agent: LangChain/LangGraph ReAct agent
    ↓                  ↓
LLM call            Tool call
    ↓                  ↓
vLLM server       local tools/subprocess

AgentProf: external controller — callback / wrapper / client timing / metrics adapter
```

## Quick Start

```bash
# 1. Copy and fill environment variables
cp .env.example .env

# 2. Install dependencies
pip install -r requirements.lock.txt

# 3. Start vLLM backend (requires GPU server)
bash scripts/start_vllm.sh

# 4. Run controlled workload
bash scripts/run_controlled_workload.sh

# 5. View report
cat profiles/<run_id>/report.md
```

## Project Structure

```
configs/            # Profiling spec, target system, observer configs
agentprof/          # Core profiling controller
targets/            # Target agents (LangChain ReAct)
scripts/            # Startup and utility scripts
experiments/        # Experiment indexes, reports, figures
docs/               # Design docs, meeting notes, weekly reports
docker/             # Containerization
profiles/           # Experiment outputs (not in git for large runs)
```

## Current Milestone

- [x] Milestone 0: Repository skeleton and docs
- [ ] Milestone 1: Minimal event chain (events.jsonl)
- [ ] Milestone 2: Timeline + Report
- [ ] Milestone 3: AgentProf controller (LangChain tool-calling)
- [ ] Milestone 4: Multi-program workload
- [ ] Milestone 5: Real benchmark subset (BFCL V3)

## Docs

- [Design: AgentProf](docs/design/agentprof_design.md)
- [Project Status](PROJECT_STATUS.md)
- [Changelog](CHANGELOG.md)
- [Coding Agent Rules](AGENTS.md)
