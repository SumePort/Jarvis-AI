"""Persistent experiment scheduler with safety and resource gates."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
@dataclass
class ScheduledExperiment:
    experiment_id:str
    run_at:str
    physical:bool=False
    authorized:bool=False
    status:str="scheduled"
class ExperimentScheduler:
    def __init__(self,controller): self.controller=controller; self.items={}
    def schedule(self,item):
        if item.physical and not item.authorized: raise PermissionError("Physical experiment requires authorization")
        self.items[item.experiment_id]=item; return item
    def due(self,now=None):
        now=now or datetime.now(timezone.utc)
        return [x for x in self.items.values() if x.status=="scheduled" and datetime.fromisoformat(x.run_at)<=now]
