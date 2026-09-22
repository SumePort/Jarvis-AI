class RobotSafetyGate:
    def __init__(self): self.armed=False
    def arm(self,explicit_confirmation):
        if not explicit_confirmation: raise PermissionError("Explicit human confirmation required")
        self.armed=True
    def authorize(self):
        if not self.armed: raise PermissionError("Robot execution is not armed")
    def disarm(self): self.armed=False
