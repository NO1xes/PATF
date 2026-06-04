"""Layer 2 — LLM Serving profiling tools.

Query the vLLM Prometheus metrics endpoint (or any OpenAI-compatible
server that exposes Prometheus-format metrics).  These tools are
grey-box: they need the metrics endpoint URL but do not require
code-level instrumentation of the target system.
"""

from __future__ import annotations

import time
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


def _fetch_prometheus_metrics(url: str, timeout: float = 5.0) -> str | None:
    """Fetch raw Prometheus text from *url*.  Returns None on failure."""
    try:
        req = Request(url, headers={"Accept": "text/plain"})
        with urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8")
    except (URLError, OSError, ValueError):
        return None


def _parse_prometheus_value(text: str, metric_name: str) -> float | None:
    """Extract the first numeric value for *metric_name* from Prometheus text.

    Prometheus lines are formatted as:
        metric_name{labels} value timestamp
        metric_name value timestamp
    """
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#"):
            continue
        if line.startswith(metric_name):
            parts = line.split()
            if len(parts) >= 2:
                try:
                    return float(parts[1])
                except ValueError:
                    continue
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_vllm_metrics(
    metrics_url: str = "http://localhost:18796/metrics",
    metrics: list[str] | None = None,
) -> dict[str, Any]:
    """Query a vLLM Prometheus metrics endpoint for key serving metrics.

    Args:
        metrics_url: Full URL to the Prometheus /metrics endpoint.
        metrics: Which metric groups to return.  Defaults to all.
            Options: ``"queue"``, ``"throughput"``, ``"cache"``, ``"latency"``.

    Returns a dict with the requested metric groups.  If the endpoint is
    unreachable, the ``error`` key explains why and all metric values are
    ``null``.
    """
    if metrics is None:
        metrics = ["queue", "throughput", "cache", "latency"]

    raw = _fetch_prometheus_metrics(metrics_url)
    if raw is None:
        return {"metrics_url": metrics_url, "error": "vLLM metrics endpoint unreachable"}

    result: dict[str, Any] = {"metrics_url": metrics_url}

    if "queue" in metrics:
        result["queue"] = {
            "running_requests": _parse_prometheus_value(
                raw, "vllm:num_requests_running"
            ),
            "waiting_requests": _parse_prometheus_value(
                raw, "vllm:num_requests_waiting"
            ),
            "swapped_requests": _parse_prometheus_value(
                raw, "vllm:num_requests_swapped"
            ),
        }
    if "throughput" in metrics:
        result["throughput"] = {
            "prompt_tokens_total": _parse_prometheus_value(
                raw, "vllm:prompt_tokens_total"
            ),
            "generation_tokens_total": _parse_prometheus_value(
                raw, "vllm:generation_tokens_total"
            ),
        }
    if "cache" in metrics:
        gpu_cache = _parse_prometheus_value(
            raw, "vllm:gpu_cache_usage_perc"
        )
        cpu_cache = None
        if gpu_cache is None:
            cpu_cache = _parse_prometheus_value(
                raw, "vllm:cpu_cache_usage_perc"
            )
        result["cache"] = {
            "gpu_cache_usage_pct": gpu_cache,
            "cpu_cache_usage_pct": cpu_cache,
        }
    if "latency" in metrics:
        result["latency"] = {
            "time_to_first_token_avg": _parse_prometheus_value(
                raw, "vllm:time_to_first_token_seconds_sum"
            ),
            "time_per_output_token_avg": _parse_prometheus_value(
                raw, "vllm:time_per_output_token_seconds_sum"
            ),
            "e2e_request_latency_avg": _parse_prometheus_value(
                raw, "vllm:e2e_request_latency_seconds_sum"
            ),
        }

    return result


def sample_vllm_metrics(
    duration_sec: float,
    interval_sec: float = 5.0,
    metrics_url: str = "http://localhost:18796/metrics",
    metrics: list[str] | None = None,
) -> dict[str, Any]:
    """Sample vLLM metrics over a time window.

    Args:
        duration_sec: Total observation window in seconds.
        interval_sec: Sampling interval.  Start coarse (5-10s), narrow
                      down if you spot queue buildup.
        metrics_url: vLLM Prometheus endpoint.
        metrics: Metric groups to collect.

    Returns ``samples`` (list of per-tick readings) and ``summary``.
    """
    if metrics is None:
        metrics = ["queue", "throughput"]

    samples: list[dict[str, Any]] = []
    deadline = time.monotonic() + duration_sec
    while time.monotonic() < deadline:
        snapshot = get_vllm_metrics(metrics_url=metrics_url, metrics=metrics)
        snapshot["ts"] = round(time.time(), 3)
        samples.append(snapshot)
        time.sleep(interval_sec)

    return {
        "samples": samples,
        "summary": {
            "sample_count": len(samples),
            "duration_sec": duration_sec,
            "interval_sec": interval_sec,
            "endpoint_reachable": "error" not in (samples[0] if samples else {}),
        },
    }


# ---------------------------------------------------------------------------
# OpenAI function-calling tool definitions
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_vllm_metrics",
            "description": (
                "Query the vLLM model server's Prometheus metrics endpoint.  "
                "Returns queue depth (running/waiting/swapped requests), "
                "token throughput, KV-cache usage, and latency.  "
                "Use this after get_system_overview() shows high GPU usage "
                "or when you suspect the LLM serving layer is the bottleneck.  "
                "If the endpoint is unreachable, the tool returns an error — "
                "this means either vLLM is not running locally or the metrics "
                "port is wrong.  Do NOT retry more than once."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "metrics_url": {
                        "type": "string",
                        "description": "Prometheus metrics endpoint URL (default http://localhost:18796/metrics).",
                        "default": "http://localhost:18796/metrics",
                    },
                    "metrics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Metric groups: queue, throughput, cache, latency. Default all.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sample_vllm_metrics",
            "description": (
                "Sample vLLM metrics over a time window.  Use a COARSE "
                "interval (5-10s) first to see trends; narrow down if you "
                "spot queue buildup or latency spikes."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "duration_sec": {
                        "type": "number",
                        "description": "Observation window in seconds.",
                    },
                    "interval_sec": {
                        "type": "number",
                        "description": "Sampling interval (default 5.0).",
                        "default": 5.0,
                    },
                    "metrics_url": {
                        "type": "string",
                        "description": "Prometheus endpoint URL.",
                        "default": "http://localhost:18796/metrics",
                    },
                },
                "required": ["duration_sec"],
            },
        },
    },
]

TOOL_DISPATCH = {
    "get_vllm_metrics": get_vllm_metrics,
    "sample_vllm_metrics": sample_vllm_metrics,
}
