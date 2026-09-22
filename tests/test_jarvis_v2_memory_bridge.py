from pathlib import Path

from jarvis_v2.knowledge.findings import Finding
from jarvis_v2.knowledge.memory_bridge import KnowledgeMemoryBridge
from jarvis_v2.memory.store import MemoryStore


def test_finding_is_projected_to_memory(tmp_path: Path):
    store = MemoryStore(tmp_path / "memory.jsonl")
    finding = Finding("fd_1", "SumePort uses PostgreSQL", "verified", 0.95)
    link = KnowledgeMemoryBridge(store).remember_finding(finding, project="SumePort")
    assert link.action == "added"
    records = store.all()
    assert any(r.id == "finding:fd_1" for r in records)
    assert records[-1].metadata["confidence"] == 0.95
