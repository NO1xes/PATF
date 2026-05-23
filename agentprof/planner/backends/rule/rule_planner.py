"""Rule-based planner (ablation baseline b).

Selects the next observer using deterministic rules derived from breakdown:
  - tool_pct > 0.5  → tool_process observer (drill into which tool dominates)
  - llm_pct > 0.5   → vllm_metrics observer (drill into inference latency)
  - errors > 0      → tool_events (examine retry cost)
  - otherwise       → resource_snapshot (check hardware health)

Used for ablation: compare against llm_planner to verify LLM adds value.
"""

from __future__ import annotations

import uuid

from agentprof.planner.base import BasePlanner
from agentprof.schema.observations import ObservationPlan
from agentprof.state import ProfilingState


class RulePlanner(BasePlanner):
    """Deterministic rule-based planner for ablation experiments."""

    def plan_observation(self, state: ProfilingState) -> ObservationPlan:
        bd = state.breakdown or {}
        tool_pct = bd.get("tool_pct", 0.0)
        llm_pct = bd.get("llm_pct", 0.0)
        errors = bd.get("errors", 0)

        # Pick the diagnostic question to address (first unanswered, or default)
        answered_ids = {e.question_id for e in state.evidence}
        open_questions = [
            q for q in state.diagnostic_questions
            if q["question_id"] not in answered_ids
        ]
        question_id = open_questions[0]["question_id"] if open_questions else "q_rule_default"

        # Deterministic observer selection
        if tool_pct > 0.5:
            observers = ["tool_events"]
            rationale = f"tool_pct={tool_pct:.0%} dominates — drill into tool execution"
        elif llm_pct > 0.5:
            observers = ["llm_client_timing"]
            rationale = f"llm_pct={llm_pct:.0%} dominates — examine LLM request latency"
        elif errors > 0:
            observers = ["tool_events"]
            rationale = f"{errors} error(s) detected — examine retry cost"
        else:
            observers = ["resource_snapshot"]
            rationale = "no clear dominant component — check hardware health"

        # Filter to observers actually available in registry
        available = set(state.observer_registry.all_names())
        observers = [o for o in observers if o in available] or ["resource_snapshot"]

        return ObservationPlan(
            plan_id=f"plan_rule_{uuid.uuid4().hex[:8]}",
            question_id=question_id,
            observers=observers,
            scope={},
            mode="query_existing",
            rationale=rationale,
            expected_evidence=["breakdown confirms dominant component"],
        )
