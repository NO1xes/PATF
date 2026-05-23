"""Timeline builder: converts raw AgentEvents into SpanRecords.

Pairs start/end events by span_id, computes duration, identifies
wait/retry/error/unknown spans.

Input:  events.jsonl (path)
Output: list[SpanRecord], written to timeline.csv
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from agentprof.schema.events import AgentEvent
from agentprof.schema.spans import SpanRecord


_NAME_KIND_MAP = {
    "run": "AGENT",
    "llm_call": "LLM",
    "llm_request": "LLM",
    "tool_call": "TOOL",
}

_LAYER_KIND_MAP = {
    "agent_semantic": "AGENT",
    "llm_serving": "LLM",
    "tool_execution": "TOOL",
    "hardware_resource": "UNKNOWN",
}


def _infer_kind(name: str, layer: str) -> str:
    return _NAME_KIND_MAP.get(name) or _LAYER_KIND_MAP.get(layer, "UNKNOWN")


def build_timeline(events_path: Path, output_dir: Path) -> list[SpanRecord]:
    """Parse events.jsonl and produce SpanRecords + timeline.csv.

    Returns the list of closed SpanRecords.
    """
    from agentprof.storage import read_events

    events = read_events(events_path)

    # Group by span_id, collect start and end events
    starts: dict[str, AgentEvent] = {}
    ends: dict[str, AgentEvent] = {}
    for ev in events:
        if ev.event_type == "start":
            starts[ev.span_id] = ev
        elif ev.event_type == "end":
            ends[ev.span_id] = ev

    spans: list[SpanRecord] = []
    for span_id, start_ev in starts.items():
        end_ev = ends.get(span_id)
        if end_ev is None:
            continue  # unclosed span — skip
        duration_ms = (end_ev.ts - start_ev.ts) * 1000.0
        merged_attrs = {**start_ev.attrs, **end_ev.attrs}
        error = merged_attrs.get("status") == "error" or merged_attrs.get("error") is not None
        spans.append(SpanRecord(
            trace_id=start_ev.trace_id,
            program_id=start_ev.program_id,
            span_id=span_id,
            parent_span_id=start_ev.parent_span_id,
            span_kind=_infer_kind(start_ev.name, start_ev.layer),
            name=start_ev.name,
            start_ts=start_ev.ts,
            end_ts=end_ev.ts,
            duration_ms=duration_ms,
            attrs=merged_attrs,
            error=error,
        ))

    # Populate children lists
    span_map = {s.span_id: s for s in spans}
    for span in spans:
        if span.parent_span_id and span.parent_span_id in span_map:
            span_map[span.parent_span_id].children.append(span.span_id)

    spans.sort(key=lambda s: s.start_ts)
    write_timeline_csv(spans, output_dir)
    return spans


def write_timeline_csv(spans: list[SpanRecord], output_dir: Path) -> Path:
    """Write spans to timeline.csv. Returns path."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "timeline.csv"
    fieldnames = [
        "span_id", "parent_span_id", "span_kind", "name",
        "start_ts", "end_ts", "duration_ms", "error", "is_retry",
        "trace_id", "program_id",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for s in spans:
            writer.writerow({
                "span_id": s.span_id,
                "parent_span_id": s.parent_span_id or "",
                "span_kind": s.span_kind,
                "name": s.name,
                "start_ts": s.start_ts,
                "end_ts": s.end_ts,
                "duration_ms": round(s.duration_ms, 3),
                "error": s.error,
                "is_retry": s.is_retry,
                "trace_id": s.trace_id,
                "program_id": s.program_id,
            })
    return out_path
