from pathlib import Path

from jarvis_v2.code.change_intelligence import ChangedFile
from jarvis_v2.knowledge.causal import CausalChangeAnalyzer
from jarvis_v2.knowledge.world_graph import UnifiedWorldGraph, WorldNode, WorldEdge


def test_causal_change_analysis(tmp_path: Path):
    graph = UnifiedWorldGraph()
    graph.add_node(WorldNode("file:api.py", "file", "api.py"))
    graph.add_node(WorldNode("route:GET /users", "api_route", "GET /users"))
    graph.add_node(WorldNode("failure:test_users", "test_failure", "test_users"))
    graph.add_edge(WorldEdge("file:api.py", "defines", "route:GET /users"))
    graph.add_edge(WorldEdge("route:GET /users", "associated_with", "failure:test_users"))

    result = CausalChangeAnalyzer(tmp_path).analyze(
        [ChangedFile("api.py", "M")], graph, ["failure:test_users"]
    )
    assert "file:api.py" in result.root_candidates
    assert "route:GET /users" in result.affected_nodes
    assert result.links
