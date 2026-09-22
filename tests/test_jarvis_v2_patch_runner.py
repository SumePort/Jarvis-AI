from pathlib import Path
from jarvis_v2.code.patch_runner import PatchRunner
from jarvis_v2.code.repair import CodeRepairIntelligence


def test_patch_runner_requires_confirmation(tmp_path: Path):
    p = tmp_path / "app.py"
    p.write_text("x = 1\n", encoding="utf-8")
    proposal = CodeRepairIntelligence(tmp_path).propose_text_patch(p, "x = 2\n", "fix")
    result = PatchRunner(tmp_path).apply(proposal, confirmed=False)
    assert not result.applied
    assert "confirmation" in result.error.lower()


def test_patch_runner_rolls_back_failed_tests(tmp_path: Path):
    p = tmp_path / "app.py"
    p.write_text("def value():\n    return 2\n", encoding="utf-8")
    (tmp_path / "test_value.py").write_text(
        "from app import value\n\ndef test_value():\n    assert value() == 1\n",
        encoding="utf-8",
    )
    proposal = CodeRepairIntelligence(tmp_path).propose_text_patch(
        p, "def value():\n    return 3\n", "deliberately failing patch"
    )
    cycle = PatchRunner(tmp_path, timeout_seconds=20).run_and_verify(proposal, confirmed=True)
    assert not cycle.verified
    assert cycle.rolled_back
    assert "return 2" in p.read_text(encoding="utf-8")
