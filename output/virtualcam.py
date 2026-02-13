import cv2

try:
    import pyvirtualcam
    HAS_VCAM = True
except ImportError:
    HAS_VCAM = False


class VirtualCamOutput:
    """Send processed frames to a virtual camera for OBS/projector."""

    def __init__(self, width=1280, height=720, fps=30):
        self.width = width
        self.height = height
        self.fps = fps
        self._cam = None
        self._enabled = False
        self._available = HAS_VCAM

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
            print("[vcam] pyvirtualcam not installed. Install with: pip install pyvirtualcam")
            print("[vcam] Also install OBS Virtual Camera or similar virtual cam driver")
            return False
        if self._enabled:
            return True

        try:
            self._cam = pyvirtualcam.Camera(
                width=self.width,
                height=self.height,
                fps=self.fps,
            )
            self._enabled = True
            print(f"[vcam] enabled ({self.width}x{self.height}@{self.fps} via {self._cam.device})")
            return True
        except Exception as e:
            print(f"[vcam] Failed to start: {e}")
            print("[vcam] Make sure OBS Virtual Camera or another virtual cam driver is installed")
            return False

    def send(self, frame):
        """Send a BGR frame to the virtual camera."""
        if not self._enabled or self._cam is None:
            return

        # Resize if needed
        h, w = frame.shape[:2]
        if w != self.width or h != self.height:
            frame = cv2.resize(frame, (self.width, self.height))

        # Convert BGR to RGB (pyvirtualcam expects RGB)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self._cam.send(rgb)

    def stop(self):
        if self._cam is not None:
            self._cam.close()
            self._cam = None
        self._enabled = False
        print("[vcam] disabled")
