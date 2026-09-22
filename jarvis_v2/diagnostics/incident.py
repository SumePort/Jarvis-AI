from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from jarvis_v2.code.change_intelligence import ChangedFile
from jarvis_v2.knowledge.causal import CausalAnalysis
from jarvis_v2.knowledge.temporal import CommitSnapshot
from jarvis_v2.knowledge.world_graph import UnifiedWorldGraph
from jarvis_v2.tests.intelligence import TestFailure


@dataclass
class IncidentEvidence:
    kind: str
    summary: str
    source: str = ""
    confidence: float = 1.0

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class IncidentReport:
    incident_id: str
    title: str
    status: str
    started_at: str | None = None
    suspected_changes: list[str] = field(default_factory=list)
    affected_components: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    evidence: list[IncidentEvidence] = field(default_factory=list)
    uncertainties: list[str] = field(default_factory=list)
    timeline: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "incident_id": self.incident_id,
            "title": self.title,
            "status": self.status,
            "started_at": self.started_at,
            "suspected_changes": self.suspected_changes,
            "affected_components": self.affected_components,
            "failures": self.failures,
            "evidence": [e.to_dict() for e in self.evidence],
            "uncertainties": self.uncertainties,
            "timeline": self.timeline,
        }


class IncidentReconstructor:
    """Reconstruct a bounded incident narrative from available evidence."""

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()

    def reconstruct(
        self,
        incident_id: str,
        changes: list[ChangedFile],
        causal: CausalAnalysis,
        failures: Iterable[TestFailure] = (),
        commits: Iterable[CommitSnapshot] = (),
        graph: UnifiedWorldGraph | None = None,
    ) -> IncidentReport:
        failure_list = list(failures)
        commit_list = list(commits)
        evidence: list[IncidentEvidence] = []
        timeline: list[str] = []

        suspected = [x.path for x in changes]
        affected = list(causal.affected_nodes)

        for change in changes:
            evidence.append(IncidentEvidence(
                "change", f"{change.status} {change.path}",
                "git", 0.95
            ))

        for failure in failure_list:
            label = failure.test_name
            if failure.file:
                label += f" ({failure.file}:{failure.line or '?'})"
            evidence.append(IncidentEvidence(
                "test_failure", label, failure.framework, 0.95
            ))

        for commit in commit_list:
            touched = set(commit.changed_files)
            if touched.intersection(suspected):
                timeline.append(
                    f"{commit.timestamp}: {commit.commit[:12]} — {commit.subject}"
                )

        for link in causal.links[:50]:
            evidence.append(IncidentEvidence(
                "causal_link",
                f"{link.source} {link.relation} {link.target}",
                "world_graph",
                link.confidence,
            ))

        uncertainties = []
        if not changes:
            uncertainties.append("No Git change evidence was supplied.")
        if not failure_list:
            uncertainties.append("No test failure evidence was supplied.")
        if not causal.links:
            uncertainties.append("No causal graph links were established.")
        if not commit_list:
            uncertainties.append("No commit timeline was supplied.")

        if failure_list and changes and causal.links:
            status = "evidence-backed"
        elif changes or failure_list:
            status = "partial"
        else:
            status = "insufficient-evidence"

        title = (
            f"Incident involving {len(changes)} changed file(s) and "
            f"{len(failure_list)} failure(s)"
        )

        return IncidentReport(
            incident_id=incident_id,
            title=title,
            status=status,
            started_at=commit_list[0].timestamp if commit_list else None,
            suspected_changes=suspected,
            affected_components=affected,
            failures=[f.test_name for f in failure_list],
            evidence=evidence,
            uncertainties=uncertainties,
            timeline=timeline,
        )
