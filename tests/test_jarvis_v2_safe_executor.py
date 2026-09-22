from jarvis_v2.code.safe_executor import SafeProjectExecutor


def test_safe_executor_blocks_unapproved_commands(tmp_path):
    executor = SafeProjectExecutor()
    try:
        executor.execute("del everything", str(tmp_path))
        assert False
    except PermissionError:
        assert True


def test_safe_executor_allows_readonly_git_command(tmp_path):
    (tmp_path / ".git").mkdir()
    result = SafeProjectExecutor().execute("git status", str(tmp_path))
    assert "returncode" in result
