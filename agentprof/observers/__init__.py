"""Observer package — factory interface.

Usage:
    from agentprof.observers import get_observer, get_all_baseline_observers

The active backend is selected by AGENTPROF_BACKEND in .env (default: langchain).
Adding a new backend: create agentprof/observers/backends/<name>/ with the same
four classes, then add a branch in get_observer() and get_all_baseline_observers().
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from agentprof.observers.base import BaseObserver

if TYPE_CHECKING:
    pass

__all__ = [
    "BaseObserver",
    "get_observer",
    "get_all_baseline_observers",
]

_BACKEND = os.environ.get("AGENTPROF_BACKEND", "langchain")

_OBSERVER_NAMES = {
    "semantic_langchain",
    "llm_client_timing",
    "tool_events",
    "resource_snapshot",
}


def get_observer(name: str, run_id: str, backend: str | None = None) -> BaseObserver:
    """Return an instantiated observer by name.

    Args:
        name:    Observer name as registered in ObserverRegistry.
        run_id:  Current profiling run ID.
        backend: Override AGENTPROF_BACKEND for this call.
    """
    b = backend or _BACKEND
    if b == "langchain":
        return _get_langchain_observer(name, run_id)
    raise ValueError(f"Unknown backend {b!r}. Available: langchain")


def get_all_baseline_observers(run_id: str, backend: str | None = None) -> list[BaseObserver]:
    """Return all four baseline observers for a run.

    Baseline observers attach on every run regardless of ObservationPlan.
    """
    b = backend or _BACKEND
    if b == "langchain":
        from agentprof.observers.backends.langchain.semantic_langchain import LangChainSemanticObserver
        from agentprof.observers.backends.langchain.llm_client_timing import LLMClientTimingObserver
        from agentprof.observers.backends.langchain.tool_events import ToolEventsObserver
        from agentprof.observers.backends.langchain.resource_snapshot import ResourceSnapshotObserver
        return [
            LangChainSemanticObserver(run_id),
            LLMClientTimingObserver(run_id),
            ToolEventsObserver(run_id),
            ResourceSnapshotObserver(run_id),
        ]
    raise ValueError(f"Unknown backend {b!r}.")


def _get_langchain_observer(name: str, run_id: str) -> BaseObserver:
    if name == "semantic_langchain":
        from agentprof.observers.backends.langchain.semantic_langchain import LangChainSemanticObserver
        return LangChainSemanticObserver(run_id)
    if name == "llm_client_timing":
        from agentprof.observers.backends.langchain.llm_client_timing import LLMClientTimingObserver
        return LLMClientTimingObserver(run_id)
    if name == "tool_events":
        from agentprof.observers.backends.langchain.tool_events import ToolEventsObserver
        return ToolEventsObserver(run_id)
    if name == "resource_snapshot":
        from agentprof.observers.backends.langchain.resource_snapshot import ResourceSnapshotObserver
        return ResourceSnapshotObserver(run_id)
    raise ValueError(f"Unknown observer {name!r} for backend 'langchain'.")
