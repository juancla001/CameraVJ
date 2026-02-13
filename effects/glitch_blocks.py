import cv2
import numpy as np
from .base import Effect


class GlitchBlocks(Effect):
    name = "glitch_blocks"

    def __init__(self):
        self.block_count = 8       # number of glitch blocks per frame
        self.max_shift = 30        # max pixel displacement
        self.intensity = 0.5       # probability of glitch per frame
        self.t = 0

    def reset(self):
        self.t = 0

    def apply(self, frame):
        self.t += 1
        h, w = frame.shape[:2]
        out = frame.copy()

        if np.random.random() > self.intensity:
            return out

        for _ in range(self.block_count):
            # Random block
            bh = np.random.randint(10, h // 4)
            bw = np.random.randint(20, w // 2)
            y = np.random.randint(0, h - bh)
            x = np.random.randint(0, w - bw)

            # Random displacement
            dx = np.random.randint(-self.max_shift, self.max_shift + 1)
            dy = np.random.randint(-self.max_shift // 4, self.max_shift // 4 + 1)

            # Source coords (clamped)
            sy = max(0, min(y + dy, h - bh))
            sx = max(0, min(x + dx, w - bw))

            # Copy block from displaced position
            out[y:y+bh, x:x+bw] = frame[sy:sy+bh, sx:sx+bw]

            # Occasional color channel swap on block
            if np.random.random() < 0.3:
                block = out[y:y+bh, x:x+bw]
                out[y:y+bh, x:x+bw] = block[:, :, [2, 1, 0]]

        return out

    def set_controls(self, controls: dict):
        m = float(controls.get("motion", 0.0))
        beat = float(controls.get("beat", 0.0))

        self.block_count = int(4 + 16 * m)
        self.max_shift = int(10 + 60 * m)
        self.intensity = 0.3 + 0.6 * m

        if beat > 0.5:
            self.block_count = int(self.block_count * 1.5)
            self.intensity = min(1.0, self.intensity + 0.3)
