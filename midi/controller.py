from .input import MidiInput, HAS_MIDO
from .mapper import K2State


class MidiController:
    """High-level MIDI controller interface for CameraVJ.

    K2 Mapping:
    - Pads 1-12: Toggle effects 1-12
    - Pad 13: Clear stack
    - Pad 14: Toggle Auto-VJ (placeholder)
    - Pad 15: Toggle Audio
    - Pad 16: Toggle Pose
    - Knobs 1-4: Params of active effect (dynamic)
    - Knobs 5-8: motion_gain, deadzone, preset, reserved
    - Fader: Global intensity (mix original/processed)
    """

    def __init__(self):
        self.input = MidiInput()
        self.state = K2State()
        self._enabled = False
        self._available = HAS_MIDO

    @property
    def available(self):
        return self._available

    @property
    def enabled(self):
        return self._enabled

    def toggle(self):
        if self._enabled:
            self.stop()
        else:
            self.start()
        return self._enabled

    def start(self):
        if not self._available:
            print("[midi] mido not installed. Install with: pip install mido python-rtmidi")
            return False
        if self._enabled:
            return True
        ok = self.input.start()
        self._enabled = ok
        return ok

    def stop(self):
        self.input.stop()
        self._enabled = False
        print("[midi] disabled")

    def poll(self, runner):
        """Poll MIDI messages and apply to runner.

        Args:
            runner: PipelineRunner instance to control
        """
        if not self._enabled:
            return

        msgs = self.input.poll()
        for msg in msgs:
            event = self.state.process_message(msg)
            if event is None:
                continue

            self._handle_event(event, runner)

    def _handle_event(self, event, runner):
        etype = event[0]

        if etype == "pad":
            pad_num = event[1]
            self._handle_pad(pad_num, runner)

        elif etype == "knob":
            knob_idx = event[1]
            value = event[2]
            self._handle_knob(knob_idx, value, runner)

        elif etype == "fader":
            value = event[1]
            self._handle_fader(value, runner)

    def _handle_pad(self, pad_num, runner):
        from effects import EFFECTS_FACTORY

        if 1 <= pad_num <= 12:
            # Toggle effect
            if pad_num in EFFECTS_FACTORY:
                runner._toggle_effect(pad_num)

        elif pad_num == 13:
            runner._clear_effects()

        elif pad_num == 14:
            # Auto-VJ toggle (placeholder for FASE 6)
            pass

        elif pad_num == 15:
            runner.audio.toggle()

        elif pad_num == 16:
            runner.pose_enabled = not runner.pose_enabled

    def _handle_knob(self, knob_idx, value, runner):
        import config

        if knob_idx <= 3:
            # Knobs 1-4: active effect params
            self._map_knob_to_effect(knob_idx, value, runner)

        elif knob_idx == 4:
            # Knob 5: motion gain (1.0 - 5.0)
            config.MOTION_GAIN = 1.0 + 4.0 * value

        elif knob_idx == 5:
            # Knob 6: motion deadzone (0.0 - 0.1)
            config.MOTION_DEADZONE = 0.1 * value

        elif knob_idx == 6:
            # Knob 7: preset select (0, 1, 2)
            preset = int(value * 2.99)
            runner._apply_preset(preset)

    def _handle_fader(self, value, runner):
        # Store fader value for global mix (used in runner)
        runner._midi_fader = value

    def _map_knob_to_effect(self, knob_idx, value, runner):
        """Map knobs 1-4 to active effect parameters dynamically."""
        effect, eid = runner._active_effect()
        if effect is None:
            return

        name = getattr(effect, "name", "")

        # Each effect gets its own knob mapping
        if name == "color_posterize":
            if knob_idx == 0:
                effect.levels = int(2 + 14 * value)
            elif knob_idx == 1:
                effect.speed = 0.01 + 0.15 * value

        elif name == "feedback_glitch":
            if knob_idx == 0:
                effect.feedback = 0.80 + 0.18 * value
            elif knob_idx == 1:
                effect.warp = int(1 + 20 * value)
            elif knob_idx == 2:
                effect.noise = int(1 + 30 * value)

        elif name == "contours_glow":
            if knob_idx == 0:
                effect.t1 = int(10 + 90 * value)
            elif knob_idx == 1:
                effect.t2 = int(50 + 200 * value)
            elif knob_idx == 2:
                k = int(3 + 20 * value)
                effect.blur_ksize = k if k % 2 == 1 else k + 1

        elif name == "scanlines_rgbshift":
            if knob_idx == 0:
                effect.scan_strength = 0.05 + 0.50 * value
            elif knob_idx == 1:
                effect.shift = int(1 + 20 * value)
            elif knob_idx == 2:
                effect.speed = int(1 + 5 * value)

        elif name == "chromatic_aberration":
            if knob_idx == 0:
                effect.strength = int(2 + 30 * value)

        elif name == "pixel_sort":
            if knob_idx == 0:
                effect.threshold = int(20 + 200 * value)
            elif knob_idx == 1:
                effect.intensity = value

        elif name == "strobe_flash":
            if knob_idx == 0:
                effect.rate = max(1, int(1 + 12 * (1.0 - value)))
            elif knob_idx == 1:
                effect.intensity = 0.2 + 0.8 * value
            elif knob_idx == 2:
                effect.color_mode = 1 if value > 0.5 else 0

        elif name == "edge_neon":
            if knob_idx == 0:
                effect.hue_speed = 0.5 + 8.0 * value
            elif knob_idx == 1:
                effect.glow_size = int(1 + 12 * value)

        elif name == "vhs_retro":
            if knob_idx == 0:
                effect.tracking_intensity = value
            elif knob_idx == 1:
                effect.color_bleed = int(1 + 15 * value)
            elif knob_idx == 2:
                effect.noise_amount = int(2 + 40 * value)

        elif name == "motion_trails":
            if knob_idx == 0:
                effect.persist = 0.70 + 0.28 * value
            elif knob_idx == 1:
                effect.glow = 0.5 * value

        elif name == "thermal_vision":
            if knob_idx == 0:
                effect.contrast = 0.8 + 1.5 * value
            elif knob_idx == 1:
                effect._map_idx = int(value * 2.99)
                effect.colormap = effect._colormaps[effect._map_idx]
