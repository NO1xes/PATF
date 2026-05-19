"""Executor: runs an approved ObservationPlan.

Dispatches to the correct observer(s), writes outputs to profiles/<run_id>/,
and updates the action_log in ProfilingState.
"""

from __future__ import annotations

from pathlib import Path

from agentprof.schema.observations import ObservationPlan
from agentprof.state import ProfilingState


def execute(plan: ObservationPlan, state: ProfilingState, output_dir: Path) -> dict:
    """Execute an approved plan. Returns a summary dict for evidence building.

    Raises ValueError if plan.approved is False.
    """
    if not plan.approved:
        raise ValueError(f"Cannot execute unapproved plan: {plan.rejection_reason}")

    raise NotImplementedError("Milestone 2")
