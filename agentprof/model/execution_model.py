"""ExecutionModel: cross-layer correlation graph.

Stores nodes, edges, and data references only.
Raw metrics, events, and resource samples live in separate files;
this model only holds the pointers (data_refs) and relationships (edges).

Node types: system_run, program_run, span, llm_request, tool_call, process, resource_entity
Edge types: parent_child, span_maps_to_request, tool_maps_to_pid,
            span_overlaps_resource_window, program_served_by_endpoint
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExecutionModel:
    trace_id: str
    nodes: dict[str, dict[str, Any]] = field(default_factory=dict)
    # node_id -> {type, name, layer, attrs}
    edges: list[dict[str, Any]] = field(default_factory=list)
    # [{src, dst, kind, attrs}]
    data_refs: dict[str, str] = field(default_factory=dict)
    # logical_name -> file path, e.g. "events" -> "profiles/run_001/events.jsonl"

    def add_node(self, node_id: str, node_type: str, layer: str, **attrs: Any) -> None:
        self.nodes[node_id] = {"type": node_type, "layer": layer, **attrs}

    def add_edge(self, src: str, dst: str, kind: str, **attrs: Any) -> None:
        self.edges.append({"src": src, "dst": dst, "kind": kind, **attrs})

    def set_data_ref(self, name: str, path: str) -> None:
        self.data_refs[name] = path
