from jarvis_v2.tools import create_default_registry

def test_default_registry_has_safe_local_tools():
    registry=create_default_registry()
    names={x.name for x in registry.specs_list()}
    assert {"open_app","open_file","read_file","calculate"} <= names
    assert all(x.risk.value == "allow" for x in registry.specs_list())

def test_calculator_does_not_execute_names():
    registry=create_default_registry()
    result=registry.handlers["calculate"]("2 + 3 * 4")
    assert result["result"] == "14"
