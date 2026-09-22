from pathlib import Path
from jarvis_v2.code.change_intelligence import ChangedFile, RepositoryChangeIntelligence


def test_impact_detects_tests_routes_and_tables(tmp_path: Path):
    (tmp_path / "api.py").write_text('@app.get("/users")\ndef users(): pass\n', encoding="utf-8")
    (tmp_path / "test_api.py").write_text("def test_users(): pass\n", encoding="utf-8")
    (tmp_path / "schema.sql").write_text("CREATE TABLE users (id INT);\n", encoding="utf-8")
    impact = RepositoryChangeIntelligence(tmp_path).impact([
        ChangedFile("api.py", "M"), ChangedFile("test_api.py", "M"), ChangedFile("schema.sql", "A")
    ])
    assert "test_api.py" in impact.affected_tests
    assert "GET /users" in impact.affected_routes
    assert "users" in impact.affected_tables
    assert impact.risk == "high"
