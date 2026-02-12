import numpy as np


class ZoneMapper:
    """
    Divide en 4 zonas: left/right/top/bottom.
    Calcula movimiento por zona a partir de una máscara binaria (255 = movimiento).
    """

    def __init__(self):
        self.last = {"left": 0.0, "right": 0.0, "top": 0.0, "bottom": 0.0}

    def compute(self, mask):
        # mask: 2D uint8 (0/255)
        h, w = mask.shape[:2]
        if h < 2 or w < 2:
            return self.last

        left = mask[:, : w // 2]
        right = mask[:, w // 2 :]
        top = mask[: h // 2, :]
        bottom = mask[h // 2 :, :]

        def intensity(m):
            return float(np.mean(m > 0))

        self.last = {
            "left": intensity(left),
            "right": intensity(right),
            "top": intensity(top),
            "bottom": intensity(bottom),
        }
        return self.last
