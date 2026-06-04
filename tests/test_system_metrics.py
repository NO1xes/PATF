"""Tests for Layer 1 system metrics tools.

No LLM, GPU, Docker, or vLLM required.
"""

from agentprof.tools.system_metrics import (
    get_gpu_metrics,
    get_process_tree,
    get_system_overview,
    sample_resources,
)


def test_get_system_overview_has_expected_keys():
    result = get_system_overview()
    assert "cpu" in result
    assert "memory" in result
    assert "disk" in result
    assert "network" in result
    assert result["cpu"]["util_pct"] >= 0.0
    assert result["memory"]["total_gb"] > 0


def test_get_process_tree_returns_top_n():
    result = get_process_tree(top_n=3)
    assert len(result["processes"]) <= 3
    assert result["total_process_count"] > 0
    for p in result["processes"]:
        assert "pid" in p
        assert "name" in p
        assert "cpu_pct" in p


def test_get_gpu_metrics_returns_dict():
    result = get_gpu_metrics()
    assert "gpus" in result
    # On a machine without nvidia-smi, we just get the error key.
    if result.get("error"):
        assert len(result["gpus"]) == 0


def test_sample_resources_basic():
    result = sample_resources(duration_sec=0.3, interval_sec=0.1)
    assert len(result["samples"]) >= 2
    assert result["summary"]["sample_count"] >= 2
    assert result["summary"]["cpu"]["mean"] >= 0.0
