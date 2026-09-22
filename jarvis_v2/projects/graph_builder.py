"""Build a project relationship graph from ProjectModel."""
from __future__ import annotations
from .graph import GraphEdge, GraphNode, ProjectGraph
from .intelligence import ProjectModel

class ProjectGraphBuilder:
    def build(self, model: ProjectModel) -> ProjectGraph:
        g = ProjectGraph()
        root = "project:" + model.root
        g.add_node(GraphNode(root, "project", model.name))
        for rel in model.source_files + model.test_files + model.config_files + model.documentation:
            nid = "file:" + rel
            g.add_node(GraphNode(nid, "file", rel))
            g.add_edge(GraphEdge(root, "contains", nid))
        for rel, symbols in model.symbols.items():
            fid = "file:" + rel
            for symbol in symbols:
                sid = f"symbol:{rel}:{symbol}"
                g.add_node(GraphNode(sid, "symbol", symbol, {"file": rel}))
                g.add_edge(GraphEdge(fid, "defines", sid))
        for group, deps in model.dependencies.items():
            for dep in deps:
                did = f"dependency:{group}:{dep}"
                g.add_node(GraphNode(did, "dependency", dep, {"ecosystem": group}))
                g.add_edge(GraphEdge(root, "depends_on", did))
        return g
