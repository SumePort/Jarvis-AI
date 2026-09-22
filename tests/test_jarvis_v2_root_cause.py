from pathlib import Path

from jarvis_v2.code.change_intelligence import ChangedFile
from jarvis_v2.diagnostics.incident import IncidentReport
from jarvis_v2.diagnostics.root_cause import RootCauseInvestigator
from jarvis_v2.knowledge.world_graph import UnifiedWorldGraph, WorldNode, WorldEdge


def test_root_cause_investigation_generates_hypothesis(tmp_path: Path):
    graph = UnifiedWorldGraph()
    graph.add_node(WorldNode("file:api.py", "file", "api.py"))
    graph.add_node(WorldNode("route:GET /users", "api_route", "GET /users"))
    graph.add_edge(WorldEdge("file:api.py", "defines", "route:GET /users"))

    incident = IncidentReport(
        "inc-1", "API incident", "partial",
        suspected_changes=["api.py"],
        affected_components=["route:GET /users"],
    )
    result = RootCauseInvestigator(tmp_path).investigate(
        incident, graph, [ChangedFile("api.py", "M")]
    )
    assert result.hypotheses
    assert result.hypotheses[0].evidence_for
    assert result.next_actions
