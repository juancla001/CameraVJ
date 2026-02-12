import numpy as np


class BeatDetector:
    """Energy-based beat detection using RMS over a moving average."""

    def __init__(self, history_len=43, threshold_mult=1.4):
        self.history_len = history_len  # ~1 sec at 44100/1024
        self.threshold_mult = threshold_mult
        self._energy_history = []
        self._beat = False
        self._cooldown = 0
        self._cooldown_max = 8  # frames between beats

    def update(self, audio_buffer):
        """Process audio buffer and return (is_beat, energy)."""
        # RMS energy
        energy = float(np.sqrt(np.mean(audio_buffer ** 2)))

        self._energy_history.append(energy)
        if len(self._energy_history) > self.history_len:
            self._energy_history.pop(0)

        # Beat = energy significantly above moving average
        avg = np.mean(self._energy_history) if self._energy_history else 0.0

        if self._cooldown > 0:
            self._cooldown -= 1
            self._beat = False
        elif energy > avg * self.threshold_mult and energy > 0.01:
            self._beat = True
            self._cooldown = self._cooldown_max
        else:
            self._beat = False

        return self._beat, energy

    @property
    def is_beat(self):
        return self._beat
