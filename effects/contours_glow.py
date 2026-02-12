import cv2
import numpy as np
from .base import Effect


class ContoursGlow(Effect):
    name = "contours_glow"

    def __init__(self, edge_threshold1=50, edge_threshold2=150, blur_ksize=9):
        self.t1 = int(edge_threshold1)
        self.t2 = int(edge_threshold2)
        self.blur_ksize = int(blur_ksize) if int(blur_ksize) % 2 == 1 else int(blur_ksize) + 1

    def apply(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, self.t1, self.t2)

        # “Glow” barato: dilate + blur sobre bordes
        edges_d = cv2.dilate(edges, None, iterations=1)
        glow = cv2.GaussianBlur(edges_d, (self.blur_ksize, self.blur_ksize), 0)

        # Convertimos a BGR
        glow_bgr = cv2.cvtColor(glow, cv2.COLOR_GRAY2BGR)

        # Mezcla aditiva suave (clip)
        out = cv2.addWeighted(frame, 1.0, glow_bgr, 0.8, 0.0)
        return out

    def set_controls(self, controls: dict):
        m = float(controls.get("motion", 0.0))
        self.t1 = int(60 - 30 * m)
        self.t2 = int(180 - 80 * m)
        k = int(9 + 8 * m)
        self.blur_ksize = k if k % 2 == 1 else k + 1
