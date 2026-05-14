# AgentProf Coding Rules

## Project Goal

Build a methodology-driven profiling controller for agent systems under workload.

**Current stage: profiling only. No optimization.**

## Architecture

```
Target Agent    = LangChain/LangGraph ReAct single agent
LLM Backend     = vLLM OpenAI-compatible server
AgentProf       = external profiling controller
```

These three components must remain separate. Do NOT merge AgentProf logic into the Target Agent.

## Forbidden

- Do NOT implement: `change_concurrency`, `change_arrival_rate`, `toggle_cache`, `set_retry_cap`, `set_resource_quota`
- Do NOT delete files under `profiles/` (historical experiment results)
- Do NOT commit: `.env`, API keys, model weights (`.pt`, `.safetensors`), large logs, large JSONL files
- Do NOT hardcode machine paths like `/root/xxx`, `localhost:8000` — read from config or env vars
- Do NOT change the research goal or profiling methodology

## Required

- After any code change: update `CHANGELOG.md`
- After any task status change: update `PROJECT_STATUS.md`
- Every new experiment run must generate `profiles/<run_id>/metadata.yaml`
- All output must go to `profiles/<run_id>/` (events.jsonl, timeline.csv, summary.json, report.md)
- All paths must be configurable via `configs/` or `.env`

## Allowed Actions (MVP)

```python
ALLOWED_ACTIONS_MVP = {
    "run_workload",
    "build_timeline",
    "generate_diagnostic_questions",
    "select_next_observer",
    "export_report",
}
```

## Output Schema

Every profiling run must produce:
1. `events.jsonl` — normalized event log
2. `timeline.csv` — per-span timeline
3. `summary.json` — layer-wise breakdown
4. `report.md` — structured profiling report

## Task Format

When assigning tasks to coding agents, use this format:

```
Task: <specific module>
Input: <what it reads>
Output: <what it produces>
Constraints: <what not to touch>
Acceptance: <test command and expected output> + must update CHANGELOG.md
```
