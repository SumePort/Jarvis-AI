"""Playwright-backed semantic browser controller."""
from __future__ import annotations
from typing import Any


class PlaywrightController:
    def __init__(self, page):
        self.page = page

    def navigate(self, url: str) -> dict[str, Any]:
        self.page.goto(url, wait_until="domcontentloaded")
        return {"url": self.page.url, "title": self.page.title()}

    def click(self, selector: dict[str, str]) -> dict[str, Any]:
        locator = self._locator(selector)
        locator.click()
        return {"clicked": selector}

    def type_text(self, selector: dict[str, str], text: str) -> dict[str, Any]:
        locator = self._locator(selector)
        locator.fill(text)
        return {"typed": True, "selector": selector}

    def read(self) -> dict[str, Any]:
        return {"url": self.page.url, "title": self.page.title(),
                "text": self.page.locator("body").inner_text()[:30000]}

    def _locator(self, selector: dict[str, str]):
        if "role" in selector:
            return self.page.get_by_role(selector["role"], name=selector.get("name"))
        if "label" in selector:
            return self.page.get_by_label(selector["label"])
        if "text" in selector:
            return self.page.get_by_text(selector["text"])
        if "css" in selector:
            return self.page.locator(selector["css"])
        raise ValueError("Selector must contain role, label, text, or css")
