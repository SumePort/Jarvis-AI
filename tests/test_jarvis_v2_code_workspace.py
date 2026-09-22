from jarvis_v2.code.workspace import ProjectWorkspace
import pytest


def test_workspace_blocks_traversal(tmp_path):
    ws = ProjectWorkspace(str(tmp_path))
    with pytest.raises(PermissionError):
        ws.resolve("../outside.txt")


def test_workspace_roundtrip(tmp_path):
    ws = ProjectWorkspace(str(tmp_path))
    ws.write("src/test.py", "print('ok')")
    assert ws.read("src/test.py") == "print('ok')"
