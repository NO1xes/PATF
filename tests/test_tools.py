"""Tests for controlled tools in targets/langchain_react_agent/tools.py.

Verifies that slow_tool, cpu_tool, and flaky_tool behave as designed.
These tools are the controlled workload for MVP-0.
No LLM or vLLM required.
"""

import time

import pytest

# Import the underlying Python functions (not the LangChain @tool wrappers)
# to test behavior directly without needing a LangChain agent.
from targets.langchain_react_agent import tools as tool_module
from agentprof.schema.events import AgentEvent
from agentprof.tools.run_workload_tool import _tag_event_program


def reset_flaky():
    """Reset flaky_tool call counter between tests."""
    tool_module._flaky_call_count.clear()


class TestSlowTool:
    def test_returns_string(self):
        result = tool_module.slow_tool.invoke({"dummy": ""})
        assert isinstance(result, str)
        assert "2" in result or "Wait" in result.lower() or "waited" in result.lower()

    def test_takes_approximately_2_seconds(self):
        start = time.monotonic()
        tool_module.slow_tool.invoke({"dummy": ""})
        elapsed = time.monotonic() - start
        assert 1.8 <= elapsed <= 3.0, f"Expected ~2s, got {elapsed:.2f}s"


class TestCpuTool:
    def test_returns_string_with_result(self):
        result = tool_module.cpu_tool.invoke({"n": 1000})
        assert isinstance(result, str)
        assert "499500" in result  # sum(range(1000)) = 499500

    def test_completes_quickly_for_small_n(self):
        start = time.monotonic()
        tool_module.cpu_tool.invoke({"n": 10000})
        elapsed = time.monotonic() - start
        assert elapsed < 2.0


class TestFlakyTool:
    def test_first_call_raises(self):
        reset_flaky()
        with pytest.raises(Exception, match="transient failure"):
            tool_module.flaky_tool.invoke({"task_id": "test_first"})

    def test_second_call_succeeds(self):
        reset_flaky()
        with pytest.raises(Exception):
            tool_module.flaky_tool.invoke({"task_id": "test_second"})
        result = tool_module.flaky_tool.invoke({"task_id": "test_second"})
        assert "succeeded" in result.lower()

    def test_different_task_ids_are_independent(self):
        reset_flaky()
        with pytest.raises(Exception):
            tool_module.flaky_tool.invoke({"task_id": "task_a"})
        # task_b has its own counter, first call should also fail
        with pytest.raises(Exception):
            tool_module.flaky_tool.invoke({"task_id": "task_b"})
        # second call for task_a should succeed
        result = tool_module.flaky_tool.invoke({"task_id": "task_a"})
        assert "succeeded" in result.lower()


class TestRunWorkloadProgramTagging:
    def test_rewrites_program_id_and_task_id(self):
        event = AgentEvent(
            event_id="evt_test",
            trace_id="trace_run_123",
            program_id="run_123",
            span_id="span_run",
            parent_span_id=None,
            layer="agent_semantic",
            event_type="start",
            name="run",
            ts=1.0,
            attrs={"task_id": "run_123"},
            source_observer="semantic_langchain",
        )
        _tag_event_program(event, "slow_001", "run_123")
        assert event.program_id == "slow_001"
        assert event.attrs["task_id"] == "slow_001"
