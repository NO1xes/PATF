"""AgentProf main controller.

Orchestrates the profiling loop:
  run_workload → build_timeline → generate_questions → select_observer → repeat → export_report

MVP is rule-based. Future: LangChain tool-calling controller.
"""

from __future__ import annotations

from pathlib import Path

from agentprof.state import ProfilingState


def run_profiling(
    workload_config: dict,
    target_config: dict,
    observer_config: dict,
    profiling_spec: dict,
    output_dir: Path,
) -> ProfilingState:
    """Run the full profiling loop and return the final state.

    Writes events.jsonl, timeline.csv, summary.json, report.md to output_dir.
    """
    raise NotImplementedError("Milestone 3")
