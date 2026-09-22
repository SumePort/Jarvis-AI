from pathlib import Path
from jarvis_v2.code.repair import CodeRepairIntelligence
from jarvis_v2.tests.intelligence import TestFailure


def test_locates_python_function(tmp_path: Path):
    source = "def broken():\n    value = 1\n    return value + missing\n"
    path = tmp_path / "app.py"
    path.write_text(source, encoding="utf-8")
    failure = TestFailure("pytest", "test_broken", "NameError: missing", str(path), 3)
    candidates = CodeRepairIntelligence(tmp_path).locate(failure)
    assert candidates
    assert candidates[0].file == str(path.resolve())


def test_patch_is_reviewable_and_does_not_write(tmp_path: Path):
    path = tmp_path / "app.py"
    path.write_text("x = 1\n", encoding="utf-8")
    result = CodeRepairIntelligence(tmp_path).propose_text_patch(
        path, "x = 2\n", "fix expected value", 0.8
    )
    assert "x = 2" in result.unified_diff
    assert path.read_text(encoding="utf-8") == "x = 1\n"
