import os
import time
from datetime import datetime
from pathlib import Path
from pprint import pprint
from queue import Queue
from typing import Dict

import bluesky.plan_stubs as bps
import bluesky.plans as bp
from bluesky import RunEngine
from bluesky.protocols import Descriptor, Reading, Status, SyncOrAsync
from ophyd import Component, Device, DeviceStatus, Signal

from PhysicalCamera import VideoCaptureSignal

import h5py

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
        path_to_data = "/%d" % self.count.get()

        file_loc: Path = Path(self.directory.get()) / (self.filename.get() + ".h5py")
        mode = "w" if not file_loc.is_file() else "r+"

        with h5py.File(str(file_loc), mode) as h5_file:
            h5_file.create_dataset(path_to_data, data=image)

        self.queue.put(path_to_data)
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


def take_pictures():
    yield from bps.abs_set(lpc.directory, "/home/rose/Documents/projects/camera/webcam")
    yield from bps.abs_set(lpc.filename, "test")
    yield from bp.count([lpc], num=10, delay=1)


RE(take_pictures(), lambda name, doc: pprint({"name": name, "doc": doc}))
