"""LangChain ReAct target agent.

This is the agent being profiled — not the profiler.
AgentProf attaches observers externally; this file should not import agentprof.

Milestone 1 implementation target.
"""

from __future__ import annotations

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from targets.langchain_react_agent.tools import slow_tool, cpu_tool, flaky_tool


def build_agent(base_url: str, api_key: str, model: str):
    """Build and return a LangGraph ReAct agent with controlled tools."""
    llm = ChatOpenAI(
        base_url=base_url,
        api_key=api_key,
        model=model,
        temperature=0,
    )
    return create_react_agent(llm, tools=[slow_tool, cpu_tool, flaky_tool])


def run_task(agent, prompt: str) -> str:
    """Run a single task and return the final answer string."""
    raise NotImplementedError("Milestone 1")
