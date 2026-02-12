import threading
import numpy as np

try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False


class AudioCapture:
    """Non-blocking mic capture using sounddevice callback."""

    def __init__(self, sample_rate=44100, block_size=1024, channels=1):
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.channels = channels

        self._buffer = np.zeros(block_size, dtype=np.float32)
        self._lock = threading.Lock()
        self._stream = None
        self._running = False

    def start(self):
        if not HAS_SOUNDDEVICE:
            print("[audio] sounddevice not installed, skipping audio capture")
            return False

        try:
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                blocksize=self.block_size,
                channels=self.channels,
                dtype="float32",
                callback=self._callback,
            )
            self._stream.start()
            self._running = True
            return True
        except Exception as e:
            print(f"[audio] Failed to open mic: {e}")
            return False

    def _callback(self, indata, frames, time_info, status):
        # indata shape: (frames, channels) - take mono
        with self._lock:
            self._buffer = indata[:, 0].copy()

    def get_buffer(self):
        with self._lock:
            return self._buffer.copy()

    def stop(self):
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        self._running = False

    @property
    def is_running(self):
        return self._running
