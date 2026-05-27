"""Tests for report writers.

No LLM, vLLM, or GPU required.
"""

import json

from agentprof.report.markdown_report import write_markdown_report
from agentprof.report.summary_json import write_summary_json
from agentprof.state import ProfilingState


def _state_with_program_breakdown() -> ProfilingState:
    return ProfilingState(
        run_id="run_report_test",
        workload_name="controlled_multi_program",
        spec={
            "experiment_name": "report_test",
            "stage": "test",
            "workload": {
                "programs": [
                    {"id": "slow_001", "prompt": "wait"},
                    {"id": "cpu_001", "prompt": "compute"},
                ],
            },
        },
        breakdown={
            "total_ms": 3700.0,
            "llm_ms": 900.0,
            "llm_pct": 0.2432,
            "tool_ms": 2800.0,
            "tool_pct": 0.7568,
            "wait_retry_ms": 0.0,
            "wait_retry_pct": 0.0,
            "unknown_ms": 0.0,
            "unknown_pct": 0.0,
            "llm_calls": 2,
            "tool_calls": 2,
            "errors": 0,
            "dominant_component": "tool",
            "program_count": 2,
            "slowest_program_id": "slow_001",
            "slowest_program_ms": 2500.0,
            "programs": {
                "slow_001": {
                    "total_ms": 2500.0,
                    "llm_ms": 500.0,
                    "llm_pct": 0.2,
                    "tool_ms": 2000.0,
                    "tool_pct": 0.8,
                    "wait_retry_ms": 0.0,
                    "wait_retry_pct": 0.0,
                    "unknown_ms": 0.0,
                    "unknown_pct": 0.0,
                    "llm_calls": 1,
                    "tool_calls": 1,
                    "errors": 0,
                    "dominant_component": "tool",
                },
                "cpu_001": {
                    "total_ms": 1200.0,
                    "llm_ms": 400.0,
                    "llm_pct": 0.3333,
                    "tool_ms": 800.0,
                    "tool_pct": 0.6667,
                    "wait_retry_ms": 0.0,
                    "wait_retry_pct": 0.0,
                    "unknown_ms": 0.0,
                    "unknown_pct": 0.0,
                    "llm_calls": 1,
                    "tool_calls": 1,
                    "errors": 0,
                    "dominant_component": "tool",
                },
            },
        },
        resource_health={
            "sample_count": 2,
            "cpu_util_mean_pct": 10.0,
            "cpu_util_max_pct": 20.0,
            "memory_util_mean_pct": 30.0,
            "memory_util_max_pct": 40.0,
            "cpu_saturated": False,
            "memory_saturated": False,
            "symptoms": [],
        },
    )


def test_markdown_report_includes_program_breakdown_table(tmp_path):
    state = _state_with_program_breakdown()
    out_path = write_markdown_report(state, tmp_path)

    text = out_path.read_text(encoding="utf-8")
    assert "| Program | Time (ms) | Dominant | LLM | Tool | Wait/Retry | Unknown | Errors |" in text
    assert "| `slow_001` | 2500 | tool | 20.0% | 80.0% | 0.0% | 0.0% | 0 |" in text
    assert "| `cpu_001` | 1200 | tool | 33.3% | 66.7% | 0.0% | 0.0% | 0 |" in text
    assert "Slowest program: `slow_001` (2500 ms)" in text


def test_summary_json_includes_program_breakdown_fields(tmp_path):
    state = _state_with_program_breakdown()
    out_path = write_summary_json(state, tmp_path)

    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert data["program_count"] == 2
    assert data["slowest_program_id"] == "slow_001"
    assert data["programs"]["slow_001"]["tool_ms"] == 2000.0
    assert data["programs"]["cpu_001"]["llm_calls"] == 1
