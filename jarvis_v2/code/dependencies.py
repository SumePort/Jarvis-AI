"""Dependency and API surface intelligence for application projects."""
from __future__ import annotations
import json, re
from dataclasses import dataclass, field
from pathlib import Path

@dataclass(frozen=True)
class Dependency:
    name: str
    version: str = ""
    source: str = ""

@dataclass(frozen=True)
class APIRoute:
    method: str
    path: str
    file: str
    line: int = 0
    framework: str = ""

@dataclass
class DependencyModel:
    dependencies: list[Dependency] = field(default_factory=list)
    routes: list[APIRoute] = field(default_factory=list)
    configs: list[str] = field(default_factory=list)

class DependencyAnalyzer:
    def analyze(self, root: str | Path) -> DependencyModel:
        root=Path(root).resolve(); model=DependencyModel()
        req=root/"requirements.txt"
        if req.is_file():
            for line in req.read_text(encoding="utf-8",errors="replace").splitlines():
                line=line.strip()
                if not line or line.startswith("#"): continue
                m=re.match(r"([A-Za-z0-9_.-]+)\\s*(?:([<>=!~].*))?$",line)
                if m: model.dependencies.append(Dependency(m.group(1),m.group(2) or "",str(req)))
        package=root/"package.json"
        if package.is_file():
            try:
                data=json.loads(package.read_text(encoding="utf-8"))
                for section in ("dependencies","devDependencies"):
                    for name,version in data.get(section,{}).items(): model.dependencies.append(Dependency(name,str(version),str(package)))
            except (json.JSONDecodeError,OSError): pass
        for candidate in (root/"pyproject.toml",root/"pubspec.yaml",root/"package.json",root/"requirements.txt"):
            if candidate.is_file(): model.configs.append(str(candidate))
        for p in root.rglob("*.py"):
            if any(part in {".git",".venv","venv","node_modules","__pycache__"} for part in p.parts): continue
            try: text=p.read_text(encoding="utf-8",errors="replace")
            except OSError: continue
            for i,line in enumerate(text.splitlines(),1):
                for m in re.finditer(r"@(?:app|router)\\.(get|post|put|patch|delete)\\(\\s*[\"']([^\"']+)",line):
                    model.routes.append(APIRoute(m.group(1).upper(),m.group(2),str(p),i,"FastAPI-like"))
        return model
