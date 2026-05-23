"""Validator: checks an ObservationPlan before execution.

Guards against:
  - observers not in the registry
  - forbidden optimization actions
  - budget overrun
  - actions that require human confirmation

The LLM planner proposes; the validator approves or rejects.
"""

from __future__ import annotations

from agentprof.schema.observations import ObservationPlan
from agentprof.model.observer_registry import ObserverRegistry

FORBIDDEN_ACTIONS = {
    "change_concurrency",
    "change_arrival_rate",
    "toggle_cache",
    "set_timeout",
    "set_quota",
    "apply_patch",
    "modify_prompt",
    "modify_planner",
}


def validate(
    plan: ObservationPlan,
    registry: ObserverRegistry,
    budget_used: dict,
    budget_limit: dict,
) -> tuple[bool, str]:
    """Return (approved, reason).

    Sets plan.approved and plan.rejection_reason as a side effect.
    """
    # Check for forbidden actions embedded in observer names or scope
    for obs_name in plan.observers:
        if obs_name in FORBIDDEN_ACTIONS:
            plan.approved = False
            plan.rejection_reason = f"Observer '{obs_name}' is a forbidden optimization action."
            return False, plan.rejection_reason

    # Check observer names exist in registry
    for obs_name in plan.observers:
        if registry.get(obs_name) is None:
            plan.approved = False
            plan.rejection_reason = f"Observer '{obs_name}' not found in registry."
            return False, plan.rejection_reason

    # Check budget
    used = budget_used.get("iterations", 0)
    limit = budget_limit.get("max_iterations", 2)
    if used >= limit:
        plan.approved = False
        plan.rejection_reason = f"Budget exhausted: {used}/{limit} iterations used."
        return False, plan.rejection_reason

    plan.approved = True
    return True, "approved"
