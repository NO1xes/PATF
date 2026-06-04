"""Tests for Layer 2–4 profiling tools.

No LLM, GPU, or Docker required.
"""

from agentprof.tools.llm_serving_metrics import get_vllm_metrics, sample_vllm_metrics
from agentprof.tools.tool_execution_metrics import (
    inspect_span,
    observe_tool_calls,
    query_events,
)
from agentprof.tools.agent_semantic_metrics import (
    list_active_agents,
    trace_agent_loop,
)


# -- Layer 2 -----------------------------------------------------------


def test_get_vllm_metrics_unreachable_default():
    """Default port 18796 is not running — should return error gracefully."""
    result = get_vllm_metrics(metrics_url="http://localhost:18796/metrics")
    assert "error" in result
    assert "unreachable" in result["error"].lower()


def test_sample_vllm_metrics_unreachable():
    result = sample_vllm_metrics(duration_sec=0.3, interval_sec=0.1)
    assert result["summary"]["sample_count"] >= 1
    assert not result["summary"]["endpoint_reachable"]


# -- Layer 3 -----------------------------------------------------------


def test_observe_tool_calls_no_data():
    result = observe_tool_calls(events_path="/nonexistent/events.jsonl")
    assert result["available"] is False
    assert "No events" in result["error"]


def test_inspect_span_no_data():
    result = inspect_span("fake_span", events_path="/nonexistent/events.jsonl")
    assert result["available"] is False


def test_query_events_no_data():
    result = query_events(layer="tool_execution", events_path="/nonexistent/events.jsonl")
    assert result["available"] is False


# -- Layer 4 -----------------------------------------------------------


def test_list_active_agents_returns_dict():
    result = list_active_agents()
    assert "agent_processes" in result
    assert "agent_count" in result
    assert "docker_containers" in result
    assert isinstance(result["agent_count"], int)


def test_trace_agent_loop_no_data():
    result = trace_agent_loop(events_path="/nonexistent/events.jsonl")
    assert result["available"] is False
