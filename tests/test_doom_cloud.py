from fastapi.testclient import TestClient
from doom.cloud.server import create_worker_app

def test_worker_requires_token():
    client = TestClient(create_worker_app("secret"))
    assert client.get("/health").status_code == 401
    assert client.get("/health", headers={"Authorization": "Bearer secret"}).json()["ok"] is True

def test_worker_does_not_enable_arbitrary_execution():
    client = TestClient(create_worker_app("secret"))
    response = client.post(
        "/v1/execute",
        headers={"Authorization": "Bearer secret"},
        json={"task": "run_shell", "payload": {"command": "whoami"}},
    )
    assert response.status_code == 501
