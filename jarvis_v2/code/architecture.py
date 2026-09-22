"""Combine code symbols, dependencies and API routes into architecture facts."""
from __future__ import annotations
from dataclasses import dataclass, field
from .dependencies import DependencyModel
from .graph import CodeGraph

@dataclass
class ArchitectureModel:
    code_graph: CodeGraph | None = None
    dependencies: DependencyModel = field(default_factory=DependencyModel)
    facts: list[dict] = field(default_factory=list)

    def build_facts(self):
        self.facts=[]
        for d in self.dependencies.dependencies:
            self.facts.append({"kind":"dependency","name":d.name,"version":d.version,"source":d.source})
        for r in self.dependencies.routes:
            self.facts.append({"kind":"api_route","method":r.method,"path":r.path,"file":r.file,"line":r.line,"framework":r.framework})
        for c in self.dependencies.configs:
            self.facts.append({"kind":"config","path":c})
        return self.facts
