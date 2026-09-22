"""Turn a user request into targeted context from memory and project graph."""
from __future__ import annotations
from dataclasses import dataclass, field
import re
from typing import Any

from jarvis_v2.memory import MemoryStore
from jarvis_v2.projects.world_model import ProjectWorldModel

@dataclass
class RetrievalResult:
    query: str
    memories: list[dict[str, Any]] = field(default_factory=list)
    graph_nodes: list[dict[str, Any]] = field(default_factory=list)
    graph_edges: list[dict[str, Any]] = field(default_factory=list)
    source_targets: list[str] = field(default_factory=list)

    def to_context(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "memories": self.memories,
            "project_graph": {"nodes": self.graph_nodes, "edges": self.graph_edges},
            "source_targets": self.source_targets,
        }

class ContextRetriever:
    def __init__(self, memory: MemoryStore | None = None) -> None:
        self.memory = memory or MemoryStore()

    def retrieve(self, query: str, world_model: ProjectWorldModel | None = None, limit: int = 8) -> RetrievalResult:
        result = RetrievalResult(query=query)
        memories = self.memory.search(query, limit=limit, project=world_model.project.root if world_model else None)
        result.memories = [{"id": m.id, "kind": m.kind, "text": m.text, "source": m.source, "tags": m.tags} for m in memories]
        if world_model:
            terms = set(re.findall(r"[a-zA-Z0-9_./-]+", query.lower()))
            matched = []
            for node in world_model.graph.nodes.values():
                hay = (node.label + " " + node.id).lower()
                if any(t in hay for t in terms if len(t) > 2):
                    matched.append(node)
            # Always include the project root so graph context has an anchor.
            matched_ids = {n.id for n in matched}
            root_id = "project:" + world_model.project.root
            if root_id in world_model.graph.nodes:
                matched_ids.add(root_id)
            # Expand one hop from matched nodes.
            expanded = set(matched_ids)
            for edge in world_model.graph.edges:
                if edge.source in matched_ids or edge.target in matched_ids:
                    expanded.add(edge.source); expanded.add(edge.target)
            result.graph_nodes = [world_model.graph.nodes[x].__dict__ for x in expanded if x in world_model.graph.nodes]
            result.graph_edges = [e.__dict__ for e in world_model.graph.edges if e.source in expanded and e.target in expanded]
            result.source_targets = sorted({n.attributes.get("file") for n in world_model.graph.nodes.values() if n.id in expanded and n.attributes.get("file")})
        return result
