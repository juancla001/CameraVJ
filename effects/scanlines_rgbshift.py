import cv2
import numpy as np
from .base import Effect


class ScanlinesRGBShift(Effect):
    name = "scanlines_rgbshift"

    def __init__(self, scan_strength=0.25, shift=4, speed=1):
        self.scan_strength = float(scan_strength)
        self.shift = int(shift)
        self.speed = int(speed)
        self.t = 0

    def reset(self):
        self.t = 0

    def apply(self, frame):
        self.t += 1
        h, w = frame.shape[:2]

        # RGB shift: desplazamos canal R a la derecha y B a la izquierda
        b, g, r = cv2.split(frame)
        s = int(np.sin(self.t * 0.08 * self.speed) * self.shift)

        r2 = np.roll(r, s, axis=1)
        b2 = np.roll(b, -s, axis=1)
        out = cv2.merge([b2, g, r2])

        # Scanlines: oscurecer filas alternas
        mask = np.ones((h, 1), dtype=np.float32)
        mask[::2] = 1.0 - self.scan_strength
        out = (out.astype(np.float32) * mask[:, None]).clip(0, 255).astype(np.uint8)

        return out

    def set_controls(self, controls: dict):
        m = float(controls.get("motion", 0.0))
        zones = controls.get("zones", {})
        top = float(zones.get("top", 0.0))
        bottom = float(zones.get("bottom", 0.0))

        self.shift = int(2 + 18 * m)
        self.speed = int(1 + 4 * m)
        self.scan_strength = 0.10 + 0.45 * (top + bottom) / 2.0
