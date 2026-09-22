"""Browser-native research provider for background web search."""
from __future__ import annotations
from urllib.parse import quote_plus
from jarvis_v2.research.pipeline import ResearchSource


class BrowserResearchProvider:
    """Extract multiple search-result-like blocks from the rendered page.

    It deliberately keeps extraction provider-neutral: if the browser exposes
    structured links, those are preferred; otherwise rendered text remains a
    fallback source.
    """

    def __init__(self, browser, search_url: str = "https://www.google.com/search?q={query}"):
        self.browser = browser
        self.search_url = search_url

    def search(self, query: str, limit: int = 5) -> list[ResearchSource]:
        page = self.browser.require_provider().open(
            self.search_url.format(query=quote_plus(query))
        )
        sources: list[ResearchSource] = []
        extractor = getattr(page, "research_results", None)
        if callable(extractor):
            for item in extractor(limit=limit):
                if isinstance(item, ResearchSource):
                    sources.append(item)
                elif isinstance(item, dict) and item.get("url"):
                    sources.append(ResearchSource(
                        title=str(item.get("title") or item["url"]),
                        url=str(item["url"]),
                        content=str(item.get("content") or ""),
                        published_at=item.get("published_at"),
                    ))
        if sources:
            return sources[:limit]
        text = getattr(page, "text", "")[:30000]
        return [ResearchSource(
            title=getattr(page, "title", None) or query,
            url=getattr(page, "url", "") or self.search_url.format(query=quote_plus(query)),
            content=text,
        )]
