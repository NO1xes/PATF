"""Timeline and breakdown builder.

Reads events from ProfilingState and produces:
- timeline.csv: one row per span with start_ns, end_ns, duration_ms, layer, name
- summary.json: layer-wise breakdown (total_ms, pct, dominant_span)
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from agentprof.state import ProfilingState


def build_timeline(state: ProfilingState, output_dir: Path) -> dict:
    """Build timeline.csv and summary.json from collected events.

    Returns the summary dict (also written to summary.json).
    """
    raise NotImplementedError("Milestone 2")
