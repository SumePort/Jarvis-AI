from pathlib import Path
import subprocess

from jarvis_v2.knowledge.temporal import TemporalIntelligence


def git(cwd: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True)


def test_temporal_history(tmp_path: Path):
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")
    git(tmp_path, "add", "app.py")
    git(tmp_path, "commit", "-m", "initial")
    (tmp_path / "app.py").write_text("x = 2\n", encoding="utf-8")
    git(tmp_path, "commit", "-am", "change")
    history = TemporalIntelligence(tmp_path).file_history("app.py")
    assert len(history.commits) == 2
    assert history.commits[0] != history.commits[1]
