import os
import time
import cv2
import config

from vision.motion import MotionEstimator
from vision.zones import ZoneMapper
from vision.pose import PoseEstimator, NeonSkeletonRenderer, detect_gestures
from effects import EFFECTS_FACTORY
from audio import AudioManager
from midi import MidiController
from autovj import AutoVJManager
from output import VirtualCamOutput, VideoRecorder
from scenes import SceneManager


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

        self.show_hud = config.SHOW_HUD_DEFAULT
        self.perf_mode = config.PERF_MODE_DEFAULT
        self.fullscreen = False

        # --- Effect Stack ---
        self.effect_stack = []       # list of (effect_id, Effect instance)
        self.active_idx = 0          # index into effect_stack for preset control
        self.preset_idx = 0
        self.fx_page = 0             # 0=effects 1-12, 1=effects 13-20

        # --- Effect instance cache (avoid recreating on toggle) ---
        self._effect_cache = {}

        # --- Movimiento + Zonas ---
        self.motion = MotionEstimator(
            scale=config.MOTION_SCALE,
            smooth=config.MOTION_SMOOTH
        )
        self.zones = ZoneMapper()
        self.show_vision_debug = False

        # --- Pose ---
        self.pose_enabled = False
        self.pose = PoseEstimator(model_complexity=1)
        self.neon = NeonSkeletonRenderer(trail_len=14, glow=2)
        self._gesture_cooldown = 0

        # --- Audio ---
        self.audio = AudioManager()

        # --- MIDI ---
        self.midi = MidiController()
        self._midi_fader = 1.0  # global mix (1.0 = full effect)

        # --- Auto-VJ ---
        self.autovj = AutoVJManager()

        # --- Output ---
        self.vcam = VirtualCamOutput()
        self.recorder = VideoRecorder()

        # --- Scenes ---
        self.scene_mgr = SceneManager()

        # --- FPS counter ---
        self._fps_time = time.time()
        self._fps_count = 0
        self._fps = 0.0

        self._ensure_output_dir()

    def _ensure_output_dir(self):
        os.makedirs("output", exist_ok=True)

    # -------- Effect Stack Management --------

    def _get_effect(self, effect_id):
        """Get or create cached effect instance."""
        if effect_id not in self._effect_cache:
            EffectCls = EFFECTS_FACTORY.get(effect_id)
            if EffectCls is None:
                return None
            self._effect_cache[effect_id] = EffectCls()
        return self._effect_cache[effect_id]

    def _toggle_effect(self, effect_id):
        """Add effect to stack if not present, remove if present."""
        # Check if already in stack
        for i, (eid, _) in enumerate(self.effect_stack):
            if eid == effect_id:
                self.effect_stack.pop(i)
                # Adjust active_idx
                if self.active_idx >= len(self.effect_stack):
                    self.active_idx = max(0, len(self.effect_stack) - 1)
                return

        # Add if under max
        if len(self.effect_stack) >= config.EFFECT_STACK_MAX:
            return

        effect = self._get_effect(effect_id)
        if effect is not None:
            self.effect_stack.append((effect_id, effect))
            self.active_idx = len(self.effect_stack) - 1
            self.preset_idx = 0

    def _set_single_effect(self, effect_id):
        """Clear stack and set a single effect (legacy mode)."""
        self._clear_effects()
        if effect_id == 0:
            return
        effect = self._get_effect(effect_id)
        if effect is not None:
            self.effect_stack.append((effect_id, effect))
            self.active_idx = 0
            self.preset_idx = 0

    def _clear_effects(self):
        """Remove all effects from stack."""
        self.effect_stack.clear()
        self.active_idx = 0
        self.preset_idx = 0

    def _reset_active_effect(self):
        """Reset the currently active effect."""
        if self.effect_stack and self.active_idx < len(self.effect_stack):
            self.effect_stack[self.active_idx][1].reset()

    def _active_effect(self):
        """Get the active effect (for preset changes)."""
        if not self.effect_stack or self.active_idx >= len(self.effect_stack):
            return None, 0
        eid, effect = self.effect_stack[self.active_idx]
        return effect, eid

    def _stack_ids(self):
        """Return list of effect IDs in stack."""
        return [eid for eid, _ in self.effect_stack]

    def _stack_names(self):
        """Return formatted stack string."""
        if not self.effect_stack:
            return "bypass"
        parts = []
        for i, (eid, effect) in enumerate(self.effect_stack):
            name = getattr(effect, "name", str(eid))
            marker = ">" if i == self.active_idx else " "
            parts.append(f"{marker}{eid}:{name}")
        return " | ".join(parts)

    def _screenshot(self, frame):
        ts = time.strftime("%Y%m%d-%H%M%S")
        path = os.path.join("output", f"snap-{ts}.png")
        cv2.imwrite(path, frame)
        if not self.perf_mode:
            print(f"[screenshot] {path}")

    def _current_scale(self):
        return config.PREVIEW_SCALE_PERF if self.perf_mode else config.PREVIEW_SCALE_DEBUG

    # -------- Presets (applied to active effect) --------
    def _apply_preset(self, idx):
        self.preset_idx = max(0, min(2, idx))
        effect, eid = self._active_effect()
        if effect is None:
            return

        name = getattr(effect, "name", "")

        if name == "color_posterize":
            if self.preset_idx == 0:
                effect.levels, effect.speed = 6, 0.03
            elif self.preset_idx == 1:
                effect.levels, effect.speed = 4, 0.06
            else:
                effect.levels, effect.speed = 10, 0.02

        elif name == "contours_glow":
            if self.preset_idx == 0:
                effect.t1, effect.t2, effect.blur_ksize = 50, 150, 9
            elif self.preset_idx == 1:
                effect.t1, effect.t2, effect.blur_ksize = 30, 100, 13
            else:
                effect.t1, effect.t2, effect.blur_ksize = 80, 200, 7

        elif name == "feedback_glitch":
            if self.preset_idx == 0:
                effect.feedback, effect.warp, effect.noise = 0.90, 4, 4
            elif self.preset_idx == 1:
                effect.feedback, effect.warp, effect.noise = 0.94, 7, 8
            else:
                effect.feedback, effect.warp, effect.noise = 0.88, 10, 12

        elif name == "mirror_kaleido":
            effect.mode = self.preset_idx

        elif name == "scanlines_rgbshift":
            if self.preset_idx == 0:
                effect.scan_strength, effect.shift, effect.speed = 0.20, 3, 1
            elif self.preset_idx == 1:
                effect.scan_strength, effect.shift, effect.speed = 0.35, 6, 2
            else:
                effect.scan_strength, effect.shift, effect.speed = 0.15, 10, 3

        elif name == "chromatic_aberration":
            if self.preset_idx == 0:
                effect.strength, effect.radial = 8, True
            elif self.preset_idx == 1:
                effect.strength, effect.radial = 16, True
            else:
                effect.strength, effect.radial = 12, False

        elif name == "pixel_sort":
            if self.preset_idx == 0:
                effect.threshold, effect.intensity, effect._step = 80, 0.5, 4
            elif self.preset_idx == 1:
                effect.threshold, effect.intensity, effect._step = 40, 0.8, 2
            else:
                effect.threshold, effect.intensity, effect._step = 120, 0.4, 6

        elif name == "thermal_vision":
            effect._map_idx = self.preset_idx % 3
            effect.colormap = effect._colormaps[effect._map_idx]

        elif name == "strobe_flash":
            if self.preset_idx == 0:
                effect.rate, effect.intensity, effect.color_mode = 6, 0.8, 0
            elif self.preset_idx == 1:
                effect.rate, effect.intensity, effect.color_mode = 3, 1.0, 0
            else:
                effect.rate, effect.intensity, effect.color_mode = 4, 0.9, 1

        elif name == "edge_neon":
            if self.preset_idx == 0:
                effect.t1, effect.t2, effect.hue_speed, effect.glow_size = 40, 120, 2.0, 5
            elif self.preset_idx == 1:
                effect.t1, effect.t2, effect.hue_speed, effect.glow_size = 20, 80, 4.0, 8
            else:
                effect.t1, effect.t2, effect.hue_speed, effect.glow_size = 60, 160, 1.0, 3

        elif name == "vhs_retro":
            if self.preset_idx == 0:
                effect.tracking_intensity, effect.color_bleed, effect.noise_amount = 0.3, 4, 12
            elif self.preset_idx == 1:
                effect.tracking_intensity, effect.color_bleed, effect.noise_amount = 0.7, 8, 25
            else:
                effect.tracking_intensity, effect.color_bleed, effect.noise_amount = 0.15, 2, 6

        elif name == "glitch_blocks":
            if self.preset_idx == 0:
                effect.block_count, effect.max_shift, effect.intensity = 8, 30, 0.5
            elif self.preset_idx == 1:
                effect.block_count, effect.max_shift, effect.intensity = 16, 60, 0.8
            else:
                effect.block_count, effect.max_shift, effect.intensity = 4, 15, 0.3

        elif name == "ascii_art":
            if self.preset_idx == 0:
                effect.cell_size, effect.colored = 8, True
            elif self.preset_idx == 1:
                effect.cell_size, effect.colored = 5, True
            else:
                effect.cell_size, effect.colored = 8, False

        elif name == "datamosh":
            if self.preset_idx == 0:
                effect.corruption, effect.intensity, effect.block_size = 0.3, 0.7, 16
            elif self.preset_idx == 1:
                effect.corruption, effect.intensity, effect.block_size = 0.6, 0.9, 8
            else:
                effect.corruption, effect.intensity, effect.block_size = 0.15, 0.5, 24

        elif name == "zoom_pulse":
            if self.preset_idx == 0:
                effect.amplitude, effect.speed = 0.08, 0.12
            elif self.preset_idx == 1:
                effect.amplitude, effect.speed = 0.20, 0.20
            else:
                effect.amplitude, effect.speed = 0.04, 0.06

        elif name == "duotone":
            effect.palette_idx = self.preset_idx % len(effect.PALETTES)

        elif name == "slit_scan":
            if self.preset_idx == 0:
                effect.buffer_size, effect.spread = 30, 1.0
            elif self.preset_idx == 1:
                effect.buffer_size, effect.spread = 50, 2.0
            else:
                effect.buffer_size, effect.spread = 15, 0.5

    # -------- FPS --------
    def _update_fps(self):
        self._fps_count += 1
        now = time.time()
        elapsed = now - self._fps_time
        if elapsed >= 1.0:
            self._fps = self._fps_count / elapsed
            self._fps_count = 0
            self._fps_time = now

    # -------- Main Loop --------
    def run(self):
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

            # --- Audio ---
            audio_controls = self.audio.update()

            controls = {"motion": m, "zones": zone_vals}
            controls.update(audio_controls)

            # --- MIDI poll ---
            self.midi.poll(self)

            # --- Auto-VJ ---
            if self.autovj.enabled:
                pre_change_frame = None
                old_stack = self._stack_ids()
                self.autovj.update(self, controls)
                if self._stack_ids() != old_stack:
                    self.autovj.start_crossfade(frame)

            # --- Apply effect stack ---
            out = frame
            for _, effect in self.effect_stack:
                try:
                    effect.set_controls(controls)
                except Exception:
                    pass
                out = effect.apply(out)

            # --- Auto-VJ crossfade ---
            if self.autovj.enabled:
                out = self.autovj.apply_crossfade(out)

            # --- MIDI fader: global mix (original vs processed) ---
            if self._midi_fader < 0.99 and self.effect_stack:
                out = cv2.addWeighted(frame, 1.0 - self._midi_fader, out, self._midi_fader, 0)

            # --- Pose overlay ---
            if self.pose_enabled:
                out = self.neon.render(out, pose_data)

            if self._gesture_cooldown > 0:
                self._gesture_cooldown -= 1

            if self.pose_enabled and gestures["hands_up"] and self._gesture_cooldown == 0:
                self._apply_preset(self.preset_idx + 1)
                self._gesture_cooldown = 20

            # --- FPS ---
            self._update_fps()

            # --- HUD ---
            if self.show_hud and not self.perf_mode:
                bars = (
                    f"L:{zone_vals['left']:.2f} R:{zone_vals['right']:.2f} "
                    f"T:{zone_vals['top']:.2f} B:{zone_vals['bottom']:.2f}"
                )
                audio_str = ""
                if self.audio.enabled:
                    ac = audio_controls
                    audio_str = (
                        f" | Beat:{ac['beat']:.0f} E:{ac['energy']:.2f}"
                        f" B:{ac['bass']:.2f} M:{ac['mid']:.2f} H:{ac['high']:.2f}"
                    )
                out = _apply_hud(out, [
                    f"FPS: {self._fps:.1f} | Stack: [{','.join(str(e) for e in self._stack_ids())}]",
                    f"Active: {self._stack_names()}",
                    f"Preset: {self.preset_idx} | Motion: {m:.2f} | Pose: {self.pose_enabled} | Audio: {self.audio.enabled} | MIDI: {self.midi.enabled} | AutoVJ: {self.autovj.enabled}{audio_str}",
                    f"VCam: {self.vcam.enabled} | Rec: {self.recorder.enabled} | Page: {self.fx_page} ({self.fx_page*12+1}-{self.fx_page*12+12}) | {bars}",
                    "1-9-=\\ fx | n page | 0 clr | [] pst | TAB cyc | c vcam | w rec | F1-8/!-* scene | a m x g f h q",
                ])

            # --- Virtual cam + Recorder (clean frame, no HUD/FPS overlay) ---
            if self.vcam.enabled:
                self.vcam.send(out)
            if self.recorder.enabled:
                self.recorder.write(out)

            # --- FPS overlay (always visible) ---
            cv2.putText(out, f"{self._fps:.0f}", (out.shape[1] - 60, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA)

            # --- Scaling ---
            scale = self._current_scale()
            if scale != 1.0:
                h, w = out.shape[:2]
                out = cv2.resize(out, (int(w * scale), int(h * scale)))

            cv2.imshow(config.WINDOW_NAME, out)

            if self.show_vision_debug and not self.perf_mode:
                cv2.imshow("MotionMask (debug)", motion_mask)

            raw_key = cv2.waitKeyEx(1)
            key = raw_key & 0xFF

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

            # Effect page toggle: n
            elif key == ord("n"):
                self.fx_page = 1 - self.fx_page
                if not self.perf_mode:
                    print(f"[fx_page] {self.fx_page} (effects {self.fx_page*12+1}-{self.fx_page*12+12})")

            # Effect toggle: 1-9 (page-aware)
            elif ord("1") <= key <= ord("9"):
                effect_id = key - ord("0") + self.fx_page * 12
                if effect_id in EFFECTS_FACTORY:
                    self._toggle_effect(effect_id)

            # Effects 10-12 on current page: - = \
            elif key == ord("-"):
                eid = 10 + self.fx_page * 12
                if eid in EFFECTS_FACTORY:
                    self._toggle_effect(eid)
            elif key == ord("="):
                eid = 11 + self.fx_page * 12
                if eid in EFFECTS_FACTORY:
                    self._toggle_effect(eid)
            elif key == ord("\\"):
                eid = 12 + self.fx_page * 12
                if eid in EFFECTS_FACTORY:
                    self._toggle_effect(eid)

            # Clear effects: 0
            elif key == ord("0"):
                self._clear_effects()

            # Cycle active effect in stack: TAB
            elif key == 9:  # TAB
                if self.effect_stack:
                    self.active_idx = (self.active_idx + 1) % len(self.effect_stack)
                    self.preset_idx = 0

            # Presets for active effect
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

            elif key == ord("a"):
                self.audio.toggle()
            elif key == ord("m"):
                self.midi.toggle()
            elif key == ord("x"):
                self.autovj.toggle()
            elif key == ord("c"):
                self.vcam.toggle()
            elif key == ord("w"):
                self.recorder.toggle(frame_size=frame.shape[:2])

            elif key == ord("r"):
                self._reset_active_effect()
            elif key == ord("s"):
                self._screenshot(out)

            # Scene load: F1-F8 (OpenCV waitKeyEx codes on Windows)
            elif 0x700000 <= raw_key <= 0x700007:
                self.scene_mgr.load_scene(raw_key - 0x700000 + 1, self)
            # Scene save: Shift+1-8 (!@#$%^&*)
            elif key in (ord("!"), ord("@"), ord("#"), ord("$"), ord("%"), ord("^"), ord("&"), ord("*")):
                save_map = {"!": 1, "@": 2, "#": 3, "$": 4, "%": 5, "^": 6, "&": 7, "*": 8}
                slot = save_map.get(chr(key), 0)
                if slot:
                    self.scene_mgr.save_scene(slot, self)

        # Cleanup
        self.vcam.stop()
        self.recorder.stop()
        self.audio.stop()
        self.midi.stop()
        cv2.destroyAllWindows()
