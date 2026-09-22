from pathlib import Path
from jarvis_v2.memory import KnowledgeExtractor, MemoryRecord, MemoryStore
from jarvis_v2.projects.intelligence import ProjectIntelligence

def test_memory_persists_and_retrieves(tmp_path: Path):
    store=MemoryStore(tmp_path/"memory.jsonl")
    store.add(MemoryRecord(id="1", kind="fact", text="SumePort uses FastAPI authentication", project="SumePort"))
    assert store.search("FastAPI authentication", project="SumePort")[0].id == "1"

def test_project_knowledge_extraction(tmp_path: Path):
    (tmp_path/"requirements.txt").write_text("fastapi\n", encoding="utf-8")
    (tmp_path/"main.py").write_text("def login():\n    pass\n", encoding="utf-8")
    model=ProjectIntelligence(tmp_path).inspect()
    records=KnowledgeExtractor().from_project(model)
    assert any(r.kind == "project" for r in records)
    assert any("login" in r.text for r in records)
