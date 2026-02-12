import cv2


class CrossfadeTransition:
    """Smooth crossfade between effect changes over N frames."""

    def __init__(self, duration_frames=30):
        self.duration = duration_frames
        self._progress = 0
        self._active = False
        self._old_frame = None

    def start(self, current_frame):
        """Begin crossfade from the current output."""
        self._old_frame = current_frame.copy()
        self._progress = 0
        self._active = True

    def apply(self, new_frame):
        """Blend old and new frames during transition.

        Returns:
            Blended frame if transitioning, or new_frame if done.
        """
        if not self._active:
            return new_frame

        self._progress += 1
        alpha = min(1.0, self._progress / max(1, self.duration))

        if self._old_frame is not None and self._old_frame.shape == new_frame.shape:
            out = cv2.addWeighted(self._old_frame, 1.0 - alpha, new_frame, alpha, 0)
        else:
            out = new_frame

        if alpha >= 1.0:
            self._active = False
            self._old_frame = None

        return out

    @property
    def is_active(self):
        return self._active
