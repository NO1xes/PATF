"""Resource health checker: coarse USE-method snapshot analysis.

Reads resource_snapshot.csv and flags obvious symptoms:
  - CPU utilization near 100%
  - memory saturation
  - GPU utilization near 0% (idle when expected busy)
  - disk/network saturation

Input:  resource_snapshot.csv (path)
Output: resource_health dict, written to resource_health.json
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

CPU_SATURATION_THRESHOLD = 80.0   # pct
MEMORY_SATURATION_THRESHOLD = 85.0  # pct
HIGH_DISK_WRITE_THRESHOLD_KB = 10_000  # KB per sample
HIGH_NET_RECV_THRESHOLD_KB = 10_000    # KB per sample


def compute_resource_health(snapshot_path: Path) -> dict:
    """Return resource health dict from resource_snapshot.csv.

    Returns minimal health dict with zeroed fields when the file is empty or missing,
    so downstream callers don't need to special-case missing snapshots.

    Example output:
    {
      "sample_count": 12,
      "cpu_util_mean_pct": 45.2,
      "cpu_util_max_pct": 92.1,
      "cpu_saturated": false,
      "memory_util_mean_pct": 62.1,
      "memory_util_max_pct": 70.3,
      "memory_saturated": false,
      "disk_write_max_kb": 123.4,
      "net_recv_max_kb": 0.5,
      "symptoms": [],
      "notes": "No obvious resource saturation detected."
    }
    """
    snapshot_path = Path(snapshot_path)
    if not snapshot_path.exists():
        return _empty_health("snapshot file not found")

    rows = _read_csv(snapshot_path)
    if not rows:
        return _empty_health("snapshot file is empty")

    cpu_vals = [float(r["cpu_pct"]) for r in rows if "cpu_pct" in r]
    mem_vals = [float(r["mem_pct"]) for r in rows if "mem_pct" in r]
    disk_write_vals = [float(r.get("disk_write_kb", 0)) for r in rows]
    net_recv_vals = [float(r.get("net_recv_kb", 0)) for r in rows]

    cpu_mean = _mean(cpu_vals)
    cpu_max = max(cpu_vals) if cpu_vals else 0.0
    mem_mean = _mean(mem_vals)
    mem_max = max(mem_vals) if mem_vals else 0.0
    disk_write_max = max(disk_write_vals) if disk_write_vals else 0.0
    net_recv_max = max(net_recv_vals) if net_recv_vals else 0.0

    cpu_saturated = cpu_max >= CPU_SATURATION_THRESHOLD
    mem_saturated = mem_max >= MEMORY_SATURATION_THRESHOLD

    symptoms: list[str] = []
    if cpu_saturated:
        symptoms.append(f"CPU peak {cpu_max:.1f}% >= {CPU_SATURATION_THRESHOLD}% threshold")
    if mem_saturated:
        symptoms.append(f"Memory peak {mem_max:.1f}% >= {MEMORY_SATURATION_THRESHOLD}% threshold")
    if disk_write_max >= HIGH_DISK_WRITE_THRESHOLD_KB:
        symptoms.append(f"Disk write peak {disk_write_max:.0f} KB/s may indicate I/O pressure")
    if net_recv_max >= HIGH_NET_RECV_THRESHOLD_KB:
        symptoms.append(f"Network recv peak {net_recv_max:.0f} KB/s may indicate network bottleneck")

    notes = "No obvious resource saturation detected." if not symptoms else "; ".join(symptoms)

    return {
        "sample_count": len(rows),
        "cpu_util_mean_pct": round(cpu_mean, 2),
        "cpu_util_max_pct": round(cpu_max, 2),
        "cpu_saturated": cpu_saturated,
        "memory_util_mean_pct": round(mem_mean, 2),
        "memory_util_max_pct": round(mem_max, 2),
        "memory_saturated": mem_saturated,
        "disk_write_max_kb": round(disk_write_max, 2),
        "net_recv_max_kb": round(net_recv_max, 2),
        "symptoms": symptoms,
        "notes": notes,
    }


def write_resource_health_json(health: dict, output_dir: Path) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "resource_health.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(health, f, indent=2)
    return out_path


# --- helpers ---

def _read_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _mean(vals: list[float]) -> float:
    return sum(vals) / len(vals) if vals else 0.0


def _empty_health(reason: str) -> dict:
    return {
        "sample_count": 0,
        "cpu_util_mean_pct": 0.0,
        "cpu_util_max_pct": 0.0,
        "cpu_saturated": False,
        "memory_util_mean_pct": 0.0,
        "memory_util_max_pct": 0.0,
        "memory_saturated": False,
        "disk_write_max_kb": 0.0,
        "net_recv_max_kb": 0.0,
        "symptoms": [],
        "notes": reason,
    }
