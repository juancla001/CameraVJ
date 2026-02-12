import config
from capture.camera import CameraCapture
from pipeline.runner import PipelineRunner


def main():
    cam = CameraCapture(config.CAMERA_INDEX, config.CAPTURE_BACKEND).open()
    runner = PipelineRunner(cam)
    try:
        runner.run()
    finally:
        cam.release()


if __name__ == "__main__":
    main()
