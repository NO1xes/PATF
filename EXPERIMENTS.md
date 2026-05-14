# Experiments Index

Each row is one profiling run. Large output files stay local; only `report.md` and `summary.json` go into git under `experiments/reports/`.

| run_id | date | machine | workload | observers | key finding | report |
|--------|------|---------|----------|-----------|-------------|--------|
| _(none yet)_ | | | | | | |

## How to Register a Run

After each experiment, add a row above and copy key files:

```bash
cp profiles/<run_id>/report.md experiments/reports/<run_id>_report.md
cp profiles/<run_id>/summary.json experiments/reports/<run_id>_summary.json
```

Then commit `experiments/reports/` and update this table.

## Run Directory Structure

```
profiles/<run_id>/
  metadata.yaml       # run_id, date, machine, config snapshot ref, git commit hash
  config_snapshot/    # frozen copy of configs used
  events.jsonl        # normalized event log (may be large — check .gitignore)
  timeline.csv        # per-span timeline
  summary.json        # layer-wise breakdown
  report.md           # structured profiling report
  logs/               # raw observer logs
  artifacts/          # figures, extra outputs
```
