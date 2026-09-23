"""Dataset manifest utilities for a JARVIS-owned voice corpus."""
from __future__ import annotations
import json
from dataclasses import asdict, dataclass
from pathlib import Path
@dataclass(frozen=True)
class VoiceSample:
    audio: str
    text: str
    speaker: str = "jarvis"
    language: str = "en"
    emotion: str = "neutral"
    quality: str = "clean"
class VoiceDataset:
    def __init__(self,root:str|Path): self.root=Path(root); self.manifest=self.root/"manifest.jsonl"; self.root.mkdir(parents=True,exist_ok=True)
    def add(self,sample:VoiceSample):
        path=(self.root/sample.audio).resolve(); root=self.root.resolve()
        if root not in path.parents: raise ValueError("audio path escapes dataset root")
        with self.manifest.open("a",encoding="utf-8") as fh: fh.write(json.dumps(asdict(sample),ensure_ascii=False)+"\n")
    def samples(self):
        if not self.manifest.exists(): return []
        return [VoiceSample(**json.loads(line)) for line in self.manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
