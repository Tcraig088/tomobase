import os
import numpy as np
from qtpy.QtWidgets import QApplication, QFileDialog
import collections
collections.Iterable = collections.abc.Iterable

from abc import ABC, abstractmethod

from tomobase.registrations.datatypes import TOMOBASE_DATATYPES
from tomobase.registrations.environment import GPUContext, xp

class Data(ABC):
    """Abstract base class for microscopy and tomography datasets

    To implement a child of this class you must:
     - implement methods to read data from a file, these should be class methods
       that return an instance of the class
     - implement methods to write data to a file
     - create the class variables ``_readers`` and ``_writers`` which are
       dictionaries that link each supported filetype to the correct reader or
       writer respectively, the keys should be the extensions in lowercase
     - implement the methods _to_napari_layer and _from_napari_layer inorder to create napari image layers from the data and vice versa
    """

    def __init__(self, pixelsize, metadata={}):
        self.pixelsize = pixelsize
        self.metadata = metadata
        self._context = GPUContext.NUMPY
        self._device = 0
        self._layer_index = None

    @classmethod
    def from_file(cls, filename=None, **kwargs):
        """Read an image from a file

        Arguments:
            filename (str)
                The name of the file from which to read the data, a GUI will be
                opened to select a file if none is specified (default: None)

        Returns:
            Data
                The data
        """
        if filename is None:
            app = QApplication([])
            filename, _ = QFileDialog.getOpenFileName(None, "Select File", "", 
                                    [(f"{ext.upper()} files", f"*.{ext}") for ext in cls._readers.keys()])
            if not filename:
                raise Exception("No file selected or file could not be found")
            app.quit()

        _, ext = os.path.splitext(filename)
        ext = ext[1:]  # remove the dot

        try:
            reader = cls._readers[ext]
            reader(filename, **kwargs)
            sinogram = reader(filename, **kwargs)
            return sinogram
        except KeyError:
            raise ValueError(f"The given file type {ext.upper()} is not supported.")

    @classmethod
    def get_type_id(cls):
        """Return the type ID of the class

        Returns:
            str
                The type ID of the class
        """
        class_name_upper = cls.__name__.upper()
        return TOMOBASE_DATATYPES[class_name_upper].value
      
    def to_file(self, filename=None, **kwargs):
        """Save the data to a file

        Arguments:
            filename (str)
                The name of the file to which to write the data, a GUI will be
                opened to select a file if none is specified (default: None)
        """
        if filename is None:
            app = QApplication([])
            filename, _ = QFileDialog.getSaveFileName(None, "Save File", "", ";;".join([f"{ext.upper()} files (*.{ext})"
                                                                            for ext in self._writers.keys()]))
            if not filename:
                raise Exception("No file selected or file could not be found")
            app.quit()

        _, ext = os.path.splitext(filename)
        ext = ext[1:]  # remove the dot

        try:
            writer = self._writers[ext]
            writer(self, filename, **kwargs)
        except KeyError:
            raise ValueError(f"The given file type {ext.upper()} is not supported.")


    @property
    @abstractmethod
    def _writers(self):
        pass

    @property
    @abstractmethod
    def _readers(self):
        pass

    def set_context(self, context=None, device=None):
        if context is None:
            context = xp.context
        if device is None:
            device = xp.device

        self.data = xp.asarray(self.data, context, device)
        self._context = context
        self._device = device

    

    @property
    def layer_metadata(self, metadata={}):
        # We dont want to clutter the metadata with ctomo data in case other plugins would like to use it 
        if 'ctomo' not in metadata:
            metadata['ctomo'] = {}

        for key, value in self.metadata.items():
            metadata['ctomo'][key] = value

        #must replace with the correct type in subclasses
        metadata['ctomo']['type'] = TOMOBASE_DATATYPES.DATA.value()

    @property
    def layer_attributes(self, attributes={}):     
        attributes['name'] = attributes.get('name', 'Data')
        attributes['scale'] = attributes.get('pixelsize' ,(self.pixelsize, self.pixelsize, self.pixelsize))
        attributes['colormap'] = attributes.get('colormap', 'gray')
        attributes['contrast_limits'] = attributes.get('contrast_limits', [0, np.max(self.data)*1.5])
        return attributes

    def to_data_tuple(self, attributes:dict={}, metadata:dict={}):
        """_summary_

        Args:
            attributes (dict, optional): _description_. Defaults to {}.
            metadata (dict, optional): _description_. Defaults to {}.

        Returns:
            layerdata: Napari Layer Data Tuple
        """
        attributes = self.layer_attributes(attributes)
        metadata = self.layer_metadata(metadata)
        layerdata = (self.data, attributes, 'image')
        return layerdata
    
    @classmethod
    def from_data_tuple(cls, index, layer, attributes=None):
        if attributes is None:
            data = layer.data
            scale = layer.scale[0]
            layer_metadata = layer.metadata['ctomo']
        else:
            data = layer
            scale = attributes['scale'][0]
            layer_metadata = attributes['metadata']['ctomo']

        return cls(data, scale, index)
