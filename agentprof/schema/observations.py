"""ObservationPlan: the output of llm_planner.plan_observation().

This is what the LLM decides; the validator then approves or rejects it.
A plan can select multiple observers and specify scope (program, span, time window).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ObservationPlan:
    plan_id: str
    question_id: str                        # which diagnostic question this answers
    observers: list[str]                    # observer names from registry
    scope: dict[str, Any] = field(default_factory=dict)
    # scope keys: program_id, span_id, time_window_start, time_window_end
    mode: str = "same_run"
    # same_run | replay_if_deterministic | query_existing
    rationale: str = ""                     # LLM must explain why
    expected_evidence: list[str] = field(default_factory=list)
    budget: dict[str, Any] = field(default_factory=dict)
    approved: bool = False
    rejection_reason: str = ""
