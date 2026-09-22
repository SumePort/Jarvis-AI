from jarvis_v2.environment.ui import WindowsUIProvider
from jarvis_v2.perception.ui import UIPerception

def test_ui_provider_has_bounded_snapshot_api():
    p=WindowsUIProvider()
    result=p.snapshot(max_depth=0,max_elements=1)
    assert "elements" in result

def test_ui_perception_handles_unavailable():
    result=UIPerception().perceive({"available":False,"reason":"test"})
    assert result.percepts == []
