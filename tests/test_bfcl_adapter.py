"""Tests for BFCL workload adapter.

These tests use tiny local fixtures and do not run BFCL or call any model.
"""

import yaml
from pathlib import Path

from agentprof.adapters.bfcl import (
    cases_to_workload,
    filter_cases,
    load_bfcl_cases,
    write_workload_yaml,
)


FIXTURE = Path(__file__).parent / "fixtures" / "bfcl_cases.jsonl"


def test_load_bfcl_cases_from_jsonl_fixture():
    cases = load_bfcl_cases(FIXTURE)
    assert len(cases) == 2
    assert cases[0]["id"] == "multi_turn_base_15"


def test_filter_cases_by_run_id():
    cases = load_bfcl_cases(FIXTURE)
    selected = filter_cases(cases, run_ids=["multi_turn_miss_func_03"])
    assert len(selected) == 1
    assert selected[0]["test_case_id"] == "multi_turn_miss_func_03"


def test_cases_to_workload_renders_programs():
    cases = filter_cases(load_bfcl_cases(FIXTURE), limit=1)
    workload = cases_to_workload(cases, source_path=str(FIXTURE))
    program = workload["programs"][0]
    assert workload["workload_name"] == "bfcl_v3_demo_subset"
    assert program["task_id"] == "multi_turn_base_15"
    assert "calendar event" in program["prompt"]
    assert "calendar_search" in program["notes"]


def test_write_workload_yaml(tmp_path):
    workload = cases_to_workload(load_bfcl_cases(FIXTURE))
    out_path = write_workload_yaml(workload, tmp_path / "workload_bfcl.yaml")
    data = yaml.safe_load(out_path.read_text(encoding="utf-8"))
    assert data["source"]["version"] == "v3"
    assert len(data["programs"]) == 2
