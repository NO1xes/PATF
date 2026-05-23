"""ProfilingState: the full state of one AgentProf profiling campaign.

Carried through the entire profiling loop. Every module reads from or writes to this.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agentprof.model.execution_model import ExecutionModel
from agentprof.model.observer_registry import ObserverRegistry
from agentprof.schema.observations import ObservationPlan
from agentprof.schema.evidence import EvidenceRecord


@dataclass
class ProfilingState:
    # Campaign identity
    run_id: str
    workload_name: str

    # Config
    spec: dict = field(default_factory=dict)

    # Observer registry (loaded from observers.yaml)
    observer_registry: ObserverRegistry = field(default_factory=ObserverRegistry)

    # Cross-layer correlation graph
    execution_model: ExecutionModel = field(default_factory=lambda: ExecutionModel(trace_id=""))

    # Active observers (names from registry)
    enabled_observers: set[str] = field(default_factory=set)

    # File paths (set after each step writes output)
    events_path: str | None = None
    timeline_path: str | None = None
    breakdown: dict | None = None
    resource_health: dict | None = None

    # Drill-down state
    diagnostic_questions: list[dict] = field(default_factory=list)
    observation_plans: list[ObservationPlan] = field(default_factory=list)
    evidence: list[EvidenceRecord] = field(default_factory=list)
    known_unknowns: list[str] = field(default_factory=list)

    # Audit and budget
    action_log: list[dict] = field(default_factory=list)
    budget_used: dict[str, Any] = field(default_factory=dict)
    iteration: int = 0
