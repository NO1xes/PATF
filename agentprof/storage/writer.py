"""Event writer: appends AgentEvents to profiles/<run_id>/events.jsonl."""

from __future__ import annotations

import json
from pathlib import Path

from agentprof.schema import AgentEvent


class EventWriter:
    def __init__(self, output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        self._path = output_dir / "events.jsonl"
        self._fh = self._path.open("a", encoding="utf-8")

    def write(self, event: AgentEvent) -> None:
        self._fh.write(event.model_dump_json() + "\n")
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()

    def __enter__(self) -> "EventWriter":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
