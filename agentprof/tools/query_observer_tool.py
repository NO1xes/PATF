"""query_observer_tool: activates an observer for a specific scope on demand.

Used when an ObservationPlan requests same_run or replay mode for an observer
not active during the baseline run.

Milestone 2 implementation target.
"""

from __future__ import annotations

from pathlib import Path

from agentprof.schema.observations import ObservationPlan
from agentprof.state import ProfilingState


def query_observer(
    state: ProfilingState,
    plan: ObservationPlan,
    output_dir: Path,
) -> dict:
    """Activate the requested observer per the plan's scope. Return result summary."""
    raise NotImplementedError("Milestone 2")
