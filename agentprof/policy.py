"""Rule-based observer selection policy.

Maps diagnostic questions to the next observer to activate.
MVP uses a fixed rule table — no LLM reasoning at this layer.
"""

from __future__ import annotations

from agentprof.state import ProfilingState

# Rule table: question keyword -> observer name
QUESTION_TO_OBSERVER: dict[str, str] = {
    "tool_time_dominates": "tool_process",
    "llm_time_dominates": "vllm_metrics",
    "unattributed_time_high": "semantic_langchain",
    "tool_error_or_retry": "tool_process",
    "multi_program_workload": "resource_counters",
}


def select_next_observer(state: ProfilingState) -> str | None:
    """Return the name of the next observer to activate, or None if done.

    Only returns observers that are not already active.
    """
    raise NotImplementedError("Milestone 3")
