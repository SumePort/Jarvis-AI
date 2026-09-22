from pathlib import Path
import pytest
from doom.policy import DataClass
from doom.workspace import LocalObjectStore, WorkspaceManifest, WorkspaceSync, WorkspaceSyncError

def test_manifest_is_content_addressed(tmp_path: Path):
    root = tmp_path / "project"; root.mkdir()
    file_path = root / "README.md"; file_path.write_text("hello DOOM", encoding="utf-8")
    entry = WorkspaceManifest("demo").add_file(root, file_path)
    assert entry.path == "README.md"
    assert len(entry.sha256) == 64
    assert entry.size == len("hello DOOM")

def test_normal_files_push_and_pull(tmp_path: Path):
    root = tmp_path / "project"; root.mkdir()
    source = root / "app.txt"; source.write_text("distributed", encoding="utf-8")
    manifest = WorkspaceManifest("demo"); manifest.add_file(root, source)
    store = LocalObjectStore(tmp_path / "objects")
    assert WorkspaceSync(root, store).push(manifest) == ["app.txt"]
    source.unlink()
    assert WorkspaceSync(root, store).pull(manifest) == ["app.txt"]
    assert source.read_text(encoding="utf-8") == "distributed"

def test_protected_files_never_leave_local_workspace(tmp_path: Path):
    root = tmp_path / "project"; root.mkdir()
    secret = root / "credentials.txt"; secret.write_text("do-not-upload", encoding="utf-8")
    manifest = WorkspaceManifest("demo")
    manifest.add_file(root, secret, data_class=DataClass.PROTECTED)
    store = LocalObjectStore(tmp_path / "objects")
    with pytest.raises(WorkspaceSyncError): WorkspaceSync(root, store).push(manifest)
    assert not (tmp_path / "objects").exists()

def test_manifest_rejects_workspace_escape(tmp_path: Path):
    root = tmp_path / "project"; root.mkdir()
    outside = tmp_path / "outside.txt"; outside.write_text("x", encoding="utf-8")
    with pytest.raises(ValueError): WorkspaceManifest("demo").add_file(root, outside)
