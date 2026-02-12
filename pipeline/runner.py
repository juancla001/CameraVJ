import os
import time
import cv2
import config

from vision.motion import MotionEstimator
from vision.zones import ZoneMapper
from vision.pose import PoseEstimator, NeonSkeletonRenderer, detect_gestures
from effects import EFFECTS_FACTORY


def _apply_hud(frame, lines):
    y = 30
    for line in lines:
        cv2.putText(
            frame,
            line,
            (20, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )
        y += 26
    return frame


class PipelineRunner:
    def __init__(self, capture):
        self.capture = capture
        self.effect_id = 0
        self.effect = None

        self.show_hud = config.SHOW_HUD_DEFAULT
        self.perf_mode = config.PERF_MODE_DEFAULT
        self.preset_idx = 0
        self.fullscreen = False

        # --- FASE 2: Movimiento + Zonas ---
        self.motion = MotionEstimator(
            scale=config.MOTION_SCALE,
            smooth=config.MOTION_SMOOTH
        )
        self.zones = ZoneMapper()
        self.show_vision_debug = False  # toggle con 'v'

        # --- FASE 3: Pose ---
        self.pose_enabled = False  # toggle con 'g'
        self.pose = PoseEstimator(model_complexity=1)
        self.neon = NeonSkeletonRenderer(trail_len=14, glow=2)
        self._gesture_cooldown = 0

        self._ensure_output_dir()
        self._set_effect(0)

    def _ensure_output_dir(self):
        os.makedirs("output", exist_ok=True)

    def _set_effect(self, effect_id: int):
        self.effect_id = effect_id
        if effect_id == 0:
            self.effect = None
            return

        EffectCls = EFFECTS_FACTORY.get(effect_id)
        self.effect = EffectCls() if EffectCls else None
        self.preset_idx = 0

    def _reset_effect(self):
        if self.effect is not None:
            self.effect.reset()

    def _screenshot(self, frame):
        ts = time.strftime("%Y%m%d-%H%M%S")
        path = os.path.join("output", f"snap-{ts}.png")
        cv2.imwrite(path, frame)
        if not self.perf_mode:
            print(f"[screenshot] {path}")

    def _current_scale(self):
        return config.PREVIEW_SCALE_PERF if self.perf_mode else config.PREVIEW_SCALE_DEBUG

    def _effect_name(self):
        if self.effect is None:
            return "bypass"
        return getattr(self.effect, "name", "effect")

    # -------- Presets --------
    def _apply_preset(self, idx: int):
        self.preset_idx = max(0, min(2, idx))
        e = self.effect
        if e is None:
            return

        name = getattr(e, "name", "")

        if name == "color_posterize":
            if self.preset_idx == 0:
                e.levels, e.speed = 6, 0.03
            elif self.preset_idx == 1:
                e.levels, e.speed = 4, 0.06
            else:
                e.levels, e.speed = 10, 0.02

        elif name == "contours_glow":
            if self.preset_idx == 0:
                e.t1, e.t2, e.blur_ksize = 50, 150, 9
            elif self.preset_idx == 1:
                e.t1, e.t2, e.blur_ksize = 30, 100, 13
            else:
                e.t1, e.t2, e.blur_ksize = 80, 200, 7

        elif name == "feedback_glitch":
            if self.preset_idx == 0:
                e.feedback, e.warp, e.noise = 0.90, 4, 4
            elif self.preset_idx == 1:
                e.feedback, e.warp, e.noise = 0.94, 7, 8
            else:
                e.feedback, e.warp, e.noise = 0.88, 10, 12

        elif name == "mirror_kaleido":
            e.mode = self.preset_idx

        elif name == "scanlines_rgbshift":
            if self.preset_idx == 0:
                e.scan_strength, e.shift, e.speed = 0.20, 3, 1
            elif self.preset_idx == 1:
                e.scan_strength, e.shift, e.speed = 0.35, 6, 2
            else:
                e.scan_strength, e.shift, e.speed = 0.15, 10, 3

    def run(self):
        self._apply_preset(0)

        # 🔹 Crear ventana UNA sola vez
        cv2.namedWindow(config.WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(config.WINDOW_NAME, 1280, 720)

        while True:
            ok, frame = self.capture.read()
            if not ok:
                break

            # --- Movimiento + Zonas ---
            motion_global, motion_mask = self.motion.update(frame)
            zone_vals = self.zones.compute(motion_mask)

            # --- Pose ---
            pose_data = None
            gestures = {"hands_up": False, "arms_open": False}

            if self.pose_enabled:
                pose_data = self.pose.update(frame)
                gestures = detect_gestures(pose_data)

            # Motion normalizado
            m = max(0.0, motion_global - config.MOTION_DEADZONE)
            m = min(1.0, m * config.MOTION_GAIN)

            if self.pose_enabled and gestures["arms_open"]:
                m = min(1.0, m + 0.35)

            controls = {"motion": m, "zones": zone_vals}

            if self.effect is not None:
                try:
                    self.effect.set_controls(controls)
                except Exception:
                    pass

            out = self.effect.apply(frame) if self.effect else frame

            if self.pose_enabled:
                out = self.neon.render(out, pose_data)

            if self._gesture_cooldown > 0:
                self._gesture_cooldown -= 1

            if self.pose_enabled and gestures["hands_up"] and self._gesture_cooldown == 0:
                self._apply_preset(self.preset_idx + 1)
                self._gesture_cooldown = 20

            # HUD
            if self.show_hud and not self.perf_mode:
                bars = (
                    f"L:{zone_vals['left']:.2f} R:{zone_vals['right']:.2f} "
                    f"T:{zone_vals['top']:.2f} B:{zone_vals['bottom']:.2f}"
                )
                out = _apply_hud(out, [
                    f"Effect: {self._effect_name()} (id {self.effect_id})",
                    f"Preset: {self.preset_idx}",
                    f"Motion: {m:.2f} | {bars} | Pose: {self.pose_enabled}",
                    "Keys: 0-6 | [ ] | g pose | f fullscreen | h HUD | p PERF | v mask | q quit",
                ])

            # Scaling
            scale = self._current_scale()
            if scale != 1.0:
                h, w = out.shape[:2]
                out = cv2.resize(out, (int(w * scale), int(h * scale)))

            cv2.imshow(config.WINDOW_NAME, out)

            if self.show_vision_debug and not self.perf_mode:
                cv2.imshow("MotionMask (debug)", motion_mask)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break

            elif key == ord("f"):
                self.fullscreen = not self.fullscreen
                cv2.setWindowProperty(
                    config.WINDOW_NAME,
                    cv2.WND_PROP_FULLSCREEN,
                    cv2.WINDOW_FULLSCREEN if self.fullscreen else cv2.WINDOW_NORMAL
                )

            elif key == ord("g"):
                self.pose_enabled = not self.pose_enabled
                if not self.perf_mode:
                    print(f"[pose] enabled={self.pose_enabled}")

            elif key in (ord("0"), ord("1"), ord("2"), ord("3"), ord("4"), ord("5"), ord("6")):
                self._set_effect(int(chr(key)))
                self._apply_preset(0)

            elif key == ord("["):
                self._apply_preset(self.preset_idx - 1)
            elif key == ord("]"):
                self._apply_preset(self.preset_idx + 1)

            elif key == ord("h"):
                self.show_hud = not self.show_hud
            elif key == ord("p"):
                self.perf_mode = not self.perf_mode
            elif key == ord("v"):
                self.show_vision_debug = not self.show_vision_debug

            elif key == ord("r"):
                self._reset_effect()
            elif key == ord("s"):
                self._screenshot(out)

        cv2.destroyAllWindows()
