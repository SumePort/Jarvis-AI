from jarvis_v2.environment.browser import DOMElement, StaticDOMProvider
from jarvis_v2.perception.browser import BrowserPerception

def test_dom_snapshot_is_bounded():
    p=StaticDOMProvider("https://example.test","Example",[DOMElement("button","Save",role="button")])
    assert len(p.snapshot(1)["elements"]) == 1

def test_browser_perception():
    p=StaticDOMProvider("https://example.test","Example",[DOMElement("button","Save",role="button")])
    result=BrowserPerception().perceive(p.snapshot())
    assert "Save" in result.percepts[0].text
