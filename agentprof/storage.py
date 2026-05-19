"""Storage utilities: read/write events.jsonl and other profile files."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from agentprof.schema.events import AgentEvent


def write_event(event: AgentEvent, events_path: Path) -> None:
    """Append one AgentEvent as a JSON line to events_path."""
    with events_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(event)) + "\n")


def read_events(events_path: Path) -> list[AgentEvent]:
    """Read all AgentEvents from a JSONL file."""
    events = []
    with events_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(AgentEvent(**json.loads(line)))
    return events


def ensure_run_dir(profiles_base: Path, run_id: str) -> Path:
    """Create and return profiles/<run_id>/ directory."""
    run_dir = profiles_base / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir
