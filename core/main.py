"""Runnable local-first Jarvis command loop."""
from __future__ import annotations

import ast
import operator
import os
import re

from dotenv import load_dotenv

load_dotenv()

from brain.local_brain import LocalBrain, LocalBrainError
from browser.chrome import search as browser_search
from computer import apps, files, keyboard, mouse, system, windows
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
        self.brain = LocalBrain()
        self.executor = ToolExecutor()
        self.memory = MemoryStore()

    def _execute_natural_command(self, text: str):
        """Turn a small, deterministic subset of natural language into real tools.

        This deliberately handles only unambiguous local/browser actions. Anything
        outside this safe command grammar falls through to the local LLM.
        """
        q = text.strip()
        lower = q.lower()

        # Open/launch/start an application.
        app_match = re.match(
            r"^(?:please\s+)?(?:open|launch|start|run)\s+"
            r"(?:the\s+)?(google\s+chrome|chrome|notepad|calculator|calc|paint|"
            r"cmd|command prompt|control panel)\s*$",
            lower,
        )
        if app_match:
            app = app_match.group(1)
            return self.executor.run(
                "open_app",
                apps.open_app,
                app,
                description=f"Open application: {app}",
            )

        # Close a named window/application.
        close_match = re.match(
            r"^(?:please\s+)?(?:close|exit)\s+(?:the\s+)?(.+?)\s*$",
            q,
            re.IGNORECASE,
        )
        if close_match and not lower.startswith(("close file ", "close folder ")):
            title = close_match.group(1).strip()
            return self.executor.run(
                "close_app",
                apps.close_window,
                title,
                description=f"Close window: {title}",
            )

        # Type/write text into the currently focused application.
        type_match = re.match(
            r'^(?:please\s+)?(?:type|write)\s+(.+)$',
            q,
            re.IGNORECASE,
        )
        if type_match:
            value = type_match.group(1)
            return self.executor.run(
                "type_text",
                keyboard.type_text,
                value,
                description="Type text into the active window",
            )

        # Press a keyboard key.
        key_match = re.match(
            r"^(?:please\s+)?press\s+(?:the\s+)?([a-z0-9_+\-]+)$",
            lower,
        )
        if key_match:
            key = key_match.group(1)
            return self.executor.run("press_key", keyboard.press_key, key)

        # Mouse click: "click 500,300" / "click at 500, 300".
        click_match = re.match(
            r"^(?:please\s+)?click(?:\s+at)?\s+(\d+)\s*,\s*(\d+)\s*$",
            lower,
        )
        if click_match:
            x, y = int(click_match.group(1)), int(click_match.group(2))
            return self.executor.run("click", mouse.click, x, y)

        # Mouse scroll.
        scroll_match = re.match(
            r"^(?:please\s+)?scroll\s+(-?\d+)\s*$",
            lower,
        )
        if scroll_match:
            amount = int(scroll_match.group(1))
            return self.executor.run("scroll", mouse.scroll, amount)

        # Calculation requests. Only evaluate the arithmetic expression itself.
        calc_match = re.match(
            r"^(?:please\s+)?(?:calculate|compute|what is)\s+"
            r"([0-9().+\-*/%\s]+)\??$",
            lower,
        )
        if calc_match:
            try:
                return str(safe_calculate(calc_match.group(1).strip()))
            except (SyntaxError, ValueError, ZeroDivisionError):
                return "I could not calculate that expression safely."

        # Explicit natural-language web search.
        search_match = re.match(
            r"^(?:please\s+)?(?:search|google|look up)\s+(?:for\s+)?(.+)$",
            q,
            re.IGNORECASE,
        )
        if search_match:
            query = search_match.group(1).strip()
            return self.executor.run("web_search", browser_search, query)

        # Open/read a local path. Require an actual existing path so a phrase
        # such as "open my project" is not accidentally treated as a file path.
        path_match = re.match(
            r"^(?:please\s+)?(?:open|read)\s+(.+)$",
            q,
            re.IGNORECASE,
        )
        if path_match:
            candidate = os.path.expandvars(os.path.expanduser(path_match.group(1).strip().strip('"')))
            if os.path.exists(candidate):
                if lower.startswith(("read ", "please read ")):
                    return self.executor.run("read_file", files.read_file, candidate)
                return self.executor.run(
                    "open_file",
                    files.open_path,
                    candidate,
                    description=f"Open local path: {candidate}",
                )

        # Learn a project only when the supplied directory exists.
        learn_match = re.match(
            r"^(?:please\s+)?(?:learn|analyze|scan)\s+(?:my\s+)?project\s+(.+)$",
            q,
            re.IGNORECASE,
        )
        if learn_match:
            candidate = os.path.expandvars(os.path.expanduser(learn_match.group(1).strip().strip('"')))
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
            app = text[10:].strip()
            result = self.executor.run(
                "open_app",
                apps.open_app,
                app,
                description=f"Open app {app}",
            )
        elif q.startswith("/close "):
            title = text[7:].strip()
            result = self.executor.run(
                "close_app",
                apps.close_window,
                title,
                description=f"Close window {title}",
            )
        elif q.startswith("/open "):
            path = text[6:].strip()
            result = self.executor.run(
                "open_file",
                files.open_path,
                path,
                description=f"Open path {path}",
            )
        elif q.startswith("/read "):
            result = self.executor.run("read_file", files.read_file, text[6:].strip())
        elif q.startswith("/type "):
            result = self.executor.run(
                "type_text",
                keyboard.type_text,
                text[6:],
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
            # Natural language gets first chance to become an actual Jarvis action.
            result = self._execute_natural_command(text)

            if result is None:
                context = "\n".join(
                    f"{m['role']}: {m['content']}" for m in self.memory.recent(10)
                )
                route = self.router.decide(text)
                prompt = (
                    "You are Jarvis, a local-first Windows AI assistant. "
                    "Answer concisely in natural Hinglish when appropriate. "
                    f"Route: {route.route.value}.\n"
                    f"Conversation:\n{context}\nUser: {text}"
                )
                try:
                    result = self.brain.ask(prompt)
                except LocalBrainError as exc:
                    result = (
                        f"Local brain unavailable: {exc}\n"
                        "Use /help for deterministic commands."
                    )

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
  /search <query>       (opens Chrome)
  /system
  /windows
  /help
  /exit

Natural-language commands are also supported for common actions:
  "Open Chrome"
  "Open Notepad"
  "Type hello world"
  "Press enter"
  "Click 500,300"
  "Scroll -5"
  "Calculate 25 * 4"
  "Search for the latest Python release"
  "Read C:\\path\\file.txt"
  "Open C:\\path\\folder"
  "Learn project E:\\MyProject"

Anything outside the deterministic command set is answered by the local LLM.
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
