from __future__ import annotations
from .screenshot import capture
from .ocr import read_image

def inspect_screen() -> str:
    path=capture()
    return read_image(path)
