"""Bounded mental sandbox for parameterized engineering experiments."""
from __future__ import annotations
import ast, math
from itertools import product
from .models import SimulationSpec, SimulationRun, SimulationOutcome

_ALLOWED={"abs":abs,"min":min,"max":max,"sqrt":math.sqrt,"sin":math.sin,
          "cos":math.cos,"tan":math.tan,"pi":math.pi,"exp":math.exp,"log":math.log}

class _SafeEval(ast.NodeVisitor):
    def __init__(self, variables): self.variables=variables
    def eval(self, expression):
        tree=ast.parse(expression,mode="eval")
        return self.visit(tree.body)
    def visit_Constant(self,node):
        if isinstance(node.value,(int,float)): return float(node.value)
        raise ValueError("constant not allowed")
    def visit_Name(self,node):
        if node.id in self.variables: return float(self.variables[node.id])
        if node.id in _ALLOWED: return _ALLOWED[node.id]
        raise ValueError(f"name not allowed: {node.id}")
    def visit_BinOp(self,node):
        a,b=self.visit(node.left),self.visit(node.right)
        return {ast.Add:lambda:a+b,ast.Sub:lambda:a-b,ast.Mult:lambda:a*b,
                ast.Div:lambda:a/b,ast.Pow:lambda:a**b}[type(node.op)]()
    def visit_UnaryOp(self,node):
        x=self.visit(node.operand)
        return +x if isinstance(node.op,ast.UAdd) else -x
    def visit_Call(self,node):
        fn=self.visit(node.func)
        args=[self.visit(x) for x in node.args]
        return fn(*args)
    def visit_Compare(self,node):
        left=self.visit(node.left)
        for op,right_node in zip(node.ops,node.comparators):
            right=self.visit(right_node)
            ok={ast.Lt:left<right,ast.LtE:left<=right,ast.Gt:left>right,
                ast.GtE:left>=right,ast.Eq:left==right,ast.NotEq:left!=right}[type(op)]
            if not ok:return False
            left=right
        return True
    def generic_visit(self,node):
        raise ValueError(f"expression node not allowed: {type(node).__name__}")

class MentalSandbox:
    """Run small, transparent simulations without arbitrary code execution.

    Equations are expressions, never shell/Python code. This is deliberately a
    mental model: results are estimates and cannot prove that a physical system
    will work.
    """
    def run(self,spec:SimulationSpec,steps:int=3)->SimulationRun:
        params={p.name:p.value for p in spec.parameters}
        grids=[]
        for p in spec.parameters:
            if p.minimum is None or p.maximum is None:
                grids.append([p.value])
            else:
                n=max(2,steps)
                grids.append([p.minimum+(p.maximum-p.minimum)*i/(n-1) for i in range(n)])
        outcomes=[]
        for values in product(*grids):
            variables=dict(zip(params,values))
            result={}
            violations=[]
            try:
                for eq in spec.equations:
                    if "=" not in eq: continue
                    name,expr=eq.split("=",1)
                    result[name.strip()]=float(_SafeEval({**variables,**result}).eval(expr.strip()))
                for constraint in spec.constraints:
                    if not bool(_SafeEval({**variables,**result}).eval(constraint)):
                        violations.append(constraint)
                outcomes.append(SimulationOutcome(
                    "constrained" if violations else "ok",result,tuple(violations)
                ))
            except Exception as exc:
                outcomes.append(SimulationOutcome("model_error",result,notes=(str(exc),)))
        return SimulationRun(spec,outcomes=outcomes,conclusion=self._conclusion(outcomes))

    def _conclusion(self,outcomes):
        valid=[o for o in outcomes if o.status=="ok"]
        if not outcomes:return "No simulation cases were generated."
        if not valid:return "All modeled cases violated constraints or failed evaluation."
        return f"{len(valid)}/{len(outcomes)} modeled cases satisfied the supplied constraints."

    def compare(self,a:SimulationRun,b:SimulationRun)->dict:
        return {"a_valid":sum(x.status=="ok" for x in a.outcomes),
                "b_valid":sum(x.status=="ok" for x in b.outcomes),
                "a_total":len(a.outcomes),"b_total":len(b.outcomes)}
