import cv2
import numpy as np
from .base import Effect


class ChromaticAberration(Effect):
    name = "chromatic_aberration"

    def __init__(self, strength=8, radial=True):
        self.strength = int(strength)
        self.radial = radial
        self.t = 0

    def reset(self):
        self.t = 0

    def apply(self, frame):
        self.t += 1
        h, w = frame.shape[:2]
        b, g, r = cv2.split(frame)

        s = self.strength
        pulse = int(np.sin(self.t * 0.06) * s * 0.3)
        sr = s + pulse
        sb = -(s + pulse)

        if self.radial:
            # Radial: scale channels slightly different from center
            cx, cy = w // 2, h // 2
            # Red channel: zoom in slightly
            M_r = cv2.getRotationMatrix2D((cx, cy), 0, 1.0 + sr * 0.002)
            r2 = cv2.warpAffine(r, M_r, (w, h), borderMode=cv2.BORDER_REFLECT)
            # Blue channel: zoom out slightly
            M_b = cv2.getRotationMatrix2D((cx, cy), 0, 1.0 + sb * 0.002)
            b2 = cv2.warpAffine(b, M_b, (w, h), borderMode=cv2.BORDER_REFLECT)
            out = cv2.merge([b2, g, r2])
        else:
            # Simple horizontal shift
            r2 = np.roll(r, sr, axis=1)
            b2 = np.roll(b, sb, axis=1)
            out = cv2.merge([b2, g, r2])

        return out

    def set_controls(self, controls: dict):
        m = float(controls.get("motion", 0.0))
        self.strength = int(4 + 20 * m)
