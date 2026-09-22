"""Temporal object tracking contracts for physical-world perception."""
from __future__ import annotations
from dataclasses import dataclass
from .world import Percept
@dataclass
class Track:
    track_id:str
    percept:Percept
    age:int=1
    missed:int=0
class ObjectTracker:
    def __init__(self,max_missed=5): self.max_missed=max_missed; self.tracks={}
    def update(self,percepts):
        updated={}
        for i,p in enumerate(percepts):
            key=f"{p.kind}:{p.label}"
            old=self.tracks.get(key)
            updated[key]=Track(key,p,(old.age+1 if old else 1),0)
        for key,old in self.tracks.items():
            if key not in updated and old.missed<self.max_missed:
                updated[key]=Track(key,old.percept,old.age,old.missed+1)
        self.tracks=updated
        return list(updated.values())
