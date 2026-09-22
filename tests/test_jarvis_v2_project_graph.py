from pathlib import Path
from jarvis_v2.projects.intelligence import ProjectIntelligence
from jarvis_v2.projects.graph_builder import ProjectGraphBuilder

def test_graph_connects_files_symbols_and_dependencies(tmp_path: Path):
    (tmp_path / "requirements.txt").write_text("fastapi\n", encoding="utf-8")
    (tmp_path / "main.py").write_text("class App:\n    pass\n", encoding="utf-8")
    model = ProjectIntelligence(tmp_path).inspect()
    graph = ProjectGraphBuilder().build(model)
    assert any(e.relation == "contains" and e.target == "file:main.py" for e in graph.edges)
    assert any(e.relation == "defines" and e.target == "symbol:main.py:App" for e in graph.edges)
    assert any(e.relation == "depends_on" and e.target == "dependency:python:fastapi" for e in graph.edges)
