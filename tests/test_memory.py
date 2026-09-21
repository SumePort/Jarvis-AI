from memory.store import MemoryStore

def test_memory_roundtrip(tmp_path):
    store=MemoryStore(str(tmp_path/"jarvis.db"))
    store.add_message("user","hello")
    assert store.recent(1)[0]["content"]=="hello"
