"""Rule-based planner (ablation baseline b).

Selects the next observer using deterministic rules derived from breakdown.json:
  - If tool_pct > 0.5  → select tool_process observer
  - If llm_pct > 0.5   → select vllm_metrics observer (if available)
  - Otherwise          → select resource_snapshot

Used for ablation: compare against llm_planner to verify LLM adds value.
No LLM call, no context window required.

Milestone 2 implementation target (needed for baseline comparison).
"""

from __future__ import annotations

import uuid

from agentprof.planner.base import BasePlanner
from agentprof.schema.observations import ObservationPlan
from agentprof.state import ProfilingState


class RulePlanner(BasePlanner):
    """Deterministic rule-based planner for ablation experiments."""

    def plan_observation(self, state: ProfilingState) -> ObservationPlan:
        raise NotImplementedError("Milestone 2 — rule planner baseline")
