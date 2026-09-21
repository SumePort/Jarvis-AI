"""Project knowledge formatting and persistence."""
from __future__ import annotations
from dataclasses import asdict
from .learner import ProjectSnapshot
from memory.store import MemoryStore

def learn_project(root: str, store: MemoryStore) -> ProjectSnapshot:
    from .learner import ProjectLearner
    snap=ProjectLearner().scan(root)
    store.save_project(snap.name, asdict(snap))
    return snap
