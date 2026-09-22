"""Small deterministic physics helpers; outputs are models, not physical proof."""
from __future__ import annotations
class PhysicsSimulator:
    G=9.80665
    def projectile(self,v0,angle_deg,dt=0.02,steps=100):
        import math
        a=math.radians(angle_deg); vx=v0*math.cos(a); vy=v0*math.sin(a)
        x=y=0.0; out=[]
        for i in range(steps+1):
            t=i*dt; x=vx*t; y=vy*t-.5*self.G*t*t
            out.append({"t":t,"x":x,"y":y})
            if y<0 and i>0: break
        return out
    def free_fall(self,height,dt=.02):
        t=(2*height/self.G)**.5
        return {"time":t,"impact_velocity":self.G*t}
