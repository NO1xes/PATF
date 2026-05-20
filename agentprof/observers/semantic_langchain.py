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
from agentprof.schema.events import AgentEvent


def _new_event(run_id: str, span_id: str, parent_span_id: str | None,
               event_type: str, name: str, attrs: dict) -> AgentEvent:
    return AgentEvent(
        event_id=f"evt_{uuid.uuid4().hex[:8]}",
        trace_id=f"trace_{run_id}",
        program_id=run_id,
        span_id=span_id,
        parent_span_id=parent_span_id,
        layer="agent_semantic",
        event_type=event_type,
        name=name,
        ts=time.time(),
        attrs=attrs,
        source_observer="semantic_langchain",
    )


class LangChainSemanticObserver(BaseObserver, BaseCallbackHandler):
    name = "semantic_langchain"
    layer = "agent_semantic"

    def __init__(self, run_id: str) -> None:
        BaseCallbackHandler.__init__(self)
        self._run_id = run_id
        self._buffer: list[AgentEvent] = []
        # map langchain run_id (UUID) → span_id string
        self._span_ids: dict[str, str] = {}
        self._parent_ids: dict[str, str | None] = {}

    def _span_id(self, lc_run_id: Any) -> str:
        key = str(lc_run_id)
        if key not in self._span_ids:
            self._span_ids[key] = f"span_{uuid.uuid4().hex[:8]}"
        return self._span_ids[key]

    def _parent_span_id(self, parent_run_id: Any) -> str | None:
        if parent_run_id is None:
            return None
        return self._span_ids.get(str(parent_run_id))

    def attach(self, target: object) -> None:
        pass  # passed as callback at agent construction time

    def detach(self) -> None:
        self._buffer.clear()
        self._span_ids.clear()

    def flush(self, state=None) -> list[AgentEvent]:
        events, self._buffer = self._buffer, []
        return events

    # --- LangChain callback hooks ---

    def on_chain_start(self, serialized: dict, inputs: dict, **kwargs: Any) -> None:
        run_id = kwargs.get("run_id")
        parent_run_id = kwargs.get("parent_run_id")
        span_id = self._span_id(run_id)
        self._buffer.append(_new_event(
            self._run_id, span_id, self._parent_span_id(parent_run_id),
            "start", "run", {"task_id": self._run_id},
        ))

    def on_chain_end(self, outputs: dict, **kwargs: Any) -> None:
        run_id = kwargs.get("run_id")
        span_id = self._span_id(run_id)
        self._buffer.append(_new_event(
            self._run_id, span_id, None,
            "end", "run", {"task_id": self._run_id, "status": "success"},
        ))

    def on_llm_start(self, serialized: dict, prompts: list, **kwargs: Any) -> None:
        run_id = kwargs.get("run_id")
        parent_run_id = kwargs.get("parent_run_id")
        span_id = self._span_id(run_id)
        self._buffer.append(_new_event(
            self._run_id, span_id, self._parent_span_id(parent_run_id),
            "start", "llm_call", {},
        ))

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        run_id = kwargs.get("run_id")
        span_id = self._span_id(run_id)
        attrs: dict = {}
        try:
            usage = response.llm_output.get("token_usage", {}) if response.llm_output else {}
            attrs["prompt_tokens"] = usage.get("prompt_tokens", 0)
            attrs["completion_tokens"] = usage.get("completion_tokens", 0)
        except Exception:
            pass
        self._buffer.append(_new_event(
            self._run_id, span_id, None, "end", "llm_call", attrs,
        ))

    def on_tool_start(self, serialized: dict, input_str: str, **kwargs: Any) -> None:
        run_id = kwargs.get("run_id")
        parent_run_id = kwargs.get("parent_run_id")
        span_id = self._span_id(run_id)
        tool_name = serialized.get("name", "unknown_tool")
        self._buffer.append(_new_event(
            self._run_id, span_id, self._parent_span_id(parent_run_id),
            "start", "tool_call", {"tool_name": tool_name},
        ))

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        run_id = kwargs.get("run_id")
        span_id = self._span_id(run_id)
        tool_name = kwargs.get("name", "unknown_tool")
        self._buffer.append(_new_event(
            self._run_id, span_id, None,
            "end", "tool_call", {"tool_name": tool_name},
        ))

    def on_tool_error(self, error: Exception, **kwargs: Any) -> None:
        run_id = kwargs.get("run_id")
        span_id = self._span_id(run_id)
        tool_name = kwargs.get("name", "unknown_tool")
        self._buffer.append(_new_event(
            self._run_id, span_id, None,
            "end", "tool_call", {"tool_name": tool_name, "error": str(error), "status": "error"},
        ))

