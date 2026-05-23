"""Tests for storage.py — event read/write.

Verifies that write_event and read_events correctly serialize and
deserialize AgentEvent objects via JSONL. No LLM required.
"""

import time
from pathlib import Path

import pytest

from agentprof.schema.events import AgentEvent
from agentprof.storage import write_event, read_events, ensure_run_dir


def make_event(event_id: str, name: str, ts: float | None = None) -> AgentEvent:
    return AgentEvent(
        event_id=event_id,
        trace_id="trace_001",
        program_id="prog_001",
        span_id=f"span_{event_id}",
        parent_span_id=None,
        layer="tool_execution",
        event_type="start",
        name=name,
        ts=ts or time.time(),
        attrs={"tool_name": name},
        source_observer="tool_events",
    )


class TestEnsureRunDir:
    def test_creates_directory(self, tmp_path):
        run_dir = ensure_run_dir(tmp_path, "run_test_001")
        assert run_dir.exists()
        assert run_dir.name == "run_test_001"

    def test_idempotent(self, tmp_path):
        ensure_run_dir(tmp_path, "run_test_001")
        ensure_run_dir(tmp_path, "run_test_001")  # should not raise


class TestWriteAndReadEvents:
    def test_write_single_event(self, tmp_path):
        events_path = tmp_path / "events.jsonl"
        evt = make_event("evt_001", "slow_tool")
        write_event(evt, events_path)
        assert events_path.exists()
        lines = events_path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1

    def test_write_multiple_events(self, tmp_path):
        events_path = tmp_path / "events.jsonl"
        for i in range(5):
            write_event(make_event(f"evt_{i:03d}", "cpu_tool"), events_path)
        lines = events_path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 5

    def test_roundtrip(self, tmp_path):
        events_path = tmp_path / "events.jsonl"
        original = [
            make_event("evt_001", "slow_tool", ts=1000.0),
            make_event("evt_002", "cpu_tool", ts=1001.0),
        ]
        for evt in original:
            write_event(evt, events_path)

        restored = read_events(events_path)
        assert len(restored) == 2
        assert restored[0].event_id == "evt_001"
        assert restored[0].name == "slow_tool"
        assert restored[1].event_id == "evt_002"
        assert restored[1].ts == pytest.approx(1001.0)

    def test_append_mode(self, tmp_path):
        events_path = tmp_path / "events.jsonl"
        write_event(make_event("evt_001", "slow_tool"), events_path)
        write_event(make_event("evt_002", "cpu_tool"), events_path)
        restored = read_events(events_path)
        assert len(restored) == 2

    def test_empty_file_returns_empty_list(self, tmp_path):
        events_path = tmp_path / "events.jsonl"
        events_path.write_text("", encoding="utf-8")
        assert read_events(events_path) == []
