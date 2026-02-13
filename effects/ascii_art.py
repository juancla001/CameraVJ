import cv2
import numpy as np
from .base import Effect


class ASCIIArt(Effect):
    name = "ascii_art"

    # Characters ordered by density (dark to bright)
    CHARS = " .:-=+*#%@"

    def __init__(self):
        self.cell_size = 8       # pixel size of each character cell
        self.colored = True      # use original colors or green monochrome
        self.font_scale = 0.35
        self.t = 0

    def reset(self):
        self.t = 0

    def apply(self, frame):
        self.t += 1
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        out = np.zeros_like(frame)
        cs = max(4, self.cell_size)
        n_chars = len(self.CHARS)

        for y in range(0, h - cs, cs):
            for x in range(0, w - cs, cs):
                # Average brightness of cell
                cell = gray[y:y+cs, x:x+cs]
                brightness = int(np.mean(cell))

                # Map to character
                char_idx = int(brightness / 256 * n_chars)
                char_idx = min(char_idx, n_chars - 1)
                char = self.CHARS[char_idx]

                if char == " ":
                    continue

                # Color from original frame center of cell
                if self.colored:
                    color = tuple(int(c) for c in frame[y + cs//2, x + cs//2])
                else:
                    color = (0, 255, 0)

                cv2.putText(
                    out, char, (x, y + cs),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    self.font_scale, color, 1, cv2.LINE_AA
                )

        return out

    def set_controls(self, controls: dict):
        m = float(controls.get("motion", 0.0))
        # More motion = smaller cells (more detail but slower)
        self.cell_size = max(4, int(10 - 6 * m))
        self.font_scale = 0.25 + 0.2 * m
