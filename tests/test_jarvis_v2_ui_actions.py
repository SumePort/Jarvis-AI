from jarvis_v2.tools.ui_actions import semantic_ui_specs

def test_semantic_ui_actions_require_confirmation():
    assert all(s.risk.value == "confirm" for s in semantic_ui_specs())
