import pathlib
import os

import ncempy
import numpy as np
 
from ...core.data_classes import Sinogram, Image

def _convert_time_to_seconds(date_str):
    time_str = date_str.split(' ')[3]
    time_parts = time_str.split(':')
    hours = int(time_parts[0])
    minutes = int(time_parts[1])
    seconds = int(time_parts[2])
    total_seconds = hours * 3600 + minutes * 60 + seconds
    return total_seconds

def _read_ser(filename: pathlib.Path, name=None,  **kwargs):
    if name is None:
        name = filename.parent.name
    obj = ncempy.io.ser.fileSER(filename)
    data = obj.getDataset(0)[0]
    Image(name, data, pixel_size=1.0, metadata=obj.metadata)

def _read_emi_stack(filename: pathlib.Path, **kwargs):
    name = kwargs.get('name', filename.parent.name)
    i = 0
    for file in os.listdir(path):
        if file.endswith('.ser'):
            ser = os.path.join(path, file)
            emi = os.path.join(path, file.replace('_1.ser', '.emi'))
            obj = ncempy.io.ser.fileSER(ser)
            angles.append(np.degrees(obj._emi['Tilt1']))
            times.append(_convert_time_to_seconds(obj._emi['AcquireDate']))
            data[i, :, :] = obj.getDataset(0)[0]
            i+=1

    angles = np.array(angles)
    times = np.array(times)
    times = times - np.min(times)
    return Sinogram(name, data, angles, pixel_size=1.0, times=times)


Image.readers['.ser'] = _read_ser
Sinogram.readers['.emi'] = _read_emi_stack
