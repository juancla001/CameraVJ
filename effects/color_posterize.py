import numpy as np
import cv2
from .base import Effect


class ColorPosterize(Effect):
    name = "color_posterize"

    def __init__(self, levels=6, speed=0.03):
        self.levels = max(2, int(levels))
        self.speed = float(speed)
        self.phase = 0.0

    def apply(self, frame):
        # Hue shift (HSV) + posterize (cuantización)
        self.phase = (self.phase + self.speed) % 180.0

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)

        h = (h.astype(np.float32) + self.phase).astype(np.uint8)
        hsv2 = cv2.merge([h, s, v])
        out = cv2.cvtColor(hsv2, cv2.COLOR_HSV2BGR)

        # Posterize: niveles por canal
        step = 256 // self.levels
        out = (out // step) * step
        return out

    def set_controls(self, controls: dict):
        m = float(controls.get("motion", 0.0))
        self.speed = 0.02 + 0.10 * m
        self.levels = int(10 - 6 * m)
        self.levels = max(2, self.levels)
