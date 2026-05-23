"""Tests for Milestone 2 analysis modules: resource_health and questions.

No LLM or GPU required.
"""

from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path

import pytest

from agentprof.analysis.resource_health import compute_resource_health, write_resource_health_json
from agentprof.analysis.questions import generate_questions
from agentprof.model.execution_model import ExecutionModel


# --- helpers ---

def _write_snapshot_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("")
        return
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _make_rows(cpu_pct: float, mem_pct: float, n: int = 5) -> list[dict]:
    return [
        {
            "ts": 1000.0 + i,
            "cpu_pct": cpu_pct,
            "mem_used_mb": 1024.0,
            "mem_total_mb": 2048.0,
            "mem_pct": mem_pct,
            "net_sent_kb": 0.0,
            "net_recv_kb": 0.0,
            "disk_read_kb": 0.0,
            "disk_write_kb": 0.0,
        }
        for i in range(n)
    ]


# ============================================================
# resource_health
# ============================================================

class TestComputeResourceHealth:
    def test_missing_file_returns_empty(self):
        health = compute_resource_health(Path("/nonexistent/resource_snapshot.csv"))
        assert health["sample_count"] == 0
        assert health["cpu_saturated"] is False

    def test_empty_file_returns_empty(self, tmp_path):
        snap = tmp_path / "resource_snapshot.csv"
        snap.write_text("")
        health = compute_resource_health(snap)
        assert health["sample_count"] == 0

    def test_normal_run_no_symptoms(self, tmp_path):
        snap = tmp_path / "resource_snapshot.csv"
        _write_snapshot_csv(snap, _make_rows(cpu_pct=30.0, mem_pct=40.0))
        health = compute_resource_health(snap)
        assert health["sample_count"] == 5
        assert health["cpu_saturated"] is False
        assert health["memory_saturated"] is False
        assert health["symptoms"] == []
        assert "No obvious" in health["notes"]

    def test_cpu_saturation_detected(self, tmp_path):
        snap = tmp_path / "resource_snapshot.csv"
        _write_snapshot_csv(snap, _make_rows(cpu_pct=95.0, mem_pct=40.0))
        health = compute_resource_health(snap)
        assert health["cpu_saturated"] is True
        assert any("CPU" in s for s in health["symptoms"])

    def test_memory_saturation_detected(self, tmp_path):
        snap = tmp_path / "resource_snapshot.csv"
        _write_snapshot_csv(snap, _make_rows(cpu_pct=30.0, mem_pct=90.0))
        health = compute_resource_health(snap)
        assert health["memory_saturated"] is True
        assert any("Memory" in s or "memory" in s for s in health["symptoms"])

    def test_mean_and_max_computed(self, tmp_path):
        snap = tmp_path / "resource_snapshot.csv"
        rows = _make_rows(cpu_pct=50.0, mem_pct=60.0, n=4)
        rows[0]["cpu_pct"] = 10.0  # one low sample
        _write_snapshot_csv(snap, rows)
        health = compute_resource_health(snap)
        assert health["cpu_util_max_pct"] == 50.0
        assert health["cpu_util_mean_pct"] < 50.0


class TestWriteResourceHealthJson:
    def test_writes_file(self, tmp_path):
        health = {"sample_count": 3, "symptoms": []}
        out = write_resource_health_json(health, tmp_path)
        assert out.exists()
        data = json.loads(out.read_text())
        assert data["sample_count"] == 3

    def test_creates_output_dir(self, tmp_path):
        health = {"sample_count": 0, "symptoms": []}
        out_dir = tmp_path / "new_dir"
        write_resource_health_json(health, out_dir)
        assert (out_dir / "resource_health.json").exists()


# ============================================================
# questions
# ============================================================

def _tool_dominated_breakdown() -> dict:
    return {
        "total_ms": 5000.0,
        "llm_ms": 800.0, "llm_pct": 0.16,
        "tool_ms": 3800.0, "tool_pct": 0.76,
        "wait_retry_ms": 0.0, "wait_retry_pct": 0.0,
        "unknown_ms": 400.0, "unknown_pct": 0.08,
        "llm_calls": 2, "tool_calls": 3, "errors": 0,
        "dominant_component": "tool",
    }


def _llm_dominated_breakdown() -> dict:
    return {
        "total_ms": 5000.0,
        "llm_ms": 3500.0, "llm_pct": 0.70,
        "tool_ms": 500.0, "tool_pct": 0.10,
        "wait_retry_ms": 0.0, "wait_retry_pct": 0.0,
        "unknown_ms": 1000.0, "unknown_pct": 0.20,
        "llm_calls": 2, "tool_calls": 1, "errors": 0,
        "dominant_component": "llm",
    }


def _clean_health() -> dict:
    return {
        "cpu_saturated": False, "memory_saturated": False,
        "cpu_util_max_pct": 30.0, "memory_util_max_pct": 40.0,
        "symptoms": [],
    }


class TestGenerateQuestions:
    def test_returns_list(self):
        em = ExecutionModel(trace_id="t1")
        qs = generate_questions(_tool_dominated_breakdown(), _clean_health(), em)
        assert isinstance(qs, list)

    def test_tool_dominated_produces_tool_question(self):
        em = ExecutionModel(trace_id="t1")
        qs = generate_questions(_tool_dominated_breakdown(), _clean_health(), em)
        texts = " ".join(q["text"] for q in qs)
        assert "tool" in texts.lower() or "Tool" in texts

    def test_llm_dominated_produces_llm_question(self):
        em = ExecutionModel(trace_id="t1")
        qs = generate_questions(_llm_dominated_breakdown(), _clean_health(), em)
        texts = " ".join(q["text"] for q in qs)
        assert "llm" in texts.lower() or "LLM" in texts

    def test_questions_sorted_by_priority(self):
        em = ExecutionModel(trace_id="t1")
        qs = generate_questions(_tool_dominated_breakdown(), _clean_health(), em)
        priorities = [q["priority"] for q in qs]
        assert priorities == sorted(priorities)

    def test_cpu_saturation_adds_question(self):
        em = ExecutionModel(trace_id="t1")
        health = {**_clean_health(), "cpu_saturated": True, "cpu_util_max_pct": 95.0}
        qs = generate_questions(_tool_dominated_breakdown(), health, em)
        texts = " ".join(q["text"] for q in qs)
        assert "CPU" in texts or "cpu" in texts.lower()

    def test_high_unknown_pct_adds_question(self):
        em = ExecutionModel(trace_id="t1")
        bd = {**_tool_dominated_breakdown(), "unknown_pct": 0.25, "dominant_component": "tool"}
        qs = generate_questions(bd, _clean_health(), em)
        texts = " ".join(q["text"] for q in qs)
        assert "unattributed" in texts.lower() or "unknown" in texts.lower() or "gap" in texts.lower()

    def test_errors_add_question(self):
        em = ExecutionModel(trace_id="t1")
        bd = {**_tool_dominated_breakdown(), "errors": 1}
        qs = generate_questions(bd, _clean_health(), em)
        texts = " ".join(q["text"] for q in qs)
        assert "error" in texts.lower() or "retry" in texts.lower()

    def test_question_ids_unique(self):
        em = ExecutionModel(trace_id="t1")
        qs = generate_questions(_tool_dominated_breakdown(), _clean_health(), em)
        ids = [q["question_id"] for q in qs]
        assert len(ids) == len(set(ids))

    def test_candidate_observers_nonempty(self):
        em = ExecutionModel(trace_id="t1")
        qs = generate_questions(_tool_dominated_breakdown(), _clean_health(), em)
        for q in qs:
            assert q["candidate_observers"], f"question {q['question_id']} has no observers"

    def test_no_questions_when_all_clean(self):
        em = ExecutionModel(trace_id="t1")
        bd = {
            "total_ms": 1000.0, "llm_ms": 400.0, "llm_pct": 0.40,
            "tool_ms": 300.0, "tool_pct": 0.30, "wait_retry_ms": 0.0,
            "wait_retry_pct": 0.0, "unknown_ms": 0.0, "unknown_pct": 0.0,
            "llm_calls": 1, "tool_calls": 1, "errors": 0,
            "dominant_component": "none",
        }
        qs = generate_questions(bd, _clean_health(), em)
        assert qs == []
