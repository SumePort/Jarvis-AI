from jarvis_v2.capabilities import CapabilityRegistry
from jarvis_v2.tools.discovery import ToolDiscovery
from jarvis_v2.tools.runtime_registry import RuntimeToolRegistry

def test_tool_discovery_is_capability_aware():
    caps=CapabilityRegistry().discover()
    names={x.spec.name for x in ToolDiscovery(caps).discover()}
    assert "calculate" in names

def test_runtime_registry_builds():
    caps=CapabilityRegistry().discover()
    registry=RuntimeToolRegistry(caps).build()
    assert registry.specs_list()
