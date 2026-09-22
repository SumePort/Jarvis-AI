import pytest
from doom.control.identity import IdentityRegistry
from doom.control.registry import WorkerRegistry
from doom.control.scheduler import Scheduler
from doom.policy import DataClass
from doom.workers import ResourcePolicyError, TaskRequest, Worker, WorkerType

def test_device_enrollment_authentication_and_revocation():
    registry = IdentityRegistry()
    identity, token = registry.enroll("test-pc")
    assert registry.authenticate(identity.device_id, token)
    assert not registry.authenticate(identity.device_id, "wrong")
    registry.revoke(identity.device_id)
    assert not registry.authenticate(identity.device_id, token)

def test_scheduler_routes_protected_data_to_local_worker():
    registry = WorkerRegistry()
    registry.register(Worker("cloud", WorkerType.CLOUD, {"gpu"}))
    registry.register(Worker("pc", WorkerType.LOCAL, {"gpu"}))
    result = Scheduler(registry).select(TaskRequest("secret", "gpu", DataClass.PROTECTED))
    assert result.worker_id == "pc"

def test_scheduler_blocks_protected_data_when_only_remote_worker_exists():
    registry = WorkerRegistry()
    registry.register(Worker("cloud", WorkerType.CLOUD, {"gpu"}))
    with pytest.raises(ResourcePolicyError):
        Scheduler(registry).select(TaskRequest("secret", "gpu", DataClass.PROTECTED))

def test_scheduler_can_prefer_cloud_for_authorized_normal_work():
    registry = WorkerRegistry()
    registry.register(Worker("pc", WorkerType.LOCAL, {"gpu"}))
    registry.register(Worker("cloud-gpu", WorkerType.CLOUD, {"gpu"}, endpoint="https://worker.example"))
    result = Scheduler(registry).select(
        TaskRequest("model-job", "gpu", DataClass.NORMAL, preferred_worker_type=WorkerType.CLOUD)
    )
    assert result.worker_id == "cloud-gpu"
