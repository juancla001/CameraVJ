import cv2
import config


_BACKENDS = {
    "DSHOW": cv2.CAP_DSHOW,
    "MSMF": cv2.CAP_MSMF,
}


class CameraCapture:
    def __init__(self, index: int, backend_name: str):
        backend = _BACKENDS.get(backend_name.upper(), 0)
        self.cap = cv2.VideoCapture(index, backend)

    def open(self):
        if not self.cap.isOpened():
            raise RuntimeError("No pude abrir la webcam. Probá otro CAMERA_INDEX o CAPTURE_BACKEND.")
        return self

    def read(self):
        return self.cap.read()

    def release(self):
        if self.cap:
            self.cap.release()
            self.cap = None
