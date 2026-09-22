"""Connect application architecture to database facts."""
from __future__ import annotations
from dataclasses import dataclass
from .database import DatabaseModel
from .graph import CodeGraph

@dataclass
class DataArchitecture:
    code_graph: CodeGraph | None
    database: DatabaseModel
    def facts(self) -> list[dict]:
        out=[]
        for t in self.database.tables: out.append({"kind":"table","name":t.name,"columns":list(t.columns),"source":t.source})
        for r in self.database.relationships: out.append({"kind":"relationship","source_table":r.source_table,"source_column":r.source_column,"target_table":r.target_table,"target_column":r.target_column,"source":r.source})
        for m in self.database.migrations: out.append({"kind":"migration","path":m})
        return out
