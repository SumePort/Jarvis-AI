"""Persistent invention-cycle journal."""
from __future__ import annotations
import json,os
class InventionJournal:
    def __init__(self,path="data/jarvis_v2/invention_cycles.jsonl"): self.path=path
    def append(self,cycle):
        os.makedirs(os.path.dirname(self.path),exist_ok=True)
        with open(self.path,"a",encoding="utf-8") as f:
            f.write(json.dumps({"idea":cycle.idea,"research":cycle.research,"conclusion":getattr(cycle.imagination,"conclusion","")},ensure_ascii=False)+"\n")
