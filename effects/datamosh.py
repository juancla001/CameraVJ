import cv2
import numpy as np
from .base import Effect


class Datamosh(Effect):
    name = "datamosh"

    def __init__(self):
        self.intensity = 0.7     # blend with previous
        self.block_size = 16     # motion block size
        self.corruption = 0.3    # chance of corrupting a block
        self.prev = None
        self.t = 0

    def reset(self):
        self.prev = None
        self.t = 0

    def apply(self, frame):
        self.t += 1
        h, w = frame.shape[:2]

        if self.prev is None:
            self.prev = frame.copy()
            return frame

        out = frame.copy()
        bs = max(8, self.block_size)

        # Iterate over blocks
        for by in range(0, h - bs, bs):
            for bx in range(0, w - bs, bs):
                if np.random.random() < self.corruption:
                    # Use block from previous frame (displaced)
                    dx = np.random.randint(-bs, bs + 1)
                    dy = np.random.randint(-bs // 2, bs // 2 + 1)
                    sy = max(0, min(by + dy, h - bs))
                    sx = max(0, min(bx + dx, w - bs))
                    out[by:by+bs, bx:bx+bs] = self.prev[sy:sy+bs, sx:sx+bs]

        # Blend with previous for trailing effect
        out = cv2.addWeighted(out, 1.0 - self.intensity * 0.3, self.prev, self.intensity * 0.3, 0)

        self.prev = out.copy()
        return out

    def set_controls(self, controls: dict):
        m = float(controls.get("motion", 0.0))
        beat = float(controls.get("beat", 0.0))

        self.corruption = 0.1 + 0.5 * m
        self.intensity = 0.4 + 0.5 * m
        self.block_size = max(8, int(24 - 16 * m))

        if beat > 0.5:
            self.corruption = min(0.8, self.corruption + 0.3)
