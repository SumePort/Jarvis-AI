from pathlib import Path
from jarvis_v2.code.analyzer import CodeAnalyzer
from jarvis_v2.code.graph import CodeGraphBuilder

def test_python_ast_analysis(tmp_path: Path):
    p=tmp_path/"app.py"; p.write_text("class A:\n    def run(self, x):\n        return x\n",encoding="utf-8")
    symbols=CodeAnalyzer().analyze_python(p)
    assert {s.kind for s in symbols} >= {"class","function"}
    graph=CodeGraphBuilder().build({str(p):symbols})
    assert any(e["relation"]=="contains" for e in graph.edges)
