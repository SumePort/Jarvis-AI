from pathlib import Path
import pytest

from doom.policy import DataClass
from doom.workspace.manifest import WorkspaceEntry, WorkspaceManifest
from doom.workspace.store import LocalObjectStore
from jarvis_v2.doom.workspace_sync import IdentityWorkspaceSync


def entry(path, digest, cls=DataClass.NORMAL):
    return WorkspaceEntry(path, digest * 64 if len(digest) == 1 else digest, 1, cls)


def test_sync_plan_detects_conflicts_and_blocks_protected(tmp_path: Path):
    local = WorkspaceManifest("p1")
    remote = WorkspaceManifest("p1")
    local.entries["a.txt"] = WorkspaceEntry("a.txt", "a" * 64, 1, DataClass.NORMAL)
    remote.entries["a.txt"] = WorkspaceEntry("a.txt", "b" * 64, 1, DataClass.NORMAL)
    local.entries["secret.txt"] = WorkspaceEntry("secret.txt", "c" * 64, 1, DataClass.PROTECTED)
    plan = IdentityWorkspaceSync("shubham", tmp_path, LocalObjectStore(tmp_path / "objects")).plan(local, remote)
    assert plan.conflicts[0].path == "a.txt"
    assert "secret.txt" in plan.blocked


def test_sync_applies_non_conflicting_upload(tmp_path: Path):
    root = tmp_path / "workspace"
    root.mkdir()
    source = root / "a.txt"
    source.write_text("hello", encoding="utf-8")
    local = WorkspaceManifest("p1")
    local.add_file(root, source)
    remote = WorkspaceManifest("p1")
    sync = IdentityWorkspaceSync("shubham", root, LocalObjectStore(tmp_path / "objects"))
    plan = sync.plan(local, remote)
    result = sync.apply(plan, local, remote)
    assert result["uploaded"] == ["a.txt"]
