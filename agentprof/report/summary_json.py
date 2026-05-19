"""Summary JSON writer.

Produces summary.json from breakdown + resource_health + known_unknowns.
"""

from __future__ import annotations

import json
from pathlib import Path

from agentprof.state import ProfilingState


def write_summary_json(state: ProfilingState, output_dir: Path) -> Path:
    """Write summary.json to output_dir. Returns path."""
    raise NotImplementedError("Milestone 2")
