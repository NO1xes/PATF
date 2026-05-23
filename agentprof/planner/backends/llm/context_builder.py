"""Context builder: formats ProfilingState into the LLM planner prompt context."""

from __future__ import annotations

from agentprof.state import ProfilingState


def build_planner_context(state: ProfilingState) -> dict[str, str]:
    """Return a dict of formatted strings for use in PLAN_REQUEST_TEMPLATE.

    Keys: spec_summary, breakdown, resource_health, observer_registry_summary,
          diagnostic_questions, known_unknowns, budget
    """
    return {
        "spec_summary": _fmt_spec(state),
        "breakdown": _fmt_breakdown(state.breakdown),
        "resource_health": _fmt_health(state.resource_health),
        "observer_registry_summary": _fmt_registry(state),
        "diagnostic_questions": _fmt_questions(state),
        "known_unknowns": _fmt_unknowns(state),
        "budget": _fmt_budget(state),
    }


def _fmt_spec(state: ProfilingState) -> str:
    spec = state.spec
    name = spec.get("experiment_name", state.workload_name)
    stage = spec.get("stage", "unknown")
    return f"Experiment: {name} | Stage: {stage} | Run ID: {state.run_id}"


def _fmt_breakdown(bd: dict | None) -> str:
    if not bd:
        return "No breakdown available yet."
    return (
        f"Total: {bd.get('total_ms', 0):.0f} ms | "
        f"LLM: {bd.get('llm_pct', 0):.0%} ({bd.get('llm_calls', 0)} calls) | "
        f"Tool: {bd.get('tool_pct', 0):.0%} ({bd.get('tool_calls', 0)} calls) | "
        f"Unknown: {bd.get('unknown_pct', 0):.0%} | "
        f"Errors: {bd.get('errors', 0)} | "
        f"Dominant: {bd.get('dominant_component', 'none')}"
    )


def _fmt_health(rh: dict | None) -> str:
    if not rh:
        return "No resource health data available."
    symptoms = rh.get("symptoms", [])
    cpu = rh.get("cpu_util_mean_pct", 0)
    mem = rh.get("memory_util_mean_pct", 0)
    sym_str = ("; ".join(symptoms)) if symptoms else "none"
    return f"CPU avg {cpu:.1f}% | Memory avg {mem:.1f}% | Symptoms: {sym_str}"


def _fmt_registry(state: ProfilingState) -> str:
    names = state.observer_registry.all_names()
    if not names:
        return "No observers registered."
    lines = []
    for name in names:
        cap = state.observer_registry.get(name)
        gpu_note = " [GPU required]" if cap.constraints.get("requires_gpu") else ""
        lines.append(f"  - {cap.name} ({cap.layer}){gpu_note}: observes {', '.join(cap.observes)}")
    return "\n".join(lines)


def _fmt_questions(state: ProfilingState) -> str:
    qs = state.diagnostic_questions
    if not qs:
        return "No diagnostic questions generated."
    answered = {e.question_id for e in state.evidence}
    lines = []
    for q in qs:
        status = "[answered]" if q["question_id"] in answered else "[open]"
        lines.append(
            f"  {status} [{q['priority']}] {q['question_id']}: {q['text']} "
            f"(observers: {', '.join(q['candidate_observers'])})"
        )
    return "\n".join(lines)


def _fmt_unknowns(state: ProfilingState) -> str:
    if not state.known_unknowns:
        return "None."
    return "\n".join(f"  - {u}" for u in state.known_unknowns)


def _fmt_budget(state: ProfilingState) -> str:
    used = state.budget_used.get("iterations", 0)
    limit = state.spec.get("stop_condition", {}).get("max_iterations", 2)
    return f"Iterations: {used}/{limit} used"
