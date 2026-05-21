"""Planner package — factory interface.

Usage:
    from agentprof.planner import get_planner

    planner = get_planner()          # uses AGENTPROF_PLANNER env var (default: llm)
    plan = planner.plan_observation(state)

Available backends:
    llm   — LLM generates ObservationPlan (default, Milestone 3)
    rule  — Deterministic rule-based selection (ablation baseline, Milestone 2)

Adding a new backend: create agentprof/planner/backends/<name>/ with a BasePlanner
subclass, then add a branch in get_planner().
"""

from __future__ import annotations

import os

from agentprof.planner.base import BasePlanner

__all__ = ["BasePlanner", "get_planner"]

_PLANNER = os.environ.get("AGENTPROF_PLANNER", "llm")


def get_planner(backend: str | None = None) -> BasePlanner:
    """Return an instantiated planner backend.

    Args:
        backend: Override AGENTPROF_PLANNER for this call. One of: llm, rule.
    """
    b = backend or _PLANNER
    if b == "llm":
        from agentprof.planner.backends.llm.llm_planner import LLMPlanner
        return LLMPlanner()
    if b == "rule":
        from agentprof.planner.backends.rule.rule_planner import RulePlanner
        return RulePlanner()
    raise ValueError(f"Unknown planner backend {b!r}. Available: llm, rule")
