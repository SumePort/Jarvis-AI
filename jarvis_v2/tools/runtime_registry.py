"""Build the live Windows/local tool registry from discovered capabilities."""
from __future__ import annotations

from .discovery import ToolDiscovery
from .registry import ToolRegistry
from .adapters import LocalAdapters
from .windows import WindowsAdapters, windows_tool_specs
from .system import SystemAdapters


class RuntimeToolRegistry:
    def __init__(self, capabilities) -> None:
        self.capabilities = capabilities
        self.discovery = ToolDiscovery(capabilities)

    def build(self) -> ToolRegistry:
        registry = ToolRegistry()
        adapters = LocalAdapters()
        handlers = {
            "calculate": adapters.calculate,
            "read_file": adapters.read_file,
            "open_file": adapters.open_file,
            "open_app": adapters.open_app,
        }
        for descriptor in self.discovery.discover():
            handler = handlers.get(descriptor.spec.name)
            if handler is not None:
                registry.register(descriptor.spec, handler)

        if self.capabilities.get("os.windows") and self.capabilities.get("os.windows").available:
            windows = WindowsAdapters()
            for spec in windows_tool_specs():
                handler = getattr(windows, spec.name)
                registry.register(spec, handler)

        system = SystemAdapters()
        for spec in system.windows_tool_specs():
            registry.register(spec, getattr(system, spec.name))

        return registry
