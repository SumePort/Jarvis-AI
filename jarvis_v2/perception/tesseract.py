"""Optional local OCR vision provider."""
from __future__ import annotations
import io
from jarvis_v2.perception.vision import VisualObservation


class TesseractVisionProvider:
    def analyze(self, image: bytes) -> VisualObservation:
        try:
            from PIL import Image
            import pytesseract
        except ImportError as exc:
            raise RuntimeError("Pillow and pytesseract are required") from exc
        with Image.open(io.BytesIO(image)) as img:
            text = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            rows = []
            for i, value in enumerate(text["text"]):
                value = value.strip()
                if value:
                    rows.append({
                        "text": value,
                        "confidence": text["conf"][i],
                        "x": text["left"][i],
                        "y": text["top"][i],
                        "width": text["width"][i],
                        "height": text["height"][i],
                    })
            return VisualObservation(img.width, img.height, text=tuple(rows), source="local-ocr")
