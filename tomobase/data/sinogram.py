import os
import glob
import h5py
import numpy as np
import imageio as iio
import stackview


import ipywidgets as widgets
from IPython.display import display, clear_output
from copy import deepcopy
from tomobase.log import logger

from scipy.io import savemat, loadmat
import mrcz

from qtpy.QtWidgets import QApplication, QFileDialog
import collections
collections.Iterable = collections.abc.Iterable

from abc import ABC, abstractmethod


from tomobase.registrations.environment import TOMOBASE_ENVIRONMENT
if TOMOBASE_ENVIRONMENT.hyperspy:
    import hyperspy.api as hs
    
from tomobase.data.base import Data
from tomobase.registrations.datatypes import TOMOBASE_DATATYPES
from tomobase.data.image import Image


class Sinogram(Data):
    """A stack of projection images

    The sinogram is a stack of projection images, indexed using the
    (rows, columns, slices) standard, which corresponds to (y, x, alpha).
    
    Attributes:
        data (numpy.ndarray)
            The data as a stack of images. The data is indexed using the
            (rows, columns, slices) standard, which corresponds to
            (y, x, alpha)
        angles (numpy.ndarray)
            The tilt angles in degrees corresponding to the projection images
        pixelsize (float)
            The width of the pixels in nanometer
            
    Methods:
        _read_h5(filename)
            Read a sinogram from an HDF5 file(.h5) 
    """

    def __init__(self, data, angles, pixelsize=1.0, times=None, metadata={}):
        """Create a sinogram

        Arguments:
            data (numpy.ndarray)
                The data as a stack of images. The data is indexed using the
                (rows, columns, slices) standard, which corresponds to
                (y, x, alpha)
            angles (numpy.ndarray)
                The tilt angles in degrees corresponding to the projection
                images
            pixelsize (float)
                The width of the pixels in nanometer (default 1.0)
        """
        if len(angles) != data.shape[0]:
            raise ValueError(("There should be the same number of projection images as tilt angles."))
        if times is None:
            times = np.linspace(1, len(angles), len(angles)+1)
        elif len(times) != len(angles):
            raise ValueError(("There should be the same number of projection images as times."))
        
        self.times = times
        self.data = data
        super().__init__(pixelsize, metadata)
        self.angles = np.asarray(angles)
        
    def sort(self, bytime = False):
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
            
    def insert(self, img, angle, time=None):
        """
        Insert a new image into the sinogram
        
        Args:
            img (numpy.ndarray): The image to insert
            angle (float): The angle of the image
            time (float): The time of acquisition
        """
        if time is None:
            time = self.times[-1] + 1
        self.data = np.dstack((self.data, img))
        self.angles = np.append(self.angles, angle)
        self.times = np.append(self.times, time)
        
    def remove(self, index):
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
                data = np.zeros([nx,ny,nt])
            data[:,:,i] = f[key]['HAADF']
            times[i] = np.array(f[key]['acquisition timee (s)']).item()
            angles[i] = np.array(f[key]['alpha tilt (deg)']).item()
        return Sinogram(data, angles, times=times)


    @staticmethod
    def _read_mrc(filename, **kwargs):
        data, metadata = mrcz.readMRC(filename)
        print(metadata)
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
        p = obj[key]['pixelsize'][0][0]
        if 'times' in obj[key]:
            t = obj[key]['times'][0][0]
        else:
            t = np.linspace(1, len(a), len(a)+1)

        ts = Sinogram(d.squeeze(), a.squeeze(), p.squeeze(), t.squeeze())
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

    _readers = {}
    _writers = {
        'mrc': _write_mrc,
        'mat': _write_mat,
        'ali': _write_mrc,
    }
    

    def to_data_tuple(self, attributes:dict={}, metadata:dict={}):
        """_summary_

        Args:
            attributes (dict, optional): _description_. Defaults to {}.
            metadata (dict, optional): _description_. Defaults to {}.

        Returns:
            layerdata: Napari Layer Data Tuple
        """
        logger.debug('Converting Sinogram to Napari Layer Data Tuple: Shape: %s, Angles: %s, Pixelsize: %s', self.data.shape, self.angles, self.pixelsize)
        attributes = attributes
        attributes['name'] = attributes.get('name', 'Sinogram')
        attributes['scale'] = attributes.get('pixelsize' ,(self.pixelsize, self.pixelsize, self.pixelsize))
        attributes['colormap'] = attributes.get('colormap', 'gray')
        attributes['contrast_limits'] = attributes.get('contrast_limits', [0, np.max(self.data)*1.5])
        
        metadata = metadata
        metadata['type'] = TOMOBASE_DATATYPES.SINOGRAM.value()
        metadata['angles'] = self.angles
        metadata['axis'] = ['Projection', 'y', 'x'] if len(self.data.shape) == 3 else ['Projection', 'Signal', 'y', 'x']
        
        for key, value in self.metadata.items():
            metadata[key] = value

        attributes['metadata'] = {'ct metadata': metadata}
        layerdata = (self.data, attributes, 'image')
        
        return layerdata
    
    @classmethod
    def from_data_tuple(cls, layerdata, attributes=None):
        if attributes is None:
            data = layerdata.data
            scale = layerdata.scale[0]
            layer_metadata = layerdata.metadata
        else:
            data = layerdata
            scale = attributes['scale'][0]
            layer_metadata = attributes['metadata']

        layer_metadata = deepcopy(layer_metadata)
        metadata = layer_metadata['ct metadata']
        angles = metadata.pop('angles')
        metadata.pop('axis')
        metadata.pop('type')

        return cls(data, angles, scale)

    def show(self, display_width=800, display_height=800, showdisplay=True):
        """shows the sinogram in a stackview window

        Returns:
            _type_: _description_
        """
        self._angle_widget = widgets.FloatText(value=self.angles[0],description='Angle:',disabled=True)
        self._time_widget = widgets.FloatText(value=self.times[0],description='Time:',disabled=True)
        
        
        
        data = self._transpose_to_view(use_copy=True)
        
        image_widget = stackview.slice(data, display_width=display_width, display_height=display_height)
        slider = image_widget.children[0].children[0].children[1].children[0].children[0].children[1]
        slider.observe(self._on_slider_change, names='value')
        slider.value = 0
        obj = widgets.VBox([image_widget, self._angle_widget, self._time_widget]) 
        if showdisplay:
            display(obj)
        else: 
            return obj
        
    def _on_slider_change(self, change):
            self._angle_widget.value = self.angles[change['new']]
            self._time_widget.value = self.times[change['new']]

# Register the readers
Sinogram._readers = {
    'mrc': Sinogram._read_mrc,
    'ali': Sinogram._read_mrc,
    'emi': Sinogram._read_emi_stack,
    'mat': Sinogram._read_mat,
    'h5': Sinogram._read_h5,
}

