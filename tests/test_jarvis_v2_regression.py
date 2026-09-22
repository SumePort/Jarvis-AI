from pathlib import Path
from jarvis_v2.code.change_intelligence import ChangedFile
from jarvis_v2.code.impact_graph import CrossLayerImpactBuilder
from jarvis_v2.code.regression import RegressionIntelligence


def test_regression_targets_affected_api(tmp_path: Path):
    (tmp_path / "api.py").write_text('@app.get("/users")\ndef users(): pass\n', encoding="utf-8")
    (tmp_path / "test_api.py").write_text("from api import users\ndef test_users(): pass\n", encoding="utf-8")
    graph = CrossLayerImpactBuilder(tmp_path).build()
    assessment = RegressionIntelligence(tmp_path).assess([ChangedFile("api.py", "M")], graph)
    assert assessment.targets
    assert assessment.risk == "high"
