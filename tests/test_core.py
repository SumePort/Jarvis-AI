from core.router import JarvisRouter, Route

def test_local_command_routes_to_tool():
    d=JarvisRouter().decide("open notepad")
    assert d.route is Route.LOCAL_TOOL
