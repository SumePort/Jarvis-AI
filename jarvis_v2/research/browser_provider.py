"""Browser-native research provider for background web search."""
from __future__ import annotations
from urllib.parse import quote_plus
from jarvis_v2.research.pipeline import ResearchSource


class BrowserResearchProvider:
    """Use an existing controlled browser provider for research.

    Search URL is configurable; the browser remains subject to the same
    session, network and UI policies as foreground browsing.
    """

    def __init__(self, browser, search_url: str = "https://www.google.com/search?q={query}"):
        self.browser = browser
        self.search_url = search_url

    def search(self, query: str, limit: int = 5) -> list[ResearchSource]:
        page = self.browser.require_provider().open(self.search_url.format(query=quote_plus(query)))
        # Provider-neutral extraction: the browser provider may return rendered
        # page text. A richer DOM extractor can be attached later.
        text = page.text[:30000]
        return [ResearchSource(
            title=page.title or query,
            url=page.url,
            content=text,
        )]
