"""Structured browser/DOM observation provider.

Provider-neutral interface. A concrete browser connector can supply a page DOM
snapshot without requiring screenshots as the canonical representation.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict, field
from typing import Any, Protocol

@dataclass(frozen=True)
class DOMElement:
    tag: str
    text: str = ""
    role: str = ""
    name: str = ""
    element_id: str = ""
    href: str = ""
    value: str = ""
    attributes: dict[str, str] = field(default_factory=dict)

class BrowserDOMProvider(Protocol):
    def snapshot(self, max_elements: int = 500) -> dict[str, Any]: ...

class StaticDOMProvider:
    """Adapter useful for tests and for browser connectors to implement against."""
    def __init__(self, url: str, title: str, elements: list[DOMElement]) -> None:
        self.url=url; self.title=title; self.elements=elements

    def snapshot(self, max_elements: int = 500) -> dict[str, Any]:
        if max_elements <= 0: raise ValueError("max_elements must be positive")
        return {"url":self.url,"title":self.title,"elements":[asdict(x) for x in self.elements[:max_elements]]}
