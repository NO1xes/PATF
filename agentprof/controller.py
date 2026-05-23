"""AgentProf main controller — v0.4 architecture.

Orchestrates the profiling loop:
  load_spec → load_registry → run_baseline → analyze →
  generate_questions → planner → validator → executor → repeat → report
"""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()  # load .env before any os.environ.get() calls

from agentprof.state import ProfilingState
from agentprof.model.execution_model import ExecutionModel
from agentprof.model.observer_registry import ObserverRegistry
from agentprof.storage import ensure_run_dir
from agentprof.validator import validate
from agentprof.planner import get_planner
from agentprof.executor import execute
from agentprof.analysis.timeline import build_timeline
from agentprof.analysis.breakdown import compute_breakdown, write_breakdown_json
from agentprof.analysis.resource_health import compute_resource_health, write_resource_health_json
from agentprof.analysis.questions import generate_questions
from agentprof.tools.run_workload_tool import run_workload
from agentprof.report.markdown_report import write_markdown_report
from agentprof.report.summary_json import write_summary_json


def run_profiling(
    spec_path: str,
    target_config_path: str,
    observers_config_path: str,
    workload_config_path: str,
    profiles_base: str = "./profiles",
) -> ProfilingState:
    """Run the full profiling campaign and return final state."""

    # --- Load configs ---
    spec = _load_yaml(spec_path)
    workload_cfg = _load_yaml(workload_config_path)
    registry = ObserverRegistry.from_yaml(observers_config_path)

    # Merge workload into spec so run_workload can read it
    spec["workload"] = {
        "programs": [
            {"id": p.get("task_id", p.get("id", "task")), "prompt": p["prompt"]}
            for p in workload_cfg.get("programs", [])
        ]
    }

    run_id = f"run_{uuid.uuid4().hex[:8]}"
    profiles_base_path = Path(profiles_base)
    output_dir = ensure_run_dir(profiles_base_path, run_id)

    state = ProfilingState(
        run_id=run_id,
        workload_name=workload_cfg.get("workload_name", "unknown"),
        spec=spec,
        observer_registry=registry,
        execution_model=ExecutionModel(trace_id=f"trace_{run_id}"),
    )

    planner_backend = os.environ.get("AGENTPROF_PLANNER", "llm")

    # --- Phase 1: Baseline run ---
    print(f"[AgentProf] run_id={run_id}  phase=baseline")
    run_workload(state, output_dir)

    # --- Phase 2: Analysis ---
    print(f"[AgentProf] phase=analysis")
    events_path = Path(state.events_path)
    spans = build_timeline(events_path, output_dir)
    # write_timeline_csv is called internally by build_timeline
    state.timeline_path = str(output_dir / "timeline.csv")

    breakdown = compute_breakdown(spans)
    write_breakdown_json(breakdown, output_dir)
    state.breakdown = breakdown

    snapshot_path = output_dir / "resource_snapshot.csv"
    health = compute_resource_health(snapshot_path)
    write_resource_health_json(health, output_dir)
    state.resource_health = health

    state.diagnostic_questions = generate_questions(breakdown, health, state.execution_model)

    # --- Phase 3: Observation loop ---
    max_iter = spec.get("stop_condition", {}).get("max_iterations", 2)
    budget_limit = {"max_iterations": max_iter}

    for i in range(max_iter):
        state.iteration = i + 1
        state.budget_used["iterations"] = i
        print(f"[AgentProf] phase=plan  iteration={i+1}/{max_iter}")

        planner = get_planner(backend=planner_backend)
        plan = planner.plan_observation(state)

        approved, reason = validate(plan, registry, state.budget_used, budget_limit)
        state.observation_plans.append(plan)

        if not approved:
            state.known_unknowns.append(f"Plan {plan.plan_id} rejected: {reason}")
            print(f"[AgentProf] plan rejected: {reason}")
            break

        print(f"[AgentProf] phase=execute  plan={plan.plan_id}  observers={plan.observers}")
        execute(plan, state, output_dir)
        state.budget_used["iterations"] = i + 1

    # --- Phase 4: Report ---
    print(f"[AgentProf] phase=report")
    write_markdown_report(state, output_dir)
    write_summary_json(state, output_dir)

    report_path = output_dir / "report.md"
    print(f"[AgentProf] done  report={report_path}")
    return state


def _load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
