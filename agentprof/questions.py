"""Diagnostic question generator.

Given a breakdown dict, generates a prioritized list of diagnostic questions
following Gregg's drill-down methodology: highest-cost layer first.
"""

from __future__ import annotations

from agentprof.state import ProfilingState

DOMINANCE_THRESHOLD = 0.5  # layer is dominant if it accounts for >50% of total time


def generate_questions(state: ProfilingState) -> list[str]:
    """Return diagnostic questions based on current breakdown.

    Questions drive observer selection in the next iteration.
    """
    raise NotImplementedError("Milestone 3")
