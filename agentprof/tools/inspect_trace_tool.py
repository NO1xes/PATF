"""inspect_trace_tool: queries existing events.jsonl for a span or time window.

Used when mode=query_existing in an ObservationPlan — no re-run needed.

Milestone 2 implementation target.
"""

from __future__ import annotations

from pathlib import Path

from agentprof.schema.events import AgentEvent


def inspect_trace(
    events_path: Path,
    span_id: str | None = None,
    time_window: tuple[float, float] | None = None,
    layer: str | None = None,
) -> list[AgentEvent]:
    """Return matching events from events.jsonl."""
    raise NotImplementedError("Milestone 2")
