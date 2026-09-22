from __future__ import annotations

from dataclasses import dataclass, field
from jarvis_v2.knowledge.world_graph import UnifiedWorldGraph, WorldNode, WorldEdge
from jarvis_v2.knowledge.temporal import TemporalIntelligence


@dataclass
class TimelineEvidence:
    node_id: str
    commits: list[str] = field(default_factory=list)
    changed_paths: list[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict:
        return self.__dict__.copy()


class WorldTimeline:
    """Attach Git history to world-graph entities without mutating repository state."""

    def __init__(self, temporal: TemporalIntelligence):
        self.temporal = temporal

    def enrich(self, graph: UnifiedWorldGraph, paths: list[str] | None = None) -> list[TimelineEvidence]:
        evidence = []
        selected = set(paths or [])
        for node in graph.nodes.values():
            path = node.attributes.get("file") or node.source if node.kind == "file" else node.attributes.get("file")
            if not path or (selected and path not in selected):
                continue
            try:
                history = self.temporal.file_history(path)
            except (OSError, ValueError, RuntimeError):
                continue
            if history.commits:
                evidence.append(TimelineEvidence(
                    node.id, history.commits,
                    [path],
                    f"{path} has {len(history.commits)} recorded commit(s).",
                ))
        return evidence

    def attach(self, graph: UnifiedWorldGraph, evidence: list[TimelineEvidence]) -> UnifiedWorldGraph:
        for item in evidence:
            node = graph.nodes.get(item.node_id)
            if not node:
                continue
            attrs = dict(node.attributes)
            attrs["commits"] = item.commits
            attrs["history_summary"] = item.summary
            graph.nodes[item.node_id] = WorldNode(node.id, node.kind, node.label, node.source, attrs)
            for commit in item.commits[:10]:
                cid = "commit:" + commit
                graph.add_node(WorldNode(cid, "commit", commit, "git"))
                graph.add_edge(WorldEdge(item.node_id, "changed_in", cid, "git"))
        return graph
