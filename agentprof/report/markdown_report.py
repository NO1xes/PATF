"""Markdown report generator."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from agentprof.state import ProfilingState


def write_markdown_report(state: ProfilingState, output_dir: Path) -> Path:
    """Write report.md to output_dir. Returns path."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "report.md"

    lines: list[str] = []

    def h(level: int, text: str) -> None:
        lines.append(f"{'#' * level} {text}\n")

    def p(text: str) -> None:
        lines.append(text + "\n")

    h(1, f"AgentProf Report — {state.run_id}")
    p(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    p("")

    # 1. Profiling Scope
    h(2, "1. Profiling Scope")
    spec = state.spec
    p(f"- Experiment: `{spec.get('experiment_name', state.workload_name)}`")
    p(f"- Stage: `{spec.get('stage', 'unknown')}`")
    p(f"- Goal: profiling only — no optimization")
    p("")

    # 2. Workload
    h(2, "2. Workload")
    programs = spec.get("workload", {}).get("programs", [])
    if programs:
        for prog in programs:
            p(f"- `{prog.get('id', prog.get('task_id', '?'))}`: {prog.get('prompt', '')}")
    else:
        p("_(no programs recorded)_")
    p("")

    # 3. Enabled Observers
    h(2, "3. Enabled Observers")
    obs_names = sorted(state.enabled_observers) if state.enabled_observers else state.observer_registry.all_names()
    for name in obs_names:
        cap = state.observer_registry.get(name)
        layer = cap.layer if cap else "unknown"
        p(f"- `{name}` ({layer})")
    p("")

    # 4. Initial Baseline
    h(2, "4. Initial Baseline")
    p(f"- Events path: `{state.events_path or 'not recorded'}`")
    p(f"- Timeline: `{state.timeline_path or 'not recorded'}`")
    p("")

    # 5. Timeline / Breakdown
    h(2, "5. Timeline / Breakdown")
    bd = state.breakdown or {}
    if bd:
        total = bd.get("total_ms", 0)
        p(f"| Component | Time (ms) | Share |")
        p(f"| --- | --- | --- |")
        p(f"| LLM | {bd.get('llm_ms', 0):.0f} | {bd.get('llm_pct', 0):.1%} |")
        p(f"| Tool | {bd.get('tool_ms', 0):.0f} | {bd.get('tool_pct', 0):.1%} |")
        p(f"| Wait/Retry | {bd.get('wait_retry_ms', 0):.0f} | {bd.get('wait_retry_pct', 0):.1%} |")
        p(f"| Unknown | {bd.get('unknown_ms', 0):.0f} | {bd.get('unknown_pct', 0):.1%} |")
        p(f"| **Total** | **{total:.0f}** | — |")
        p("")
        p(f"Dominant component: **{bd.get('dominant_component', 'none')}**  "
          f"| LLM calls: {bd.get('llm_calls', 0)} | Tool calls: {bd.get('tool_calls', 0)} "
          f"| Errors: {bd.get('errors', 0)}")
    else:
        p("_(breakdown not available)_")
    p("")

    # 6. Resource Health Snapshot
    h(2, "6. Resource Health Snapshot")
    rh = state.resource_health or {}
    if rh:
        p(f"- Samples: {rh.get('sample_count', 0)}")
        p(f"- CPU: avg {rh.get('cpu_util_mean_pct', 0):.1f}% / max {rh.get('cpu_util_max_pct', 0):.1f}%"
          f" — {'**SATURATED**' if rh.get('cpu_saturated') else 'OK'}")
        p(f"- Memory: avg {rh.get('memory_util_mean_pct', 0):.1f}% / max {rh.get('memory_util_max_pct', 0):.1f}%"
          f" — {'**SATURATED**' if rh.get('memory_saturated') else 'OK'}")
        symptoms = rh.get("symptoms", [])
        if symptoms:
            p(f"- Symptoms: {'; '.join(symptoms)}")
    else:
        p("_(no resource health data)_")
    p("")

    # 7. Observation Plans
    h(2, "7. Observation Plans")
    if state.observation_plans:
        for plan in state.observation_plans:
            status = "✓ approved" if plan.approved else f"✗ rejected ({plan.rejection_reason})"
            p(f"- `{plan.plan_id}` [{status}]: {plan.rationale[:120]}")
    else:
        p("_(no observation plans — baseline run only)_")
    p("")

    # 8. Evidence
    h(2, "8. Evidence")
    if state.evidence:
        for ev in state.evidence:
            p(f"- [{ev.confidence}] `{ev.evidence_id}` ({ev.observer}): {ev.finding}")
    else:
        p("_(no evidence collected beyond baseline)_")
    p("")

    # 9. Known Unknowns
    h(2, "9. Known Unknowns")
    if state.known_unknowns:
        for u in state.known_unknowns:
            p(f"- {u}")
    else:
        p("_(none recorded)_")
    p("")

    # 10. Suggested Next Observation
    h(2, "10. Suggested Next Observation")
    p("_This section is for profiling suggestions only — not optimization._")
    open_qs = [
        q for q in state.diagnostic_questions
        if q["question_id"] not in {e.question_id for e in state.evidence}
    ]
    if open_qs:
        top = open_qs[0]
        p(f"Highest-priority open question: [{top['priority']}] {top['text']}")
        p(f"Candidate observers: {', '.join(top['candidate_observers'])}")
    else:
        p("All diagnostic questions addressed.")
    p("")

    out_path.write_text("".join(lines), encoding="utf-8")
    return out_path
