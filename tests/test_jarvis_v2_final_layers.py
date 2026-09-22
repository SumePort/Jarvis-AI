from jarvis_v2.perception.tracking import ObjectTracker
from jarvis_v2.perception.world import Percept
from jarvis_v2.simulation.physics import PhysicsSimulator
from jarvis_v2.robotics.safety import RobotSafetyGate
from jarvis_v2.experiments.controller import ExperimentController,ExperimentRun
def test_tracking():
    t=ObjectTracker(); assert len(t.update([Percept("object","cup",.9,"test")]))==1
def test_physics():
    r=PhysicsSimulator().free_fall(10); assert r["time"]>0 and r["impact_velocity"]>0
def test_robot_gate():
    g=RobotSafetyGate()
    try: g.authorize(); assert False
    except PermissionError: pass
def test_physical_experiment_gate():
    c=ExperimentController()
    try: c.start(ExperimentRun(),physical=True,authorized=False); assert False
    except PermissionError: pass
