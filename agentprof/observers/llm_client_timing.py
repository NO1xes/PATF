"""OpenAI-compatible client timing observer (LLM Serving Layer).

Wraps the OpenAI client to record request_start, request_end, model,
token_usage for each LLM call. Does not require access to vLLM internals.

Milestone 1 implementation target.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from agentprof.observers.base import BaseObserver
from agentprof.schema.events import AgentEvent


def _new_event(run_id: str, span_id: str, parent_span_id: str | None,
               event_type: str, attrs: dict) -> AgentEvent:
    return AgentEvent(
        event_id=f"evt_{uuid.uuid4().hex[:8]}",
        trace_id=f"trace_{run_id}",
        program_id=run_id,
        span_id=span_id,
        parent_span_id=parent_span_id,
        layer="llm_serving",
        event_type=event_type,
        name="llm_request",
        ts=time.time(),
        attrs=attrs,
        source_observer="llm_client_timing",
    )


class LLMClientTimingObserver(BaseObserver):
    name = "llm_client_timing"
    layer = "llm_serving"

    def __init__(self, run_id: str) -> None:
        self._run_id = run_id
        self._buffer: list[AgentEvent] = []
        self._original_create = None
        self._client = None

    def attach(self, target: object) -> None:
        """Monkey-patch target.chat.completions.create to record timing."""
        self._client = target
        original = target.chat.completions.create
        self._original_create = original
        observer = self

        def timed_create(*args: Any, **kwargs: Any):
            span_id = f"span_llm_{uuid.uuid4().hex[:8]}"
            model = kwargs.get("model", "unknown")
            observer._buffer.append(_new_event(
                observer._run_id, span_id, None,
                "start", {"model": model},
            ))
            t0 = time.time()
            try:
                result = original(*args, **kwargs)
            except Exception as exc:
                observer._buffer.append(_new_event(
                    observer._run_id, span_id, None,
                    "end", {"model": model, "error": str(exc), "status": "error"},
                ))
                raise
            elapsed_ms = (time.time() - t0) * 1000
            attrs: dict = {"model": model, "duration_ms": round(elapsed_ms, 1)}
            try:
                usage = result.usage
                if usage:
                    attrs["prompt_tokens"] = usage.prompt_tokens
                    attrs["completion_tokens"] = usage.completion_tokens
            except Exception:
                pass
            observer._buffer.append(_new_event(
                observer._run_id, span_id, None, "end", attrs,
            ))
            return result

        target.chat.completions.create = timed_create

    def detach(self) -> None:
        if self._client is not None and self._original_create is not None:
            self._client.chat.completions.create = self._original_create
        self._original_create = None
        self._client = None

    def flush(self, state=None) -> list[AgentEvent]:
        events, self._buffer = self._buffer, []
        return events

