"""AST-backed Python code intelligence with bounded parsing."""
from __future__ import annotations
import ast
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass(frozen=True)
class CodeSymbol:
    kind: str
    name: str
    file: str
    line: int
    end_line: int
    parent: str = ""
    signature: str = ""

class CodeAnalyzer:
    def analyze_python(self, path: str | Path) -> list[CodeSymbol]:
        p=Path(path).resolve()
        if not p.is_file() or p.suffix.lower() != ".py": raise ValueError("Python source file required")
        source=p.read_text(encoding="utf-8", errors="replace")
        if len(source) > 1_000_000: raise ValueError("Source file exceeds analysis limit")
        tree=ast.parse(source, filename=str(p))
        result=[]
        def walk(nodes, parent=""):
            for node in nodes:
                if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                    args=[a.arg for a in node.args.args]
                    result.append(CodeSymbol("function",node.name,str(p),node.lineno,getattr(node,"end_lineno",node.lineno),parent,f"{node.name}({', '.join(args)})"))
                    walk(node.body,node.name)
                elif isinstance(node,ast.ClassDef):
                    result.append(CodeSymbol("class",node.name,str(p),node.lineno,getattr(node,"end_lineno",node.lineno),parent,node.name))
                    walk(node.body,node.name)
                elif isinstance(node,(ast.Import,ast.ImportFrom)):
                    names=[x.name for x in node.names]
                    result.append(CodeSymbol("import",", ".join(names),str(p),node.lineno,getattr(node,"end_lineno",node.lineno),parent))
                elif isinstance(node,(ast.Assign,ast.AnnAssign)):
                    names=[]
                    targets=node.targets if isinstance(node,ast.Assign) else [node.target]
                    for target in targets:
                        if isinstance(target,ast.Name): names.append(target.id)
                    if names: result.append(CodeSymbol("variable",", ".join(names),str(p),node.lineno,getattr(node,"end_lineno",node.lineno),parent))
        walk(tree.body)
        return result

    def to_dict(self, symbols: list[CodeSymbol]) -> list[dict]:
        return [asdict(s) for s in symbols]
