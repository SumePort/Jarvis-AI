from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
import ast


@dataclass(frozen=True)
class ImpactNode:
    id: str
    kind: str
    label: str
    file: str = ""


@dataclass(frozen=True)
class ImpactEdge:
    source: str
    relation: str
    target: str


@dataclass
class ImpactGraph:
    nodes: dict[str, ImpactNode] = field(default_factory=dict)
    edges: list[ImpactEdge] = field(default_factory=list)

    def add_node(self, node: ImpactNode) -> None:
        self.nodes[node.id] = node

    def add_edge(self, edge: ImpactEdge) -> None:
        if edge.source in self.nodes and edge.target in self.nodes:
            self.edges.append(edge)

    def neighbors(self, node_id: str, relation: str | None = None) -> list[ImpactNode]:
        ids = [e.target for e in self.edges if e.source == node_id and (relation is None or e.relation == relation)]
        return [self.nodes[i] for i in ids]

    def to_dict(self) -> dict:
        return {
            "nodes": [n.__dict__ for n in self.nodes.values()],
            "edges": [e.__dict__ for e in self.edges],
        }


class CrossLayerImpactBuilder:
    """Build a bounded file/import/API/test/schema relationship graph."""

    IGNORED = {".git", ".venv", "venv", "node_modules", "__pycache__", "build", "dist"}

    def __init__(self, root: str | Path, max_files: int = 2000):
        self.root = Path(root).resolve()
        self.max_files = max_files

    def build(self) -> ImpactGraph:
        graph = ImpactGraph()
        files = self._files()
        for path in files:
            rel = path.relative_to(self.root).as_posix()
            graph.add_node(ImpactNode("file:" + rel, "file", rel, rel))

        file_ids = {n.file: n.id for n in graph.nodes.values()}
        for path in files:
            rel = path.relative_to(self.root).as_posix()
            source = file_ids[rel]
            text = self._read(path)
            for imported in self._imports(path, text):
                target_rel = self._resolve_import(path, imported)
                if target_rel in file_ids:
                    graph.add_edge(ImpactEdge(source, "imports", file_ids[target_rel]))

            if path.name.startswith("test_") or ".test." in path.name or ".spec." in path.name:
                for target in self._test_targets(text, file_ids):
                    graph.add_edge(ImpactEdge(source, "tests", target))

            for method, route in self._routes(text):
                rid = f"route:{method} {route}"
                graph.add_node(ImpactNode(rid, "api_route", f"{method} {route}", rel))
                graph.add_edge(ImpactEdge(source, "defines", rid))

            for table in self._tables(text):
                tid = "table:" + table
                graph.add_node(ImpactNode(tid, "database_table", table, rel))
                graph.add_edge(ImpactEdge(source, "references", tid))

        return graph

    def _files(self) -> list[Path]:
        found = []
        if not self.root.is_dir():
            return found
        import os
        for base, dirs, names in os.walk(self.root):
            dirs[:] = [d for d in dirs if d not in self.IGNORED]
            for name in names:
                p = Path(base) / name
                if p.suffix in {".py", ".js", ".jsx", ".ts", ".tsx", ".sql", ".dart"}:
                    found.append(p)
                    if len(found) >= self.max_files:
                        return found
        return found

    @staticmethod
    def _read(path: Path) -> str:
        try:
            if path.stat().st_size > 1_000_000:
                return ""
            return path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""

    @staticmethod
    def _imports(path: Path, text: str) -> list[str]:
        if path.suffix == ".py":
            try:
                tree = ast.parse(text)
                imports = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        imports.extend(alias.name for alias in node.names)
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        imports.append(node.module)
                return imports
            except SyntaxError:
                return re.findall(r"^\s*(?:from|import)\s+([A-Za-z_][\w.]*)", text, re.M)
        return re.findall(r"""(?:from|import)\s+["']([^"']+)["']""", text)

    def _resolve_import(self, source: Path, imported: str) -> str:
        if imported.startswith("."):
            base = (source.parent / imported.lstrip(".")).resolve()
        elif source.suffix == ".py":
            base = (self.root / imported.replace(".", "/")).resolve()
        else:
            base = (self.root / imported).resolve()
        candidates = [base, Path(str(base) + ".py"), Path(str(base) + ".ts"), Path(str(base) + ".tsx"),
                      base / "__init__.py", base / "index.ts", base / "index.js"]
        for c in candidates:
            try:
                return c.relative_to(self.root).as_posix() if c.is_file() else ""
            except ValueError:
                continue
        return ""

    @staticmethod
    def _test_targets(text: str, file_ids: dict[str, str]) -> list[str]:
        refs = re.findall(r"(?:from\s+|import\s+)([A-Za-z_][\w./-]*)", text)
        targets = []
        for ref in refs:
            ref = ref.replace(".", "/")
            for rel, fid in file_ids.items():
                if rel.endswith(ref) or rel.removesuffix(Path(rel).suffix) == ref:
                    targets.append(fid)
        return targets

    @staticmethod
    def _routes(text: str) -> list[tuple[str, str]]:
        return [(m.group(1).upper(), m.group(2)) for m in re.finditer(
            r'@(?:app|router)\.(get|post|put|patch|delete)\(\s*["\']([^"\']+)', text, re.I)]

    @staticmethod
    def _tables(text: str) -> list[str]:
        return re.findall(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([\w.-]+)", text, re.I)
