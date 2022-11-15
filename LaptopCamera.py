import os
import time
from datetime import datetime
from pathlib import Path
from pprint import pprint
from queue import Queue
from typing import Dict

import bluesky.plan_stubs as bps
import bluesky.plans as bp
import cv2
from bluesky import RunEngine
from bluesky.protocols import Descriptor, Reading, Status, SyncOrAsync
from ophyd import Component, Device, DeviceStatus, Signal

from PhysicalCamera import VideoCaptureSignal

os.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH")


class LaptopCamera(Device):
    directory: Signal = Component(Signal, kind="config")
    filename: Signal = Component(Signal, kind="config")
    count: Signal = Component(Signal, value=0)
    camera: Signal = Component(VideoCaptureSignal)

    def __init__(self, **kwargs):
        super(LaptopCamera, self).__init__(**kwargs)
        self.stage_sigs[self.count] = 0
        self.queue = Queue(1)

    def trigger(self) -> Status:
        image = self.camera.get()
        self.count.set(self.count.get() + 1)
        saved_location = str(
            Path(self.directory.get())
            / (self.filename.get() + f"_{self.count.get()}.png")
        )

        cv2.imwrite(saved_location, image)

        self.queue.put(saved_location)
        status = DeviceStatus(self)
        status.set_finished()
        return status

    def read(self) -> SyncOrAsync[Dict[str, Reading]]:
        if not self.queue.empty():
            saved_location = self.queue.get_nowait()
        else:
            self.trigger()
            self.read()

        result = {
            "location": Reading(
                value=saved_location, timestamp=time.mktime(datetime.now().timetuple())
            )
        }

        return result

    def describe(self) -> SyncOrAsync[Dict[str, Descriptor]]:

        result = {"location": Descriptor(source="cv2 camera", dtype="string", shape=[])}
        return result


lpc = LaptopCamera(name="lpc")

RE = RunEngine()


def take_picture():
    yield from bps.abs_set(
        lpc.directory, "/home/rose/Documents/projects/ophyd-test/webcam"
    )
    yield from bps.abs_set(lpc.filename, "test")

    yield from bp.count([lpc], num=50, delay=0.001)


RE(take_picture(), lambda name, doc: pprint({"name": name, "doc": doc}))
