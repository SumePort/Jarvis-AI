from jarvis_v2.capabilities import CapabilityRegistry

def test_discovery_has_python():
    r=CapabilityRegistry().discover()
    assert r.get("python").available

def test_discovery_is_serializable():
    r=CapabilityRegistry().discover()
    assert "python" in r.as_dict()
