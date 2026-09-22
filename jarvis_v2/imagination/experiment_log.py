"""Persistent record of imaginative hypotheses and experiment outcomes."""
from __future__ import annotations
from pathlib import Path
import json, time
from dataclasses import asdict
from .models import ImaginationResult

class ExperimentLog:
    def __init__(self, path="data/jarvis_v2/experiments.jsonl"):
        self.path=Path(path); self.path.parent.mkdir(parents=True, exist_ok=True)
    def append(self, result: ImaginationResult, outcome: str | None = None):
        record={"timestamp":time.time(),"goal":result.goal,"result":asdict(result),"outcome":outcome}
        with self.path.open("a",encoding="utf-8") as f: f.write(json.dumps(record,ensure_ascii=False)+"\n")
