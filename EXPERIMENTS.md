# Experiments Index

Each row is one completed profiling run. Large output files stay local (gitignored);
key result files may be copied to `experiments/reports/` for record-keeping.

| run_id | date | machine | planner | workload | key finding |
|--------|------|---------|---------|----------|-------------|
| run_c9ef5986 | 2026-05-23 | nusa100 | rule | controlled (slow/cpu/flaky) | tool 65% / llm 35%; 6 calls, 2 errors (flaky); report.md correct |
| run_fd052729 | 2026-05-23 | nusa100 | llm (Qwen3-30B-A3B-Instruct-2507) | controlled (slow/cpu/flaky) | LLM generated 2 valid ObservationPlans; tool_events+tool_process selected; consistent with rule baseline |

## How to Register a Run

After each experiment, add a row to the table above. CC should do this automatically
after any `run_profiling()` call that produces a report.

Optionally copy key files for git record:

```bash
cp profiles/<run_id>/report.md experiments/reports/<run_id>_report.md
cp profiles/<run_id>/summary.json experiments/reports/<run_id>_summary.json
git add experiments/reports/ EXPERIMENTS.md
git commit -m "exp: register run_<id>"
```

## Run Directory Structure

```
profiles/<run_id>/
  events.jsonl        # normalized event log (gitignored)
  timeline.csv        # per-span timeline (gitignored via profiles/)
  breakdown.json      # layer-wise time split (gitignored)
  resource_snapshot.csv / resource_health.json  (gitignored)
  summary.json        # structured summary
  report.md           # structured profiling report
```

Note: `profiles/` is fully gitignored. Results are preserved only if explicitly
copied to `experiments/reports/`.
