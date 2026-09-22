from jarvis_v2.models import ModelGateway, ModelProfile
from jarvis_v2.core.types import DataClass

def test_protected_data_only_selects_local_model():
    g=ModelGateway()
    g.register(ModelProfile("local","local",{"reasoning"},local=True), lambda p:"local")
    g.register(ModelProfile("cloud","cloud",{"reasoning"},local=False), lambda p:"cloud")
    assert g.select("reasoning", DataClass.PROTECTED).model_id == "local"

def test_gateway_completes():
    g=ModelGateway(); g.register(ModelProfile("m","test",{"text"}), lambda p:"ok")
    assert g.complete("m","hello") == "ok"
