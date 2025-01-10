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


def _bin(data, factor, inplace=True):
    """
    Bin a 3D or 4D array along the first two axes.

    Parameters:
    data (numpy.ndarray): Input array to be binned.
    factor (int): Binning factor.
    inplace (bool): Whether to modify the array in place or return a new array.

    Returns:
    numpy.ndarray: Binned array.
    """
    if not inplace:
        data = deepcopy(data)
    
    if data.ndim == 3:
        # Bin the data for the first two axes
        data = data.reshape(data.shape[0]//factor, factor, data.shape[1]//factor, factor, data.shape[2])
        data = data.mean(axis=1)
        data = data.mean(axis=2)
    elif data.ndim == 4:
        # Bin the data for the first two axes
        data = data.reshape(data.shape[0]//factor, factor, data.shape[1]//factor, factor, data.shape[2], data.shape[3])
        data = data.mean(axis=1)
        data = data.mean(axis=2)
    else:
        raise ValueError("Input data must be a 3D or 4D array.")
    
    return data

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

    def __init__(self, data, angles, pixelsize=1.0, metadata={}):
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
        if len(angles) != data.shape[2]:
            raise ValueError(("There should be the same number of projection "
                              "images as tilt angles."))
        super().__init__(data, pixelsize, metadata)
        self.angles = np.asarray(angles)


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

        return Sinogram(data, angles, metadata={'times': times})


    @staticmethod
    def _read_mrc(filename, **kwargs):
        data, metadata = mrcz.readMRC(filename)
        print(metadata)
        pixelsize = metadata['pixelsize'][0]
        angles = metadata['angles']
        return Sinogram(data, angles, pixelsize)


    @staticmethod
    def _read_mat(path):
        obj = loadmat(path)
        #if obj has a series or stack key
        
        if 'series' in obj:
            key = 'series'
        elif 'stack' in obj:
            key = 'stack'
        else:
            key = None
            
        if key is not None:
            d = obj[key]['data'][0][0]
            a = obj[key]['angles'][0][0]
            p = obj[key]['pixelsize'][0][0]
        else:
            d = obj['obj']['data'][0][0]
            a = obj['obj']['angles'][0][0]
            p = obj['obj']['pixelsize'][0][0]

        ts = Sinogram(d.squeeze(), a.squeeze(), p.squeeze())
        return ts
    
    def _write_mrc(self, filename, **kwargs):
        mrcz.writeMRC(self.data, filename, meta={'angles': self.angles},pixelsize=[self.pixelsize, self.pixelsize, self.pixelsize])

    def _write_mat(self, filename, **kwargs):
        myrec = {'data':self.data, 'angles':self.angles, 'pixelsize':self.pixelsize} 
        savemat(filename, {'obj': myrec})
    
    @staticmethod
    def _read_emi_stack(filename, **kwargs):
        # List all EMI files in the directory of the selected file
        dirname = os.path.dirname(os.path.realpath(filename))
        filenames = glob.glob(dirname + "*.emi")
        # Read the first file for image size and metadata
        im = Image.from_file(filenames[0])
        data = np.zeros((im.data.shape[0], im.data.shape[1], len(filenames)))
        angles = np.zeros(len(filenames))
        # Set the contents of the first file
        data[:, :, 0] = im.data
        angles[0] = im.metadata['alpha_tilt']
        pixelsize = im.pixelsize
        # Loop over the other files to get all the projection images
        for i, filename in enumerate(filenames[1:], start=1):
            im = Image.from_file(filenames[0])
            data[:, :, i] = im.data
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
    
    def _transpose_to_view(self, use_copy=False, data=None):
        """ Transpose the data from the standard orientation for data processessing to the view orientation.
        """
        if use_copy:
            data = deepcopy(self.data)
            if len(data.shape) == 3:
                data = data.transpose(2,1,0)
            elif len(data.shape) == 4:
                data = data.transpose(2,3,1,0)
            return data

        if data is not None:
            if len(data.shape) == 3:
                data = data.transpose(2,1,0)
            elif len(data.shape) == 4:
                data = data.transpose(2,3,1,0)
            return data
            
        if len(self.data.shape) == 3:
            self.data = self.data.transpose(2,1,0)
        elif len(self.data.shape) == 4:
            self.data = self.data.transpose(2,3,1,0)
        return self.data
            
    @classmethod
    def _transpose_from_view(cls, data):
        """ Transpose the data from the view orientation to the standard orientation for data processessing.
        """
        if len(data.shape) == 3:
            data = data.transpose(2,1,0)
        else:
            data = data.transpose(3,2,0,1)
        return data
    
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
        self.data = self._transpose_to_view()
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

        return cls(cls._transpose_from_view(data), angles, scale, metadata)

    def show(self, binning=4):
        """shows the sinogram in a stackview window

        Returns:
            _type_: _description_
        """
        angle_widget = widgets.FloatText(value=self.angles[0],
                                    description='Angle:',
                                    disabled=True)
        
        def on_slider_change(change):
            angle_widget.value = self.angles[change['new']]
        
        data = _bin(self.data, binning, inplace=False)
        data = self._transpose_to_view(data=data)
        
        image_widget = stackview.slice(data)
        for item in image_widget.children:
            if isinstance(item, (widgets.IntSlider, widgets.FloatSlider)):
                item.observe(on_slider_change, names='value')
        display(widgets.VBox([image_widget, angle_widget]))
        


# Register the readers
Sinogram._readers = {
    'mrc': Sinogram._read_mrc,
    'ali': Sinogram._read_mrc,
    'emi': Sinogram._read_emi_stack,
    'mat': Sinogram._read_mat,
    'h5': Sinogram._read_h5,
}

