from pathlib import Path

import cv2

from H5Handler import H5Handler


class ConsumeDocuments:
    def __init__(self):
        self.handler = None
        self.datum_dict = {}
        self.resource_id = None

    def __call__(self, name, doc):
        if name == "resource":
            self.handler = H5Handler(
                Path(doc["root"]) / doc["resource_path"], **doc["resource_kwargs"]
            )
            self.resource_id = doc["uid"]

        if name == "datum":
            if doc["resource"] == self.resource_id:
                self.datum_dict[doc["datum_id"]] = doc["datum_kwargs"]

        if name == "event":
            datum_id = doc["data"]["value"]
            datum_kwargs = self.datum_dict[datum_id]
            data = self.handler(**datum_kwargs)
            print("event receieved...")
            did_it_write = cv2.imwrite(
                "/home/rose/Documents/projects/camera/webcam/"
                + f"{datum_id.replace('/', '_')}.png",
                data,
            )
            print(did_it_write)
