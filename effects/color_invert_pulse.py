import cv2
import numpy as np
from .base import Effect


class ColorInvertPulse(Effect):
    name = "color_invert_pulse"

    def __init__(self):
        self.rate = 8           # pulse every N frames
        self.blend = 0.0        # current blend (0=normal, 1=inverted)
        self.smooth = 0.15      # blend speed
        self.t = 0
        self._target = 0.0

    def reset(self):
        self.t = 0
        self.blend = 0.0
        self._target = 0.0

    def apply(self, frame):
        self.t += 1

        # Trigger pulse
        if self.t % max(1, self.rate) == 0:
            self._target = 1.0 if self._target < 0.5 else 0.0

        # Smooth blend toward target
        self.blend += (self._target - self.blend) * self.smooth

        if self.blend < 0.01:
            return frame

        inverted = cv2.bitwise_not(frame)
        out = cv2.addWeighted(frame, 1.0 - self.blend, inverted, self.blend, 0)
        return out

    def set_controls(self, controls: dict):
        m = float(controls.get("motion", 0.0))
        beat = float(controls.get("beat", 0.0))

        self.rate = max(2, int(12 - 10 * m))
        self.smooth = 0.1 + 0.3 * m

        # Beat triggers immediate pulse
        if beat > 0.5:
            self._target = 1.0 if self._target < 0.5 else 0.0
