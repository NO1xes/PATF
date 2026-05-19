"""Timeline builder: converts raw AgentEvents into SpanRecords.

Pairs start/end events by span_id, computes duration, identifies
wait/retry/error/unknown spans.

Input:  events.jsonl (path)
Output: list[SpanRecord], written to timeline.csv
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from agentprof.schema.events import AgentEvent
from agentprof.schema.spans import SpanRecord


def build_timeline(events_path: Path, output_dir: Path) -> list[SpanRecord]:
    """Parse events.jsonl and produce SpanRecords + timeline.csv.

    Returns the list of closed SpanRecords.
    """
    raise NotImplementedError("Milestone 1")


def write_timeline_csv(spans: list[SpanRecord], output_dir: Path) -> Path:
    """Write spans to timeline.csv. Returns path."""
    raise NotImplementedError("Milestone 1")
