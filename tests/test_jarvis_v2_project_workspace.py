from pathlib import Path

from jarvis_v2.projects.workspace import ProjectWorkspace


def test_workspace_persists_state(tmp_path: Path):
    ws = ProjectWorkspace(tmp_path)
    state = ws.set_task("finish project AI")
    ws.add_issue("test issue")
    ws.add_pending("document handoff")
    ws.add_decision("keep git push confirmation-gated")
    loaded = ws.load()
    assert loaded.task == "finish project AI"
    assert loaded.known_issues == ["test issue"]
    assert loaded.pending_work == ["document handoff"]
    assert loaded.decisions == ["keep git push confirmation-gated"]
