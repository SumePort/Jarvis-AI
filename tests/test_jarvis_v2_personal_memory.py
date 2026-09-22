from pathlib import Path

from jarvis_v2.memory.store import MemoryStore
from jarvis_v2.personal.memory import PersonalMemory
from jarvis_v2.personal.memory_extractor import PersonalMemoryExtractor


def test_explicit_memory_is_durable(tmp_path: Path):
    memory=PersonalMemory(MemoryStore(tmp_path/"memory.jsonl"))
    record=PersonalMemoryExtractor(memory).extract("I prefer dark mode")
    assert record is not None
    assert record.kind == "preference"
    assert memory.recall("dark mode")[0].text == "dark mode"


def test_temporary_memory_expires(tmp_path: Path):
    memory=PersonalMemory(MemoryStore(tmp_path/"memory.jsonl"))
    record=memory.remember("temporary context", kind="working", ttl_seconds=0)
    assert memory.recall("temporary context") == []
    assert record.metadata["durable"] is False


def test_forget_marks_memory(tmp_path: Path):
    memory=PersonalMemory(MemoryStore(tmp_path/"memory.jsonl"))
    record=memory.remember("keep this only briefly", kind="working")
    assert memory.forget(record.id)
    assert memory.store.all()[0].metadata["forgotten"] is True
