from pathlib import Path
from jarvis_v2.memory.store import MemoryRecord
from jarvis_v2.personal.distributed_memory import DistributedMemoryStore, MemoryReconciler


def test_distributed_memory_round_trip(tmp_path: Path):
    a = DistributedMemoryStore("shubham", "pc", tmp_path / "pc.jsonl")
    b = DistributedMemoryStore("shubham", "phone", tmp_path / "phone.jsonl")
    record = MemoryRecord("m1", "preference", "Dark theme", source="user")
    version = a.append(record)
    assert b.import_versions(a.export()) == 1
    assert b.latest("m1").record["text"] == "Dark theme"


def test_memory_conflict_is_explicit(tmp_path: Path):
    a = DistributedMemoryStore("shubham", "pc", tmp_path / "a.jsonl")
    b = DistributedMemoryStore("shubham", "phone", tmp_path / "b.jsonl")
    a.append(MemoryRecord("m1", "preference", "Black theme", source="user"))
    b.append(MemoryRecord("m1", "preference", "White theme", source="user"))
    winner, conflict = MemoryReconciler().reconcile(a.latest("m1"), b.latest("m1"))
    assert winner is None
    assert conflict.fields


def test_identity_isolation(tmp_path: Path):
    a = DistributedMemoryStore("shubham", "pc", tmp_path / "memory.jsonl")
    a.append(MemoryRecord("m1", "preference", "private"))
    other = DistributedMemoryStore("father", "phone", tmp_path / "memory.jsonl")
    assert other.import_versions(a.export()) == 0
