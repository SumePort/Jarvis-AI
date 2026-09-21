from __future__ import annotations

def read_image(path: str) -> str:
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        return "OCR requires pytesseract and a local Tesseract installation."
    return pytesseract.image_to_string(Image.open(path))
