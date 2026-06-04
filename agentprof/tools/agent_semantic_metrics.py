"""Layer 4 — Agent Semantic profiling tools.

Trace agent-level behaviour: plan/execute/replan cycles, multi-agent
concurrency, per-agent task attribution.  These are the finest-grained
tools and require white-box observers for full detail.

In black-box mode (no observer data), we fall back to process-level
inference via psutil.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import psutil  # type: ignore[import-untyped]


def _find_events_file() -> Path | None:
    profiles_dir = Path("profiles")
    if not profiles_dir.exists():
        return None
    candidates = sorted(
        profiles_dir.glob("*/events.jsonl"),
        key=lambda p: p.stat().st_mtime, reverse=True,
    )
    return candidates[0] if candidates else None


def _load_events(events_path: Path | None = None) -> list[dict[str, Any]]:
    path = events_path or _find_events_file()
    if path is None or not path.exists():
        return []
    events: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                events.append(json.loads(line))
    except (json.JSONDecodeError, OSError):
        return []
    return events


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def list_active_agents() -> dict[str, Any]:
    """List agent processes currently running on the host.

    Heuristic: looks for Python processes whose command lines contain
    agent-related keywords (``agent``, ``react``, ``langgraph``, ``swe``,
    ``bfcl``).  Also reports Docker containers that may contain agents.

    This is a black-box-safe tool — it only uses psutil.
    """
    agent_keywords = [
        "agent", "react", "langgraph", "langchain",
        "swe-bench", "swebench", "bfcl", "theagentcompany",
        "browsergym", "workarena",
    ]

    agents: list[dict[str, Any]] = []
    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "cmdline"]):
        try:
            info = proc.info
            cmdline = " ".join(info.get("cmdline") or [])
            cmd_lower = cmdline.lower()
            if any(kw in cmd_lower for kw in agent_keywords):
                agents.append({
                    "pid": info["pid"],
                    "name": info.get("name", "?"),
                    "cpu_pct": round(info.get("cpu_percent") or 0.0, 1),
                    "mem_pct": round(info.get("memory_percent") or 0.0, 1),
                    "cmdline": cmdline[:500],
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Also check for Docker containers
    docker_containers: list[str] = []
    try:
        import subprocess
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}} {{.Image}} {{.Status}}"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            docker_containers = [
                l.strip() for l in result.stdout.strip().split("\n") if l
            ]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return {
        "agent_processes": agents,
        "agent_count": len(agents),
        "docker_containers": docker_containers,
        "docker_container_count": len(docker_containers),
        "mode": "black-box (psutil + docker ps)",
    }


def trace_agent_loop(
    program_id: str | None = None,
    duration_sec: float | None = None,
    events_path: str | None = None,
) -> dict[str, Any]:
    """Trace agent plan/execute/replan loops from collected events.

    Args:
        program_id: If given, only trace a specific program/task.
        duration_sec: If given, only look at the last N seconds.
        events_path: Path to events.jsonl.

    In white-box mode (events available), returns the ReAct loop structure:
    llm_calls, tool_calls, retry counts, step-by-step timeline.

    In black-box mode (no events), returns ``available: false``.
    """
    events = _load_events(Path(events_path) if events_path else None)
    if not events:
        return {
            "available": False,
            "error": (
                "No events.jsonl found.  Agent-loop tracing requires "
                "white-box observers (semantic_langchain) attached to "
                "the target agent runtime.  Recommend enabling semantic "
                "tracing in the next iteration."
            ),
        }

    # Filter by program_id
    if program_id:
        events = [e for e in events if e.get("program_id") == program_id]

    # Group events by span_id to reconstruct the loop
    spans: dict[str, list[dict]] = {}
    for e in events:
        sid = e.get("span_id") or "__unlinked__"
        spans.setdefault(sid, []).append(e)

    # Classify spans
    llm_spans = []
    tool_spans = []
    agent_spans = []
    for sid, evts in spans.items():
        name = evts[0].get("name", "?")
        layer = evts[0].get("layer", "?")
        starts = [e for e in evts if e.get("event_type") == "start"]
        ends = [e for e in evts if e.get("event_type") == "end"]
        duration_ms = 0.0
        if starts and ends:
            duration_ms = round((ends[0]["ts"] - starts[0]["ts"]) * 1000, 1)
        has_error = any(
            e.get("event_type") == "error"
            or e.get("attrs", {}).get("status") == "error"
            for e in evts
        )

        entry = {
            "span_id": sid,
            "name": name,
            "duration_ms": duration_ms,
            "has_error": has_error,
            "event_count": len(evts),
        }
        if layer == "llm_serving" or "llm" in name.lower():
            llm_spans.append(entry)
        elif layer == "tool_execution" or "tool" in name.lower():
            tool_spans.append(entry)
        elif layer == "agent_semantic":
            agent_spans.append(entry)

    return {
        "available": True,
        "program_id": program_id,
        "total_events": len(events),
        "loop_structure": {
            "agent_steps": len(agent_spans),
            "llm_calls": len(llm_spans),
            "tool_calls": len(tool_spans),
            "total_llm_time_ms": round(sum(s["duration_ms"] for s in llm_spans), 1),
            "total_tool_time_ms": round(sum(s["duration_ms"] for s in tool_spans), 1),
            "retry_count": sum(1 for s in tool_spans if s["has_error"]),
        },
        "llm_calls": llm_spans[:20],
        "tool_calls": tool_spans[:20],
    }


# ---------------------------------------------------------------------------
# OpenAI function-calling tool definitions
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "list_active_agents",
            "description": (
                "List agent processes currently running on the host.  "
                "Uses psutil to find Python processes with agent-related "
                "command lines, plus 'docker ps' for containerised agents.  "
                "This is black-box safe.  Use this to understand how many "
                "agents are running and which frameworks they use."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "trace_agent_loop",
            "description": (
                "Trace the agent's ReAct loop structure from collected "
                "events.  Shows plan/execute/replan cycles: how many LLM "
                "calls, tool calls, their durations, and retry counts.  "
                "Use this as the FINAL drill-down step when you have "
                "identified a specific slow agent or program.  "
                "Requires white-box observers (semantic_langchain).  "
                "If events data is not available, returns available=false "
                "— recommend enabling semantic tracing."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "program_id": {
                        "type": "string",
                        "description": "Filter to a specific program/task ID.",
                    },
                    "events_path": {
                        "type": "string",
                        "description": "Path to events.jsonl (auto-detected).",
                    },
                },
                "required": [],
            },
        },
    },
]

TOOL_DISPATCH = {
    "list_active_agents": list_active_agents,
    "trace_agent_loop": trace_agent_loop,
}
