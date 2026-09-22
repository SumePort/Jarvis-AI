from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from doom.policy import DataClass, can_leave_local_device
from doom.workspace.manifest import WorkspaceEntry, WorkspaceManifest
from doom.workspace.sync import WorkspaceSync, WorkspaceSyncError


@dataclass
class SyncConflict:
    path: str
    local_sha256: str | None
    remote_sha256: str | None
    reason: str = "content_changed"


@dataclass
class SyncPlan:
    project_id: str
    upload: list[WorkspaceEntry] = field(default_factory=list)
    download: list[WorkspaceEntry] = field(default_factory=list)
    conflicts: list[SyncConflict] = field(default_factory=list)
    blocked: list[str] = field(default_factory=list)


class IdentityWorkspaceSync:
    """Identity-aware, conflict-aware synchronization facade.

    It never synchronizes protected entries and never silently overwrites a
    local change. The underlying content-addressed store verifies hashes.
    """

    def __init__(self, identity_id: str, workspace_root: Path, object_store: Any):
        if not identity_id:
            raise ValueError("identity_id is required")
        self.identity_id = identity_id
        self.workspace_root = workspace_root.resolve()
        self.object_store = object_store

    def plan(self, local: WorkspaceManifest, remote: WorkspaceManifest) -> SyncPlan:
        if local.project_id != remote.project_id:
            raise ValueError("Local and remote manifests must belong to the same project")
        result = SyncPlan(local.project_id)
        paths = set(local.entries) | set(remote.entries)
        for path in sorted(paths):
            left = local.entries.get(path)
            right = remote.entries.get(path)
            if left and not can_leave_local_device(left.data_class):
                result.blocked.append(path)
                continue
            if right and right.data_class == DataClass.PROTECTED:
                result.blocked.append(path)
                continue
            if left and not right:
                result.upload.append(left)
            elif right and not left:
                result.download.append(right)
            elif left and right and left.sha256 != right.sha256:
                result.conflicts.append(SyncConflict(path, left.sha256, right.sha256))
        return result

    def apply(self, plan: SyncPlan, local: WorkspaceManifest, remote: WorkspaceManifest) -> dict[str, list[str]]:
        if plan.conflicts:
            raise WorkspaceSyncError("Synchronization has unresolved conflicts; no files were changed")
        sync = WorkspaceSync(self.workspace_root, self.object_store)
        upload_manifest = WorkspaceManifest(local.project_id, {e.path: e for e in plan.upload})
        download_manifest = WorkspaceManifest(remote.project_id, {e.path: e for e in plan.download})
        uploaded = sync.push(upload_manifest)
        downloaded = sync.pull(download_manifest, overwrite=False)
        return {"uploaded": uploaded, "downloaded": downloaded, "blocked": plan.blocked}
