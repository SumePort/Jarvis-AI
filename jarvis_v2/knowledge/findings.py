from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


@dataclass
class EvidenceItem:
    id: str
    kind: str
    statement: str
    source: str = ""
    confidence: float = 1.0
    observed_at: str = ""

    def __post_init__(self):
        if not self.observed_at:
            self.observed_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class Finding:
    id: str
    statement: str
    status: str
    confidence: float
    evidence_ids: list[str] = field(default_factory=list)
    rejected_hypothesis_ids: list[str] = field(default_factory=list)
    unresolved_questions: list[str] = field(default_factory=list)
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return self.__dict__.copy()


class FindingStore:
    """Local append-only evidence/finding store.

    Findings are deliberately separate from raw memory so uncertain hypotheses
    cannot silently become permanent facts.
    """

    def __init__(self, path: str | Path = "data/jarvis/findings.jsonl"):
        self.path = Path(path)

    def _append(self, record: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    def add_evidence(self, evidence: EvidenceItem) -> str:
        self._append({"type": "evidence", **evidence.to_dict()})
        return evidence.id

    def add_finding(self, finding: Finding) -> str:
        self._append({"type": "finding", **finding.to_dict()})
        return finding.id

    def all(self) -> list[dict]:
        if not self.path.exists():
            return []
        records = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return records

    def find(self, record_id: str) -> dict | None:
        for record in reversed(self.all()):
            if record.get("id") == record_id:
                return record
        return None

    @staticmethod
    def evidence_id(statement: str, source: str = "") -> str:
        raw = f"{source}\n{statement}".encode("utf-8")
        return "ev_" + hashlib.sha256(raw).hexdigest()[:16]

    @staticmethod
    def finding_id(statement: str) -> str:
        return "fd_" + hashlib.sha256(statement.encode("utf-8")).hexdigest()[:16]
