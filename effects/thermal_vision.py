import cv2
import numpy as np
from .base import Effect


class ThermalVision(Effect):
    name = "thermal_vision"

    def __init__(self):
        self.colormap = cv2.COLORMAP_JET
        self.blur = 3
        self.contrast = 1.2
        self.t = 0
        self._colormaps = [
            cv2.COLORMAP_JET,
            cv2.COLORMAP_HOT,
            cv2.COLORMAP_INFERNO,
        ]
        self._map_idx = 0

    def reset(self):
        self.t = 0
        self._map_idx = 0
        self.colormap = self._colormaps[0]

    def apply(self, frame):
        self.t += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Enhance contrast
        gray = np.clip(gray.astype(np.float32) * self.contrast, 0, 255).astype(np.uint8)

        # Slight blur for smoother thermal look
        if self.blur > 0:
            k = self.blur * 2 + 1
            gray = cv2.GaussianBlur(gray, (k, k), 0)

        # Apply colormap
        out = cv2.applyColorMap(gray, self.colormap)

        # Subtle scan flicker
        if self.t % 3 == 0:
            row = (self.t * 7) % frame.shape[0]
            end = min(row + 2, frame.shape[0])
            out[row:end] = np.clip(out[row:end].astype(np.int16) + 30, 0, 255).astype(np.uint8)

        return out

    def set_controls(self, controls: dict):
        m = float(controls.get("motion", 0.0))
        self.contrast = 1.0 + 0.8 * m
        self.blur = int(1 + 4 * m)

        # Cycle colormap with high motion
        new_idx = min(2, int(m * 3))
        if new_idx != self._map_idx:
            self._map_idx = new_idx
            self.colormap = self._colormaps[self._map_idx]
