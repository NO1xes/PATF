from agentprof.observers.base import BaseObserver
from agentprof.observers.resource_snapshot import ResourceSnapshotObserver

__all__ = [
    "BaseObserver",
    "ResourceSnapshotObserver",
    # langchain-dependent observers — imported lazily to avoid hard dep at import time
    "LangChainSemanticObserver",
    "LLMClientTimingObserver",
    "ToolEventsObserver",
]


def __getattr__(name: str):
    if name == "LangChainSemanticObserver":
        from agentprof.observers.semantic_langchain import LangChainSemanticObserver
        return LangChainSemanticObserver
    if name == "LLMClientTimingObserver":
        from agentprof.observers.llm_client_timing import LLMClientTimingObserver
        return LLMClientTimingObserver
    if name == "ToolEventsObserver":
        from agentprof.observers.tool_events import ToolEventsObserver
        return ToolEventsObserver
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
