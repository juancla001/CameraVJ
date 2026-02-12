import cv2
import numpy as np
from .base import Effect


class MotionTrails(Effect):
    name = "motion_trails"

    def __init__(self):
        self.persist = 0.88   # 0.80..0.98 (más alto = más fantasma)
        self.glow = 0.15      # 0..0.5
        self.prev = None
        self.controls = {"motion": 0.0, "zones": {}}

    def reset(self):
        self.prev = None

    def set_controls(self, controls):
        self.controls = controls or self.controls

    def apply(self, frame):
        if self.prev is None:
            self.prev = frame.copy()
            return frame

        # motion controla persistencia (más motion = menos persistencia)
        m = float(self.controls.get("motion", 0.0))
        persist = np.clip(self.persist - 0.35 * m, 0.70, 0.98)

        # mezcla temporal
        out = cv2.addWeighted(frame, 1.0 - persist, self.prev, persist, 0.0)

        # glow suave (barato)
        if self.glow > 0:
            blur = cv2.GaussianBlur(out, (0, 0), 6)
            out = cv2.addWeighted(out, 1.0, blur, self.glow, 0.0)

        self.prev = out.copy()
        return out
