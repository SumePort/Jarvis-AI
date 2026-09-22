"""Content-addressed workspace manifest for DOOM."""
from __future__ import annotations
import hashlib, json
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath
from doom.policy import DataClass

def _safe_relative(path: str) -> str:
    normalized = PurePosixPath(path.replace("\\", "/"))
    if normalized.is_absolute() or ".." in normalized.parts:
        raise ValueError("Workspace paths must be relative and cannot escape the workspace.")
    return str(normalized)

@dataclass(frozen=True, slots=True)
class WorkspaceEntry:
    path: str
    sha256: str
    size: int
    data_class: DataClass = DataClass.NORMAL
    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _safe_relative(self.path))
        if len(self.sha256) != 64:
            raise ValueError("sha256 must be a 64-character hex digest.")
        int(self.sha256, 16)
        if self.size < 0:
            raise ValueError("size cannot be negative.")
    def to_dict(self) -> dict:
        result = asdict(self)
        result["data_class"] = self.data_class.value
        return result
    @classmethod
    def from_dict(cls, data: dict) -> "WorkspaceEntry":
        return cls(data["path"], data["sha256"], int(data["size"]),
                   DataClass(data.get("data_class", DataClass.NORMAL.value)))

@dataclass
class WorkspaceManifest:
    project_id: str
    entries: dict[str, WorkspaceEntry] = field(default_factory=dict)
    version: int = 1
    def add_file(self, workspace_root: Path, path: Path, *, data_class: DataClass = DataClass.NORMAL) -> WorkspaceEntry:
        root, file_path = workspace_root.resolve(), path.resolve()
        try:
            relative = file_path.relative_to(root).as_posix()
        except ValueError as exc:
            raise ValueError("File must be inside the workspace root.") from exc
        if not file_path.is_file():
            raise FileNotFoundError(file_path)
        digest, size = hashlib.sha256(), 0
        with file_path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk); size += len(chunk)
        entry = WorkspaceEntry(relative, digest.hexdigest(), size, data_class)
        self.entries[entry.path] = entry
        return entry
    def remove(self, path: str) -> None:
        self.entries.pop(_safe_relative(path), None)
    def to_dict(self) -> dict:
        return {"version": self.version, "project_id": self.project_id,
                "entries": {p: self.entries[p].to_dict() for p in sorted(self.entries)}}
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"
    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json(), encoding="utf-8")
    @classmethod
    def load(cls, path: Path) -> "WorkspaceManifest":
        data = json.loads(path.read_text(encoding="utf-8"))
        entries = {k: WorkspaceEntry.from_dict(v) for k, v in data.get("entries", {}).items()}
        return cls(data["project_id"], entries, int(data.get("version", 1)))
