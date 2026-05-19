"""SpanRecord: a closed span built from a start+end AgentEvent pair.

Timeline and breakdown operate on SpanRecords, not raw events.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SpanRecord:
    trace_id: str
    program_id: str
    span_id: str
    parent_span_id: str | None
    span_kind: str          # AGENT | LLM | TOOL | WAIT | UNKNOWN
    name: str
    start_ts: float         # Unix seconds
    end_ts: float
    duration_ms: float
    attrs: dict[str, Any] = field(default_factory=dict)
    children: list[str] = field(default_factory=list)   # child span_ids
    error: bool = False
    is_retry: bool = False
