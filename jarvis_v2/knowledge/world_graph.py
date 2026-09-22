from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class WorldNode:
    id: str
    kind: str
    label: str
    source: str = ""
    attributes: dict = field(default_factory=dict)


@dataclass(frozen=True)
class WorldEdge:
    source: str
    relation: str
    target: str
    source_layer: str = ""


@dataclass
class UnifiedWorldGraph:
    nodes: dict[str, WorldNode] = field(default_factory=dict)
    edges: list[WorldEdge] = field(default_factory=list)

    def add_node(self, node: WorldNode) -> None:
        self.nodes[node.id] = node

    def add_edge(self, edge: WorldEdge) -> None:
        if edge.source in self.nodes and edge.target in self.nodes:
            if edge not in self.edges:
                self.edges.append(edge)

    def neighbors(self, node_id: str, relation: str | None = None) -> list[WorldNode]:
        ids = [
            e.target for e in self.edges
            if e.source == node_id and (relation is None or e.relation == relation)
        ]
        return [self.nodes[i] for i in ids]

    def related(self, node_id: str, depth: int = 1) -> list[WorldNode]:
        depth = max(0, depth)
        seen = {node_id}
        frontier = [node_id]
        for _ in range(depth):
            next_frontier = []
            for current in frontier:
                for edge in self.edges:
                    if edge.source == current and edge.target not in seen:
                        seen.add(edge.target)
                        next_frontier.append(edge.target)
                    elif edge.target == current and edge.source not in seen:
                        seen.add(edge.source)
                        next_frontier.append(edge.source)
            frontier = next_frontier
        return [self.nodes[i] for i in seen if i != node_id and i in self.nodes]

    def to_dict(self) -> dict:
        return {
            "nodes": [n.__dict__ for n in self.nodes.values()],
            "edges": [e.__dict__ for e in self.edges],
        }
