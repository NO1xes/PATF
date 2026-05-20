"""Tool events observer — renamed from tool_wrapper to match 05 spec.

Records tool_call_start, tool_call_end, error, duration_ms for each tool call.
The decomposition fields recorded depend on what the wrapper can observe
(duration, error, input_summary, output_summary) — not a fixed schema.
"""

from __future__ import annotations

import time
import uuid
from typing import Callable, Any

from agentprof.observers.base import BaseObserver
from agentprof.schema.events import AgentEvent


def _new_event(run_id: str, span_id: str, event_type: str,
               tool_name: str, attrs: dict) -> AgentEvent:
    return AgentEvent(
        event_id=f"evt_{uuid.uuid4().hex[:8]}",
        trace_id=f"trace_{run_id}",
        program_id=run_id,
        span_id=span_id,
        parent_span_id=None,
        layer="tool_execution",
        event_type=event_type,
        name=tool_name,
        ts=time.time(),
        attrs=attrs,
        source_observer="tool_events",
    )


class ToolEventsObserver(BaseObserver):
    name = "tool_events"
    layer = "tool_execution"

    def __init__(self, run_id: str) -> None:
        self._run_id = run_id
        self._buffer: list[AgentEvent] = []

    def attach(self, target: object = None) -> None:
        pass  # wrapping is done per-tool via wrap_tool()

    def detach(self) -> None:
        self._buffer.clear()

    def flush(self, state=None) -> list[AgentEvent]:
        events, self._buffer = self._buffer, []
        return events

    def wrap_tool(self, fn: Callable) -> Callable:
        """Return a wrapped version of fn that emits start/end/error events."""
        observer = self
        tool_name = getattr(fn, "name", None) or getattr(fn, "__name__", "unknown_tool")

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            span_id = f"span_tool_{uuid.uuid4().hex[:8]}"
            observer._buffer.append(_new_event(
                observer._run_id, span_id, "start",
                tool_name, {"tool_name": tool_name},
            ))
            t0 = time.time()
            try:
                result = fn(*args, **kwargs)
            except Exception as exc:
                duration_ms = round((time.time() - t0) * 1000, 1)
                observer._buffer.append(_new_event(
                    observer._run_id, span_id, "end",
                    tool_name, {
                        "tool_name": tool_name,
                        "duration_ms": duration_ms,
                        "status": "error",
                        "error": str(exc),
                    },
                ))
                raise
            duration_ms = round((time.time() - t0) * 1000, 1)
            observer._buffer.append(_new_event(
                observer._run_id, span_id, "end",
                tool_name, {
                    "tool_name": tool_name,
                    "duration_ms": duration_ms,
                    "status": "success",
                },
            ))
            return result

        # preserve LangChain tool metadata if present
        wrapper.__name__ = getattr(fn, "__name__", tool_name)
        wrapper.__doc__ = getattr(fn, "__doc__", None)
        return wrapper

