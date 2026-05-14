"""LangChain callback observer (Agent Semantic Layer).

Attaches to a LangChain agent via callbacks and emits normalized AgentEvents
for: run_start, run_end, llm_call_start, llm_call_end, tool_call_start,
tool_call_end, error.

Milestone 1 implementation target.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from langchain_core.callbacks import BaseCallbackHandler

from agentprof.observers.base import BaseObserver
from agentprof.schema import AgentEvent, EventType
from agentprof.state import ProfilingState


class LangChainSemanticObserver(BaseObserver, BaseCallbackHandler):
    name = "semantic_langchain"
    layer = "agent_semantic"

    def __init__(self, run_id: str) -> None:
        BaseCallbackHandler.__init__(self)
        self._run_id = run_id
        self._buffer: list[AgentEvent] = []

    def attach(self, target: object) -> None:
        pass  # passed as callback at agent construction time

    def detach(self) -> None:
        self._buffer.clear()

    def flush(self, state: ProfilingState) -> list[AgentEvent]:
        events, self._buffer = self._buffer, []
        return events

    # --- LangChain callback hooks (Milestone 1) ---

    def on_chain_start(self, serialized: dict, inputs: dict, **kwargs: Any) -> None:
        raise NotImplementedError("Milestone 1")

    def on_chain_end(self, outputs: dict, **kwargs: Any) -> None:
        raise NotImplementedError("Milestone 1")

    def on_llm_start(self, serialized: dict, prompts: list, **kwargs: Any) -> None:
        raise NotImplementedError("Milestone 1")

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        raise NotImplementedError("Milestone 1")

    def on_tool_start(self, serialized: dict, input_str: str, **kwargs: Any) -> None:
        raise NotImplementedError("Milestone 1")

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        raise NotImplementedError("Milestone 1")

    def on_tool_error(self, error: Exception, **kwargs: Any) -> None:
        raise NotImplementedError("Milestone 1")
