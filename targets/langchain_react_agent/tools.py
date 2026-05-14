"""Controlled tools for MVP-0 workload.

Three tools designed to exercise distinct bottleneck patterns:
- slow_tool: I/O wait (sleeps 2s)
- cpu_tool: CPU-bound computation
- flaky_tool: fails on first call, succeeds on second (tests error + retry attribution)
"""

from __future__ import annotations

import time

from langchain_core.tools import tool


@tool
def slow_tool(dummy: str = "") -> str:
    """Wait for 2 seconds and return a confirmation. Use this tool when asked to wait."""
    time.sleep(2.0)
    return "Waited 2 seconds."


@tool
def cpu_tool(n: int = 500_000) -> str:
    """Run a CPU-bound computation (sum of range n). Use this tool when asked to compute."""
    result = sum(range(n))
    return f"Computed sum(range({n})) = {result}"


_flaky_call_count: dict[str, int] = {}


@tool
def flaky_tool(task_id: str = "default") -> str:
    """Attempt an operation that may fail. Retry once if it fails."""
    _flaky_call_count[task_id] = _flaky_call_count.get(task_id, 0) + 1
    if _flaky_call_count[task_id] == 1:
        raise RuntimeError("flaky_tool: transient failure on first attempt")
    return f"flaky_tool succeeded on attempt {_flaky_call_count[task_id]}."
