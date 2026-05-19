"""Markdown report generator.

Reads ProfilingState and writes report.md with all 10 required sections.
"""

from __future__ import annotations

from pathlib import Path

from agentprof.state import ProfilingState

REQUIRED_SECTIONS = [
    "Profiling Scope",
    "Workload",
    "Enabled Observers",
    "Initial Baseline",
    "Timeline / Breakdown",
    "Resource Health Snapshot",
    "Observation Plans",
    "Evidence",
    "Known Unknowns",
    "Suggested Next Observation",  # NOT optimization
]


def write_markdown_report(state: ProfilingState, output_dir: Path) -> Path:
    """Write report.md to output_dir. Returns path."""
    raise NotImplementedError("Milestone 2")
