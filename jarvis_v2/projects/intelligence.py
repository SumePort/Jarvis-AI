"""Repository/project understanding for JARVIS V2."""
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from jarvis_v2.core.types import EnvironmentSnapshot

IGNORED = {".git", ".venv", "venv", "node_modules", "__pycache__", ".idea", ".vscode", "build", "dist"}
CONFIG_NAMES = {"pyproject.toml", "requirements.txt", "package.json", "pubspec.yaml", "Cargo.toml", "go.mod", "pom.xml", "build.gradle", "README.md"}

@dataclass
class ProjectModel:
    name: str
    root: str
    project_type: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    entry_points: list[str] = field(default_factory=list)
    config_files: list[str] = field(default_factory=list)
    source_files: list[str] = field(default_factory=list)
    test_files: list[str] = field(default_factory=list)
    documentation: list[str] = field(default_factory=list)
    dependencies: dict[str, list[str]] = field(default_factory=dict)
    git: dict[str, Any] = field(default_factory=dict)
    symbols: dict[str, list[str]] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

class ProjectIntelligence:
    """Build a compact structural model without sending the repository to a model."""

    def __init__(self, root: str | Path, max_files: int = 3000) -> None:
        self.root = Path(root).expanduser().resolve()
        self.max_files = max_files

    def inspect(self) -> ProjectModel:
        files = self._files()
        model = ProjectModel(name=self.root.name, root=str(self.root))
        for path in files:
            rel = path.relative_to(self.root).as_posix()
            suffix = path.suffix.lower()
            if path.name in CONFIG_NAMES or path.name.lower().startswith(".env"):
                model.config_files.append(rel)
            if path.name.lower() in {"readme.md", "readme.txt", "docs.md"} or "/docs/" in f"/{rel.lower()}/":
                model.documentation.append(rel)
            if any(part.lower() in {"test", "tests", "spec", "specs"} for part in path.parts):
                model.test_files.append(rel)
            elif suffix in {".py", ".js", ".ts", ".tsx", ".jsx", ".dart", ".java", ".go", ".rs", ".cpp", ".c", ".h", ".cs", ".php", ".rb"}:
                model.source_files.append(rel)
            language = self._language(suffix)
            if language and language not in model.languages:
                model.languages.append(language)
            self._entry_point(model, rel)
        self._detect_project_types(model)
        self._read_dependencies(model)
        self._extract_symbols(model)
        model.git = self._git()
        model.metadata["file_count"] = len(files)
        model.metadata["truncated"] = len(files) >= self.max_files
        return model

    def environment_observation(self) -> dict[str, Any]:
        model = self.inspect()
        return {"source": "project_intelligence", "project": model.to_dict()}

    def _files(self) -> list[Path]:
        if not self.root.is_dir():
            return []
        found: list[Path] = []
        for current, dirs, names in __import__("os").walk(self.root):
            dirs[:] = [d for d in dirs if d not in IGNORED]
            for name in names:
                path = Path(current) / name
                if path.is_file():
                    found.append(path)
                    if len(found) >= self.max_files:
                        return found
        return found

    @staticmethod
    def _language(suffix: str) -> str | None:
        return {".py":"Python", ".js":"JavaScript", ".ts":"TypeScript", ".tsx":"TypeScript", ".jsx":"JavaScript", ".dart":"Dart", ".java":"Java", ".go":"Go", ".rs":"Rust", ".cpp":"C++", ".c":"C", ".h":"C/C++", ".cs":"C#", ".php":"PHP", ".rb":"Ruby", ".sql":"SQL"}.get(suffix)

    @staticmethod
    def _entry_point(model: ProjectModel, rel: str) -> None:
        name = Path(rel).name.lower()
        if name in {"main.py", "app.py", "server.py", "manage.py", "main.dart", "index.js", "index.ts", "index.html"}:
            model.entry_points.append(rel)

    def _detect_project_types(self, model: ProjectModel) -> None:
        names = {Path(x).name.lower() for x in model.config_files}
        if "pubspec.yaml" in names:
            model.project_type.append("Flutter/Dart")
        if "pyproject.toml" in names or "requirements.txt" in names:
            model.project_type.append("Python")
        if "package.json" in names:
            model.project_type.append("Node.js/JavaScript")
        if "cargo.toml" in names:
            model.project_type.append("Rust")
        if "go.mod" in names:
            model.project_type.append("Go")
        text = " ".join(model.source_files).lower()
        if "fastapi" in text:
            model.frameworks.append("FastAPI")
        if "flutter" in text and "Flutter" not in model.frameworks:
            model.frameworks.append("Flutter")
        if "react" in text:
            model.frameworks.append("React")

    def _read_dependencies(self, model: ProjectModel) -> None:
        req = self.root / "requirements.txt"
        if req.exists():
            model.dependencies["python"] = [x.strip() for x in req.read_text(encoding="utf-8", errors="ignore").splitlines() if x.strip() and not x.lstrip().startswith("#")]
        pkg = self.root / "package.json"
        if pkg.exists():
            try:
                data = json.loads(pkg.read_text(encoding="utf-8"))
                model.dependencies["node"] = sorted(set(data.get("dependencies", {})) | set(data.get("devDependencies", {})))
            except (OSError, json.JSONDecodeError):
                pass

    def _extract_symbols(self, model: ProjectModel) -> None:
        for rel in model.source_files[:1000]:
            path = self.root / rel
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if path.suffix == ".py":
                symbols = re.findall(r"^(?:class|def|async def)\s+([A-Za-z_]\w*)", text, re.M)
            elif path.suffix in {".js", ".ts", ".tsx", ".jsx"}:
                symbols = re.findall(r"^(?:export\s+)?(?:async\s+)?(?:function|class)\s+([A-Za-z_]\w*)", text, re.M)
            else:
                symbols = []
            if symbols:
                model.symbols[rel] = symbols[:100]

    def _git(self) -> dict[str, Any]:
        def run(*args: str) -> str:
            result = subprocess.run(["git", "-C", str(self.root), *args], capture_output=True, text=True, timeout=10, check=False)
            return result.stdout.strip()
        branch = run("branch", "--show-current")
        if not branch:
            return {}
        status = run("status", "--short")
        return {"branch": branch, "commit": run("rev-parse", "HEAD"), "dirty": bool(status), "changed_files": [x[3:] for x in status.splitlines() if len(x) >= 3]}
