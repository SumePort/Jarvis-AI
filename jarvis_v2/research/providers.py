"""Explicit research provider adapters."""
from __future__ import annotations
from jarvis_v2.research.pipeline import ResearchSource


class CallableResearchProvider:
    def __init__(self, search_fn):
        self.search_fn = search_fn

    def search(self, query: str, limit: int = 5) -> list[ResearchSource]:
        rows = self.search_fn(query, limit)
        return [
            ResearchSource(
                str(row.get("title", "")),
                str(row.get("url", "")),
                str(row.get("content", "")),
                row.get("published_at"),
            )
            for row in rows
        ]
