"""Summary JSON writer."""

from __future__ import annotations

import json
from pathlib import Path

from agentprof.state import ProfilingState


def write_summary_json(state: ProfilingState, output_dir: Path) -> Path:
    """Write summary.json to output_dir. Returns path."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "summary.json"

    summary = {
        "run_id": state.run_id,
        "workload_name": state.workload_name,
        "breakdown": state.breakdown,
        "resource_health": state.resource_health,
        "dominant_component": (state.breakdown or {}).get("dominant_component", "none"),
        "program_count": (state.breakdown or {}).get("program_count", 0),
        "programs": (state.breakdown or {}).get("programs", {}),
        "slowest_program_id": (state.breakdown or {}).get("slowest_program_id"),
        "observation_plans": len(state.observation_plans),
        "evidence_count": len(state.evidence),
        "known_unknowns": state.known_unknowns,
        "diagnostic_questions": [
            {"id": q["question_id"], "priority": q["priority"], "text": q["text"]}
            for q in state.diagnostic_questions
        ],
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    return out_path
