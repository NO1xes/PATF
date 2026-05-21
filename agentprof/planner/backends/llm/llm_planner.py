"""LLM Planner: generates an ObservationPlan given the current profiling state.

The LLM receives a structured context (breakdown, resource health, observer registry,
diagnostic questions, known unknowns, budget) and decides:
  - which question(s) to address next
  - which observers to activate
  - what scope (program_id, span_id, time_window) to focus on
  - which mode to use (same_run / query_existing / replay)

The planner does NOT execute observers and does NOT compute metrics.
Those are handled by executor.py using deterministic tools.

Milestone 3 implementation target.
"""

from __future__ import annotations

from agentprof.planner.base import BasePlanner
from agentprof.schema.observations import ObservationPlan
from agentprof.state import ProfilingState


class LLMPlanner(BasePlanner):
    """LLM-based planner — calls the configured LLM to produce an ObservationPlan."""

    def plan_observation(self, state: ProfilingState) -> ObservationPlan:
        """Call the LLM with current profiling context; return an ObservationPlan.

        The plan is then passed to validator.validate() before execution.
        """
        raise NotImplementedError("Milestone 3")

