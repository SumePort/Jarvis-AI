"""Controlled browser runtime contract."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class BrowserPage:
    url: str
    title: str
    text: str = ""


class BrowserProvider(Protocol):
    def open(self, url: str) -> BrowserPage: ...
    def click(self, selector: str) -> None: ...
    def type(self, selector: str, text: str) -> None: ...
    def read(self) -> BrowserPage: ...


class BrowserRuntime:
    def __init__(self, provider: BrowserProvider | None = None) -> None:
        self.provider = provider

    def require_provider(self) -> BrowserProvider:
        if not self.provider:
            raise RuntimeError("No browser provider configured")
        return self.provider
