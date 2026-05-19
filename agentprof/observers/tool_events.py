"""Tool events observer — renamed from tool_wrapper to match 05 spec.

Records tool_call_start, tool_call_end, error, duration_ms for each tool call.
The decomposition fields recorded depend on what the wrapper can observe
(duration, error, input_summary, output_summary) — not a fixed schema.
"""

from __future__ import annotations

from typing import Callable

from agentprof.observers.base import BaseObserver
from agentprof.state import ProfilingState
from agentprof.schema.events import AgentEvent


class ToolEventsObserver(BaseObserver):
    name = "tool_events"
    layer = "tool_execution"

    def __init__(self, run_id: str) -> None:
        self._run_id = run_id
        self._buffer: list[AgentEvent] = []

    def attach(self, target: object) -> None:
        pass  # wrapping is done per-tool via wrap_tool()

    def detach(self) -> None:
        self._buffer.clear()

    def flush(self, state: ProfilingState) -> list[AgentEvent]:
        events, self._buffer = self._buffer, []
        return events

    def wrap_tool(self, fn: Callable) -> Callable:
        """Return a wrapped version of fn that emits start/end/error events."""
        raise NotImplementedError("Milestone 1")
