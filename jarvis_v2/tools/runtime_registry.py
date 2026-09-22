"""Build a live tool registry from discovered adapters."""
from __future__ import annotations
from .discovery import ToolDiscovery
from .registry import ToolRegistry
from .adapters import LocalAdapters

class RuntimeToolRegistry:
    def __init__(self, capabilities) -> None:
        self.capabilities=capabilities
        self.discovery=ToolDiscovery(capabilities)

    def build(self) -> ToolRegistry:
        registry=ToolRegistry()
        adapters=LocalAdapters()
        handlers={
            "calculate": adapters.calculate,
            "read_file": adapters.read_file,
            "open_file": adapters.open_file,
            "open_app": adapters.open_app,
        }
        for descriptor in self.discovery.discover():
            handler=handlers.get(descriptor.spec.name)
            if handler is not None:
                registry.register(descriptor.spec, handler)
        return registry
