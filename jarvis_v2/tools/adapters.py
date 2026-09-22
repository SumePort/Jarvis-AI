"""Conservative Windows/local adapters. No shell execution is exposed here."""
from __future__ import annotations
import os
import subprocess
from pathlib import Path
from typing import Any
from jarvis_v2.core.types import ActionRisk, ToolSpec
from .registry import ToolRegistry

class LocalAdapters:
    def open_app(self, name: str) -> dict[str, Any]:
        # Use Windows shell association only for a named application/document.
        if os.name != "nt": raise RuntimeError("open_app currently requires Windows")
        subprocess.Popen(["cmd", "/c", "start", "", name], shell=False)
        return {"opened": name}

    def open_file(self, path: str) -> dict[str, Any]:
        p=Path(path).expanduser().resolve()
        if not p.exists(): raise FileNotFoundError(str(p))
        if os.name != "nt": raise RuntimeError("open_file currently requires Windows")
        os.startfile(str(p))
        return {"opened": str(p)}

    def read_file(self, path: str, max_chars: int = 20000) -> dict[str, Any]:
        p=Path(path).expanduser().resolve()
        if not p.is_file(): raise FileNotFoundError(str(p))
        if p.stat().st_size > max_chars * 8: raise ValueError("File is too large for direct tool read")
        return {"path": str(p), "content": p.read_text(encoding="utf-8", errors="replace")[:max_chars]}

    def calculate(self, expression: str) -> dict[str, str]:
        import ast, operator
        ops={ast.Add:operator.add, ast.Sub:operator.sub, ast.Mult:operator.mul, ast.Div:operator.truediv, ast.Pow:operator.pow, ast.Mod:operator.mod, ast.USub:operator.neg}
        def ev(n):
            if isinstance(n, ast.Constant) and isinstance(n.value,(int,float)): return n.value
            if isinstance(n, ast.BinOp) and type(n.op) in ops: return ops[type(n.op)](ev(n.left),ev(n.right))
            if isinstance(n, ast.UnaryOp) and type(n.op) in ops: return ops[type(n.op)](ev(n.operand))
            raise ValueError("Unsupported expression")
        return {"expression":expression,"result":str(ev(ast.parse(expression,mode="eval").body))}

def create_default_registry() -> ToolRegistry:
    a=LocalAdapters(); r=ToolRegistry()
    r.register(ToolSpec("open_app","Open a named application or document",risk=ActionRisk.ALLOW), a.open_app)
    r.register(ToolSpec("open_file","Open a local file",risk=ActionRisk.ALLOW), a.open_file)
    r.register(ToolSpec("read_file","Read a bounded local text file",risk=ActionRisk.ALLOW), a.read_file)
    r.register(ToolSpec("calculate","Evaluate a restricted arithmetic expression",risk=ActionRisk.ALLOW), a.calculate)
    return r
