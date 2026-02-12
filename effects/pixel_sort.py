import cv2
import numpy as np
from .base import Effect


class PixelSort(Effect):
    name = "pixel_sort"

    def __init__(self, threshold=80, direction=0):
        self.threshold = int(threshold)  # brightness threshold for sorting
        self.direction = int(direction)  # 0=horizontal, 1=vertical
        self.intensity = 0.5             # blend with original
        self._step = 4                   # process every Nth row for perf

    def reset(self):
        self.intensity = 0.5

    def apply(self, frame):
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        out = frame.copy()

        if self.direction == 1:
            out = cv2.rotate(out, cv2.ROTATE_90_CLOCKWISE)
            gray = cv2.rotate(gray, cv2.ROTATE_90_CLOCKWISE)
            h, w = out.shape[:2]

        # Sort rows where brightness > threshold
        for y in range(0, h, self._step):
            row_gray = gray[y]
            mask = row_gray > self.threshold
            indices = np.where(mask)[0]
            if len(indices) < 2:
                continue
            start, end = indices[0], indices[-1] + 1
            segment = out[y, start:end].copy()
            # Sort by luminance
            lum = row_gray[start:end]
            order = np.argsort(lum)
            out[y, start:end] = segment[order]

        if self.direction == 1:
            out = cv2.rotate(out, cv2.ROTATE_90_COUNTERCLOCKWISE)

        # Blend with original
        result = cv2.addWeighted(frame, 1.0 - self.intensity, out, self.intensity, 0)
        return result

    def set_controls(self, controls: dict):
        m = float(controls.get("motion", 0.0))
        zones = controls.get("zones", {})
        top = float(zones.get("top", 0.0))

        self.threshold = int(120 - 80 * m)
        self.intensity = 0.3 + 0.6 * m
        self._step = max(2, int(6 - 4 * top))
