"""Turn project world-model facts into durable, retrievable knowledge."""
from __future__ import annotations
from .store import MemoryRecord

class KnowledgeExtractor:
    def from_project(self, model) -> list[MemoryRecord]:
        records=[]
        root=model.root
        records.append(MemoryRecord(id=f"project:{root}", kind="project", project=root, source="project_intelligence", text=f"Project {model.name}. Types: {', '.join(model.project_type) or 'unknown'}. Languages: {', '.join(model.languages) or 'unknown'}. Frameworks: {', '.join(model.frameworks) or 'none detected'}."))
        for rel, symbols in model.symbols.items():
            records.append(MemoryRecord(id=f"symbols:{root}:{rel}", kind="code_symbols", project=root, source=rel, tags=["code", "symbols"], text=f"{rel} defines: {', '.join(symbols)}."))
        for ecosystem, deps in model.dependencies.items():
            if deps:
                records.append(MemoryRecord(id=f"deps:{root}:{ecosystem}", kind="dependencies", project=root, source=f"{ecosystem} manifest", tags=["dependencies", ecosystem], text=f"{ecosystem} dependencies: {', '.join(deps)}."))
        return records
