"""Provider registry for optional JARVIS integrations."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class ProviderRegistry:
    _items: dict[str, Any]

    def __init__(self):
        self._items = {}

    def register(self, name: str, provider: Any) -> None:
        if not name or provider is None:
            raise ValueError("Provider name and instance are required")
        self._items[name] = provider

    def get(self, name: str) -> Any | None:
        return self._items.get(name)

    def available(self) -> tuple[str, ...]:
        return tuple(sorted(self._items))

    def require(self, name: str) -> Any:
        provider = self.get(name)
        if provider is None:
            raise RuntimeError(f"Provider not configured: {name}")
        return provider
