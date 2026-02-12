import time
from .sequencer import Sequencer
from .transitions import CrossfadeTransition


class AutoVJManager:
    """Automatic effect sequencing based on combined energy.

    Combines motion and audio energy to determine intensity level,
    then selects appropriate effects from pools with crossfade transitions.
    """

    def __init__(self, interval=8.0, crossfade_frames=30):
        self.interval = interval  # seconds between effect changes
        self.crossfade = CrossfadeTransition(duration_frames=crossfade_frames)
        self.sequencer = Sequencer()
        self._enabled = False
        self._last_change = 0.0
        self._energy_smooth = 0.0

    @property
    def enabled(self):
        return self._enabled

    def toggle(self):
        self._enabled = not self._enabled
        if self._enabled:
            self._last_change = 0.0  # trigger immediate change
            print("[autovj] enabled")
        else:
            print("[autovj] disabled")
        return self._enabled

    def update(self, runner, controls):
        """Called once per frame. May trigger effect changes.

        Args:
            runner: PipelineRunner instance
            controls: Current controls dict with motion, audio data
        """
        if not self._enabled:
            return

        # Compute combined energy
        motion = float(controls.get("motion", 0.0))
        audio_energy = float(controls.get("energy", 0.0))
        bass = float(controls.get("bass", 0.0))

        raw_energy = motion * 0.5 + audio_energy * 0.3 + bass * 0.2
        # Smooth it
        self._energy_smooth = self._energy_smooth * 0.9 + raw_energy * 0.1

        now = time.time()
        elapsed = now - self._last_change

        # Change effects when interval elapses, or on strong beat
        beat = float(controls.get("beat", 0.0))
        force_change = beat > 0.5 and elapsed > self.interval * 0.5

        if elapsed >= self.interval or force_change:
            self._change_effects(runner)
            self._last_change = now

    def _change_effects(self, runner):
        """Select new effects and apply with crossfade."""
        # Capture current frame for crossfade (will be applied in runner)
        new_ids = self.sequencer.select(self._energy_smooth)

        # Clear and set new effects
        runner._clear_effects()
        for eid in new_ids:
            runner._toggle_effect(eid)

    def apply_crossfade(self, frame):
        """Apply crossfade transition if active."""
        return self.crossfade.apply(frame)

    def start_crossfade(self, frame):
        """Start crossfade from current frame."""
        self.crossfade.start(frame)
