"""Policy-aware workspace synchronization for DOOM."""
from __future__ import annotations
from pathlib import Path
from doom.policy import DataClass, can_leave_local_device
from .manifest import WorkspaceManifest
from .store import ObjectStore

class WorkspaceSyncError(PermissionError): pass

class WorkspaceSync:
    def __init__(self, workspace_root: Path, object_store: ObjectStore) -> None:
        self.workspace_root = workspace_root.resolve()
        self.object_store = object_store
    def push(self, manifest: WorkspaceManifest) -> list[str]:
        uploaded = []
        for entry in manifest.entries.values():
            if not can_leave_local_device(entry.data_class):
                raise WorkspaceSyncError(f"Protected workspace entry cannot be synchronized: {entry.path}")
            source = self._safe_path(entry.path)
            if not source.is_file(): raise FileNotFoundError(source)
            if not self.object_store.has(entry.sha256):
                self.object_store.put(entry.sha256, source)
                uploaded.append(entry.path)
        return uploaded
    def pull(self, manifest: WorkspaceManifest, *, overwrite: bool = False) -> list[str]:
        restored = []
        for entry in manifest.entries.values():
            if entry.data_class == DataClass.PROTECTED:
                raise WorkspaceSyncError(f"Protected workspace entry cannot be pulled from distributed storage: {entry.path}")
            destination = self._safe_path(entry.path)
            if destination.exists() and not overwrite: continue
            self.object_store.get(entry.sha256, destination)
            restored.append(entry.path)
        return restored
    def _safe_path(self, relative: str) -> Path:
        path = (self.workspace_root / relative).resolve()
        try: path.relative_to(self.workspace_root)
        except ValueError as exc: raise WorkspaceSyncError("Workspace path escapes the workspace root.") from exc
        return path
