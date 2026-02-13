import cv2
import numpy as np
from .base import Effect


class ParticleRain(Effect):
    name = "particle_rain"

    def __init__(self):
        self.max_particles = 200
        self.speed = 3.0
        self.direction = 1       # 1=down, -1=up
        self.hue_shift = 0.0
        self._particles = None
        self._frame_shape = None

    def reset(self):
        self._particles = None

    def _init_particles(self, h, w):
        self._frame_shape = (h, w)
        n = self.max_particles
        self._particles = np.zeros((n, 5), dtype=np.float32)
        # columns: x, y, speed, size, hue
        self._particles[:, 0] = np.random.randint(0, w, n)        # x
        self._particles[:, 1] = np.random.randint(0, h, n)        # y
        self._particles[:, 2] = np.random.uniform(1, 4, n)        # speed
        self._particles[:, 3] = np.random.randint(1, 4, n)        # size
        self._particles[:, 4] = np.random.uniform(0, 180, n)      # hue

    def apply(self, frame):
        h, w = frame.shape[:2]

        if self._particles is None or self._frame_shape != (h, w):
            self._init_particles(h, w)

        out = frame.copy()
        p = self._particles

        # Update positions
        p[:, 1] += p[:, 2] * self.speed * self.direction

        # Wrap around
        if self.direction > 0:
            mask = p[:, 1] > h
            p[mask, 1] = 0
            p[mask, 0] = np.random.randint(0, w, np.sum(mask))
        else:
            mask = p[:, 1] < 0
            p[mask, 1] = h
            p[mask, 0] = np.random.randint(0, w, np.sum(mask))

        # Shift hues
        p[:, 4] = (p[:, 4] + self.hue_shift) % 180

        # Draw particles
        for i in range(len(p)):
            x, y, _, size, hue = p[i]
            # Convert hue to BGR
            hsv_px = np.array([[[int(hue), 255, 255]]], dtype=np.uint8)
            bgr = cv2.cvtColor(hsv_px, cv2.COLOR_HSV2BGR)[0, 0]
            color = (int(bgr[0]), int(bgr[1]), int(bgr[2]))
            cv2.circle(out, (int(x), int(y)), int(size), color, -1)

        return out

    def set_controls(self, controls: dict):
        m = float(controls.get("motion", 0.0))
        zones = controls.get("zones", {})
        top = float(zones.get("top", 0.0))
        bottom = float(zones.get("bottom", 0.0))

        self.speed = 1.0 + 6.0 * m
        self.hue_shift = 0.5 + 3.0 * m
        self.max_particles = int(100 + 300 * m)

        # Direction based on vertical zone movement
        if top > bottom + 0.1:
            self.direction = -1  # upward
        else:
            self.direction = 1   # downward
