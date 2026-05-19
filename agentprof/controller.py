"""AgentProf main controller — v0.4 architecture.

Orchestrates the profiling loop:
  load_spec → load_registry → run_baseline → analyze →
  generate_questions → llm_planner → validator → executor → repeat → report

LLM decides: which questions to address, which observers, what scope, what mode.
Python tools decide: how to collect, compute, validate, write.
Validator enforces: no optimization actions, no budget overrun.
"""

from __future__ import annotations

from pathlib import Path

from agentprof.state import ProfilingState


def run_profiling(
    spec_path: str,
    target_config_path: str,
    observers_config_path: str,
    workload_config_path: str,
    profiles_base: str = "./profiles",
) -> ProfilingState:
    """Run the full profiling campaign and return final state.

    Writes to profiles/<run_id>/: events.jsonl, timeline.csv, breakdown.json,
    resource_snapshot.csv, resource_health.json, execution_model.json,
    observation_plans.jsonl, evidence.jsonl, known_unknowns.md, report.md
    """
    raise NotImplementedError("Milestone 3")
