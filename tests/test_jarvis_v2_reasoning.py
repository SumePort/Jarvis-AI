from pathlib import Path
from jarvis_v2.memory import MemoryRecord, MemoryStore
from jarvis_v2.projects.world_model import ProjectWorldModelBuilder
from jarvis_v2.reasoning import ContextRetriever

def test_retriever_combines_memory_and_graph(tmp_path: Path):
    (tmp_path/"requirements.txt").write_text("fastapi\n", encoding="utf-8")
    (tmp_path/"main.py").write_text("def login():\n    pass\n", encoding="utf-8")
    memory=MemoryStore(tmp_path/"memory.jsonl")
    memory.add(MemoryRecord(id="auth", kind="fact", text="login uses FastAPI", project=str(tmp_path)))
    world=ProjectWorldModelBuilder().build(str(tmp_path))
    result=ContextRetriever(memory).retrieve("login FastAPI", world)
    assert result.memories and any("login" in x["text"] for x in result.memories)
    assert any(x["label"] == "main.py" for x in result.graph_nodes)
    assert "main.py" in result.source_targets
