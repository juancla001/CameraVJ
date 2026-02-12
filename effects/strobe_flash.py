import cv2
import numpy as np
from .base import Effect


class StrobeFlash(Effect):
    name = "strobe_flash"

    def __init__(self):
        self.rate = 6          # flash every N frames
        self.intensity = 0.8   # 0..1 flash brightness
        self.color_mode = 0    # 0=white, 1=color cycle
        self.t = 0
        self._hue = 0.0

    def reset(self):
        self.t = 0
        self._hue = 0.0

    def apply(self, frame):
        self.t += 1
        h, w = frame.shape[:2]

        if self.t % max(1, self.rate) != 0:
            return frame

        # Flash frame
        if self.color_mode == 0:
            flash = np.full((h, w, 3), 255, dtype=np.uint8)
        else:
            self._hue = (self._hue + 30) % 180
            hsv = np.full((h, w, 3), (int(self._hue), 255, 255), dtype=np.uint8)
            flash = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

        out = cv2.addWeighted(frame, 1.0 - self.intensity, flash, self.intensity, 0)
        return out

    def set_controls(self, controls: dict):
        m = float(controls.get("motion", 0.0))
        # More motion = faster strobe
        self.rate = max(2, int(10 - 8 * m))
        self.intensity = 0.4 + 0.5 * m

        # Beat from audio (if available)
        beat = float(controls.get("beat", 0.0))
        if beat > 0.5:
            self.rate = 2
            self.intensity = min(1.0, self.intensity + 0.2)
