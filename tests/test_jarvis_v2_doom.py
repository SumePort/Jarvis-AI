from jarvis_v2.core.types import DataClass
from jarvis_v2.doom import DoomResourceRouter

class FakeDoom:
    def status(self):
        return {"workers":[
            {"id":"local-pc","type":"local","online":True,"capabilities":["cpu","filesystem"]},
            {"id":"cloud-1","type":"cloud","online":True,"capabilities":["cpu","gpu"]},
        ]}

def test_protected_routes_local():
    routed=DoomResourceRouter(FakeDoom()).route("read vault","filesystem",DataClass.PROTECTED)
    assert routed.worker_id == "local-pc"

def test_gpu_can_route_cloud_for_normal_data():
    routed=DoomResourceRouter(FakeDoom()).route("render","gpu",DataClass.NORMAL)
    assert routed.worker_id == "cloud-1"
