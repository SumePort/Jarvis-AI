from jarvis_v2.simulation.models import SimulationSpec,Parameter
from jarvis_v2.simulation.sandbox import MentalSandbox

def test_sandbox_is_deterministic_and_bounded():
    spec=SimulationSpec("power","estimate",(
        Parameter("voltage",5,5,10),Parameter("current",1,1,2)),
        ("power=voltage*current",),(),("power<=20",))
    run=MentalSandbox().run(spec,steps=2)
    assert len(run.outcomes)==4
    assert all(o.status in {"ok","constrained"} for o in run.outcomes)

def test_sandbox_rejects_code():
    spec=SimulationSpec("bad","",(),("x=__import__('os').system('whoami')",))
    run=MentalSandbox().run(spec)
    assert run.outcomes[0].status=="model_error"
