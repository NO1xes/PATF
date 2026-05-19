"""AgentEvent: the normalized event emitted by every observer.

All callbacks / wrappers / adapters must convert their raw data into AgentEvent
before writing to events.jsonl. This is the cross-layer correlation primitive.

Field design follows OpenTelemetry trace/span/event model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentEvent:
    event_id: str                      # unique event ID
    trace_id: str                      # ties all events in one profiling campaign
    program_id: str                    # which agent program (task) this event belongs to
    span_id: str | None                # span this event opens or closes
    parent_span_id: str | None         # parent span (builds the call tree)
    layer: str                         # agent | llm | tool | resource
    event_type: str                    # start | end | error | metric | snapshot
    name: str                          # e.g. "llm_call", "slow_tool", "run"
    ts: float                          # Unix timestamp, seconds (float for sub-ms)
    attrs: dict[str, Any] = field(default_factory=dict)
    source_observer: str = ""          # which observer emitted this
    raw_ref: str | None = None         # path to raw observer output if exists
