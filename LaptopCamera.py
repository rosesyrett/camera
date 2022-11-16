import os
import time
from datetime import datetime
from pathlib import Path
from pprint import pprint
from typing import Dict, Iterator, List
import uuid

import bluesky.plan_stubs as bps
import bluesky.plans as bp
from bluesky import RunEngine
from bluesky.protocols import Descriptor, Reading, Status, SyncOrAsync, Asset
from ophyd import Component, Device, DeviceStatus, Signal

from PhysicalCamera import VideoCaptureSignal

import h5py
import cv2
from collections import deque

os.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH")


class LaptopCamera(Device):
    directory: Signal = Component(Signal, kind="config")
    filename: Signal = Component(Signal, kind="config")
    count: Signal = Component(Signal, value=0)
    camera: Signal = Component(VideoCaptureSignal)

    def __init__(self, **kwargs):
        super(LaptopCamera, self).__init__(**kwargs)
        self.stage_sigs[self.count] = 0
        self._asset_docs_cache = deque()
        self.filestore_spec = "HDF5"
        self.path_semantics = "posix"
        self.h5_file = None
        self.resource_path = None

    def resource_factory(
        self,
        resource_kwargs,
    ):
        resource_uid = str(uuid.uuid4())
        resource_doc = {
            "spec": self.filestore_spec,
            "root": self.directory.get(),
            "resource_path": str(self.resource_path),
            "resource_kwargs": resource_kwargs,
            "path_semantics": self.path_semantics,
            "uid": resource_uid,
        }

        def datum_factory(datum_kwargs):
            i = self.count.get()
            datum_id = "{}/{}".format(resource_uid, i)
            datum = {
                "resource": resource_uid,
                "datum_id": datum_id,
                "datum_kwargs": datum_kwargs,
            }

            return datum

        return resource_doc, datum_factory

    def generate_resource(self, resource_kwargs) -> None:
        # this generates a resource document

        resource, self.datum_factory = self.resource_factory(
            resource_kwargs,
        )

        self._asset_docs_cache.append(("resource", resource))

    def generate_datum(self, datum_kwargs) -> str:
        datum = self.datum_factory(datum_kwargs)
        self._asset_docs_cache.append(("datum", datum))

        datum_id = datum["datum_id"]
        return datum_id

    def stage(self) -> List["LaptopCamera"]:
        self.resource_path = Path(self.filename.get() + ".h5py")

        self.generate_resource({})

        self.h5_file = h5py.File(
            str(Path(self.directory.get()) / self.resource_path), "w"
        )
        return [self]

    def unstage(self) -> List["LaptopCamera"]:
        self.h5_file.close()
        self._asset_docs_cache.clear()
        cv2.destroyAllWindows()
        return [self]

    def trigger(self) -> Status:
        image = self.camera.get()
        self.count.set(self.count.get() + 1)
        path_to_data = "%d" % self.count.get()

        self.h5_file.create_dataset(path_to_data, data=image)

        cv2.imshow("video", image)

        status = DeviceStatus(self)
        status.set_finished()
        return status

    def read(self) -> SyncOrAsync[Dict[str, Reading]]:
        self.generate_datum({})
        datum_id = self.datum_factory({})
        result = {
            "value": Reading(
                value=datum_id["datum_id"],
                timestamp=time.mktime(datetime.now().timetuple()),
            )
        }

        return result

    def describe(self) -> SyncOrAsync[Dict[str, Descriptor]]:

        result = {"value": Descriptor(source="cv2 camera", dtype="string", shape=[])}
        return result

    def collect_asset_docs(self) -> Iterator[Asset]:
        items = list(self._asset_docs_cache)
        self._asset_docs_cache.clear()
        for item in items:
            yield item


lpc = LaptopCamera(name="lpc")

RE = RunEngine()


def take_pictures():
    yield from bps.abs_set(lpc.directory, "/home/rose/Documents/projects/camera/webcam")
    yield from bps.abs_set(lpc.filename, "test")
    yield from bp.count([lpc], num=10, delay=0.1)


RE(take_pictures(), lambda name, doc: pprint({"name": name, "doc": doc}))
