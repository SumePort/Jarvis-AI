from jarvis_v2.security import IdentitySession
from jarvis_v2.runtime.secure_runner import SecureRunner

class FakePlan:
    goal="test"; steps=[]; blocked=False; warnings=[]
class FakePlanner:
    def build(self, request, context): return FakePlan()
class FakeLoop:
    def run(self, plan):
        class R: success=True; message="ok"
        return R()

def test_secure_runner_requires_auth(tmp_path):
    runner=SecureRunner(FakePlanner(), FakeLoop())
    s=IdentitySession("s")
    result=runner.run(s,"hello",{})
    assert not result.allowed

def test_secure_runner_allows_authenticated_request(tmp_path):
    runner=SecureRunner(FakePlanner(), FakeLoop())
    s=IdentitySession("s"); s.authenticate("user","device")
    result=runner.run(s,"hello",{})
    assert result.allowed
