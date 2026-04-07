import json
from pathlib import Path

import mrcfile
import numpy as np

from ...core.data_classes.images import Sinogram

def _read_mrc(filename, **kwargs):
    filename = Path(filename)

    with mrcfile.open(filename, permissive=True) as mrc:
        data = np.asarray(mrc.data).copy()
        ext_bytes = int(mrc.header.nsymbt)
        exttyp = bytes(mrc.header.exttyp).rstrip(b"\x00 ")

        metadata = {}
        if ext_bytes > 0 and exttyp == b"json":
            raw = bytes(mrc.extended_header).rstrip(b"\x00")
            metadata = json.loads(raw[:ext_bytes].decode("utf-8"))

    
    pixelsize = metadata.get("pixelsize", 1.0)
    angles = np.asarray(metadata.get("angles", []))
    if angles.size == 0:
        raise ValueError(f"No angles found for {filename}. Expected in metadata.")

    if "times" in metadata:
        times = np.asarray(metadata["times"])
    else:
        times = np.arange(len(angles))

    name = metadata.get("name", kwargs.get("name", filename.parent.name))

    return Sinogram(name, data, angles, pixelsize, times)


def _write_mrc(sino, filename, **kwargs):
    filename = Path(filename)

    with mrcfile.new(filename, overwrite=True) as mrc:
        mrc.set_data(np.asarray(sino.data))
        mrc.voxel_size = (sino.pixelsize, sino.pixelsize, sino.pixelsize)

    # write non-standard metadata to a sidecar json
    meta = {
        "name": sino.name,
        "angles": np.asarray(sino.angles).tolist(),
        "times": np.asarray(sino.times).tolist(),
    }

    meta_path = filename.with_suffix(filename.suffix + ".json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

Sinogram.readers['.mrc'] = _read_mrc    
Sinogram.writers['.mrc'] = _write_mrc