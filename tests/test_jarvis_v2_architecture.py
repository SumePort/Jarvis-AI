from pathlib import Path
from jarvis_v2.code.dependencies import DependencyAnalyzer
from jarvis_v2.code.architecture import ArchitectureModel

def test_dependency_and_route_analysis(tmp_path: Path):
    (tmp_path/"requirements.txt").write_text("fastapi>=1\nrequests==2\n",encoding="utf-8")
    (tmp_path/"api.py").write_text("@app.get('/health')\ndef health(): pass\n",encoding="utf-8")
    m=DependencyAnalyzer().analyze(tmp_path)
    assert any(d.name=="fastapi" for d in m.dependencies)
    assert any(r.path=="/health" for r in m.routes)
    assert ArchitectureModel(dependencies=m).build_facts()
