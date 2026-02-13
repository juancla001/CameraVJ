import cv2
import numpy as np
from .base import Effect


class ZoomPulse(Effect):
    name = "zoom_pulse"

    def __init__(self):
        self.amplitude = 0.08    # zoom range (0.05 = subtle, 0.2 = intense)
        self.speed = 0.12        # oscillation speed
        self.t = 0

    def reset(self):
        self.t = 0

    def apply(self, frame):
        self.t += 1
        h, w = frame.shape[:2]
        cx, cy = w // 2, h // 2

        # Sinusoidal zoom factor
        zoom = 1.0 + np.sin(self.t * self.speed) * self.amplitude

        # Zoom from center using affine transform
        M = cv2.getRotationMatrix2D((cx, cy), 0, zoom)
        out = cv2.warpAffine(frame, M, (w, h), borderMode=cv2.BORDER_REFLECT)

        return out

    def set_controls(self, controls: dict):
        m = float(controls.get("motion", 0.0))
        beat = float(controls.get("beat", 0.0))
        bass = float(controls.get("bass", 0.0))

        self.amplitude = 0.04 + 0.20 * m
        self.speed = 0.08 + 0.15 * m

        # Bass drives amplitude
        if bass > 0.3:
            self.amplitude = min(0.3, self.amplitude + bass * 0.15)

        # Beat triggers a pulse
        if beat > 0.5:
            self.amplitude = min(0.35, self.amplitude + 0.1)
