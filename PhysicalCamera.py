import cv2

import numpy as np
from ophyd import SignalRO


class VideoCaptureSignal(SignalRO):
    def __init__(self, camera_no: int = 0, **kwargs):
        super(VideoCaptureSignal, self).__init__(**kwargs)
        self.camera = cv2.VideoCapture(camera_no)

    def get(self) -> np.ndarray:
        has_image, image = self.camera.read()
        if has_image:
            return image
        else:
            raise ValueError("oops!")

    def __del__(self):
        self.camera.release()
