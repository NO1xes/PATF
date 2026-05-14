"""Tool wrapper observer (Tool/External Execution Layer).

Wraps tool functions to emit tool_call_start, tool_call_end, error events
with duration_ms, tool_name, input_summary, output_summary, error_type.

Milestone 1 implementation target.
"""

from __future__ import annotations

from typing import Callable

from agentprof.observers.base import BaseObserver
from agentprof.state import ProfilingState
from agentprof.schema import AgentEvent


class ToolWrapperObserver(BaseObserver):
    name = "tool_wrapper"
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
        """Return a wrapped version of fn that emits timing events."""
        raise NotImplementedError("Milestone 1")
