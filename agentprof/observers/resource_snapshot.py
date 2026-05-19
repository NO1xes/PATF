"""Resource snapshot observer (Hardware/Resource Layer).

Low-cost coarse-grained snapshot: CPU, memory, GPU (if available), disk, network.
Runs alongside baseline trace — not deferred to the end.
Used for early USE health check, not root cause attribution.

Output: resource_snapshot.csv
"""

from __future__ import annotations

from agentprof.observers.base import BaseObserver
from agentprof.state import ProfilingState
from agentprof.schema.events import AgentEvent


class ResourceSnapshotObserver(BaseObserver):
    name = "resource_snapshot"
    layer = "hardware_resource"

    def __init__(self, run_id: str, interval_s: float = 1.0) -> None:
        self._run_id = run_id
        self._interval_s = interval_s
        self._buffer: list[AgentEvent] = []

    def attach(self, target: object) -> None:
        """Start background sampling thread."""
        raise NotImplementedError("Milestone 1")

    def detach(self) -> None:
        """Stop sampling thread."""
        raise NotImplementedError("Milestone 1")

    def flush(self, state: ProfilingState) -> list[AgentEvent]:
        events, self._buffer = self._buffer, []
        return events
