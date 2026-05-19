"""Diagnostic question generator.

Produces structured diagnostic questions from:
  - breakdown (dominant component)
  - resource_health (symptoms)
  - execution_model summary (unattributed spans, missing correlation)

Each question includes: id, text, priority, candidate_observers.
The LLM planner then selects which questions to address and how.

Input:  breakdown dict + resource_health dict + execution_model summary
Output: list[dict] diagnostic questions
"""

from __future__ import annotations

from agentprof.model.execution_model import ExecutionModel

DOMINANCE_THRESHOLD = 0.5
UNKNOWN_TIME_THRESHOLD = 0.2


def generate_questions(
    breakdown: dict,
    resource_health: dict,
    execution_model: ExecutionModel,
) -> list[dict]:
    """Return prioritized diagnostic questions.

    Each question:
    {
      "question_id": "q_001",
      "priority": 1,
      "text": "Tool time accounts for 58% of total time. Which tool dominates?",
      "source": "breakdown",
      "candidate_observers": ["tool_events", "tool_process"]
    }
    """
    raise NotImplementedError("Milestone 1")
