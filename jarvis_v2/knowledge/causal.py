from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from jarvis_v2.code.change_intelligence import ChangedFile
from jarvis_v2.knowledge.temporal import TemporalIntelligence
from jarvis_v2.knowledge.world_graph import UnifiedWorldGraph


@dataclass
class CausalLink:
    source: str
    relation: str
    target: str
    confidence: float
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class CausalAnalysis:
    links: list[CausalLink] = field(default_factory=list)
    root_candidates: list[str] = field(default_factory=list)
    affected_nodes: list[str] = field(default_factory=list)
    explanation: str = ""

    def to_dict(self) -> dict:
        return {
            "links": [x.to_dict() for x in self.links],
            "root_candidates": self.root_candidates,
            "affected_nodes": self.affected_nodes,
            "explanation": self.explanation,
        }


class CausalChangeAnalyzer:
    """Build conservative causal hypotheses from changes and observed evidence.

    These are evidence-backed hypotheses, not claims of proven causality.
    """

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        self.temporal = TemporalIntelligence(self.root)

    def analyze(
        self,
        changed: list[ChangedFile],
        graph: UnifiedWorldGraph,
        failure_nodes: list[str] | None = None,
    ) -> CausalAnalysis:
        links: list[CausalLink] = []
        roots: list[str] = []
        affected: set[str] = set()
        changed_ids = {"file:" + x.path.replace("\\", "/") for x in changed}

        for item in changed:
            fid = "file:" + item.path.replace("\\", "/")
            if fid not in graph.nodes:
                continue
            roots.append(fid)
            frontier = [fid]
            seen = {fid}
            for depth in range(3):
                next_frontier = []
                for source in frontier:
                    for edge in graph.edges:
                        if edge.source != source or edge.target in seen:
                            continue
                        seen.add(edge.target)
                        next_frontier.append(edge.target)
                        target = graph.nodes.get(edge.target)
                        if not target:
                            continue
                        confidence = max(0.4, 0.9 - depth * 0.15)
                        links.append(CausalLink(
                            source, edge.relation, edge.target, confidence,
                            [f"graph relation: {edge.relation}", f"changed file: {item.path}"],
                        ))
                        affected.add(edge.target)
                frontier = next_frontier

        for failure_id in failure_nodes or []:
            if failure_id not in graph.nodes:
                continue
            for edge in graph.edges:
                if edge.source == failure_id and edge.target in affected:
                    links.append(CausalLink(
                        edge.target, "associated_with_failure", failure_id, 0.75,
                        ["test failure points to affected node"],
                    ))

        if roots and affected:
            explanation = (
                f"Found {len(links)} evidence-backed relationship(s) from "
                f"{len(roots)} changed file(s) across the current world graph."
            )
        elif roots:
            explanation = "Changed files were found, but no downstream graph evidence was available."
        else:
            explanation = "No changed files could be mapped into the world graph."

        return CausalAnalysis(links, sorted(set(roots)), sorted(affected), explanation)
