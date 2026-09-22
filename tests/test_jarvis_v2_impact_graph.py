from pathlib import Path
from jarvis_v2.code.impact_graph import CrossLayerImpactBuilder


def test_builds_import_and_api_relationships(tmp_path: Path):
    (tmp_path / "service.py").write_text("def get_users(): return []\n", encoding="utf-8")
    (tmp_path / "api.py").write_text(
        "from service import get_users\n@app.get('/users')\ndef users(): return get_users()\n",
        encoding="utf-8",
    )
    graph = CrossLayerImpactBuilder(tmp_path).build()
    assert any(e.relation == "imports" for e in graph.edges)
    assert any(n.kind == "api_route" for n in graph.nodes.values())
