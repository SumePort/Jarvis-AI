from pathlib import Path
import subprocess

from jarvis_v2.projects.handoff import ProjectHandoff


def git(root: Path, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, shell=False)


def test_handoff_requires_confirmation(tmp_path: Path):
    assert git(tmp_path, "init").returncode == 0
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "README.md").write_text("hello", encoding="utf-8")
    report = ProjectHandoff(tmp_path).prepare("test: handoff", tests_passed=True)
    try:
        ProjectHandoff(tmp_path).commit(report, confirmed=False)
    except PermissionError:
        pass
    else:
        raise AssertionError("commit was not confirmation-gated")
