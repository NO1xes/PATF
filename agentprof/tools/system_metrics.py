"""Layer 1 — Hardware/System profiling tools.

These tools are the first tier of the AgentProf tool hierarchy.  They rely
only on ``psutil`` and ``nvidia-smi`` (both black-box safe) and expose
tuneable granularity so the LLM can follow the coarse→fine drill-down path.

All functions return plain dicts so they can be serialised directly into the
LLM context.  Optional event emission to the AgentEvent stream is handled
by a ``SystemMetricsObserver`` (see ``agentprof/observers/backends/system/``).
"""

from __future__ import annotations

import subprocess
import time
from typing import Any

import psutil  # type: ignore[import-untyped]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_system_overview() -> dict[str, Any]:
    """One-shot snapshot of CPU, memory, disk, and network utilisation.

    Returns a dict with keys ``cpu``, ``memory``, ``disk``, ``network``.
    Designed as the first tool the LLM should call — cheap (< 0.1 s),
    no parameters, gives a coarse health picture.
    """
    cpu_pct = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()

    return {
        "cpu": {
            "util_pct": round(cpu_pct, 1),
            "core_count_logical": psutil.cpu_count(logical=True),
            "core_count_physical": psutil.cpu_count(logical=False),
        },
        "memory": {
            "total_gb": round(mem.total / (1024**3), 1),
            "used_gb": round(mem.used / (1024**3), 1),
            "available_gb": round(mem.available / (1024**3), 1),
            "util_pct": round(mem.percent, 1),
        },
        "disk": {
            "total_gb": round(disk.total / (1024**3), 1),
            "used_gb": round(disk.used / (1024**3), 1),
            "free_gb": round(disk.free / (1024**3), 1),
            "util_pct": round(disk.percent, 1),
        },
        "network": {
            "bytes_sent_mb": round(net.bytes_sent / (1024**2), 1),
            "bytes_recv_mb": round(net.bytes_recv / (1024**2), 1),
            "packets_sent": net.packets_sent,
            "packets_recv": net.packets_recv,
        },
    }


def get_process_tree(top_n: int = 10) -> dict[str, Any]:
    """Return the top-N processes sorted by CPU usage (descending).

    Args:
        top_n: Number of processes to return.  LLM can increase this to
               widen the search or decrease it for a quick scan.

    Returns a dict with ``processes`` (list of per-process dicts) and
    ``total_process_count``.
    """
    procs: list[dict[str, Any]] = []
    for proc in psutil.process_iter(
        ["pid", "name", "cpu_percent", "memory_percent", "cmdline"]
    ):
        try:
            info = proc.info
            cmdline = info.get("cmdline")
            procs.append(
                {
                    "pid": info["pid"],
                    "name": info["name"] or "?",
                    "cpu_pct": round(info["cpu_percent"] or 0.0, 1),
                    "mem_pct": round(info["memory_percent"] or 0.0, 1),
                    "cmdline": " ".join(cmdline) if cmdline else "",
                }
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    procs.sort(key=lambda p: p["cpu_pct"], reverse=True)
    return {"processes": procs[:top_n], "total_process_count": len(procs)}


def get_gpu_metrics() -> dict[str, Any]:
    """Query GPU utilisation, memory, and temperature via nvidia-smi.

    Returns a dict with ``gpus`` (list of per-GPU dicts) and ``error``
    if nvidia-smi is not available (e.g. CPU-only machine).

    This tool is black-box safe — it does not import CUDA libraries.
    """
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=index,name,utilization.gpu,memory.used,memory.total,"
                "temperature.gpu,power.draw,power.limit",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return {"gpus": [], "error": "nvidia-smi not available"}

    if result.returncode != 0:
        return {"gpus": [], "error": result.stderr.strip()}

    gpus: list[dict[str, Any]] = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 7:
            continue
        gpus.append(
            {
                "index": int(parts[0]),
                "name": parts[1],
                "gpu_util_pct": float(parts[2]) if parts[2] else 0.0,
                "mem_used_mb": float(parts[3]) if parts[3] else 0.0,
                "mem_total_mb": float(parts[4]) if parts[4] else 0.0,
                "mem_util_pct": round(
                    (float(parts[3]) / float(parts[4]) * 100) if parts[4] and float(parts[4]) > 0 else 0.0, 1
                ),
                "temp_c": float(parts[5]) if parts[5] else 0.0,
                "power_w": float(parts[6]) if parts[6] else 0.0,
                "power_limit_w": float(parts[7]) if len(parts) > 7 and parts[7] else 0.0,
            }
        )
    return {"gpus": gpus}


def sample_resources(duration_sec: float, interval_sec: float = 1.0) -> dict[str, Any]:
    """Sample CPU and memory over a time window at the given interval.

    Args:
        duration_sec: Total observation window in seconds.
        interval_sec: Sampling interval in seconds.  Smaller = finer
                      granularity but more data.  LLM should start coarse
                      (e.g. 5 s) and narrow down when it spots an anomaly.

    Returns a dict with ``samples`` (list of per-tick readings) and
    ``summary`` (min/max/mean over the window).
    """
    samples: list[dict[str, Any]] = []
    deadline = time.monotonic() + duration_sec
    while time.monotonic() < deadline:
        cpu = psutil.cpu_percent(interval=0.0)
        mem = psutil.virtual_memory()
        samples.append(
            {
                "ts": round(time.time(), 3),
                "cpu_pct": round(cpu, 1),
                "mem_pct": round(mem.percent, 1),
            }
        )
        time.sleep(interval_sec)

    cpu_vals = [s["cpu_pct"] for s in samples]
    mem_vals = [s["mem_pct"] for s in samples]
    return {
        "samples": samples,
        "summary": {
            "sample_count": len(samples),
            "duration_sec": duration_sec,
            "interval_sec": interval_sec,
            "cpu": {
                "min": round(min(cpu_vals), 1) if cpu_vals else 0.0,
                "max": round(max(cpu_vals), 1) if cpu_vals else 0.0,
                "mean": round(sum(cpu_vals) / len(cpu_vals), 1) if cpu_vals else 0.0,
            },
            "memory": {
                "min": round(min(mem_vals), 1) if mem_vals else 0.0,
                "max": round(max(mem_vals), 1) if mem_vals else 0.0,
                "mean": round(sum(mem_vals) / len(mem_vals), 1) if mem_vals else 0.0,
            },
        },
    }


# ---------------------------------------------------------------------------
# OpenAI function-calling tool definitions
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_system_overview",
            "description": (
                "Take a one-shot snapshot of CPU, memory, disk, and network "
                "utilisation.  Call this FIRST to get a coarse health picture "
                "of the system.  If you spot an anomaly (high CPU, low "
                "available memory, disk/network saturation), drill down with "
                "sample_resources() or get_process_tree()."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_process_tree",
            "description": (
                "Return the top-N processes sorted by CPU usage.  Use this "
                "to identify WHICH process is consuming resources — a drill-"
                "down step after get_system_overview() shows high CPU.  "
                "Increase top_n to widen the search."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "top_n": {
                        "type": "integer",
                        "description": "Number of processes to return (default 10).",
                        "default": 10,
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_gpu_metrics",
            "description": (
                "Query GPU utilisation, memory, and temperature via nvidia-smi.  "
                "Use this when the target system uses a GPU model server (vLLM).  "
                "Returns per-GPU stats.  Only call this after confirming the "
                "machine has GPUs (check machine_info in your context)."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sample_resources",
            "description": (
                "Sample CPU and memory over a time window at a configurable "
                "interval.  Use a COARSE interval (5-10 s) first to see the "
                "trend; if you spot a burst or anomaly, re-sample with a "
                "FINER interval (0.5-1 s) over a narrower window.  "
                "Do NOT start with fine-grained sampling — it wastes resources."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "duration_sec": {
                        "type": "number",
                        "description": "Total observation window in seconds.",
                    },
                    "interval_sec": {
                        "type": "number",
                        "description": "Sampling interval in seconds (default 1.0).",
                        "default": 1.0,
                    },
                },
                "required": ["duration_sec"],
            },
        },
    },
]

# Map tool name → callable for the ReAct loop dispatcher.
TOOL_DISPATCH = {
    "get_system_overview": get_system_overview,
    "get_process_tree": get_process_tree,
    "get_gpu_metrics": get_gpu_metrics,
    "sample_resources": sample_resources,
}
