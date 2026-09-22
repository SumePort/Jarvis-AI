from pathlib import Path

from jarvis_v2.environment.filesystem import FilesystemEnvironmentProvider
from jarvis_v2.environment.git import GitEnvironmentProvider


def test_filesystem_provider_returns_structured_entries(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("print('ok')", encoding="utf-8")
    snapshot = FilesystemEnvironmentProvider([tmp_path]).snapshot()
    entries = snapshot.filesystem[0]["entries"]
    assert any(e["relative"] == "src" and e["kind"] == "directory" for e in entries)
    assert any(e["relative"].replace("\\", "/") == "src/app.py" for e in entries)


def test_git_provider_ignores_non_repository(tmp_path: Path):
    snapshot = GitEnvironmentProvider([tmp_path]).snapshot()
    assert snapshot.repositories == []
