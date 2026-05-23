"""Tests for validator.py — forbidden action enforcement.

Verifies that the validator correctly approves valid plans and rejects
forbidden actions, unknown observers, and budget overruns.
No LLM required.
"""

import pytest

from agentprof.schema.observations import ObservationPlan
from agentprof.model.observer_registry import ObserverCapability, ObserverRegistry
from agentprof.validator import validate, FORBIDDEN_ACTIONS


def make_registry(*names: str) -> ObserverRegistry:
    registry = ObserverRegistry()
    for name in names:
        registry.register(ObserverCapability(
            name=name,
            layer="tool_execution",
            observes=["start", "end"],
            required_inputs=[],
            output_streams=["events.jsonl"],
            cost_level="low",
            mode="online",
        ))
    return registry


def make_plan(observers: list[str], question_id: str = "q_001") -> ObservationPlan:
    return ObservationPlan(
        plan_id="plan_001",
        question_id=question_id,
        observers=observers,
    )


class TestValidatorApproves:
    def test_valid_plan_approved(self):
        registry = make_registry("tool_events", "resource_snapshot")
        plan = make_plan(["tool_events"])
        approved, reason = validate(plan, registry, {"iterations": 0}, {"max_iterations": 2})
        assert approved is True
        assert plan.approved is True

    def test_multiple_valid_observers(self):
        registry = make_registry("tool_events", "resource_snapshot", "llm_client_timing")
        plan = make_plan(["tool_events", "resource_snapshot"])
        approved, _ = validate(plan, registry, {"iterations": 0}, {"max_iterations": 2})
        assert approved is True


class TestValidatorRejects:
    def test_forbidden_action_rejected(self):
        registry = make_registry("tool_events")
        for forbidden in FORBIDDEN_ACTIONS:
            plan = make_plan([forbidden])
            approved, reason = validate(plan, registry, {"iterations": 0}, {"max_iterations": 2})
            assert approved is False
            assert plan.approved is False
            assert forbidden in plan.rejection_reason

    def test_unknown_observer_rejected(self):
        registry = make_registry("tool_events")
        plan = make_plan(["nonexistent_observer"])
        approved, reason = validate(plan, registry, {"iterations": 0}, {"max_iterations": 2})
        assert approved is False
        assert "not found in registry" in reason

    def test_budget_exhausted_rejected(self):
        registry = make_registry("tool_events")
        plan = make_plan(["tool_events"])
        approved, reason = validate(plan, registry, {"iterations": 2}, {"max_iterations": 2})
        assert approved is False
        assert "Budget exhausted" in reason

    def test_budget_not_exhausted_approved(self):
        registry = make_registry("tool_events")
        plan = make_plan(["tool_events"])
        approved, _ = validate(plan, registry, {"iterations": 1}, {"max_iterations": 2})
        assert approved is True
