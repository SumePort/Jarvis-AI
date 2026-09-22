from __future__ import annotations

from jarvis_v2.knowledge.findings import EvidenceItem, Finding
from jarvis_v2.knowledge.world_graph import UnifiedWorldGraph, WorldEdge, WorldNode


class FindingGraphProjector:
    """Project verified evidence and findings into the unified world graph."""

    def project_evidence(self, graph: UnifiedWorldGraph, evidence: EvidenceItem) -> None:
        node_id = "evidence:" + evidence.id
        graph.add_node(WorldNode(
            node_id, "evidence", evidence.statement, "finding_store",
            {"kind": evidence.kind, "source": evidence.source, "confidence": evidence.confidence},
        ))

    def project_finding(self, graph: UnifiedWorldGraph, finding: Finding) -> None:
        node_id = "finding:" + finding.id
        graph.add_node(WorldNode(
            node_id, "finding", finding.statement, "finding_store",
            {"status": finding.status, "confidence": finding.confidence},
        ))
        for evidence_id in finding.evidence_ids:
            target = "evidence:" + evidence_id
            if target in graph.nodes:
                graph.add_edge(WorldEdge(node_id, "supported_by", target, "findings"))
        for hypothesis_id in finding.rejected_hypothesis_ids:
            hid = "hypothesis:" + hypothesis_id
            if hid in graph.nodes:
                graph.add_edge(WorldEdge(node_id, "rejects", hid, "findings"))
