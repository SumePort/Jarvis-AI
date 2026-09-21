from __future__ import annotations

def click(x: int, y: int, button: str = "left") -> str:
    import pyautogui
    pyautogui.click(x=x, y=y, button=button)
    return f"Clicked at ({x}, {y})."

def scroll(amount: int) -> str:
    import pyautogui
    pyautogui.scroll(amount)
    return "Scrolled."
