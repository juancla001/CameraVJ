import cv2
import numpy as np


class MotionEstimator:
    """
    Estima movimiento usando background subtraction (MOG2).
    Devuelve:
      - motion_global: float [0..1]
      - motion_mask_small: máscara binaria en resolución reducida (para debug/zones)
    """

    def __init__(self, scale=0.5, history=200, var_threshold=16, detect_shadows=False, smooth=0.2):
        self.scale = float(scale)
        self.smooth = float(smooth)
        self.bg = cv2.createBackgroundSubtractorMOG2(
            history=int(history),
            varThreshold=float(var_threshold),
            detectShadows=bool(detect_shadows),
        )
        self._ema = 0.0

    def _preprocess(self, frame_bgr):
        if self.scale != 1.0:
            h, w = frame_bgr.shape[:2]
            frame_bgr = cv2.resize(frame_bgr, (int(w * self.scale), int(h * self.scale)))
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        return gray

    def update(self, frame_bgr):
        gray = self._preprocess(frame_bgr)

        fg = self.bg.apply(gray)

        # Limpieza: binarizar + morfología para ruido
        _, fg = cv2.threshold(fg, 200, 255, cv2.THRESH_BINARY)
        fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8), iterations=1)
        fg = cv2.dilate(fg, None, iterations=1)

        # Intensidad: % de pixeles activos
        motion = float(np.mean(fg > 0))  # 0..1

        # Suavizado EMA para que no “tiemble”
        self._ema = (1 - self.smooth) * self._ema + self.smooth * motion

        return self._ema, fg
