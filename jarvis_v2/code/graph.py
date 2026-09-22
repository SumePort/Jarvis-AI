"""Code relationship graph built from structured symbols and imports."""
from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class CodeGraph:
    nodes: dict[str,dict]=field(default_factory=dict)
    edges: list[dict]=field(default_factory=list)
    def add_node(self, node_id: str, kind: str, **attrs): self.nodes[node_id]={"kind":kind,**attrs}
    def add_edge(self, source: str, relation: str, target: str): self.edges.append({"source":source,"relation":relation,"target":target})

class CodeGraphBuilder:
    def build(self, symbols_by_file: dict[str,list]) -> CodeGraph:
        g=CodeGraph()
        for path,symbols in symbols_by_file.items():
            g.add_node(path,"file",path=path)
            for s in symbols:
                sid=f"{path}::{s.name}"
                g.add_node(sid,s.kind,line=s.line,parent=s.parent,signature=s.signature)
                g.add_edge(path,"defines",sid)
                if s.parent: g.add_edge(f"{path}::{s.parent}","contains",sid)
        return g
