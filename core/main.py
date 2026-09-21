"""Runnable local-first Jarvis command loop."""
from __future__ import annotations
import ast, operator, os, shlex

from brain.local_brain import LocalBrain, LocalBrainError
from browser.chrome import search as browser_search
from computer import apps, files, keyboard, mouse, system, windows
from core.router import JarvisRouter, Route
from core.state import JarvisState
from core.tool_executor import ToolExecutor
from memory.store import MemoryStore
from projects.knowledge import learn_project
from security.authentication import AuthenticationManager

OPS={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,
     ast.Mod:operator.mod,ast.Pow:operator.pow,ast.USub:operator.neg}

def safe_calculate(expr: str):
    def ev(node):
        if isinstance(node,ast.Expression): return ev(node.body)
        if isinstance(node,ast.Constant) and isinstance(node.value,(int,float)): return node.value
        if isinstance(node,ast.BinOp) and type(node.op) in OPS: return OPS[type(node.op)](ev(node.left),ev(node.right))
        if isinstance(node,ast.UnaryOp) and type(node.op) in OPS: return OPS[type(node.op)](ev(node.operand))
        raise ValueError("Unsupported expression")
    return ev(ast.parse(expr,mode="eval"))

class Jarvis:
    def __init__(self):
        self.state=JarvisState()
        self.router=JarvisRouter()
        self.brain=LocalBrain()
        self.executor=ToolExecutor()
        self.memory=MemoryStore()

    def handle(self, text: str) -> str:
        text=text.strip()
        if not text: return ""
        self.memory.add_message("user",text)
        q=text.lower()
        if q in {"help","/help"}:
            return self.help()
        if q in {"exit","quit","/exit"}:
            raise SystemExit
        if q.startswith("/open app "):
            result=self.executor.run("open_app",apps.open_app,text[10:].strip(),description=f"Open app {text[10:].strip()}")
        elif q.startswith("/close "):
            result=self.executor.run("close_app",apps.close_window,text[7:].strip(),description=f"Close window {text[7:].strip()}")
        elif q.startswith("/open "):
            result=self.executor.run("open_file",files.open_path,text[6:].strip(),description=f"Open path {text[6:].strip()}")
        elif q.startswith("/read "):
            result=self.executor.run("read_file",files.read_file,text[6:].strip())
        elif q.startswith("/type "):
            result=self.executor.run("type_text",keyboard.type_text,text[6:],description="Type text into the active window")
        elif q.startswith("/press "):
            result=self.executor.run("press_key",keyboard.press_key,text[7:].strip())
        elif q.startswith("/click "):
            x,y=map(int,text[7:].split(",",1))
            result=self.executor.run("click",mouse.click,x,y)
        elif q.startswith("/scroll "):
            result=self.executor.run("scroll",mouse.scroll,int(text[8:].strip()))
        elif q.startswith("/calc "):
            result=str(safe_calculate(text[6:].strip()))
        elif q.startswith("/learn "):
            snap=learn_project(text[7:].strip(),self.memory)
            self.state.current_project=snap.root
            result=f"Learned {snap.name}: {len(snap.files)} files, {len(snap.directories)} directories."
        elif q.startswith("/search "):
            result=self.executor.run("web_search",browser_search,text[8:].strip())
        elif q=="/system":
            result=str(system.system_info())
        elif q=="/windows":
            result="\n".join(windows.list_windows()) or "No windows found."
        else:
            context="\n".join(f"{m['role']}: {m['content']}" for m in self.memory.recent(10))
            route=self.router.decide(text)
            prompt=f"You are Jarvis, a local-first Windows AI assistant. Answer concisely in natural Hinglish when appropriate. Route: {route.route.value}.\nConversation:\n{context}\nUser: {text}"
            try:
                result=self.brain.ask(prompt)
            except LocalBrainError as exc:
                result=f"Local brain unavailable: {exc}\nUse /help for deterministic commands."
        self.memory.add_message("assistant",result)
        return result

    @staticmethod
    def help():
        return """Jarvis commands:
  /open app chrome|notepad|calculator
  /open <file-or-folder>
  /read <file>
  /type <text>
  /press <key>
  /click x,y
  /scroll <amount>
  /calc <expression>
  /learn <project-folder>
  /search <query>       (opens Chrome)
  /system
  /windows
  /help
  /exit

Natural-language requests go to the local LLM.
"""
def main():
    if not AuthenticationManager().authenticate():
        print("Authentication failed. Jarvis locked.")
        return
    jarvis=Jarvis()
    print("="*60)
    print("JARVIS — LOCAL-FIRST")
    print("Local brain + computer + project memory + Chrome")
    print("Type /help for commands. Type /exit to quit.")
    print("="*60)
    while True:
        try:
            print("Jarvis:",jarvis.handle(input("You: ")))
        except KeyboardInterrupt:
            print("\nJarvis stopped.")
            break
        except SystemExit:
            print("Jarvis shutting down.")
            break

if __name__=="__main__":
    main()
