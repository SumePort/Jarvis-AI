"""Runnable local-first Jarvis command loop."""
from __future__ import annotations

import ast
import operator
import os
import re
import time

from dotenv import load_dotenv

load_dotenv()

from brain.local_brain import LocalBrain, LocalBrainError
from browser.chrome import search as browser_search
from browser.reader import copy_visible_page_text
from computer import apps, files, keyboard, mouse, system, windows
from core.planner import ActionStep, Planner
from core.router import JarvisRouter
from core.state import JarvisState
from core.tool_executor import ToolExecutor
from memory.store import MemoryStore
from projects.knowledge import learn_project
from security.authentication import AuthenticationManager

OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def safe_calculate(expr: str):
    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in OPS:
            return OPS[type(node.op)](ev(node.left), ev(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in OPS:
            return OPS[type(node.op)](ev(node.operand))
        raise ValueError("Unsupported expression")

    return ev(ast.parse(expr, mode="eval"))


class Jarvis:
    def __init__(self):
        self.state = JarvisState()
        self.router = JarvisRouter()
        self.planner = Planner(self.brain if hasattr(self, "brain") else None)
        self.brain = LocalBrain()
        self.planner = Planner(self.brain)
        self.executor = ToolExecutor()
        self.memory = MemoryStore()

    def _execute_plan(self, steps: list[ActionStep]) -> str:
        """Execute a validated deterministic plan in order."""
        outputs = []
        page_text = ""

        for step in steps:
            if step.action == "open_app":
                result = self.executor.run(
                    "open_app",
                    apps.open_app,
                    step.argument,
                    description=f"Open application: {step.argument}",
                )
            elif step.action == "web_search":
                result = self.executor.run(
                    "web_search",
                    browser_search,
                    step.argument,
                    description=f"Search the web for: {step.argument}",
                )
                # Give Chrome a moment to load before clipboard capture.
                time.sleep(2.0)
            elif step.action == "browser_read":
                page_text = self.executor.run(
                    "browser_read",
                    copy_visible_page_text,
                    description="Read the currently visible browser page",
                )
                result = (
                    "Captured the visible browser page."
                    if page_text and not str(page_text).startswith(("Blocked:", "Error"))
                    else page_text
                )
            elif step.action == "open_file":
                result = self.executor.run(
                    "open_file", files.open_path, step.argument,
                    description=f"Open local path: {step.argument}",
                )
            elif step.action == "read_file":
                result = self.executor.run("read_file", files.read_file, step.argument)
            elif step.action == "close_app":
                result = self.executor.run(
                    "close_app", apps.close_window, step.argument,
                    description=f"Close window: {step.argument}",
                )
            elif step.action == "type_text":
                result = self.executor.run(
                    "type_text", keyboard.type_text, step.argument,
                    description="Type text into the active window",
                )
            elif step.action == "press_key":
                result = self.executor.run("press_key", keyboard.press_key, step.argument)
            elif step.action == "click":
                try:
                    x, y = [int(v.strip()) for v in step.argument.split(",", 1)]
                    result = self.executor.run("click", mouse.click, x, y)
                except (ValueError, TypeError):
                    result = "Invalid click coordinates."
            elif step.action == "scroll":
                try:
                    result = self.executor.run("scroll", mouse.scroll, int(step.argument))
                except ValueError:
                    result = "Invalid scroll amount."
            elif step.action == "calculate":
                try:
                    result = str(safe_calculate(step.argument))
                except (SyntaxError, ValueError, ZeroDivisionError):
                    result = "I could not calculate that expression safely."
            elif step.action == "project_learn":
                if os.path.isdir(step.argument):
                    snap = learn_project(step.argument, self.memory)
                    self.state.current_project = snap.root
                    result = f"Learned {snap.name}: {len(snap.files)} files, {len(snap.directories)} directories."
                else:
                    result = f"Project folder not found: {step.argument}"
            elif step.action == "summarize":
                if not page_text:
                    result = "I could not read the browser page."
                else:
                    clipped = str(page_text)[:24000]
                    try:
                        result = self.brain.ask(
                            "Summarize the following visible web page for the user. "
                            "Use only the supplied text. Clearly distinguish page "
                            "content from your own explanation. Be concise.\n\n"
                            + clipped
                        )
                    except LocalBrainError as exc:
                        result = f"Local brain unavailable while summarizing: {exc}"
            else:
                result = f"Unsupported plan action: {step.action}"

            outputs.append(str(result))
            if str(result).startswith(("Blocked:", "Error while executing", "Cancelled.")):
                break

        return "\n".join(outputs)

    def _execute_natural_command(self, text: str):
        q = text.strip()
        lower = q.lower()

        # Multi-step plans are attempted before single-step natural commands.
        plan = self.planner.deterministic_steps(q)
        if plan:
            return self._execute_plan(plan)

        # For requests not covered by fixed patterns, ask the local model for
        # a constrained JSON action plan. The model can choose tools, but every
        # chosen action is still validated and executed through ToolExecutor.
        ai_plan = self.planner.plan_actions(q, context="")
        if ai_plan:
            return self._execute_plan(ai_plan)

        app_match = re.match(
            r"^(?:please\s+)?(?:open|launch|start|run)\s+"
            r"(?:the\s+)?(google\s+chrome|chrome|notepad|calculator|calc|paint|"
            r"cmd|command prompt|control panel)\s*$",
            lower,
        )
        if app_match:
            app = app_match.group(1)
            return self.executor.run(
                "open_app", apps.open_app, app,
                description=f"Open application: {app}",
            )

        close_match = re.match(
            r"^(?:please\s+)?(?:close|exit)\s+(?:the\s+)?(.+?)\s*$",
            q, re.IGNORECASE,
        )
        if close_match and not lower.startswith(("close file ", "close folder ")):
            title = close_match.group(1).strip()
            return self.executor.run(
                "close_app", apps.close_window, title,
                description=f"Close window: {title}",
            )

        type_match = re.match(r"^(?:please\s+)?(?:type|write)\s+(.+)$", q, re.IGNORECASE)
        if type_match:
            return self.executor.run(
                "type_text", keyboard.type_text, type_match.group(1),
                description="Type text into the active window",
            )

        key_match = re.match(
            r"^(?:please\s+)?press\s+(?:the\s+)?([a-z0-9_+\-]+)$", lower
        )
        if key_match:
            return self.executor.run("press_key", keyboard.press_key, key_match.group(1))

        click_match = re.match(
            r"^(?:please\s+)?click(?:\s+at)?\s+(\d+)\s*,\s*(\d+)\s*$", lower
        )
        if click_match:
            return self.executor.run(
                "click", mouse.click, int(click_match.group(1)), int(click_match.group(2))
            )

        scroll_match = re.match(r"^(?:please\s+)?scroll\s+(-?\d+)\s*$", lower)
        if scroll_match:
            return self.executor.run("scroll", mouse.scroll, int(scroll_match.group(1)))

        calc_match = re.match(
            r"^(?:please\s+)?(?:calculate|compute|what is)\s+"
            r"([0-9().+\-*/%\s]+)\??$", lower
        )
        if calc_match:
            try:
                return str(safe_calculate(calc_match.group(1).strip()))
            except (SyntaxError, ValueError, ZeroDivisionError):
                return "I could not calculate that expression safely."

        search_match = re.match(
            r"^(?:please\s+)?(?:search|google|look up)\s+(?:for\s+)?(.+)$",
            q, re.IGNORECASE,
        )
        if search_match:
            return self.executor.run("web_search", browser_search, search_match.group(1).strip())

        path_match = re.match(r"^(?:please\s+)?(?:open|read)\s+(.+)$", q, re.IGNORECASE)
        if path_match:
            candidate = os.path.expandvars(
                os.path.expanduser(path_match.group(1).strip().strip('"'))
            )
            if os.path.exists(candidate):
                if lower.startswith(("read ", "please read ")):
                    return self.executor.run("read_file", files.read_file, candidate)
                return self.executor.run(
                    "open_file", files.open_path, candidate,
                    description=f"Open local path: {candidate}",
                )

        learn_match = re.match(
            r"^(?:please\s+)?(?:learn|analyze|scan)\s+(?:my\s+)?project\s+(.+)$",
            q, re.IGNORECASE,
        )
        if learn_match:
            candidate = os.path.expandvars(
                os.path.expanduser(learn_match.group(1).strip().strip('"'))
            )
            if os.path.isdir(candidate):
                snap = learn_project(candidate, self.memory)
                self.state.current_project = snap.root
                return (
                    f"Learned {snap.name}: {len(snap.files)} files, "
                    f"{len(snap.directories)} directories."
                )

        return None

    def handle(self, text: str) -> str:
        text = text.strip()
        if not text:
            return ""

        self.memory.add_message("user", text)
        q = text.lower()

        if q in {"help", "/help"}:
            result = self.help()
        elif q in {"exit", "quit", "/exit"}:
            raise SystemExit
        elif q.startswith("/open app "):
            result = self.executor.run(
                "open_app", apps.open_app, text[10:].strip(),
                description=f"Open app {text[10:].strip()}",
            )
        elif q.startswith("/close "):
            result = self.executor.run("close_app", apps.close_window, text[7:].strip())
        elif q.startswith("/open "):
            result = self.executor.run(
                "open_file", files.open_path, text[6:].strip(),
                description=f"Open path {text[6:].strip()}",
            )
        elif q.startswith("/read "):
            result = self.executor.run("read_file", files.read_file, text[6:].strip())
        elif q.startswith("/type "):
            result = self.executor.run(
                "type_text", keyboard.type_text, text[6:],
                description="Type text into the active window",
            )
        elif q.startswith("/press "):
            result = self.executor.run("press_key", keyboard.press_key, text[7:].strip())
        elif q.startswith("/click "):
            x, y = map(int, text[7:].split(",", 1))
            result = self.executor.run("click", mouse.click, x, y)
        elif q.startswith("/scroll "):
            result = self.executor.run("scroll", mouse.scroll, int(text[8:].strip()))
        elif q.startswith("/calc "):
            result = str(safe_calculate(text[6:].strip()))
        elif q.startswith("/learn "):
            snap = learn_project(text[7:].strip(), self.memory)
            self.state.current_project = snap.root
            result = f"Learned {snap.name}: {len(snap.files)} files, {len(snap.directories)} directories."
        elif q.startswith("/search "):
            result = self.executor.run("web_search", browser_search, text[8:].strip())
        elif q == "/system":
            result = str(system.system_info())
        elif q == "/windows":
            result = "\n".join(windows.list_windows()) or "No windows found."
        else:
            result = self._execute_natural_command(text)
            if result is None:
                context = "\n".join(
                    f"{m['role']}: {m['content']}" for m in self.memory.recent(10)
                )
                route = self.router.decide(text)
                prompt = (
                    "You are Jarvis, a local-first Windows AI assistant. "
                    "Answer concisely in natural Hinglish when appropriate. "
                    f"Route: {route.route.value}.\nConversation:\n{context}\nUser: {text}"
                )
                try:
                    result = self.brain.ask(prompt)
                except LocalBrainError as exc:
                    result = f"Local brain unavailable: {exc}\nUse /help for deterministic commands."

        self.memory.add_message("assistant", result)
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
  /search <query>
  /system
  /windows
  /help
  /exit

Natural-language multi-step commands:
  "Open Notepad and type hello"
  "Open Notepad, type hello, then press enter"
  "Search for the latest Python release and tell me what you find"
  "Open Chrome, search for Python 3.14, and tell me what you find"

Unknown requests go to the local LLM.
"""


def main():
    if not AuthenticationManager().authenticate():
        print("Authentication failed. Jarvis locked.")
        return

    jarvis = Jarvis()
    print("=" * 60)
    print("JARVIS — LOCAL-FIRST")
    print("Local brain + computer + project memory + Chrome")
    print("Type /help for commands. Type /exit to quit.")
    print("=" * 60)

    while True:
        try:
            print("Jarvis:", jarvis.handle(input("You: ")))
        except KeyboardInterrupt:
            print("\nJarvis stopped.")
            break
        except SystemExit:
            print("Jarvis shutting down.")
            break


if __name__ == "__main__":
    main()
