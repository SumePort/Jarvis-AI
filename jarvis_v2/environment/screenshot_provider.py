"""Optional screenshot environment provider."""
from __future__ import annotations
from jarvis_v2.core.types import EnvironmentSnapshot


class ScreenshotEnvironmentProvider:
    def __init__(self, screenshot_provider, vision_service):
        self.screenshot_provider = screenshot_provider
        self.vision_service = vision_service

    def snapshot(self) -> EnvironmentSnapshot:
        snap = EnvironmentSnapshot(timestamp=__import__("time").time())
        image = self.screenshot_provider.capture()
        visual = self.vision_service.analyze(image)
        snap.visual_evidence.append({
            "width": visual.width,
            "height": visual.height,
            "objects": list(visual.objects),
            "text": list(visual.text),
            "source": visual.source,
        })
        return snap
