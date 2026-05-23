"""Executor: runs an approved ObservationPlan.

For Milestone 2/3 scope, "execute" means querying already-collected data
(mode=query_existing) or re-running the workload with additional observers
(mode=same_run). The result is an EvidenceRecord written to state.

Currently supports mode=query_existing: reads existing events.jsonl / breakdown /
resource_health and extracts a finding for the targeted question.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from agentprof.schema.observations import ObservationPlan
from agentprof.schema.evidence import EvidenceRecord
from agentprof.state import ProfilingState


def execute(plan: ObservationPlan, state: ProfilingState, output_dir: Path) -> dict:
    """Execute an approved plan. Returns a summary dict; appends to state.evidence.

    Raises ValueError if plan.approved is False.
    """
    if not plan.approved:
        raise ValueError(f"Cannot execute unapproved plan: {plan.rejection_reason}")

    output_dir = Path(output_dir)
    records: list[EvidenceRecord] = []

    for observer_name in plan.observers:
        finding, data_ref = _query_existing(observer_name, state, output_dir)
        records.append(EvidenceRecord(
            evidence_id=f"ev_{uuid.uuid4().hex[:8]}",
            question_id=plan.question_id,
            plan_id=plan.plan_id,
            observer=observer_name,
            layer=_observer_layer(observer_name),
            finding=finding,
            data_ref=data_ref,
            confidence="medium" if finding else "low",
        ))

    state.evidence.extend(records)
    state.action_log.append({
        "plan_id": plan.plan_id,
        "observers": plan.observers,
        "mode": plan.mode,
        "evidence_ids": [r.evidence_id for r in records],
    })

    return {
        "plan_id": plan.plan_id,
        "evidence_count": len(records),
        "findings": [r.finding for r in records],
    }


def _query_existing(observer_name: str, state: ProfilingState, output_dir: Path) -> tuple[str, str]:
    """Extract a finding from already-collected data for a given observer."""
    bd = state.breakdown or {}
    rh = state.resource_health or {}

    if observer_name in ("tool_events", "tool_process"):
        tool_ms = bd.get("tool_ms", 0)
        tool_pct = bd.get("tool_pct", 0)
        tool_calls = bd.get("tool_calls", 0)
        errors = bd.get("errors", 0)
        finding = (
            f"Tool execution: {tool_ms:.0f} ms ({tool_pct:.0%} of total), "
            f"{tool_calls} call(s), {errors} error(s)."
        )
        return finding, str(output_dir / "breakdown.json")

    if observer_name in ("llm_client_timing", "semantic_langchain"):
        llm_ms = bd.get("llm_ms", 0)
        llm_pct = bd.get("llm_pct", 0)
        llm_calls = bd.get("llm_calls", 0)
        finding = (
            f"LLM requests: {llm_ms:.0f} ms ({llm_pct:.0%} of total), "
            f"{llm_calls} call(s)."
        )
        return finding, str(output_dir / "breakdown.json")

    if observer_name == "resource_snapshot":
        cpu = rh.get("cpu_util_mean_pct", 0)
        mem = rh.get("memory_util_mean_pct", 0)
        symptoms = rh.get("symptoms", [])
        finding = (
            f"Resource health: CPU avg {cpu:.1f}%, memory avg {mem:.1f}%. "
            + (f"Symptoms: {'; '.join(symptoms)}" if symptoms else "No saturation detected.")
        )
        return finding, str(output_dir / "resource_health.json")

    return f"Observer '{observer_name}' queried; no specific extraction implemented.", ""


def _observer_layer(name: str) -> str:
    _map = {
        "tool_events": "tool_execution",
        "tool_process": "tool_execution",
        "llm_client_timing": "llm_serving",
        "semantic_langchain": "agent_semantic",
        "resource_snapshot": "hardware_resource",
    }
    return _map.get(name, "unknown")
