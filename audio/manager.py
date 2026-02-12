from .capture import AudioCapture, HAS_SOUNDDEVICE
from .beat import BeatDetector
from .spectrum import SpectrumAnalyzer


class AudioManager:
    """Orchestrates audio capture, beat detection, and spectrum analysis.

    Exposes a controls dict ready to merge into effect controls:
    {
        "beat": 0.0 or 1.0,
        "energy": 0.0..1.0,
        "bass": 0.0..1.0,
        "mid": 0.0..1.0,
        "high": 0.0..1.0,
    }
    """

    def __init__(self, sample_rate=44100, block_size=1024):
        self.capture = AudioCapture(sample_rate=sample_rate, block_size=block_size)
        self.beat_detector = BeatDetector()
        self.spectrum = SpectrumAnalyzer(sample_rate=sample_rate)
        self._enabled = False
        self._available = HAS_SOUNDDEVICE

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
            print("[audio] sounddevice not installed. Install with: pip install sounddevice")
            return False
        if self._enabled:
            return True
        ok = self.capture.start()
        self._enabled = ok
        if ok:
            print("[audio] enabled")
        return ok

    def stop(self):
        self.capture.stop()
        self._enabled = False
        print("[audio] disabled")

    def update(self):
        """Call once per frame. Returns audio controls dict."""
        if not self._enabled:
            return self._empty_controls()

        buf = self.capture.get_buffer()

        is_beat, energy = self.beat_detector.update(buf)
        self.spectrum.update(buf)
        bands = self.spectrum.get_bands()

        return {
            "beat": 1.0 if is_beat else 0.0,
            "energy": min(1.0, energy * 5.0),
            "bass": bands["bass"],
            "mid": bands["mid"],
            "high": bands["high"],
        }

    def _empty_controls(self):
        return {
            "beat": 0.0,
            "energy": 0.0,
            "bass": 0.0,
            "mid": 0.0,
            "high": 0.0,
        }
