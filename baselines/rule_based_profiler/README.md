# Rule-Based Profiler (baseline b — ablation)

Standalone rule-based profiler that runs without the LLM planner.
Used to answer: "Does the LLM planner actually improve over simple rules?"

## Status: stub (Milestone 2 target)

## Design

Decision rules (same logic as `agentprof/planner/backends/rule/rule_planner.py`):
- tool_pct > 0.5  → activate tool_process observer
- llm_pct > 0.5   → activate vllm_metrics observer (if available)
- otherwise       → activate resource_snapshot only

## How to run (once implemented)

```bash
# Run with rule-based planner
AGENTPROF_PLANNER=rule python -m agentprof.runner \
  --config configs/profiling_spec.yaml

# Or use the standalone script
python -m baselines.rule_based_profiler.run \
  --events profiles/<run_id>/events.jsonl \
  --output profiles/<run_id>/rule_report.md
```
