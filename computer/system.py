from __future__ import annotations
import platform
import psutil

def system_info() -> dict:
    return {
        "os": platform.platform(),
        "python": platform.python_version(),
        "cpu": platform.processor(),
        "memory_gb": round(psutil.virtual_memory().total / (1024**3), 2),
    }
