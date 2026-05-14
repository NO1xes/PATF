"""ProfilingState: mutable state carried through one AgentProf profiling session."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agentprof.schema import AgentEvent


@dataclass
class ProfilingState:
    run_id: str
    workload_name: str
    events: list[AgentEvent] = field(default_factory=list)
    active_observers: list[str] = field(default_factory=list)
    diagnostic_questions: list[str] = field(default_factory=list)
    breakdown: dict[str, float] = field(default_factory=dict)  # layer -> seconds
    known_unknowns: list[str] = field(default_factory=list)
    iteration: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
