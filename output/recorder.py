import os
import time
import cv2


class VideoRecorder:
    """Record processed video output to file."""

    def __init__(self, output_dir="output", codec="mp4v", fps=30.0):
        self.output_dir = output_dir
        self.codec = codec
        self.fps = fps
        self._writer = None
        self._enabled = False
        self._filepath = None
        self._frame_count = 0

    @property
    def enabled(self):
        return self._enabled

    def toggle(self, frame_size=None):
        """Toggle recording on/off. Pass current frame size when starting."""
        if self._enabled:
            self.stop()
        else:
            if frame_size:
                self.start(frame_size[1], frame_size[0])
            else:
                print("[rec] Need frame size to start recording")
        return self._enabled

    def start(self, width, height):
        os.makedirs(self.output_dir, exist_ok=True)
        ts = time.strftime("%Y%m%d-%H%M%S")
        self._filepath = os.path.join(self.output_dir, f"rec-{ts}.mp4")

        fourcc = cv2.VideoWriter_fourcc(*self.codec)
        self._writer = cv2.VideoWriter(self._filepath, fourcc, self.fps, (width, height))

        if self._writer.isOpened():
            self._enabled = True
            self._frame_count = 0
            print(f"[rec] recording to {self._filepath}")
            return True
        else:
            print("[rec] Failed to open video writer")
            self._writer = None
            return False

    def write(self, frame):
        """Write a frame to the recording."""
        if not self._enabled or self._writer is None:
            return
        self._writer.write(frame)
        self._frame_count += 1

    def stop(self):
        if self._writer is not None:
            self._writer.release()
            self._writer = None
        if self._enabled:
            duration = self._frame_count / max(1, self.fps)
            print(f"[rec] saved {self._filepath} ({self._frame_count} frames, {duration:.1f}s)")
        self._enabled = False
        self._filepath = None
        self._frame_count = 0
