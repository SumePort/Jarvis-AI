from pathlib import Path

from jarvis_v2.tests.intelligence import TestIntelligence


def test_discovers_pytest(tmp_path: Path):
    (tmp_path / "test_sample.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    suites = TestIntelligence(tmp_path).discover()
    assert suites
    assert suites[0].framework == "pytest"


def test_runs_pytest(tmp_path: Path):
    (tmp_path / "test_sample.py").write_text("def test_ok():\n    assert 1 + 1 == 2\n", encoding="utf-8")
    result = TestIntelligence(tmp_path, timeout_seconds=20).run_all()[0]
    assert result.passed
    assert result.return_code == 0


def test_parses_pytest_failure():
    text = """________________ test_bad ________________
E       AssertionError: expected value
=========================== short test summary info ============================
FAILED test_sample.py::test_bad - AssertionError
"""
    failures = TestIntelligence(".").parse_failures("pytest", text)
    assert failures
    assert failures[0].test_name == "test_bad"
    assert "expected value" in failures[0].message
