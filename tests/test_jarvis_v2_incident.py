from pathlib import Path

from jarvis_v2.code.change_intelligence import ChangedFile
from jarvis_v2.diagnostics.incident import IncidentReconstructor
from jarvis_v2.knowledge.causal import CausalAnalysis, CausalLink
from jarvis_v2.knowledge.temporal import CommitSnapshot
from jarvis_v2.knowledge.world_graph import UnifiedWorldGraph
from jarvis_v2.tests.intelligence import TestFailure


def test_incident_reconstruction(tmp_path: Path):
    causal = CausalAnalysis(
        links=[CausalLink("file:api.py", "defines", "route:GET /users", 0.9)],
        root_candidates=["file:api.py"],
        affected_nodes=["route:GET /users"],
        explanation="evidence",
    )
    report = IncidentReconstructor(tmp_path).reconstruct(
        "inc-1",
        [ChangedFile("api.py", "M")],
        causal,
        [TestFailure("pytest", "test_users", "failed", "tests/test_api.py", 8)],
        [CommitSnapshot("abcdef123456", "2026-09-22T10:00:00+05:30", "Test", "change API", ["api.py"], 2, 1)],
        UnifiedWorldGraph(),
    )
    assert report.status == "evidence-backed"
    assert "api.py" in report.suspected_changes
    assert report.timeline
    assert report.evidence
