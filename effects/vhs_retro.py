import cv2
import numpy as np
from .base import Effect


class VHSRetro(Effect):
    name = "vhs_retro"

    def __init__(self):
        self.tracking_intensity = 0.3
        self.color_bleed = 4
        self.noise_amount = 12
        self.t = 0

    def reset(self):
        self.t = 0

    def apply(self, frame):
        self.t += 1
        h, w = frame.shape[:2]
        out = frame.copy()

        # 1. Color bleed: shift chroma channels
        ycrcb = cv2.cvtColor(out, cv2.COLOR_BGR2YCrCb)
        y, cr, cb = cv2.split(ycrcb)
        shift = self.color_bleed
        cr = np.roll(cr, shift, axis=1)
        cb = np.roll(cb, -shift, axis=1)
        out = cv2.cvtColor(cv2.merge([y, cr, cb]), cv2.COLOR_YCrCb2BGR)

        # 2. Tracking lines (horizontal distortion bands)
        if self.tracking_intensity > 0:
            num_lines = max(1, int(3 * self.tracking_intensity))
            for _ in range(num_lines):
                line_y = (self.t * 3 + np.random.randint(0, h)) % h
                line_h = np.random.randint(1, 4)
                end_y = min(line_y + line_h, h)
                shift_px = np.random.randint(-8, 9)
                out[line_y:end_y] = np.roll(out[line_y:end_y], shift_px, axis=1)

        # 3. Scanline darkening (every other line, subtle)
        out[::2] = (out[::2].astype(np.float32) * 0.85).clip(0, 255).astype(np.uint8)

        # 4. Noise
        if self.noise_amount > 0:
            noise = np.random.randint(
                0, self.noise_amount, (h, w, 1), dtype=np.uint8
            )
            noise = np.repeat(noise, 3, axis=2)
            out = cv2.add(out, noise)

        # 5. Slight desaturation for retro look
        out = cv2.addWeighted(
            out, 0.85,
            cv2.cvtColor(cv2.cvtColor(out, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR),
            0.15, 0
        )

        # 6. Bottom "timestamp" bar flicker
        if self.t % 4 < 3:
            bar_y = h - 20
            out[bar_y:, :] = np.clip(
                out[bar_y:, :].astype(np.int16) - 40, 0, 255
            ).astype(np.uint8)

        return out

    def set_controls(self, controls: dict):
        m = float(controls.get("motion", 0.0))
        zones = controls.get("zones", {})
        bottom = float(zones.get("bottom", 0.0))

        self.tracking_intensity = 0.1 + 0.8 * m
        self.color_bleed = int(2 + 10 * m)
        self.noise_amount = int(6 + 30 * m)
