from pathlib import Path

from jarvis_v2.projects import ProjectIntelligence


def test_project_intelligence_detects_python_project(tmp_path: Path):
    (tmp_path / "requirements.txt").write_text("fastapi\nrequests\n", encoding="utf-8")
    (tmp_path / "main.py").write_text("class App:\n    pass\n\ndef run():\n    pass\n", encoding="utf-8")
    model = ProjectIntelligence(tmp_path).inspect()
    assert "Python" in model.project_type
    assert "main.py" in model.entry_points
    assert "fastapi" in model.dependencies["python"]
    assert model.symbols["main.py"] == ["App", "run"]
