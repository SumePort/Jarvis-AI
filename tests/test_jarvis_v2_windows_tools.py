from jarvis_v2.tools.windows import windows_tool_specs

def test_windows_tools_are_confirmation_gated():
    specs=windows_tool_specs()
    assert all(s.risk.value == "confirm" for s in specs)
