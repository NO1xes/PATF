"""Normalized event schema for AgentProf.

All observers must emit events conforming to AgentEvent.
The run_id + span_id + parent_span_id chain is the cross-layer correlation key.
"""

from __future__ import annotations

import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EventType(str, Enum):
    RUN_START = "run_start"
    RUN_END = "run_end"
    LLM_CALL_START = "llm_call_start"
    LLM_CALL_END = "llm_call_end"
    TOOL_CALL_START = "tool_call_start"
    TOOL_CALL_END = "tool_call_end"
    ERROR = "error"
    OBSERVER_NOTE = "observer_note"


class AgentEvent(BaseModel):
    event_type: EventType
    run_id: str
    span_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_span_id: str | None = None
    timestamp_ns: int  # Unix nanoseconds
    layer: str  # agent_semantic | llm_serving | tool_execution | hardware_resource
    attributes: dict[str, Any] = Field(default_factory=dict)
