"""Relationship graph for project intelligence."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class GraphNode:
    id: str
    kind: str
    label: str
    attributes: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class GraphEdge:
    source: str
    relation: str
    target: str
    attributes: dict[str, Any] = field(default_factory=dict)

class ProjectGraph:
    def __init__(self) -> None:
        self.nodes: dict[str, GraphNode] = {}
        self.edges: list[GraphEdge] = []

    def add_node(self, node: GraphNode) -> None:
        self.nodes[node.id] = node

    def add_edge(self, edge: GraphEdge) -> None:
        if edge.source in self.nodes and edge.target in self.nodes:
            self.edges.append(edge)

    def neighbors(self, node_id: str, relation: str | None = None) -> list[GraphNode]:
        targets = [e.target for e in self.edges if e.source == node_id and (relation is None or e.relation == relation)]
        return [self.nodes[x] for x in targets if x in self.nodes]

    def to_dict(self) -> dict[str, Any]:
        return {"nodes": [n.__dict__ for n in self.nodes.values()], "edges": [e.__dict__ for e in self.edges]}
