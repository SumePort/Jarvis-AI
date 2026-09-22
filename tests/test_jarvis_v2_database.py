from pathlib import Path
from jarvis_v2.code.database import DatabaseAnalyzer
from jarvis_v2.code.data_graph import DataArchitecture

def test_sql_schema_analysis(tmp_path: Path):
    (tmp_path/"001_migration.sql").write_text("CREATE TABLE users (\n id INTEGER,\n name TEXT\n);",encoding="utf-8")
    model=DatabaseAnalyzer().analyze(tmp_path)
    assert model.tables[0].name=="users"
    assert "id" in model.tables[0].columns
    assert model.migrations
    assert DataArchitecture(None,model).facts()
