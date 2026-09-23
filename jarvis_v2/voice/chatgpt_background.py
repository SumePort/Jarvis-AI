"""Background ChatGPT Voice bridge for JARVIS.

This optional UI bridge uses a persistent user-owned Chromium profile. It
prefers ChatGPT Temporary Chat, starts Voice in a separate browser window,
minimizes that window, and routes explicit JARVIS action markers through the
existing local JARVIS V2 runtime.

This is not an OpenAI API integration. ChatGPT web UI selectors can change.
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

ACTION_RE = re.compile(
    r"\[\[JARVIS_ACTION\]\]\s*(\{.*?\})\s*\[\[/JARVIS_ACTION\]\]",
    re.DOTALL,
)


@dataclass(frozen=True)
class ChatGPTBackgroundConfig:
    profile_dir: Path = Path("data/jarvis_v2/chatgpt_profile")
    url: str = "https://chatgpt.com/"
    poll_seconds: float = 0.8
    login_wait_seconds: float = 300.0
    prefer_temporary_chat: bool = True
    minimize_window: bool = True
    voice_start_timeout_seconds: float = 30.0


@dataclass(frozen=True)
class JarvisAction:
    command: str
    spoken: str = ""

    @classmethod
    def from_payload(cls, payload: dict) -> "JarvisAction":
        command = str(payload.get("command", "")).strip()
        spoken = str(payload.get("spoken", "")).strip()
        if not command:
            raise ValueError("JARVIS action is missing command")
        return cls(command=command, spoken=spoken)


def parse_actions(text: str) -> list[JarvisAction]:
    actions: list[JarvisAction] = []
    for match in ACTION_RE.finditer(text or ""):
        payload = json.loads(match.group(1))
        if not isinstance(payload, dict):
            raise ValueError("JARVIS action payload must be an object")
        actions.append(JarvisAction.from_payload(payload))
    return actions


class ChatGPTBackgroundBridge:
    """Run ChatGPT Voice in a separate persistent browser session."""

    def __init__(
        self,
        config: ChatGPTBackgroundConfig | None = None,
        action_handler: Optional[Callable[[str], str]] = None,
        status_handler: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.config = config or ChatGPTBackgroundConfig()
        self.action_handler = action_handler
        self.status_handler = status_handler
        self._context = None
        self._page = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._seen_assistant_text = ""
        self._started = False

    def _status(self, message: str) -> None:
        if self.status_handler:
            self.status_handler(message)
        else:
            print(f"[CHATGPT] {message}", flush=True)

    def start(self, wait_for_login: bool = True) -> None:
        if self._started:
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run,
            args=(wait_for_login,),
            name="jarvis-chatgpt-background",
            daemon=True,
        )
        self._thread.start()
        self._started = True

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=8)
        self._thread = None
        self._started = False

    def _run(self, wait_for_login: bool) -> None:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self._status(
                "Playwright is not installed. Run: pip install playwright; "
                "then: playwright install chromium"
            )
            return

        profile = Path(self.config.profile_dir)
        profile.mkdir(parents=True, exist_ok=True)

        try:
            with sync_playwright() as playwright:
                self._context = playwright.chromium.launch_persistent_context(
                    str(profile),
                    headless=False,
                    no_viewport=True,
                    permissions=["microphone"],
                    args=[
                        "--start-minimized",
                        "--autoplay-policy=no-user-gesture-required",
                        "--disable-background-timer-throttling",
                        "--disable-backgrounding-occluded-windows",
                    ],
                )
                self._page = (
                    self._context.pages[0]
                    if self._context.pages
                    else self._context.new_page()
                )
                self._page.goto(
                    self.config.url,
                    wait_until="domcontentloaded",
                    timeout=60_000,
                )

                if not self._wait_until_authenticated(wait_for_login):
                    return

                self._minimize_window()
                if self.config.prefer_temporary_chat:
                    self._enable_temporary_chat()

                self._send_bootstrap()
                self._start_voice()
                self._minimize_window()
                self._status("background voice session is running")

                while not self._stop.wait(self.config.poll_seconds):
                    self._process_assistant_actions()

        except Exception as exc:
            self._status(f"background bridge stopped: {type(exc).__name__}: {exc}")
        finally:
            try:
                if self._context:
                    self._context.close()
            except Exception:
                pass
            self._context = None
            self._page = None

    def _wait_until_authenticated(self, wait_for_login: bool) -> bool:
        deadline = time.monotonic() + (
            self.config.login_wait_seconds if wait_for_login else 5
        )
        while time.monotonic() < deadline and not self._stop.is_set():
            url = self._page.url
            if "chatgpt.com" in url and not any(
                marker in url for marker in ("/auth/", "/login", "/signup")
            ):
                try:
                    if self._find_voice_button(timeout_ms=1500):
                        return True
                except Exception:
                    pass
            if not wait_for_login:
                break
            self._status("sign in to ChatGPT once in the background browser...")
            time.sleep(2)
        if self._stop.is_set():
            return False
        self._status(
            "ChatGPT login was not detected. Sign in, then restart the bridge."
        )
        return False

    def _find_voice_button(self, timeout_ms: int = 3000):
        selectors = [
            'button[aria-label*="Voice"]',
            'button[aria-label*="voice"]',
            'button[title*="Voice"]',
            'button[title*="voice"]',
        ]
        for selector in selectors:
            locator = self._page.locator(selector)
            if locator.count():
                return locator.first
        for text in ("Voice", "Start voice", "Start Voice"):
            locator = self._page.get_by_text(text, exact=True)
            if locator.count():
                return locator.first
        raise RuntimeError("ChatGPT Voice control was not found")

    def _enable_temporary_chat(self) -> None:
        candidates = [
            'button[aria-label*="model"]',
            'button[aria-label*="Model"]',
            'button:has-text("GPT")',
        ]
        opened = False
        for selector in candidates:
            try:
                locator = self._page.locator(selector)
                if locator.count():
                    locator.first.click()
                    opened = True
                    break
            except Exception:
                continue

        if not opened:
            raise RuntimeError(
                "Temporary Chat could not be enabled safely; "
                "refusing to use an ordinary saved chat"
            )

        try:
            option = self._page.get_by_text("Temporary", exact=True)
            if option.count():
                option.first.click()
            else:
                option = self._page.get_by_text(
                    re.compile(r"Temporary Chat", re.I)
                )
                if option.count():
                    option.first.click()
                else:
                    raise RuntimeError("Temporary Chat option was not found")
            self._status("Temporary Chat enabled")
        except Exception as exc:
            raise RuntimeError("Temporary Chat could not be enabled") from exc

    def _send_bootstrap(self) -> None:
        prompt = (
            "You are the conversational voice layer for my local assistant JARVIS. "
            "Speak naturally. JARVIS, not you, is authoritative for Windows and "
            "computer actions. When the user asks JARVIS to perform a computer "
            "action, include exactly one machine instruction in this format, "
            "followed by a short natural explanation: "
            "[[JARVIS_ACTION]]"
            '{"command":"<plain-language command for JARVIS>","spoken":"<short status>"}'
            "[[/JARVIS_ACTION]]. "
            "Never put passwords, PINs, OTPs, CVVs, recovery codes, API keys or "
            "other secrets in an action."
        )
        self._send_text(prompt)

    def _send_text(self, text: str) -> None:
        composers = [
            'textarea',
            '[contenteditable="true"][role="textbox"]',
            '[contenteditable="true"]',
        ]
        for selector in composers:
            locator = self._page.locator(selector)
            if not locator.count():
                continue
            try:
                locator.last.fill(text)
                locator.last.press("Enter")
                return
            except Exception:
                continue
        raise RuntimeError("ChatGPT composer was not found")

    def _start_voice(self) -> None:
        button = self._find_voice_button(timeout_ms=5000)
        button.click()
        deadline = time.monotonic() + self.config.voice_start_timeout_seconds
        while time.monotonic() < deadline and not self._stop.is_set():
            if self._page.locator(
                'button[aria-label*="Mute"], button[aria-label*="mute"]'
            ).count():
                return
            time.sleep(0.5)
        self._status("Voice control clicked; waiting for audio session")

    def _assistant_messages(self) -> list[str]:
        selectors = [
            '[data-message-author-role="assistant"]',
            'article[data-testid*="assistant"]',
        ]
        for selector in selectors:
            locator = self._page.locator(selector)
            if locator.count():
                try:
                    return [t.strip() for t in locator.all_inner_texts() if t.strip()]
                except Exception:
                    pass
        return []

    def _process_assistant_actions(self) -> None:
        messages = self._assistant_messages()
        if not messages:
            return
        latest = messages[-1]
        if latest == self._seen_assistant_text:
            return
        self._seen_assistant_text = latest

        for action in parse_actions(latest):
            if not self.action_handler:
                self._status(f"JARVIS action waiting for handler: {action.command}")
                continue
            try:
                result = self.action_handler(action.command)
            except Exception as exc:
                result = f"JARVIS action failed: {type(exc).__name__}: {exc}"
            status = action.spoken or result
            self._send_text(
                "JARVIS completed the requested computer action. "
                f"Result: {result}. Briefly tell the user: {status}"
            )

    def _minimize_window(self) -> None:
        if not self.config.minimize_window:
            return
        try:
            import pygetwindow as gw

            for window in gw.getAllWindows():
                if "chatgpt" in (window.title or "").lower():
                    window.minimize()
                    break
        except Exception:
            pass


def build_background_bridge(
    action_handler: Optional[Callable[[str], str]] = None,
) -> ChatGPTBackgroundBridge:
    root = Path(os.getenv("JARVIS_PROJECT_ROOT", os.getcwd()))
    profile = Path(
        os.getenv(
            "JARVIS_CHATGPT_PROFILE",
            str(root / "data" / "jarvis_v2" / "chatgpt_profile"),
        )
    )
    return ChatGPTBackgroundBridge(
        ChatGPTBackgroundConfig(
            profile_dir=profile,
            url=os.getenv("JARVIS_CHATGPT_URL", "https://chatgpt.com/"),
            poll_seconds=float(os.getenv("JARVIS_CHATGPT_POLL", "0.8")),
            login_wait_seconds=float(os.getenv("JARVIS_CHATGPT_LOGIN_WAIT", "300")),
            prefer_temporary_chat=os.getenv("JARVIS_CHATGPT_TEMPORARY", "1") == "1",
            minimize_window=os.getenv("JARVIS_CHATGPT_MINIMIZE", "1") == "1",
        ),
        action_handler=action_handler,
    )
