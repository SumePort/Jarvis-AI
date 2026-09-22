"""Read-only system inspection tools."""
from __future__ import annotations
import platform, psutil
from jarvis_v2.core.types import ToolSpec, ActionRisk, DataClass
class SystemAdapters:
    def system_info(self):
        return {"platform":platform.platform(),"python":platform.python_version(),"cpu_count":psutil.cpu_count(),"memory_bytes":psutil.virtual_memory().total}
    def processes(self, limit: int=50):
        out=[]
        for p in psutil.process_iter(["pid","name","status"]):
            try: out.append(p.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied): pass
            if len(out)>=limit: break
        return out
    def windows_tool_specs(self):
        return [
            ToolSpec("system_info","Inspect basic system information",{},(),ActionRisk.ALLOW,DataClass.NORMAL),
            ToolSpec("processes","List running processes",{"limit":"integer"},(),ActionRisk.ALLOW,DataClass.NORMAL),
        ]
