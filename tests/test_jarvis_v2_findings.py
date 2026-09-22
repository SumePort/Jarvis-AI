from pathlib import Path

from jarvis_v2.knowledge.findings import EvidenceItem, Finding, FindingStore
from jarvis_v2.knowledge.finding_graph import FindingGraphProjector
from jarvis_v2.knowledge.world_graph import UnifiedWorldGraph


def test_findings_are_stored_and_projected(tmp_path: Path):
    store = FindingStore(tmp_path / "findings.jsonl")
    evidence = EvidenceItem("ev_1", "test", "test passed", "pytest", 0.99)
    finding = Finding("fd_1", "API regression fixed", "verified", 0.95, ["ev_1"])
    store.add_evidence(evidence)
    store.add_finding(finding)

    graph = UnifiedWorldGraph()
    projector = FindingGraphProjector()
    projector.project_evidence(graph, evidence)
    projector.project_finding(graph, finding)

    assert store.find("fd_1")["status"] == "verified"
    assert "finding:fd_1" in graph.nodes
    assert any(e.relation == "supported_by" for e in graph.edges)
