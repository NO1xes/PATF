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
    # Use only leaf-level spans to avoid double-counting parent wrappers.
    # A span is a leaf if no other span has it as parent_span_id.
    parent_ids = {s.parent_span_id for s in spans if s.parent_span_id}
    leaf_spans = [s for s in spans if s.span_id not in parent_ids]

    llm_ms = sum(s.duration_ms for s in leaf_spans if s.span_kind == "LLM")
    tool_ms = sum(s.duration_ms for s in leaf_spans if s.span_kind == "TOOL")
    wait_ms = sum(s.duration_ms for s in leaf_spans if s.span_kind == "WAIT")
    unknown_ms = sum(s.duration_ms for s in leaf_spans if s.span_kind == "UNKNOWN")
    total_ms = llm_ms + tool_ms + wait_ms + unknown_ms

    def pct(v: float) -> float:
        return round(v / total_ms, 4) if total_ms > 0 else 0.0

    components = {"llm": llm_ms, "tool": tool_ms, "wait_retry": wait_ms, "unknown": unknown_ms}
    dominant = max(components, key=lambda k: components[k])
    if total_ms > 0 and components[dominant] / total_ms < DOMINANCE_THRESHOLD:
        dominant = "none"

    return {
        "total_ms": round(total_ms, 3),
        "llm_ms": round(llm_ms, 3),
        "llm_pct": pct(llm_ms),
        "tool_ms": round(tool_ms, 3),
        "tool_pct": pct(tool_ms),
        "wait_retry_ms": round(wait_ms, 3),
        "wait_retry_pct": pct(wait_ms),
        "unknown_ms": round(unknown_ms, 3),
        "unknown_pct": pct(unknown_ms),
        "llm_calls": sum(1 for s in spans if s.span_kind == "LLM" and s.span_id not in parent_ids),
        "tool_calls": sum(1 for s in spans if s.span_kind == "TOOL" and s.span_id not in parent_ids),
        "errors": sum(1 for s in spans if s.error),
        "dominant_component": dominant,
    }


def write_breakdown_json(breakdown: dict, output_dir: Path) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "breakdown.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(breakdown, f, indent=2)
    return out_path
