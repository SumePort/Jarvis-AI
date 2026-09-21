"""Jarvis planning helpers.

The deterministic planner handles a small set of safe, high-confidence
multi-step commands. Complex requests can still be planned by the local LLM.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

from brain.local_brain import LocalBrain


@dataclass
class Plan:
    text: str
    steps: list[str]


@dataclass(frozen=True)
class ActionStep:
    action: str
    argument: str = ""


class Planner:
    def __init__(self, brain=None):
        self.brain = brain or LocalBrain()

    def make_plan(self, request: str, context: str = "") -> Plan:
        text = self.brain.ask(
            "Return a short numbered plan only. Do not execute anything.\n"
            "Request: " + request + "\nContext: " + context
        )
        steps = [
            line.strip(" -0123456789.")
            for line in text.splitlines()
            if line.strip()
        ]
        return Plan(text, steps)

    @staticmethod
    def deterministic_steps(request: str) -> list[ActionStep]:
        """Parse only unambiguous, safe multi-step commands."""
        q = request.strip()

        match = re.match(
            r"^(?:please\s+)?open\s+(?:the\s+)?(?:app\s+)?"
            r"(chrome|google chrome|notepad|calculator|calc|paint)"
            r"\s*[,;]\s*search\s+(?:for\s+)?(.+?)"
            r"(?:\s*,?\s*(?:and\s+)?(?:tell|show|read|summarize)\s+"
            r"(?:me\s+)?(?:what\s+you\s+find|what\s+you\s+found|"
            r"the\s+results?|it))?\s*$",
            q,
            re.IGNORECASE,
        )
        if match:
            app = match.group(1)
            query = match.group(2).strip()
            query = re.sub(
                r"\s*,?\s*(?:and\s+)?(?:tell|show|read|summarize)\s+"
                r"(?:me\s+)?(?:what\s+you\s+find|what\s+you\s+found|"
                r"the\s+results?|it)\s*$",
                "",
                query,
                flags=re.IGNORECASE,
            ).strip(" ,")
            return [
                ActionStep("open_app", app),
                ActionStep("web_search", query),
                ActionStep("browser_read"),
                ActionStep("summarize"),
            ]

        match = re.match(
            r"^(?:please\s+)?search\s+(?:for\s+)?(.+?)"
            r"\s*(?:,?\s*(?:and\s+)?(?:tell|show|read|summarize)\s+"
            r"(?:me\s+)?(?:what\s+you\s+find|what\s+you\s+found|"
            r"the\s+results?|it))\s*$",
            q,
            re.IGNORECASE,
        )
        if match:
            return [
                ActionStep("web_search", match.group(1).strip(" ,")),
                ActionStep("browser_read"),
                ActionStep("summarize"),
            ]

        match = re.match(
            r"^(?:please\s+)?open\s+(?:the\s+)?(?:app\s+)?"
            r"(notepad|calculator|calc|paint|chrome|google chrome)"
            r"\s+(?:and|then)\s+(?:type|write)\s+(.+)$",
            q,
            re.IGNORECASE,
        )
        if match:
            return [
                ActionStep("open_app", match.group(1)),
                ActionStep("type_text", match.group(2).strip()),
            ]

        match = re.match(
            r"^(?:please\s+)?open\s+(?:the\s+)?(?:app\s+)?"
            r"(notepad|calculator|calc|paint|chrome|google chrome)"
            r"\s*[,;]\s*(?:type|write)\s+(.+?)"
            r"\s*[,;]\s*(?:then\s+)?press\s+(?:the\s+)?([a-z0-9_+\-]+)\s*$",
            q,
            re.IGNORECASE,
        )
        if match:
            return [
                ActionStep("open_app", match.group(1)),
                ActionStep("type_text", match.group(2).strip()),
                ActionStep("press_key", match.group(3).strip()),
            ]

        return []
