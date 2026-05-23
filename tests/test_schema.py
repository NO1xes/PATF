"""Tests for schema data structures.

These tests verify that AgentEvent, SpanRecord, ObservationPlan, and EvidenceRecord
can be constructed, serialized to JSON, and deserialized correctly.
No LLM or vLLM required.
"""

import json
import time

import pytest

from agentprof.schema.events import AgentEvent
from agentprof.schema.spans import SpanRecord
from agentprof.schema.observations import ObservationPlan
from agentprof.schema.evidence import EvidenceRecord


def make_event(**kwargs) -> AgentEvent:
    defaults = dict(
        event_id="evt_001",
        trace_id="trace_001",
        program_id="prog_001",
        span_id="span_001",
        parent_span_id=None,
        layer="tool_execution",
        event_type="start",
        name="slow_tool",
        ts=time.time(),
        attrs={"tool_name": "slow_tool"},
        source_observer="tool_events",
    )
    defaults.update(kwargs)
    return AgentEvent(**defaults)


class TestAgentEvent:
    def test_construction(self):
        evt = make_event()
        assert evt.event_id == "evt_001"
        assert evt.layer == "tool_execution"
        assert evt.attrs["tool_name"] == "slow_tool"

    def test_json_roundtrip(self):
        import dataclasses
        evt = make_event()
        d = dataclasses.asdict(evt)
        serialized = json.dumps(d)
        restored = json.loads(serialized)
        assert restored["event_id"] == evt.event_id
        assert restored["trace_id"] == evt.trace_id

    def test_optional_fields_default_none(self):
        evt = make_event(span_id=None, parent_span_id=None, raw_ref=None)
        assert evt.span_id is None
        assert evt.raw_ref is None


class TestSpanRecord:
    def test_construction(self):
        span = SpanRecord(
            trace_id="trace_001",
            program_id="prog_001",
            span_id="span_001",
            parent_span_id=None,
            span_kind="TOOL",
            name="slow_tool",
            start_ts=1000.0,
            end_ts=1002.0,
            duration_ms=2000.0,
        )
        assert span.duration_ms == 2000.0
        assert span.span_kind == "TOOL"
        assert span.error is False
        assert span.is_retry is False

    def test_children_default_empty(self):
        span = SpanRecord(
            trace_id="t", program_id="p", span_id="s",
            parent_span_id=None, span_kind="LLM", name="llm_call",
            start_ts=0.0, end_ts=1.0, duration_ms=1000.0,
        )
        assert span.children == []


class TestObservationPlan:
    def test_construction(self):
        plan = ObservationPlan(
            plan_id="plan_001",
            question_id="q_001",
            observers=["tool_events", "tool_process"],
            scope={"program_id": "prog_001"},
            mode="same_run",
            rationale="tool_time dominates at 58%",
            expected_evidence=["tool_duration_breakdown"],
        )
        assert plan.approved is False
        assert plan.rejection_reason == ""
        assert "tool_events" in plan.observers

    def test_default_mode(self):
        plan = ObservationPlan(
            plan_id="p", question_id="q", observers=["tool_events"]
        )
        assert plan.mode == "same_run"


class TestEvidenceRecord:
    def test_construction(self):
        ev = EvidenceRecord(
            evidence_id="ev_001",
            question_id="q_001",
            plan_id="plan_001",
            observer="tool_events",
            layer="tool_execution",
            finding="slow_tool accounts for 95% of tool_time",
            data_ref="profiles/run_001/events.jsonl",
        )
        assert ev.confidence == "low"
        assert ev.finding.startswith("slow_tool")
