from jarvis_v2.environment.browser_runtime import BrowserRuntime

def test_browser_requires_provider():
    try: BrowserRuntime().require_provider(); assert False
    except RuntimeError: assert True
