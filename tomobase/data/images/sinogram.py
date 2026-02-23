import os
import glob
import h5py
import numpy as np
import imageio as iio
import copy

from ...environment import proxy
from copy import deepcopy
from scipy.io import savemat, loadmat
import mrcz


from .image import Image
from .base import BaseImageModel

class Sinogram(BaseImageModel):
    """
    The sinogram is a stack of projection images, indexed using the
    (n, x, y) orientation. 

    Supported File Types:
        - .h5
        - .mrc
        - .emi
        - .mat (experimental)

    Attributes:
        data (numpy.ndarray): The sinogram data, indexed using the (n, x, y) orientation.
        angles (numpy.ndarray): The tilt angles in degrees corresponding to the projection images.
        times (numpy.ndarray): The times of acquisition corresponding to the projection images. This defaults to the projection index starting at 1. Otherwise it should be provided in seconds


    """

    def __init__(self, data, angles: np.ndarray, pixelsize: float = 1.0, times: np.ndarray | None = None, metadata: dict = {}, *args, **kwargs):
        """Initialize a sinogram class

        Arguments:
            data (numpy.ndarray): The sinogram data, indexed using the (n, x, y) orientation.
            angles (numpy.ndarray): The tilt angles in degrees corresponding to the projection images.
            pixelsize (float): The width of the pixels in nanometer (default 1.0)
            times (numpy.ndarray | None): The times of acquisition corresponding to the projection images. This defaults to the projection index starting at 1. Otherwise it should be provided in seconds.
            metadata (dict): Additional metadata to store with the sinogram.

        """

        if len(angles) != data.shape[0]:
            raise ValueError(("There should be the same number of projection images as tilt angles."))
        if times is None:
            times = np.linspace(1, len(angles), len(angles))
        elif len(times) != len(angles):
            raise ValueError(("There should be the same number of projection images as times."))

        self.times = times
        super().__init__(data, pixelsize, metadata, *args, **kwargs)
        self.angles = np.asarray(angles)

    def sort(self, bytime:bool = False):
        """
        Sort the sinogram by angles or by time
        
        Args:
            bytime (bool): Sort by time instead of angles
        """
        if bytime:
            indices = np.argsort(self.times)
            self.times = self.times[indices]
            self.angles = self.angles[indices] 
            self.data = self.data[indices,:,:]
        else:
            indices = np.argsort(self.angles)
            self.angles = self.angles[indices]
            self.times = self.times[indices]
            self.data = self.data[indices,:,:]

    def insert(self, img: np.ndarray, angle: float, time: float | None = None):
        """
        Insert a new image into the sinogram
        
        Args:
            img (numpy.ndarray): The image to insert
            angle (float): The angle of the image
            time (float): The time of acquisition
        """
        if time is None:
            time = self.times[-1] + 1

        if self.data.ndim == 2:
            # If `self.data` is 2D, add a new first axis and stack `img`
            self.data = np.stack((self.data, img), axis=0)
        else:
            # If `self.data` is already 3D, concatenate along the first axis
            self.data = np.concatenate(    (self.data, img), axis=0)
        #self.data = np.dstack((self.data, img))
        self.angles = np.append(self.angles, angle)
        self.times = np.append(self.times, time)

    def remove(self, index: int):
        """
        Remove an image from the sinogram
        
        Args:
            index (int): The index of the image to remove
        """
        self.data = np.delete(self.data, index, axis=0)
        self.angles = np.delete(self.angles, index)
        self.times = np.delete(self.times, index)

    @staticmethod
    def _read_h5(filename):
        f = h5py.File(filename, 'r')
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

    @staticmethod
    def _read_mrc(filename, **kwargs):
        data, metadata = mrcz.readMRC(filename)
        data = proxy.asarray(data)
        pixelsize = metadata['pixelsize'][0]
        angles = metadata['angles']
        if 'times' in metadata:
            times = metadata['times']
        else:
            times = np.linspace(1, len(angles), len(angles)+1)
        return Sinogram(data, angles, pixelsize, times)


    @staticmethod
    def _read_mat(path):
        obj = loadmat(path)
        #if obj has a series or stack key
        
        if 'series' in obj:
            key = 'series'
        elif 'stack' in obj:
            key = 'stack'
        else:
            key = 'obj'
            

        d = obj[key]['data'][0][0]
        a = obj[key]['angles'][0][0]
        
        # Check field names in structured array properly
        field_names = obj[key].dtype.names if hasattr(obj[key].dtype, 'names') else []
        
        if field_names and 'pixelsize' in field_names:
            p = obj[key]['pixelsize'][0][0]
        else:
            p = 1.0
        if field_names and 'times' in field_names:
            t = np.array(obj[key]['times'][0][0])
        else:
            t = np.linspace(1, len(a), len(a)+1)

        d = np.transpose(d, (2, 0, 1))  # Rearrange to (n, x, y)
        ts = Sinogram(d.squeeze(), a.squeeze(), p, t.squeeze())
        return ts
    
    def _write_mrc(self, filename, **kwargs):
        mrcz.writeMRC(self.data, filename, meta={'angles': self.angles, 'times': self.times}, pixelsize=[self.pixelsize, self.pixelsize, self.pixelsize])

    def _write_mat(self, filename, **kwargs):
        myrec = {'data':self.data, 'angles':self.angles, 'pixelsize':self.pixelsize, 'times':self.times} 
        savemat(filename, {'obj': myrec})
    
    @staticmethod
    def _read_emi_stack(filename, **kwargs):
        # List all EMI files in the directory of the selected file
        dirname = os.path.dirname(os.path.realpath(filename))
        filenames = glob.glob(dirname + "*.emi")
        # Read the first file for image size and metadata
        im = Image.from_file(filenames[0])
        data = np.zeros((len(filenames), im.data.shape[0], im.data.shape[1] ))
        angles = np.zeros(len(filenames))
        # Set the contents of the first file
        data[0, :, :] = im.data
        angles[0] = im.metadata['alpha_tilt']
        pixelsize = im.pixelsize
        # Loop over the other files to get all the projection images
        for i, filename in enumerate(filenames[1:], start=1):
            im = Image.from_file(filenames[0])
            data[i, :, :] = im.data
            angles[i] = im.metadata['alpha_tilt']
        # Sort the images by tilt angle and return the sinogram
        sorted_indices = np.argsort(angles)
        data = data[:, :, sorted_indices]
        angles = angles[sorted_indices]
        return Sinogram(data, angles, pixelsize)

    readers = {}
    writers = {
        'mrc': _write_mrc,
        'mat': _write_mat,
        'ali': _write_mrc,
    }

    def _copy_from(self, other:'Sinogram'):
        """Copy data from another Sinogram instance

        Args:
            other (Sinogram): The instance to copy from
        """
        self.angles = other.angles.copy()
        self.times = other.times.copy()
        super()._copy_from(other)
        
    def _deepcopy_from(self, other='Sinogram', memo:dict={}):
        self.angles = copy.deepcopy(other.angles, memo)
        self.times = copy.deepcopy(other.times, memo)
        return super()._deepcopy_from(other, memo)

    def __str__(self):
        return super().__str__()
# Register the readers
Sinogram.readers = {
    'mrc': Sinogram._read_mrc,
    'ali': Sinogram._read_mrc,
    'emi': Sinogram._read_emi_stack,
    'mat': Sinogram._read_mat,
    'h5': Sinogram._read_h5,
}
