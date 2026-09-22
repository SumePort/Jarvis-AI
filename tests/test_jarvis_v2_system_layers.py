from jarvis_v2.simulation.advanced import NumericalSimulator
from doom.mesh.mesh import DoomMesh
from doom.mesh.node import DoomNode
from doom.network.protocol import Protocol,Message
def test_numerical_simulator():
    assert len(NumericalSimulator().euler(lambda t,x:x,1,.01,10))==11
def test_doom_mesh():
    m=DoomMesh(); n=m.register(DoomNode(capabilities={"gpu"},resources={"free":4}))
    assert m.choose("gpu") is n
def test_protocol_authentication():
    p=Protocol(); w=p.encode(Message(1,"ping","x",{"a":1}),b"k")
    assert p.decode(w,b"k").kind=="ping"
