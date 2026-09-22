from __future__ import annotations

from pathlib import Path

from jarvis_v2.code.impact_graph import ImpactGraph
from jarvis_v2.code.architecture import ArchitectureModel
from jarvis_v2.code.database import DatabaseModel
from jarvis_v2.diagnostics.analyzer import DiagnosticEvent
from jarvis_v2.tests.intelligence import TestFailure
from jarvis_v2.knowledge.world_graph import UnifiedWorldGraph, WorldNode, WorldEdge


class KnowledgeGraphFusion:
    """Fuse project, code, architecture, data, diagnostics and test evidence into one graph."""

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()

    def fuse(
        self,
        impact_graph: ImpactGraph | None = None,
        architecture: ArchitectureModel | None = None,
        database: DatabaseModel | None = None,
        diagnostics: list[DiagnosticEvent] | None = None,
        failures: list[TestFailure] | None = None,
    ) -> UnifiedWorldGraph:
        graph = UnifiedWorldGraph()

        if impact_graph:
            for node in impact_graph.nodes.values():
                graph.add_node(WorldNode(
                    id=node.id, kind=node.kind, label=node.label,
                    source="impact_graph", attributes={"file": node.file},
                ))
            for edge in impact_graph.edges:
                graph.add_edge(WorldEdge(edge.source, edge.relation, edge.target, "impact_graph"))

        if architecture:
            for symbol in architecture.code_graph.nodes:
                sid = "symbol:" + symbol
                graph.add_node(WorldNode(sid, "symbol", symbol, "architecture"))
            for dep in architecture.dependency_model.dependencies:
                did = "dependency:" + dep.name
                graph.add_node(WorldNode(did, "dependency", dep.name, "architecture",
                                         {"version": dep.version, "source": dep.source}))

        if database:
            for table in database.tables:
                tid = "table:" + table.name
                graph.add_node(WorldNode(tid, "database_table", table.name, "database"))
                for column in table.columns:
                    cid = f"{tid}:column:{column}"
                    graph.add_node(WorldNode(cid, "database_column", column, "database"))
                    graph.add_edge(WorldEdge(tid, "has_column", cid, "database"))
            for rel in database.relationships:
                source = "table:" + rel.source_table
                target = "table:" + rel.target_table
                if source not in graph.nodes:
                    graph.add_node(WorldNode(source, "database_table", rel.source_table, "database"))
                if target not in graph.nodes:
                    graph.add_node(WorldNode(target, "database_table", rel.target_table, "database"))
                graph.add_edge(WorldEdge(source, "relates_to", target, "database"))

        for event in diagnostics or []:
            eid = f"diagnostic:{event.kind}:{event.source}:{event.line or 0}"
            graph.add_node(WorldNode(eid, "diagnostic", event.message, "diagnostics",
                                     {"severity": event.severity, "file": event.source, "line": event.line}))
            if event.source:
                fid = "file:" + event.source.replace("\\", "/")
                if fid in graph.nodes:
                    graph.add_edge(WorldEdge(eid, "points_to", fid, "diagnostics"))

        for failure in failures or []:
            fid = f"failure:{failure.framework}:{failure.test_name}"
            graph.add_node(WorldNode(fid, "test_failure", failure.message, "tests",
                                     {"file": failure.file, "line": failure.line}))
            if failure.file:
                target = "file:" + failure.file.replace("\\", "/")
                if target in graph.nodes:
                    graph.add_edge(WorldEdge(fid, "points_to", target, "tests"))

        return graph
