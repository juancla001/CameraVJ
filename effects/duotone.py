import cv2
import numpy as np
from .base import Effect


class Duotone(Effect):
    name = "duotone"

    # Preset duotone palettes: (dark_bgr, light_bgr)
    PALETTES = [
        ((20, 0, 80), (255, 200, 50)),      # Purple-Gold
        ((80, 0, 0), (0, 255, 255)),         # Dark Blue-Cyan
        ((0, 0, 80), (0, 255, 100)),         # Dark Red-Green
        ((60, 0, 60), (255, 100, 255)),      # Dark Magenta-Pink
        ((0, 60, 0), (200, 200, 255)),       # Dark Green-Warm White
    ]

    def __init__(self):
        self.palette_idx = 0
        self.contrast = 1.2
        self.t = 0
        self._hue_offset = 0.0

    def reset(self):
        self.t = 0
        self.palette_idx = 0
        self._hue_offset = 0.0

    def apply(self, frame):
        self.t += 1
        h, w = frame.shape[:2]

        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Enhance contrast
        gray = np.clip(gray.astype(np.float32) * self.contrast, 0, 255).astype(np.uint8)

        # Normalize to 0-1
        norm = gray.astype(np.float32) / 255.0

        # Get palette colors
        dark = np.array(self.PALETTES[self.palette_idx % len(self.PALETTES)][0], dtype=np.float32)
        light = np.array(self.PALETTES[self.palette_idx % len(self.PALETTES)][1], dtype=np.float32)

        # Interpolate between dark and light
        out = np.zeros((h, w, 3), dtype=np.float32)
        for c in range(3):
            out[:, :, c] = dark[c] + norm * (light[c] - dark[c])

        return out.clip(0, 255).astype(np.uint8)

    def set_controls(self, controls: dict):
        m = float(controls.get("motion", 0.0))
        self.contrast = 1.0 + 0.8 * m

        # Cycle palette with high motion
        new_idx = int(m * (len(self.PALETTES) - 1))
        if new_idx != self.palette_idx:
            self.palette_idx = new_idx
