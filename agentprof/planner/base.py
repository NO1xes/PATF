"""BasePlanner: abstract interface for all planner backends.

Any planner backend must implement plan_observation(state) -> ObservationPlan.
The active backend is selected via configs/backends.yaml or AGENTPROF_BACKEND env var.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from agentprof.schema.observations import ObservationPlan
from agentprof.state import ProfilingState


class BasePlanner(ABC):
    """Abstract planner — decides what to observe next."""

    @abstractmethod
    def plan_observation(self, state: ProfilingState) -> ObservationPlan:
        """Given current profiling state, return the next ObservationPlan.

        The returned plan must be passed through validator.validate() before execution.
        """
