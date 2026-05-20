"""ObserverCapability and ObserverRegistry.

The registry is the authoritative list of what observers exist and what they can do.
The LLM planner selects from this registry; it cannot invent observers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ObserverCapability:
    name: str
    layer: str                          # agent_semantic | llm_serving | tool_execution | hardware_resource
    observes: list[str]                 # what events/metrics it records
    required_inputs: list[str]          # e.g. ["langchain_agent"] or ["vllm_endpoint"]
    output_streams: list[str]           # e.g. ["events.jsonl", "process_resource.csv"]
    cost_level: str                     # low | medium | high
    mode: str                           # online | replay | query
    supports_time_window: bool = False
    supports_span_scope: bool = False
    constraints: dict[str, Any] = field(default_factory=dict)
    # e.g. {"requires_gpu": true, "requires_vllm_local": true}


class ObserverRegistry:
    """Loads observer definitions from observers.yaml and provides lookup."""

    def __init__(self) -> None:
        self._registry: dict[str, ObserverCapability] = {}

    def register(self, cap: ObserverCapability) -> None:
        self._registry[cap.name] = cap

    def get(self, name: str) -> ObserverCapability | None:
        return self._registry.get(name)

    def all_names(self) -> list[str]:
        return list(self._registry.keys())

    def available_for(self, machine_constraints: dict[str, Any]) -> list[ObserverCapability]:
        """Return observers whose constraints are satisfied by the current machine."""
        result = []
        for cap in self._registry.values():
            satisfied = all(
                machine_constraints.get(k) == v
                for k, v in cap.constraints.items()
            )
            if satisfied:
                result.append(cap)
        return result

    @classmethod
    def from_yaml(cls, path: str) -> "ObserverRegistry":
        """Build registry from configs/observers.yaml."""
        import yaml

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        registry = cls()
        for name, cfg in data.get("observers", {}).items():
            caps = cfg.get("capabilities", {})
            registry.register(ObserverCapability(
                name=name,
                layer=cfg["layer"],
                observes=caps.get("observes", []),
                required_inputs=caps.get("required_inputs", []),
                output_streams=caps.get("output_streams", []),
                cost_level=cfg.get("cost", "low"),
                mode=cfg.get("mode", "online"),
                supports_time_window=cfg.get("supports_time_window", False),
                supports_span_scope=cfg.get("supports_span_scope", False),
                constraints=cfg.get("constraints", {}),
            ))
        return registry
