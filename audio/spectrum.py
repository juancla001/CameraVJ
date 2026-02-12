import numpy as np


class SpectrumAnalyzer:
    """FFT-based 3-band frequency analysis: bass, mid, high."""

    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.bass = 0.0    # 20-250 Hz
        self.mid = 0.0     # 250-2000 Hz
        self.high = 0.0    # 2000-8000 Hz

    def update(self, audio_buffer):
        """Compute FFT and extract 3 band energies (normalized 0-1)."""
        n = len(audio_buffer)
        if n < 64:
            self.bass = self.mid = self.high = 0.0
            return

        # Apply window to reduce spectral leakage
        windowed = audio_buffer * np.hanning(n)
        fft = np.abs(np.fft.rfft(windowed))
        freqs = np.fft.rfftfreq(n, d=1.0 / self.sample_rate)

        # Band energy (mean magnitude in range)
        self.bass = self._band_energy(fft, freqs, 20, 250)
        self.mid = self._band_energy(fft, freqs, 250, 2000)
        self.high = self._band_energy(fft, freqs, 2000, 8000)

    def _band_energy(self, fft, freqs, lo, hi):
        mask = (freqs >= lo) & (freqs <= hi)
        if not np.any(mask):
            return 0.0
        energy = float(np.mean(fft[mask]))
        # Normalize roughly to 0-1 range (energy is typically 0-0.5 for speech/music)
        return min(1.0, energy * 4.0)

    def get_bands(self):
        return {"bass": self.bass, "mid": self.mid, "high": self.high}
