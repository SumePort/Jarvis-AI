"""Generic HTTP JSON research provider.

The endpoint is intentionally configurable so JARVIS is not coupled to a
single search vendor. The provider expects {"results":[...]} where each result
contains title, url, content and optional published_at.
"""
from __future__ import annotations
import json
from urllib.request import Request, urlopen
from jarvis_v2.research.pipeline import ResearchSource


class HttpJsonResearchProvider:
    def __init__(self, endpoint: str, timeout: int = 15, headers: dict[str, str] | None = None):
        if not endpoint.startswith(("https://", "http://")):
            raise ValueError("Research endpoint must use HTTP(S)")
        self.endpoint, self.timeout = endpoint, timeout
        self.headers = {"Content-Type": "application/json", **(headers or {})}

    def search(self, query: str, limit: int = 5) -> list[ResearchSource]:
        payload = json.dumps({"query": query, "limit": limit}).encode()
        req = Request(self.endpoint, data=payload, headers=self.headers, method="POST")
        with urlopen(req, timeout=self.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        rows = data.get("results", [])
        return [
            ResearchSource(str(r.get("title", "")), str(r.get("url", "")),
                           str(r.get("content", "")), r.get("published_at"))
            for r in rows[:limit]
        ]
