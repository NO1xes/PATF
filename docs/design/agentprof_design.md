# AgentProf Design

## System Overview

AgentProf is an external profiling controller. It observes a running agent system and produces structured profiling reports. It does not modify the agent system's behavior.

```
┌─────────────────────────────────────────────────────────┐
│                    AgentProf Controller                  │
│  run_workload → build_timeline → gen_questions →        │
│  select_observer → (repeat) → export_report             │
└────────────────────┬────────────────────────────────────┘
                     │ observes via callbacks / wrappers / client timing
         ┌───────────▼──────────────────────────────┐
         │           Target Agent System             │
         │  LangChain ReAct Agent                    │
         │       ↓ LLM calls        ↓ tool calls     │
         │  vLLM OpenAI-compat   slow/cpu/flaky tools│
         └──────────────────────────────────────────┘
```

## Four Execution Layers

| Layer | What it covers | Default observer |
|---|---|---|
| Agent Semantic | run, step, llm_call, tool_call, retry, wait | semantic_langchain (LangChain callback) |
| LLM Serving | request, queue, prefill, decode, TTFT, TPOT | llm_client_timing (client-side timing) |
| Tool Execution | function, subprocess, API, error, duration | tool_wrapper |
| Hardware/Resource | CPU, GPU, memory, disk, network | resource_counters (deferred) |

Cross-layer correlation is via `run_id → span_id → parent_span_id` chain in every event.

## Profiling Loop (Drill-Down)

```
1. run_workload(program)
2. collect events → events.jsonl
3. build_timeline → breakdown by layer
4. generate_diagnostic_questions from breakdown
5. select_next_observer (rule-based policy)
6. if new observer selected: re-run or continue observation
7. export_report (report.md + summary.json)
```

Stop conditions: max_iterations reached, or no new observer selected.

## Event Schema

Every event is an `AgentEvent` (see `agentprof/schema.py`):

```json
{
  "event_type": "tool_call_end",
  "run_id": "run_20260514_001",
  "span_id": "uuid",
  "parent_span_id": "uuid",
  "timestamp_ns": 1747123456789000000,
  "layer": "tool_execution",
  "attributes": {
    "tool_name": "slow_tool",
    "duration_ms": 2003.1,
    "status": "success"
  }
}
```

## Output Files (per run)

```
profiles/<run_id>/
  metadata.yaml       # run config snapshot + git hash
  events.jsonl        # all normalized events
  timeline.csv        # per-span: start_ns, end_ns, duration_ms, layer, name
  summary.json        # layer breakdown: {layer: {total_ms, pct, dominant_span}}
  report.md           # structured profiling report
```

## MVP Constraints

- No optimization actions
- Single program per run (MVP-0)
- Rule-based observer selection (no LLM reasoning in controller)
- vLLM metrics observer deferred (requires GPU server)
