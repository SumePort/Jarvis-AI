from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import math
from typing import Iterable

from jarvis_v2.knowledge.findings import Finding, EvidenceItem


@dataclass
class KnowledgeFreshness:
    finding_id: str
    age_seconds: float
    freshness: float
    status: str
    revalidation_needed: bool
    reason: str

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class RevalidationRequest:
    finding_id: str
    reason: str
    priority: int
    suggested_action: str

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class LifecycleAssessment:
    freshness: list[KnowledgeFreshness] = field(default_factory=list)
    revalidation: list[RevalidationRequest] = field(default_factory=list)
    stale_finding_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "freshness": [x.to_dict() for x in self.freshness],
            "revalidation": [x.to_dict() for x in self.revalidation],
            "stale_finding_ids": self.stale_finding_ids,
        }


class KnowledgeLifecycle:
    """Assess knowledge freshness without silently deleting or rewriting findings."""

    def __init__(self, half_life_days: float = 30.0, stale_threshold: float = 0.25):
        self.half_life_seconds = max(0.01, half_life_days * 86400)
        self.stale_threshold = max(0.0, min(1.0, stale_threshold))

    def assess(
        self,
        findings: Iterable[Finding],
        evidence: Iterable[EvidenceItem] = (),
        now: datetime | None = None,
    ) -> LifecycleAssessment:
        now = now or datetime.now(timezone.utc)
        evidence_by_id = {e.id: e for e in evidence}
        freshness: list[KnowledgeFreshness] = []
        requests: list[RevalidationRequest] = []

        for finding in findings:
            timestamps = []
            for evidence_id in finding.evidence_ids:
                item = evidence_by_id.get(evidence_id)
                if not item or not item.observed_at:
                    continue
                try:
                    value = datetime.fromisoformat(item.observed_at)
                    if value.tzinfo is None:
                        value = value.replace(tzinfo=timezone.utc)
                    timestamps.append(value)
                except ValueError:
                    continue

            if timestamps:
                latest = max(timestamps)
                age = max(0.0, (now - latest).total_seconds())
            else:
                try:
                    created = datetime.fromisoformat(finding.created_at)
                    if created.tzinfo is None:
                        created = created.replace(tzinfo=timezone.utc)
                    age = max(0.0, (now - created).total_seconds())
                except ValueError:
                    age = self.half_life_seconds

            score = math.pow(0.5, age / self.half_life_seconds)
            score *= max(0.0, min(1.0, finding.confidence))

            if finding.status == "rejected":
                status = "rejected"
            elif score <= self.stale_threshold:
                status = "stale"
            elif score < 0.75:
                status = "aging"
            else:
                status = "fresh"

            needs = status in {"stale", "aging"}
            reason = f"freshness={score:.3f}; age_seconds={age:.0f}"

            freshness.append(KnowledgeFreshness(
                finding.id, age, score, status, needs, reason
            ))

            if needs:
                requests.append(RevalidationRequest(
                    finding.id,
                    reason,
                    10 if status == "stale" else 5,
                    "revalidate_finding",
                ))

        return LifecycleAssessment(
            freshness=freshness,
            revalidation=requests,
            stale_finding_ids=[x.finding_id for x in freshness if x.status == "stale"],
        )
