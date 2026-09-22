"""Optional Playwright session factory."""
from __future__ import annotations


class PlaywrightSessionFactory:
    def __init__(self, headless: bool = False) -> None:
        self.headless = headless
        self._playwright = None
        self._browser = None

    def start(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError("Playwright is not installed") from exc
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self.headless)
        return self._browser.new_page()

    def close(self) -> None:
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None
