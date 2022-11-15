#this literally just makes a class that makes an opencv2 camera, takes a pic every ms and saves that in a class attribute...
from time import sleep
import cv2
from typing import Dict

from queue import Queue
import numpy as np
from ophyd import SignalRO, DeviceStatus
from bluesky.protocols import Status, SyncOrAsync, Reading

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
