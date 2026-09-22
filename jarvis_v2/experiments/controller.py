from dataclasses import dataclass
from enum import Enum
class ExperimentState(str,Enum): PLANNED="planned"; RUNNING="running"; PAUSED="paused"; COMPLETE="complete"; ABORTED="aborted"
@dataclass
class ExperimentRun:
    state:ExperimentState=ExperimentState.PLANNED
    iteration:int=0
    observations:list=None
    def __post_init__(self):
        if self.observations is None:self.observations=[]
class ExperimentController:
    def start(self,run,physical=False,authorized=False):
        if physical and not authorized: raise PermissionError("Physical experimentation requires explicit authorization")
        run.state=ExperimentState.RUNNING; return run
    def pause(self,run): run.state=ExperimentState.PAUSED; return run
    def abort(self,run): run.state=ExperimentState.ABORTED; return run
