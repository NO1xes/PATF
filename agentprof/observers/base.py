"""Base class for all AgentProf observers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from agentprof.schema import AgentEvent
from agentprof.state import ProfilingState


class BaseObserver(ABC):
    name: str
    layer: str

    @abstractmethod
    def attach(self, target: object) -> None:
        """Attach this observer to the target (agent, client, etc.)."""

    @abstractmethod
    def detach(self) -> None:
        """Detach and clean up."""

    def flush(self, state: ProfilingState) -> list[AgentEvent]:
        """Return collected events and clear internal buffer."""
        return []
