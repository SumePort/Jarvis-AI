from jarvis_v2.knowledge.world_graph import UnifiedWorldGraph
from jarvis_v2.knowledge.fabric import JarvisKnowledgeFabric, FabricQuery


def test_fabric_connects_personal_state():
    graph = UnifiedWorldGraph()
    fabric = JarvisKnowledgeFabric(graph)
    fabric.add_personal_state(
        "shubham",
        {"name": "Shubham", "preferences": {"theme": "dark"}},
        [{"id": "t1", "title": "Build JARVIS"}],
        [{"id": "m1", "text": "SumePort is important"}],
    )
    result = fabric.query(FabricQuery("dark theme", limit=5))
    assert any(node.kind == "preference" for node in result.nodes)


def test_fabric_queries_environment():
    graph = UnifiedWorldGraph()
    fabric = JarvisKnowledgeFabric(graph)
    fabric.add_environment({"applications": [{"id": "chrome", "name": "Chrome"}]})
    result = fabric.query(FabricQuery("Chrome", limit=5))
    assert result.nodes[0].label == "Chrome"
