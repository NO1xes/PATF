"""Controller dry-run tests.

These tests monkeypatch the workload runner so they do not call a target agent,
LLM API, vLLM, Docker, or GPU resources.
"""

import json
import shutil
import textwrap
from pathlib import Path

from agentprof.controller import run_profiling


ROOT = Path(__file__).parent.parent
FIXTURE_EVENTS = ROOT / "tests" / "fixtures" / "sample_events.jsonl"
OBSERVERS_YAML = ROOT / "configs" / "observers.yaml"
TARGET_CONFIG = ROOT / "configs" / "target_system.yaml"


def _write_yaml(path: Path, text: str) -> Path:
    path.write_text(textwrap.dedent(text).strip() + "\n", encoding="utf-8")
    return path


def test_controller_dry_run_with_rule_planner_and_fixture_events(tmp_path, monkeypatch):
    spec_path = _write_yaml(
        tmp_path / "profiling_spec.yaml",
        """
        experiment_name: controller_dry_run
        stage: test
        constraints:
          forbidden_actions:
            - change_concurrency
            - change_arrival_rate
            - toggle_cache
            - set_timeout
            - set_quota
            - apply_patch
            - modify_prompt
            - modify_planner
        stop_condition:
          max_iterations: 1
        """,
    )
    workload_path = _write_yaml(
        tmp_path / "workload.yaml",
        """
        workload_name: fixture_workload
        programs:
          - task_id: slow_001
            prompt: "Use slow tool."
        """,
    )

    def fake_run_workload(state, output_dir):
        output_dir = Path(output_dir)
        events_path = output_dir / "events.jsonl"
        shutil.copyfile(FIXTURE_EVENTS, events_path)
        state.events_path = str(events_path)
        return events_path

    monkeypatch.setenv("AGENTPROF_PLANNER", "rule")
    monkeypatch.setattr("agentprof.controller.run_workload", fake_run_workload)

    state = run_profiling(
        spec_path=str(spec_path),
        target_config_path=str(TARGET_CONFIG),
        observers_config_path=str(OBSERVERS_YAML),
        workload_config_path=str(workload_path),
        profiles_base=str(tmp_path / "profiles"),
    )

    run_dir = tmp_path / "profiles" / state.run_id
    assert (run_dir / "events.jsonl").exists()
    assert (run_dir / "timeline.csv").exists()
    assert (run_dir / "breakdown.json").exists()
    assert (run_dir / "resource_health.json").exists()
    assert (run_dir / "report.md").exists()
    assert (run_dir / "summary.json").exists()

    assert state.breakdown["dominant_component"] == "tool"
    assert len(state.observation_plans) == 1
    assert state.observation_plans[0].approved is True
    assert len(state.evidence) == 1

    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary["run_id"] == state.run_id
    assert summary["dominant_component"] == "tool"
    assert summary["observation_plans"] == 1
    assert summary["evidence_count"] == 1
