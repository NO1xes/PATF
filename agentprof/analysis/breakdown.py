"""Breakdown calculator: time division by layer.

Takes SpanRecords and computes total time split into:
  llm_time, tool_time, wait_retry_time, unknown_time

For multi-program workloads, also computes system aggregation.

Input:  list[SpanRecord]
Output: breakdown dict, written to breakdown.json
"""

from __future__ import annotations

import json
from pathlib import Path

from agentprof.schema.spans import SpanRecord

DOMINANCE_THRESHOLD = 0.5


def compute_breakdown(spans: list[SpanRecord]) -> dict:
    """Return time division dict.

    Example output:
    {
      "total_ms": 10000,
      "llm_ms": 3200, "llm_pct": 0.32,
      "tool_ms": 5800, "tool_pct": 0.58,
      "wait_retry_ms": 500, "wait_retry_pct": 0.05,
      "unknown_ms": 500, "unknown_pct": 0.05,
      "llm_calls": 2, "tool_calls": 3, "errors": 1,
      "dominant_component": "tool"
    }
    """
    raise NotImplementedError("Milestone 1")


def write_breakdown_json(breakdown: dict, output_dir: Path) -> Path:
    raise NotImplementedError("Milestone 1")
