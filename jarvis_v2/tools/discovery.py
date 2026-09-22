"""Dynamic discovery of safe, installed JARVIS tool adapters."""
from __future__ import annotations
from dataclasses import dataclass
from jarvis_v2.core.types import ToolSpec, ActionRisk, DataClass
from jarvis_v2.capabilities import CapabilityRegistry

@dataclass(frozen=True)
class ToolDescriptor:
    spec: ToolSpec
    adapter: str
    available: bool = True

class ToolDiscovery:
    def __init__(self, capabilities: CapabilityRegistry) -> None:
        self.capabilities=capabilities

    def discover(self) -> list[ToolDescriptor]:
        candidates=[
            ToolDescriptor(ToolSpec("calculate","Evaluate a safe arithmetic expression",{"expression":"string"},(),ActionRisk.ALLOW,DataClass.NORMAL),"local.calculate"),
            ToolDescriptor(ToolSpec("read_file","Read a bounded local text file",{"path":"string"},("filesystem",),ActionRisk.ALLOW,DataClass.NORMAL),"local.read_file"),
            ToolDescriptor(ToolSpec("open_file","Open a local file with the host OS",{"path":"string"},("filesystem",),ActionRisk.ALLOW,DataClass.NORMAL),"local.open_file"),
            ToolDescriptor(ToolSpec("open_app","Open an installed application",{"name":"string"},("os.windows",),ActionRisk.ALLOW,DataClass.NORMAL),"local.open_app"),
        ]
        return [x for x in candidates if self._available(x.spec)]

    def _available(self, spec: ToolSpec) -> bool:
        return all((s:=self.capabilities.get(c)) is not None and s.available for c in spec.capabilities)

    def specs(self) -> list[ToolSpec]:
        return [x.spec for x in self.discover()]
