
import h5py
import numpy as np

from ...core.data_classes.images import Sinogram

def _read_h5py(filename, **kwargs):
    f = h5py.File(filename, 'r')
    detectors = f['metadata']['detectors']


    nt = len(f.keys())-2
    times = np.zeros(nt)
    angles = np.zeros(nt)
    for i in range(nt):
        key = 'image '+str(i)
        if i == 0:
            nx, ny = f[key]['HAADF'].shape
            data = proxy.zeros([nx,ny,nt])
        data[:,:,i] = f[key]['HAADF']
        times[i] = np.array(f[key]['acquisition timee (s)']).item()
        angles[i] = np.array(f[key]['alpha tilt (deg)']).item()
    return Sinogram(data, angles, times=times)

Sinogram.readers['.h5'] = _read_h5py