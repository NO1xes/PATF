"""build_report_tool: generates the final profiling report.

Reads state and writes report.md + known_unknowns.md.

Milestone 2 implementation target.
"""

from __future__ import annotations

from pathlib import Path

from agentprof.state import ProfilingState


def build_report(state: ProfilingState, output_dir: Path) -> Path:
    """Write report.md to output_dir. Returns path."""
    raise NotImplementedError("Milestone 2")
