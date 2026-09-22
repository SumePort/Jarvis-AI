"""Optional Playwright browser provider.
Install playwright separately and launch the browser before using this provider.
"""
from __future__ import annotations
from jarvis_v2.environment.browser_runtime import BrowserPage


class PlaywrightBrowserProvider:
    def __init__(self, page=None) -> None:
        self.page = page

    def _require(self):
        if self.page is None:
            raise RuntimeError("Playwright page is not configured")
        return self.page

    def open(self, url: str) -> BrowserPage:
        page = self._require()
        page.goto(url, wait_until="domcontentloaded")
        return BrowserPage(page.url, page.title(), page.locator("body").inner_text())

    def click(self, selector: str) -> None:
        self._require().locator(selector).click()

    def type(self, selector: str, text: str) -> None:
        self._require().locator(selector).fill(text)

    def read(self) -> BrowserPage:
        page = self._require()
        return BrowserPage(page.url, page.title(), page.locator("body").inner_text())
