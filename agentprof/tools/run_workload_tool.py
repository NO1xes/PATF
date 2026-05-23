"""run_workload_tool: deterministic tool that runs the target agent workload.

Called by the AgentProf controller (not by the LLM directly).
Starts the target agent, attaches baseline observers, writes events.jsonl.
"""

from __future__ import annotations

import os
from pathlib import Path

from agentprof.state import ProfilingState
from agentprof.storage import write_event
from agentprof.observers.backends.langchain.semantic_langchain import LangChainSemanticObserver
from agentprof.observers.backends.langchain.llm_client_timing import LLMClientTimingObserver
from agentprof.observers.backends.langchain.tool_events import ToolEventsObserver
from agentprof.observers.backends.langchain.resource_snapshot import ResourceSnapshotObserver


def run_workload(state: ProfilingState, output_dir: Path) -> Path:
    """Run the target agent under workload with baseline observers active.

    Attaches all baseline observers, runs each prompt in state.spec["workload"],
    flushes events to events.jsonl, writes resource_snapshot.csv.

    Returns path to events.jsonl.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    events_path = output_dir / "events.jsonl"

    workload = state.spec.get("workload", {})
    programs = workload.get("programs", [])
    if not programs:
        raise ValueError("state.spec['workload']['programs'] is empty — nothing to run")

    base_url = os.environ.get("VLLM_BASE_URL", "http://127.0.0.1:8000/v1")
    api_key = os.environ.get("VLLM_API_KEY", "dummy")
    model = os.environ.get("VLLM_MODEL", "Qwen/Qwen3-30B-A3B")

    from langchain_openai import ChatOpenAI
    from langgraph.prebuilt import create_react_agent
    from targets.langchain_react_agent.tools import slow_tool, cpu_tool, flaky_tool
    from targets.langchain_react_agent.agent import run_task

    run_id = state.run_id
    semantic_obs = LangChainSemanticObserver(run_id)
    llm_timing_obs = LLMClientTimingObserver(run_id)
    tool_obs = ToolEventsObserver(run_id)
    resource_obs = ResourceSnapshotObserver(run_id)

    # Wrap tools so tool_events observer captures their spans
    wrapped_slow = tool_obs.wrap_tool(slow_tool)
    wrapped_cpu = tool_obs.wrap_tool(cpu_tool)
    wrapped_flaky = tool_obs.wrap_tool(flaky_tool)

    # Build LLM client; monkey-patch it for timing before wiring into agent
    llm = ChatOpenAI(base_url=base_url, api_key=api_key, model=model, temperature=0)
    llm_timing_obs.attach(llm.client)  # patches llm.client.chat.completions.create

    agent = create_react_agent(
        llm,
        tools=[wrapped_slow, wrapped_cpu, wrapped_flaky],
        # semantic_obs is a BaseCallbackHandler; pass as callback
    )

    resource_obs.attach()
    try:
        for program in programs:
            program_id = program.get("id", run_id)
            prompt = program.get("prompt", "")
            if not prompt:
                continue
            try:
                # Pass semantic_obs as a callback so it receives LangChain events
                agent.invoke(
                    {"messages": [{"role": "user", "content": prompt}]},
                    config={"callbacks": [semantic_obs]},
                )
            except Exception:
                pass  # observer captures errors; don't abort the full run
    finally:
        resource_obs.detach()
        llm_timing_obs.detach()

    all_observers = [semantic_obs, llm_timing_obs, tool_obs, resource_obs]
    for obs in all_observers:
        for event in obs.flush(state):
            write_event(event, events_path)

    resource_obs.write_csv(output_dir)

    state.events_path = str(events_path)
    return events_path
