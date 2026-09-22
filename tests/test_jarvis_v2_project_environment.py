from pathlib import Path
import sys
import time

from jarvis_v2.runtime.project_environment import ProjectExecutionEnvironment


def test_project_environment_start_log_stop(tmp_path: Path):
    env = ProjectExecutionEnvironment(tmp_path)
    service = env.start("test-service", [sys.executable, "-c", "print('jarvis-service-ok')"])
    assert service.status == "running"
    for _ in range(20):
        if "jarvis-service-ok" in env.log("test-service"):
            break
        time.sleep(0.05)
    assert "jarvis-service-ok" in env.log("test-service")
    stopped = env.stop("test-service")
    assert stopped.status.startswith("exited:")


def test_project_environment_rejects_shell_metacharacter_service_name(tmp_path: Path):
    env = ProjectExecutionEnvironment(tmp_path)
    try:
        env.start("bad name", [sys.executable, "-c", "print(1)"])
    except ValueError:
        pass
    else:
        raise AssertionError("unsafe service name was accepted")
