"""Compact project world model exposed to JARVIS reasoning."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from .graph import ProjectGraph
from .graph_builder import ProjectGraphBuilder
from .intelligence import ProjectIntelligence, ProjectModel

@dataclass
class ProjectWorldModel:
    project: ProjectModel
    graph: ProjectGraph

    def context(self) -> dict[str, Any]:
        return {"project": self.project.to_dict(), "graph": self.graph.to_dict()}

class ProjectWorldModelBuilder:
    def build(self, root: str) -> ProjectWorldModel:
        project = ProjectIntelligence(root).inspect()
        graph = ProjectGraphBuilder().build(project)
        return ProjectWorldModel(project, graph)
