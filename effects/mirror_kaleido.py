import cv2
import numpy as np
from .base import Effect


class MirrorKaleido(Effect):
    name = "mirror_kaleido"

    def __init__(self, mode=0):
        # mode 0: espejo horizontal
        # mode 1: espejo vertical
        # mode 2: 4-way (kaleido simple)
        self.mode = int(mode) % 3

    def apply(self, frame):
        h, w = frame.shape[:2]

        if self.mode == 0:
            left = frame[:, : w // 2]
            right = cv2.flip(left, 1)
            return np.concatenate([left, right], axis=1)

        if self.mode == 1:
            top = frame[: h // 2, :]
            bottom = cv2.flip(top, 0)
            return np.concatenate([top, bottom], axis=0)

        # 4-way kaleido simple
        q = frame[: h // 2, : w // 2]
        q1 = q
        q2 = cv2.flip(q, 1)
        q3 = cv2.flip(q, 0)
        q4 = cv2.flip(q, -1)
        top = np.concatenate([q1, q2], axis=1)
        bottom = np.concatenate([q3, q4], axis=1)
        return np.concatenate([top, bottom], axis=0)

    def set_controls(self, controls: dict):
        pass
