# import json

import bluesky.plan_stubs as bps
import bluesky.plans as bp
from bluesky import RunEngine

from ConsumeDocuments import ConsumeDocuments
from LaptopCamera import LaptopCamera

lpc = LaptopCamera(name="lpc")

RE = RunEngine()


def take_pictures():
    yield from bps.abs_set(lpc.directory, "/home/rose/Documents/projects/camera/webcam")
    yield from bps.abs_set(lpc.filename, "test")
    yield from bp.count([lpc], num=10, delay=0.1)


# cache = []


# def save_json(name, doc):
#     # for each document, saves them to some json
#     cache.append({"name": name, "doc": doc})

#     if name == "stop":
#         with open("output.json", "w") as file:
#             json.dump(cache, file, indent=4)


# RE(take_pictures(), save_json)

picture_interface = ConsumeDocuments()
RE(take_pictures(), picture_interface)
