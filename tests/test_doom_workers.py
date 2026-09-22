import pytest
from doom.policy import DataClass
from doom.workers import ResourceManager, ResourcePolicyError, TaskRequest, Worker, WorkerType

def test_protected_task_prefers_local_worker():
    manager = ResourceManager()
    manager.register(Worker("cloud", WorkerType.CLOUD, {"gpu"}))
    manager.register(Worker("pc", WorkerType.LOCAL, {"gpu"}))
    worker = manager.route(TaskRequest("secret task", "gpu", DataClass.PROTECTED))
    assert worker.id == "pc"

def test_protected_task_cannot_use_cloud_without_authorization():
    manager = ResourceManager()
    manager.register(Worker("cloud", WorkerType.CLOUD, {"gpu"}))
    with pytest.raises(ResourcePolicyError):
        manager.route(TaskRequest("secret task", "gpu", DataClass.PROTECTED))
