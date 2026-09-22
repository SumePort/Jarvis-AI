from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from jarvis_v2.knowledge.findings import Finding
from jarvis_v2.knowledge.resolution import Resolution
from jarvis_v2.memory.store import MemoryRecord, MemoryStore


@dataclass
class KnowledgeMemoryLink:
    finding_id: str
    memory_id: str
    action: str

    def to_dict(self) -> dict:
        return self.__dict__.copy()


class KnowledgeMemoryBridge:
    """Project durable findings into JARVIS memory without losing provenance."""

    def __init__(self, store: MemoryStore):
        self.store = store

    def remember_finding(self, finding: Finding, project: str | None = None) -> KnowledgeMemoryLink:
        record = MemoryRecord(
            id=f"finding:{finding.id}",
            kind="verified_finding" if finding.status == "verified" else "knowledge_finding",
            text=finding.statement,
            source="finding_store",
            project=project,
            tags=["knowledge", "finding", finding.status],
            metadata={
                "finding_id": finding.id,
                "confidence": finding.confidence,
                "evidence_ids": finding.evidence_ids,
                "rejected_hypothesis_ids": finding.rejected_hypothesis_ids,
                "unresolved_questions": finding.unresolved_questions,
            },
        )
        existing = self.store.search(finding.statement, limit=10, project=project)
        if not any(item.id == record.id for item in existing):
            self.store.add(record)
            return KnowledgeMemoryLink(finding.id, record.id, "added")
        return KnowledgeMemoryLink(finding.id, record.id, "already_present")

    def apply_resolution(
        self,
        resolution: Resolution,
        findings: list[Finding],
        project: str | None = None,
    ) -> list[KnowledgeMemoryLink]:
        links = []
        for finding in findings:
            if finding.id == resolution.selected_finding_id:
                links.append(self.remember_finding(finding, project))
            elif finding.id in resolution.conflict_id.split(":")[1:]:
                rejected = Finding(
                    finding.id, finding.statement, "rejected", finding.confidence,
                    finding.evidence_ids, finding.rejected_hypothesis_ids,
                    finding.unresolved_questions, finding.created_at,
                )
                links.append(self.remember_finding(rejected, project))
        return links
