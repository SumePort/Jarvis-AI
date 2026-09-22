"""Local screenshot capture boundary for visual perception."""
from __future__ import annotations


class WindowsScreenshotProvider:
    def capture(self) -> bytes:
        try:
            import pyautogui
        except ImportError as exc:
            raise RuntimeError("pyautogui is required for screenshot capture") from exc
        image = pyautogui.screenshot()
        import io
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()
