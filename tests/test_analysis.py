"""Tests for analysis/timeline.py, analysis/breakdown.py, and ObserverRegistry.from_yaml.

Uses the sample_events.jsonl fixture (14 events, slow_001 trace).
No LLM or vLLM required.
"""

import json
import tempfile
from pathlib import Path

import pytest

from agentprof.analysis.timeline import build_timeline, write_timeline_csv
from agentprof.analysis.breakdown import compute_breakdown, write_breakdown_json
from agentprof.model.observer_registry import ObserverRegistry

FIXTURE = Path(__file__).parent / "fixtures" / "sample_events.jsonl"
OBSERVERS_YAML = Path(__file__).parent.parent / "configs" / "observers.yaml"


class TestBuildTimeline:
    def test_returns_span_records(self, tmp_path):
        spans = build_timeline(FIXTURE, tmp_path)
        assert len(spans) > 0

    def test_span_ids_match_fixture(self, tmp_path):
        spans = build_timeline(FIXTURE, tmp_path)
        ids = {s.span_id for s in spans}
        assert "span_run" in ids
        assert "span_llm_1_client" in ids
        assert "span_tool_1_exec" in ids

    def test_duration_ms_positive(self, tmp_path):
        spans = build_timeline(FIXTURE, tmp_path)
        for s in spans:
            assert s.duration_ms > 0, f"{s.span_id} has non-positive duration"

    def test_slow_tool_duration_approx_2000ms(self, tmp_path):
        spans = build_timeline(FIXTURE, tmp_path)
        tool_span = next(s for s in spans if s.span_id == "span_tool_1_exec")
        assert 1900 <= tool_span.duration_ms <= 2100

    def test_children_populated(self, tmp_path):
        spans = build_timeline(FIXTURE, tmp_path)
        span_map = {s.span_id: s for s in spans}
        run_span = span_map["span_run"]
        assert len(run_span.children) > 0

    def test_timeline_csv_written(self, tmp_path):
        build_timeline(FIXTURE, tmp_path)
        assert (tmp_path / "timeline.csv").exists()

    def test_spans_sorted_by_start_ts(self, tmp_path):
        spans = build_timeline(FIXTURE, tmp_path)
        ts_list = [s.start_ts for s in spans]
        assert ts_list == sorted(ts_list)


class TestComputeBreakdown:
    def _spans(self, tmp_path):
        return build_timeline(FIXTURE, tmp_path)

    def test_total_ms_positive(self, tmp_path):
        bd = compute_breakdown(self._spans(tmp_path))
        assert bd["total_ms"] > 0

    def test_tool_dominates(self, tmp_path):
        bd = compute_breakdown(self._spans(tmp_path))
        # slow_tool takes ~2000ms, LLM calls ~1300ms total
        assert bd["dominant_component"] == "tool"

    def test_pct_sums_to_one(self, tmp_path):
        bd = compute_breakdown(self._spans(tmp_path))
        total = bd["llm_pct"] + bd["tool_pct"] + bd["wait_retry_pct"] + bd["unknown_pct"]
        assert abs(total - 1.0) < 0.01

    def test_llm_calls_count(self, tmp_path):
        bd = compute_breakdown(self._spans(tmp_path))
        assert bd["llm_calls"] == 2

    def test_tool_calls_count(self, tmp_path):
        bd = compute_breakdown(self._spans(tmp_path))
        assert bd["tool_calls"] == 1

    def test_breakdown_json_written(self, tmp_path):
        bd = compute_breakdown(self._spans(tmp_path))
        write_breakdown_json(bd, tmp_path)
        assert (tmp_path / "breakdown.json").exists()


class TestObserverRegistryFromYaml:
    def test_loads_all_observers(self):
        registry = ObserverRegistry.from_yaml(str(OBSERVERS_YAML))
        names = registry.all_names()
        assert "semantic_langchain" in names
        assert "llm_client_timing" in names
        assert "tool_events" in names
        assert "resource_snapshot" in names
        assert "vllm_metrics" in names

    def test_capability_fields(self):
        registry = ObserverRegistry.from_yaml(str(OBSERVERS_YAML))
        cap = registry.get("tool_events")
        assert cap is not None
        assert cap.layer == "tool_execution"
        assert cap.supports_span_scope is True
        assert cap.cost_level == "low"

    def test_constraints_loaded(self):
        registry = ObserverRegistry.from_yaml(str(OBSERVERS_YAML))
        cap = registry.get("vllm_metrics")
        assert cap.constraints.get("requires_local_vllm") is True

    def test_available_for_no_gpu(self):
        registry = ObserverRegistry.from_yaml(str(OBSERVERS_YAML))
        available = registry.available_for({})
        names = [c.name for c in available]
        # vllm_metrics requires requires_local_vllm=True, so not available on empty constraints
        assert "vllm_metrics" not in names
        assert "tool_events" in names
