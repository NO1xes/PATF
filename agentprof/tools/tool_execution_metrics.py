"""Layer 3 — Tool Execution profiling tools.

Inspect individual tool calls, spans, and events.  In white-box mode
these tools read from ``events.jsonl`` (collected by observers).  In
black-box mode they return a "no data" signal that tells the LLM to
recommend enabling white-box observers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _find_events_file() -> Path | None:
    """Walk profiles/ looking for the most recent events.jsonl."""
    profiles_dir = Path("profiles")
    if not profiles_dir.exists():
        return None
    candidates = sorted(
        profiles_dir.glob("*/events.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    return candidates[0] if candidates else None


def _load_events(events_path: Path | None = None) -> list[dict[str, Any]]:
    """Load all events from a JSONL file.  Returns empty list on failure."""
    path = events_path or _find_events_file()
    if path is None or not path.exists():
        return []
    events: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                events.append(json.loads(line))
    except (json.JSONDecodeError, OSError):
        return []
    return events


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def observe_tool_calls(
    duration_sec: float | None = None,
    tool_filter: list[str] | None = None,
    events_path: str | None = None,
) -> dict[str, Any]:
    """Analyse tool call events from collected trace data.

    Args:
        duration_sec: If given, only look at events in the last N seconds.
        tool_filter: If given, only return calls for these tool names.
        events_path: Path to events.jsonl.  Auto-detected from profiles/ if
            not given.

    Returns a dict with ``tool_calls`` (list of per-call stats) and
    ``summary`` (aggregate latency / error counts).

    In black-box mode (no events.jsonl available), returns ``available: false``
    and the LLM should recommend enabling white-box observers.
    """
    events = _load_events(Path(events_path) if events_path else None)
    if not events:
        return {
            "available": False,
            "error": (
                "No events.jsonl found.  Tool-level metrics are only "
                "available when white-box observers are attached to the "
                "target agent runtime.  Recommend enabling the tool_events "
                "observer in the next iteration."
            ),
        }

    # Filter to tool_call events
    tool_events = [
        e for e in events
        if e.get("name", "").endswith("_tool")
        or e.get("source_observer") == "tool_events"
        or e.get("layer") == "tool_execution"
    ]
    if not tool_events:
        # Fallback: look for events with event_type "end" and layer "tool_execution"
        tool_events = [
            e for e in events
            if e.get("event_type") == "end" and e.get("layer") == "tool_execution"
        ]

    if tool_filter:
        tool_filter_set = set(tool_filter)
        tool_events = [
            e for e in tool_events
            if e.get("name", "") in tool_filter_set
            or e.get("attrs", {}).get("tool_name", "") in tool_filter_set
        ]

    # Build per-call stats
    calls: list[dict[str, Any]] = []
    for e in tool_events:
        attrs = e.get("attrs", {})
        calls.append({
            "tool_name": attrs.get("tool_name", e.get("name", "?")),
            "duration_ms": attrs.get("duration_ms", 0),
            "status": attrs.get("status", "?"),
            "ts": e.get("ts", 0),
            "span_id": e.get("span_id"),
            "program_id": e.get("program_id"),
        })

    # Summary
    durations = [c["duration_ms"] for c in calls if c["duration_ms"] > 0]
    errors = [c for c in calls if c["status"] == "error"]
    return {
        "available": True,
        "tool_calls": calls,
        "summary": {
            "total_calls": len(calls),
            "error_count": len(errors),
            "error_rate": round(len(errors) / len(calls), 3) if calls else 0.0,
            "avg_duration_ms": round(sum(durations) / len(durations), 1) if durations else 0.0,
            "max_duration_ms": round(max(durations), 1) if durations else 0.0,
            "min_duration_ms": round(min(durations), 1) if durations else 0.0,
        },
    }


def inspect_span(span_id: str, events_path: str | None = None) -> dict[str, Any]:
    """Return all events belonging to a single span.

    Args:
        span_id: The span_id to look up (from a previous tool call result).
        events_path: Path to events.jsonl.

    Returns the span's start/end/error events and computed duration.
    """
    events = _load_events(Path(events_path) if events_path else None)
    if not events:
        return {"span_id": span_id, "available": False, "error": "No events data"}

    span_events = [e for e in events if e.get("span_id") == span_id]
    if not span_events:
        return {"span_id": span_id, "available": False, "error": f"Span {span_id} not found"}

    starts = [e for e in span_events if e.get("event_type") == "start"]
    ends = [e for e in span_events if e.get("event_type") == "end"]
    errors = [e for e in span_events if e.get("event_type") == "error" or e.get("attrs", {}).get("status") == "error"]

    duration_ms = 0.0
    if starts and ends:
        duration_ms = round((ends[0]["ts"] - starts[0]["ts"]) * 1000, 1)

    return {
        "span_id": span_id,
        "available": True,
        "name": span_events[0].get("name", "?"),
        "layer": span_events[0].get("layer", "?"),
        "program_id": span_events[0].get("program_id", "?"),
        "duration_ms": duration_ms,
        "has_error": len(errors) > 0,
        "event_count": len(span_events),
        "attrs": span_events[0].get("attrs", {}),
    }


def query_events(
    layer: str | None = None,
    time_start: float | None = None,
    time_end: float | None = None,
    event_type: str | None = None,
    top_n: int = 20,
    events_path: str | None = None,
) -> dict[str, Any]:
    """Query events by layer, time window, and event type.

    Args:
        layer: Filter by layer (hardware_resource, llm_serving,
               tool_execution, agent_semantic).
        time_start/end: Time window in Unix seconds.
        event_type: Filter by type (start, end, error, metric, snapshot).
        top_n: Return at most this many events.
        events_path: Path to events.jsonl.

    Returns matching events and a count.
    """
    events = _load_events(Path(events_path) if events_path else None)
    if not events:
        return {"available": False, "error": "No events data"}

    filtered = events
    if layer:
        filtered = [e for e in filtered if e.get("layer") == layer]
    if time_start is not None:
        filtered = [e for e in filtered if e.get("ts", 0) >= time_start]
    if time_end is not None:
        filtered = [e for e in filtered if e.get("ts", 0) <= time_end]
    if event_type:
        filtered = [e for e in filtered if e.get("event_type") == event_type]

    return {
        "available": True,
        "total_matches": len(filtered),
        "returned": min(len(filtered), top_n),
        "events": filtered[:top_n],
    }


# ---------------------------------------------------------------------------
# OpenAI function-calling tool definitions
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "observe_tool_calls",
            "description": (
                "Analyse tool call events from collected trace data.  "
                "Shows per-call latency, success/error status, and aggregate "
                "stats (avg/max/min duration, error rate).  "
                "Use this after get_process_tree() confirms a tool-heavy "
                "workload, to quantify WHICH tools are slow and whether "
                "retries are the bottleneck.  "
                "If events data is not available (black-box mode), this "
                "tool returns available=false — recommend white-box observers."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "tool_filter": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Only return calls for these tool names.",
                    },
                    "events_path": {
                        "type": "string",
                        "description": "Path to events.jsonl (auto-detected).",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_span",
            "description": (
                "Look up all events belonging to a single span by span_id.  "
                "Returns the span's name, layer, duration, error status, and "
                "custom attributes.  Use this to drill into a specific slow "
                "or failed call identified by observe_tool_calls()."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "span_id": {
                        "type": "string",
                        "description": "The span_id from a previous tool call result.",
                    },
                },
                "required": ["span_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_events",
            "description": (
                "Query events by layer, time window, and event type.  "
                "Use this for cross-layer correlation — e.g. find all "
                "llm_serving events in the same time window as a slow "
                "tool call, or filter error events to find patterns."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "layer": {
                        "type": "string",
                        "description": "Layer: hardware_resource, llm_serving, tool_execution, agent_semantic.",
                    },
                    "time_start": {
                        "type": "number",
                        "description": "Start of time window (Unix seconds).",
                    },
                    "time_end": {
                        "type": "number",
                        "description": "End of time window (Unix seconds).",
                    },
                    "event_type": {
                        "type": "string",
                        "description": "Event type: start, end, error, metric, snapshot.",
                    },
                    "top_n": {
                        "type": "integer",
                        "description": "Max events to return (default 20).",
                        "default": 20,
                    },
                },
                "required": [],
            },
        },
    },
]

TOOL_DISPATCH = {
    "observe_tool_calls": observe_tool_calls,
    "inspect_span": inspect_span,
    "query_events": query_events,
}
