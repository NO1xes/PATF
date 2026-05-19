"""run_workload_tool: deterministic tool that runs the target agent workload.

Called by the AgentProf controller (not by the LLM directly).
Starts the target agent, attaches baseline observers, writes events.jsonl.

Milestone 1 implementation target.
"""

from __future__ import annotations

from pathlib import Path

from agentprof.state import ProfilingState


def run_workload(state: ProfilingState, output_dir: Path) -> Path:
    """Run the target agent under workload with baseline observers active.

    Returns path to events.jsonl.
    """
    raise NotImplementedError("Milestone 1")
