"""Resource health checker: coarse USE-method snapshot analysis.

Reads resource_snapshot.csv and flags obvious symptoms:
  - CPU utilization near 100%
  - memory saturation
  - GPU utilization near 0% (idle when expected busy)
  - disk/network saturation
  - vLLM queue depth > threshold

This runs early (alongside baseline trace), not as a last resort.
It gives health signals only — not root cause attribution.

Input:  resource_snapshot.csv (path)
Output: resource_health dict, written to resource_health.json
"""

from __future__ import annotations

import json
from pathlib import Path


def compute_resource_health(snapshot_path: Path) -> dict:
    """Return resource health dict.

    Example output:
    {
      "cpu_util_pct": 45.2,
      "cpu_saturated": false,
      "memory_util_pct": 62.1,
      "memory_saturated": false,
      "gpu_util_pct": null,   # null if no GPU
      "symptoms": [],
      "notes": "No obvious resource saturation detected."
    }
    """
    raise NotImplementedError("Milestone 1")


def write_resource_health_json(health: dict, output_dir: Path) -> Path:
    raise NotImplementedError("Milestone 1")
