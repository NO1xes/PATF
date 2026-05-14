"""OpenAI-compatible client timing observer (LLM Serving Layer).

Wraps the OpenAI client to record request_start, request_end, model,
token_usage for each LLM call. Does not require access to vLLM internals.

Milestone 1 implementation target.
"""

from __future__ import annotations

from agentprof.observers.base import BaseObserver
from agentprof.state import ProfilingState
from agentprof.schema import AgentEvent


class LLMClientTimingObserver(BaseObserver):
    name = "llm_client_timing"
    layer = "llm_serving"

    def __init__(self, run_id: str) -> None:
        self._run_id = run_id
        self._buffer: list[AgentEvent] = []
        self._original_create = None

    def attach(self, target: object) -> None:
        """Monkey-patch target.chat.completions.create to record timing."""
        raise NotImplementedError("Milestone 1")

    def detach(self) -> None:
        raise NotImplementedError("Milestone 1")

    def flush(self, state: ProfilingState) -> list[AgentEvent]:
        events, self._buffer = self._buffer, []
        return events
