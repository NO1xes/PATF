"""Report generator.

Reads summary.json and events from ProfilingState and writes report.md.
"""

from __future__ import annotations

from pathlib import Path

from agentprof.state import ProfilingState


def export_report(state: ProfilingState, output_dir: Path) -> Path:
    """Write report.md to output_dir. Returns the path to the written file."""
    raise NotImplementedError("Milestone 2")
