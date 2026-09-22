"""Read-only database/schema intelligence for local project analysis."""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from pathlib import Path

@dataclass(frozen=True)
class TableModel:
    name: str
    columns: tuple[str, ...] = ()
    source: str = ""

@dataclass(frozen=True)
class Relationship:
    source_table: str
    source_column: str
    target_table: str
    target_column: str
    source: str = ""

@dataclass
class DatabaseModel:
    tables: list[TableModel] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)
    migrations: list[str] = field(default_factory=list)
    config_files: list[str] = field(default_factory=list)

class DatabaseAnalyzer:
    """Analyze migration/schema text only; never connects to a database."""
    def analyze(self, root: str | Path) -> DatabaseModel:
        root=Path(root).resolve(); model=DatabaseModel()
        for p in root.rglob("*"):
            if not p.is_file() or any(x in {".git",".venv","venv","node_modules","__pycache__"} for x in p.parts): continue
            if p.suffix.lower() not in {".sql",".py",".ts",".js"}: continue
            try: text=p.read_text(encoding="utf-8",errors="replace")
            except OSError: continue
            if len(text)>1_000_000: continue
            if p.suffix.lower()==".sql": self._sql(text,str(p),model)
            else: self._orm(text,str(p),model)
            if "migration" in p.name.lower() or "migrations" in p.parts: model.migrations.append(str(p))
        return model

    def _sql(self,text,source,model):
        pattern=r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([A-Za-z0-9_.-]+)\s*\((.*?)\);"
        for m in re.finditer(pattern,text,re.I|re.S):
            cols=[]
            for line in m.group(2).splitlines():
                cm=re.match(r"\s*([A-Za-z0-9_.-]+)\s+",line)
                if cm and cm.group(1).upper() not in {"PRIMARY","FOREIGN","UNIQUE","CONSTRAINT","CHECK"}: cols.append(cm.group(1))
            model.tables.append(TableModel(m.group(1),tuple(cols),source))
        for m in re.finditer(r"FOREIGN\s+KEY\s*\(([^)]+)\)\s*REFERENCES\s+([A-Za-z0-9_.-]+)\s*\(([^)]+)\)",text,re.I):
            model.relationships.append(Relationship("?",m.group(1).strip(),m.group(2),m.group(3).strip(),source))

    def _orm(self,text,source,model):
        for m in re.finditer(r"class\s+(\w+).*?(?:\nclass|\Z)",text,re.S):
            block=m.group(0)
            if re.search(r"(Model|models\.Model|Base)",block):
                fields=re.findall(r"^\s+(\w+)\s*=\s*[^\n]+(?:Field|Column|CharField|IntegerField|TextField|BooleanField|DateTimeField)",block,re.M)
                model.tables.append(TableModel(m.group(1),tuple(fields),source))
