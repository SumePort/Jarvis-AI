from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime, timezone
import json

from jarvis_v2.code.change_intelligence import RepositoryChangeIntelligence
from jarvis_v2.runtime.project_environment import ProjectExecutionEnvironment, ProjectEnvironmentSnapshot


@dataclass
class ProjectWorkspaceState:
    project_root: str
    task: str | None = None
    branch: str | None = None
    recent_changes: list[str] = field(default_factory=list)
    active_services: list[dict] = field(default_factory=list)
    known_issues: list[str] = field(default_factory=list)
    pending_work: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    updated_at: str = ""

    def to_dict(self) -> dict:
        return self.__dict__.copy()


class ProjectWorkspace:
    """Persistent project session state backed by the project-local .jarvis directory."""

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        self.path = self.root / ".jarvis" / "workspace.json"
        self.changes = RepositoryChangeIntelligence(self.root)
        self.runtime = ProjectExecutionEnvironment(self.root)

    def load(self) -> ProjectWorkspaceState:
        if not self.path.exists():
            return ProjectWorkspaceState(str(self.root))
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return ProjectWorkspaceState(**{k: data.get(k) for k in ProjectWorkspaceState.__dataclass_fields__})

    def save(self, state: ProjectWorkspaceState) -> ProjectWorkspaceState:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        state.updated_at = datetime.now(timezone.utc).isoformat()
        self.path.write_text(json.dumps(state.to_dict(), indent=2), encoding="utf-8")
        return state

    def refresh(self, state: ProjectWorkspaceState | None = None, ports=()) -> ProjectWorkspaceState:
        state = state or self.load()
        state.branch = self.changes.branch()
        state.recent_changes = [x.path for x in self.changes.status()][:50]
        runtime: ProjectEnvironmentSnapshot = self.runtime.snapshot(ports)
        state.active_services = [x.to_dict() for x in runtime.processes if x.status == "running"]
        return self.save(state)

    def set_task(self, task: str | None) -> ProjectWorkspaceState:
        state = self.load(); state.task = task; return self.save(state)

    def add_issue(self, issue: str) -> ProjectWorkspaceState:
        state = self.load(); state.known_issues.append(issue); state.known_issues = state.known_issues[-100:]; return self.save(state)

    def add_pending(self, item: str) -> ProjectWorkspaceState:
        state = self.load(); state.pending_work.append(item); state.pending_work = state.pending_work[-100:]; return self.save(state)

    def add_decision(self, decision: str) -> ProjectWorkspaceState:
        state = self.load(); state.decisions.append(decision); state.decisions = state.decisions[-100:]; return self.save(state)
