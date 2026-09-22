from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from jarvis_v2.knowledge.world_graph import UnifiedWorldGraph, WorldNode, WorldEdge


@dataclass(frozen=True)
class FabricQuery:
    text: str
    kinds: tuple[str, ...] = ()
    limit: int = 20
    depth: int = 1


@dataclass
class FabricResult:
    nodes: list[WorldNode] = field(default_factory=list)
    paths: list[list[str]] = field(default_factory=list)


class JarvisKnowledgeFabric:
    """Bounded query layer over JARVIS's unified world graph.

    It combines heterogeneous facts without turning the graph into an
    unrestricted execution surface. Querying is read-only.
    """

    def __init__(self, graph: UnifiedWorldGraph):
        self.graph = graph

    def add_personal_state(self, identity_id: str, profile: dict[str, Any],
                            tasks: Iterable[dict[str, Any]] = (),
                            memories: Iterable[dict[str, Any]] = ()) -> None:
        person_id = f"identity:{identity_id}"
        self.graph.add_node(WorldNode(person_id, "identity", profile.get("name") or identity_id, "personal"))
        for key, value in profile.get("preferences", {}).items():
            nid = f"preference:{identity_id}:{key}"
            self.graph.add_node(WorldNode(nid, "preference", f"{key}={value}", "personal"))
            self.graph.add_edge(WorldEdge(person_id, "prefers", nid, "personal"))
        for task in tasks:
            tid = f"task:{identity_id}:{task.get('id')}"
            self.graph.add_node(WorldNode(tid, "task", task.get("title", ""), "personal", task))
            self.graph.add_edge(WorldEdge(person_id, "owns", tid, "personal"))
        for memory in memories:
            mid = f"memory:{identity_id}:{memory.get('id')}"
            self.graph.add_node(WorldNode(mid, "memory", memory.get("text", ""), "personal", memory))
            self.graph.add_edge(WorldEdge(person_id, "remembers", mid, "personal"))

    def add_environment(self, environment: dict[str, Any]) -> None:
        for category, items in environment.items():
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                item_id = item.get("id") or item.get("path") or item.get("name") or repr(item)
                nid = f"environment:{category}:{item_id}"
                label = item.get("name") or item.get("path") or item.get("title") or str(item_id)
                self.graph.add_node(WorldNode(nid, category.rstrip("s"), str(label), "environment", item))

    def query(self, query: FabricQuery) -> FabricResult:
        terms = {x.lower() for x in query.text.split() if x.strip()}
        candidates = []
        allowed = set(query.kinds)
        for node in self.graph.nodes.values():
            if allowed and node.kind not in allowed:
                continue
            hay = f"{node.label} {node.kind} {node.source} {node.attributes}".lower()
            score = sum(1 for term in terms if term in hay)
            if score:
                candidates.append((score, node))
        candidates.sort(key=lambda x: (-x[0], x[1].id))
        selected = [node for _, node in candidates[:max(1, query.limit)]]
        paths = []
        for node in selected:
            related = self.graph.related(node.id, depth=max(0, min(query.depth, 3)))
            for other in related[:10]:
                paths.append([node.id, other.id])
        return FabricResult(selected, paths)
