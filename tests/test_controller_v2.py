"""Tests for the Phase 1 ReAct profiling agent prompts and context builder.

No LLM, GPU, or Docker required.
"""

from agentprof.planner.backends.llm.prompts_v2 import (
    PROFILING_AGENT_SYSTEM_PROMPT,
    build_profiling_context,
    describe_available_tools,
    get_active_tools,
    get_tool_dispatch,
)
from agentprof.controller_v2 import _build_machine_info


def test_system_prompt_contains_methodology():
    assert "AgentProf" in PROFILING_AGENT_SYSTEM_PROMPT
    assert "coarse" in PROFILING_AGENT_SYSTEM_PROMPT.lower()
    assert "Layer 1" in PROFILING_AGENT_SYSTEM_PROMPT
    assert "Hard Constraints" in PROFILING_AGENT_SYSTEM_PROMPT


def test_system_prompt_mentions_all_l1_tools():
    prompt = PROFILING_AGENT_SYSTEM_PROMPT
    assert "get_system_overview" in prompt
    assert "get_process_tree" in prompt
    assert "get_gpu_metrics" in prompt
    assert "sample_resources" in prompt


def test_build_profiling_context_returns_non_empty_string():
    ctx = build_profiling_context(
        workload_description="Test workload",
        target_system_info={
            "llm_endpoint": "http://localhost:8000/v1",
            "agent_runtime": "langchain",
            "agent_count": 2,
            "sandbox": "docker",
        },
        machine_info={"cpu_cores": 8, "memory_gb": 64, "gpu_count": 1, "gpu_model": "A100"},
        available_tool_descriptions=describe_available_tools(),
    )
    assert "Test workload" in ctx
    assert "localhost:8000" in ctx
    assert "A100" in ctx
    assert "get_system_overview" in ctx


def test_get_active_tools_includes_all_layers():
    tools = get_active_tools()
    # L1: 4 + L2: 2 + L3: 3 + L4: 2 = 11
    assert len(tools) == 11
    names = [t["function"]["name"] for t in tools]
    for expected in [
        "get_system_overview", "get_process_tree", "get_gpu_metrics", "sample_resources",
        "get_vllm_metrics", "sample_vllm_metrics",
        "observe_tool_calls", "inspect_span", "query_events",
        "list_active_agents", "trace_agent_loop",
    ]:
        assert expected in names, f"Missing tool: {expected}"


def test_get_tool_dispatch_maps_all_tools():
    dispatch = get_tool_dispatch()
    assert len(dispatch) == 11
    for name in dispatch:
        assert callable(dispatch[name]), f"Not callable: {name}"


def test_build_machine_info_has_expected_keys():
    info = _build_machine_info()
    assert "cpu_cores" in info
    assert info["cpu_cores"] > 0
    assert "memory_gb" in info
    assert "gpu_count" in info
    assert "gpu_model" in info
