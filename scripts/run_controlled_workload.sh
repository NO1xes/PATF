#!/usr/bin/env bash
# Run the controlled workload (MVP-0: slow/cpu/flaky tasks).
# Requires: conda env agentprof activated, .env filled.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

if [ ! -f ".env" ]; then
  echo "ERROR: .env not found. Copy .env.example to .env and fill in values."
  exit 1
fi

echo "[agentprof] Running controlled workload..."
python -m agentprof.controller \
  --profiling-spec configs/profiling_spec.yaml \
  --target-system configs/target_system.yaml \
  --observers configs/observers.yaml \
  --workload configs/workload_controlled.yaml
