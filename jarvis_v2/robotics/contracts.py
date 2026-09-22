from dataclasses import dataclass
@dataclass(frozen=True)
class JointTarget: joint:str; position:float
@dataclass(frozen=True)
class RobotObservation: timestamp:float; joints:dict[str,float]; sensors:dict[str,float]
class RobotAdapter:
    def connect(self): raise NotImplementedError
    def observe(self): raise NotImplementedError
    def plan(self,targets): raise NotImplementedError
    def execute(self,plan): raise NotImplementedError
