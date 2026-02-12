import cv2
import numpy as np
from .base import Effect


class EdgeNeon(Effect):
    name = "edge_neon"

    def __init__(self):
        self.t1 = 40
        self.t2 = 120
        self.hue_speed = 2.0
        self.glow_size = 5
        self._hue = 0.0

    def reset(self):
        self._hue = 0.0

    def apply(self, frame):
        h, w = frame.shape[:2]
        self._hue = (self._hue + self.hue_speed) % 180

        # Detect edges
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, self.t1, self.t2)

        # Dilate for thicker edges
        edges = cv2.dilate(edges, None, iterations=1)

        # Create colored edge layer
        hue_val = int(self._hue)
        edge_hsv = np.zeros((h, w, 3), dtype=np.uint8)
        edge_hsv[:, :, 0] = hue_val
        edge_hsv[:, :, 1] = 255
        edge_hsv[:, :, 2] = edges
        edge_bgr = cv2.cvtColor(edge_hsv, cv2.COLOR_HSV2BGR)

        # Add glow
        k = self.glow_size * 2 + 1
        glow = cv2.GaussianBlur(edge_bgr, (k, k), 0)
        out = cv2.add(edge_bgr, glow)

        return out

    def set_controls(self, controls: dict):
        m = float(controls.get("motion", 0.0))
        zones = controls.get("zones", {})
        lr = abs(float(zones.get("left", 0.0)) - float(zones.get("right", 0.0)))

        self.hue_speed = 1.0 + 6.0 * m
        self.t1 = int(50 - 30 * m)
        self.t2 = int(150 - 80 * m)
        self.glow_size = int(3 + 8 * lr)
