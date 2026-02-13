import cv2
import numpy as np
from .base import Effect


class SlitScan(Effect):
    name = "slit_scan"

    def __init__(self):
        self.buffer_size = 30     # number of frames to keep
        self.spread = 1.0         # how many rows apart in time
        self._buffer = []
        self.t = 0

    def reset(self):
        self._buffer.clear()
        self.t = 0

    def apply(self, frame):
        self.t += 1
        h, w = frame.shape[:2]

        # Add frame to buffer
        self._buffer.append(frame.copy())
        if len(self._buffer) > self.buffer_size:
            self._buffer.pop(0)

        if len(self._buffer) < 2:
            return frame

        out = np.zeros_like(frame)
        n_frames = len(self._buffer)

        # Each row comes from a different frame in the buffer
        for y in range(h):
            # Map row position to frame index
            t_offset = (y / h) * (n_frames - 1) * self.spread
            frame_idx = int(t_offset) % n_frames
            out[y] = self._buffer[frame_idx][y]

        return out

    def set_controls(self, controls: dict):
        m = float(controls.get("motion", 0.0))
        zones = controls.get("zones", {})
        lr = abs(float(zones.get("left", 0.0)) - float(zones.get("right", 0.0)))

        self.buffer_size = int(15 + 45 * m)
        self.spread = 0.5 + 2.0 * m + lr
