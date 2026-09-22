from pathlib import Path

from jarvis_v2.code.impact_graph import ImpactGraph, ImpactNode, ImpactEdge
from jarvis_v2.knowledge.fusion import KnowledgeGraphFusion


def test_fuses_impact_and_diagnostic_evidence(tmp_path: Path):
    graph = ImpactGraph()
    graph.add_node(ImpactNode("file:api.py", "file", "api.py", "api.py"))
    graph.add_node(ImpactNode("route:GET /users", "api_route", "GET /users", "api.py"))
    graph.add_edge(ImpactEdge("file:api.py", "defines", "route:GET /users"))

    from jarvis_v2.diagnostics.analyzer import DiagnosticEvent
    diagnostic = DiagnosticEvent("error", "broken", "api.py", 4, "error")

    fused = KnowledgeGraphFusion(tmp_path).fuse(impact_graph=graph, diagnostics=[diagnostic])
    assert "file:api.py" in fused.nodes
    assert "route:GET /users" in fused.nodes
    assert any(n.kind == "diagnostic" for n in fused.nodes.values())
