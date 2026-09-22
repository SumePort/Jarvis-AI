"""Durable research knowledge store with provenance and freshness."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import json, time, hashlib


@dataclass(frozen=True)
class LearnedTopic:
    topic: str
    summary: str
    sources: tuple[str, ...]
    learned_at: float
    fingerprint: str


class LearningStore:
    """Store validated research summaries separately from personal memory."""

    def __init__(self, path: str | Path = "data/jarvis_v2/learned_topics.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def learn(self, topic: str, summary: str, sources: list[str]) -> LearnedTopic:
        fingerprint = hashlib.sha256(
            (topic + "\n" + summary + "\n" + "\n".join(sources)).encode()
        ).hexdigest()
        record = LearnedTopic(topic, summary, tuple(sources), time.time(), fingerprint)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")
        return record

    def latest(self, topic: str) -> LearnedTopic | None:
        if not self.path.exists():
            return None
        found = None
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            if item.get("topic", "").lower() == topic.lower():
                found = LearnedTopic(
                    item["topic"], item["summary"], tuple(item["sources"]),
                    item["learned_at"], item["fingerprint"]
                )
        return found
