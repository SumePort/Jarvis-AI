"""Provider-neutral web research pipeline with evidence boundaries."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ResearchSource:
    title: str
    url: str
    content: str
    published_at: str | None = None


@dataclass(frozen=True)
class ResearchResult:
    query: str
    sources: tuple[ResearchSource, ...]
    synthesis_context: str


class ResearchProvider(Protocol):
    def search(self, query: str, limit: int = 5) -> list[ResearchSource]: ...


class ResearchPipeline:
    def __init__(self, provider: ResearchProvider | None = None) -> None:
        self.provider = provider

    def search(self, query: str, limit: int = 5) -> ResearchResult:
        if not self.provider:
            raise RuntimeError("No research provider configured")
        sources = tuple(self.provider.search(query, limit))
        context = "\n\n".join(
            f"[{i+1}] {s.title}\n{s.url}\n{s.content[:6000]}"
            for i, s in enumerate(sources)
        )
        return ResearchResult(query, sources, context)
