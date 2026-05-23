# Langfuse Adapter (baseline a)

Wraps a Langfuse project's trace export into AgentProf's `AgentEvent` format,
enabling direct comparison of trace coverage and attribution quality.

## Status: stub (not yet implemented)

## How to use (once implemented)

```bash
# Export traces from Langfuse
python -m baselines.langfuse_adapter.export \
  --project <project_id> \
  --run_id <run_id> \
  --output profiles/<run_id>/langfuse_events.jsonl

# Compare against AgentProf events
python -m agentprof.compare \
  --agentprof profiles/<run_id>/events.jsonl \
  --baseline  profiles/<run_id>/langfuse_events.jsonl
```

## What it covers

Langfuse provides: span names, durations, LLM token counts, tool names.
It does NOT provide: hardware resource metrics, cross-layer correlation.
This gap is part of what AgentProf addresses.
