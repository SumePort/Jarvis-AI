"""Jarvis planning helpers.

The deterministic planner handles a small set of safe, high-confidence
multi-step commands. Complex requests can still be planned by the local LLM.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
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

    def plan_actions(self, request: str, context: str = "") -> list[ActionStep]:
        system = (
            "Return only JSON in the form {\\"actions\\":[{\\"action\\":\\"open_app\\",\\"argument\\":\\"chrome\\"}]}. "
            "Allowed actions: open_app, close_app, open_file, read_file, type_text, press_key, "
            "click, scroll, calculate, web_search, browser_read, project_learn. "
            "Never invent an action. Return an empty actions list when tools are unnecessary."
        )
        try:
            raw = self.brain.chat([
                {"role": "system", "content": system},
                {"role": "user", "content": "Request: " + request + "\\nContext: " + context},
            ], temperature=0.0, max_tokens=500).strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            data = json.loads(raw)
        except (LocalBrainError, json.JSONDecodeError):
            return []
        if not isinstance(data, dict):
            return []
        actions = data.get("actions", [])
        if not isinstance(actions, list) or len(actions) > 8:
            return []
        allowed = {"open_app", "close_app", "open_file", "read_file", "type_text", "press_key",
                   "click", "scroll", "calculate", "web_search", "browser_read", "project_learn"}
        result = []
        for item in actions:
            if not isinstance(item, dict):
                return []
            action = item.get("action")
            argument = item.get("argument", "")
            if action not in allowed or not isinstance(argument, str):
                return []
            result.append(ActionStep(action, argument.strip()))
        return result
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
