"""Context builder: formats ProfilingState into the LLM planner prompt context.

Converts structured state objects into human-readable / LLM-readable summaries.
Keeps the planner prompt concise enough to fit in a reasonable context window.

Milestone 3 implementation target.
"""

from __future__ import annotations

from agentprof.state import ProfilingState


def build_planner_context(state: ProfilingState) -> dict[str, str]:
    """Return a dict of formatted strings for use in PLAN_REQUEST_TEMPLATE.

    Keys: spec_summary, breakdown, resource_health, observer_registry_summary,
          diagnostic_questions, known_unknowns, budget
    """
    raise NotImplementedError("Milestone 3")
