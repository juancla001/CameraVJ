import cv2
import numpy as np
from .base import Effect


class FeedbackGlitch(Effect):
    name = "feedback_glitch"

    def __init__(self, feedback=0.92, warp=6, noise=6):
        self.feedback = float(feedback)  # más alto = más “trail”
        self.warp = int(warp)            # pixels de desplazamiento max
        self.noise = int(noise)          # intensidad de ruido
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

        # Pequeño “warp” horizontal/vertical que cambia con el tiempo
        dx = int(np.sin(self.t * 0.07) * self.warp)
        dy = int(np.cos(self.t * 0.05) * self.warp)

        M = np.float32([[1, 0, dx], [0, 1, dy]])
        warped_prev = cv2.warpAffine(self.prev, M, (w, h), borderMode=cv2.BORDER_WRAP)

        # Feedback mix
        out = cv2.addWeighted(frame, 1.0 - self.feedback, warped_prev, self.feedback, 0.0)

        # Ruido “digital”
        if self.noise > 0:
            n = np.random.randint(0, self.noise, (h, w, 1), dtype=np.uint8)
            n = np.repeat(n, 3, axis=2)
            out = cv2.add(out, n)

        # Guardar para siguiente frame
        self.prev = out.copy()
        return out

    def set_controls(self, controls: dict):
        m = float(controls.get("motion", 0.0))
        zones = controls.get("zones", {})
        lr = float(zones.get("left", 0.0)) - float(zones.get("right", 0.0))

        self.feedback = 0.86 + 0.10 * m
        self.warp = int(3 + 14 * m + 6 * abs(lr))
        self.noise = int(2 + 20 * m)

