"""First-generation hybrid router.

The router intentionally handles obvious deterministic commands without asking an
LLM to reason about them. More complex requests can be handed to the local brain.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .connection import ConnectionManager


class Route(str, Enum):
    LOCAL_TOOL = "local_tool"
    LOCAL_AI = "local_ai"
    ONLINE = "online"
    HYBRID = "hybrid"


@dataclass(frozen=True)
class RouteDecision:
    route: Route
    reason: str


class JarvisRouter:
    ONLINE_HINTS = (
        "latest", "today", "current", "search", "research", "youtube",
        "website", "online", "internet", "news", "browse",
    )
    HYBRID_HINTS = (
        "research and", "compare with the web", "look up and",
        "check documentation and", "search and fix",
    )
    LOCAL_TOOL_PREFIXES = (
        "open ", "close ", "launch ", "start ", "type ", "press ",
        "click ", "scroll ", "calculate ", "create folder",
    )

    def __init__(self, connection: ConnectionManager | None = None):
        self.connection = connection or ConnectionManager()

    def decide(self, text: str) -> RouteDecision:
        q = text.strip().lower()
        if q.startswith(self.LOCAL_TOOL_PREFIXES):
            return RouteDecision(Route.LOCAL_TOOL, "Deterministic computer/system command.")
        if any(h in q for h in self.HYBRID_HINTS):
            if self.connection.is_online():
                return RouteDecision(Route.HYBRID, "Request combines local work with online research.")
            return RouteDecision(Route.LOCAL_AI, "Hybrid request received while offline; using local capabilities.")
        if any(h in q for h in self.ONLINE_HINTS):
            if self.connection.is_online():
                return RouteDecision(Route.ONLINE, "Request benefits from current online information.")
            return RouteDecision(Route.LOCAL_AI, "Online capability requested but internet is unavailable.")
        return RouteDecision(Route.LOCAL_AI, "General reasoning/project request.")
