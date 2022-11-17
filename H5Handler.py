import h5py
import numpy as np


class H5Handler:
    def __init__(self, path, **resource_kwargs):
        # Consume the path information and the 'resource_kwargs' from the
        # Resource. Typically stashes some state and/or opens file(s).
        self.file = h5py.File(path, "r", swmr=True)

    def __call__(self, location):
        # Consumes the 'datum_kwargs' from the datum and uses them to
        # locate a specific unit (slice, chunk, or what you will...) of
        # data and return it.

        return np.array(self.file[location])

    def __del__(self):
        self.file.close()
