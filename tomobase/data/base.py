import os
import pathlib
import numpy as np
from qtpy.QtWidgets import QApplication, QFileDialog
import collections
collections.Iterable = collections.abc.Iterable

from abc import ABC, abstractmethod

from ..log import logger
from ..registrations.datatypes import TOMOBASE_DATATYPES
from ..registrations.environment import GPUContext, xp

class Data(ABC):
    """
    Abstract base class for microscopy and tomography datasets. To implement a child of this class you must:
    
    - implement methods to read data from a file, these should be class methods
      that return an instance of the class

    - implement methods to write data to a file

    - create the class variables ``_readers`` and ``_writers`` which are
      dictionaries that link each supported filetype to the correct reader or
      writer respectively, the keys should be the extensions in lowercase
    
    Attributes:
        pixelsize (float): The size of the pixels in the dataset
        metadata (dict): A dictionary containing metadata about the dataset

    """


    def __init__(self, pixelsize: float=1.0, metadata: dict = {}):
        """Initialize the Data object

        Args:
            pixelsize (float, optional): The size of the pixels in the dataset. Defaults to 1.0 nm
            metadata (dict, optional): A dictionary containing metadata about the dataset. Defaults to {}.
        """
        self.pixelsize = pixelsize
        self.metadata = metadata

        # Note these are used to swap between numpy and cupy context
        self._context = GPUContext.NUMPY
        self._device = 0

    @classmethod
    def from_file(cls, filename: pathlib.Path | None = None, **kwargs):
        """Read a dataset from a file

        Args:
            filename (pathlib.Path | None): The name of the file from which to read the data, a GUI will be opened to select a file if none is specified (default: None)

        Exceptions:
            ValueError: If the file type is not supported or the file cannot be found

        Returns:
            Data: An instance of the Data class containing the read data
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
            data = reader(filename, **kwargs)
            return data
        except KeyError:
            raise ValueError(f"The given file type {ext.upper()} is not supported.")


    def to_file(self, filename: pathlib.Path | None = None, **kwargs):
        """Save the data to a file

        Arguments:
            filename (pathlib.Path | None): The name of the file to which to write the data, a GUI will be opened to select a file if none is specified (default: None)
        
        Exceptions:
            ValueError: If the file type is not supported or the file is not found
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

    @classmethod
    def _get_type_id(cls) -> int:
        # Only use with napari used to identify the object from the layer etc
        class_name_upper = cls.__name__.upper()
        return TOMOBASE_DATATYPES[class_name_upper].value

    def _set_context(self, context:GPUContext | None = None, device:int | None = None):
        # used to set the context 
        if context is None:
            context = xp.context
        if device is None:
            device = xp.device

        self.data = xp.asarray(self.data, context, device)
        self._context = context
        self._device = device

    def layer_metadata(self, metadata: dict = {}):
        """Get the layer metadata in the format required for napari implementation

        Args:
            metadata (dict): the associated metadata for the layer

        Returns:
            dict: the layer metadata in the required format. By default the dict is wrapped in another dict of key 'ct metadata'. This avoids the metadata from conflicting with other packages.
        """

        meta = {}
        if 'ct metadata' not in metadata:
            meta['ct metadata'] = {}
        else:
            meta['ct metadata'] = metadata['ct metadata']

        for key, value in self.metadata.items():
            meta['ct metadata'][key] = value

        #must replace with the correct type in subclasses
        meta['ct metadata']['type'] = TOMOBASE_DATATYPES.DATA.value
        return meta

    def layer_attributes(self, attributes: dict = {}):
        """Get the layer attributes in the format required for napari implementation

        Args:
            attributes (dict): the associated attributes for the layer. 

        Returns:
            dict: the layer attributes in the required format. By default the structure is as follows:

        """
        attr = {}
        attr['name'] = attributes.get('name', 'Data')
        attr['scale'] = attributes.get('pixelsize' ,(self.pixelsize, self.pixelsize, self.pixelsize))
        attr['colormap'] = attributes.get('colormap', 'gray')
        attr['contrast_limits'] = attributes.get('contrast_limits', [0, np.max(self.data)*1.5])
        return attr

    def to_data_tuple(self, attributes:dict={}, metadata:dict={}):
        """ 
        Builds a Napari Layer Data Tuple

        Args:
            attributes (dict): the associated attributes for the layer. Defaults to {}.
            metadata (dict): the associated metadata for the layer. Defaults to {}.

        Returns:
            tuple: A tuple of (data, attributes, 'image') where data is the data array, attributes is a dictionary of attributes and 'image' is the layer type for napari.
        """
        attributes = self.layer_attributes(attributes)
        metadata = self.layer_metadata(metadata)
        attributes['metadata'] = metadata
        layerdata = (self.data, attributes, 'image')
        return layerdata
    
    @classmethod
    def from_data_tuple(cls, layer, attributes:dict|None=None):
        """Create an instance of the class from a Napari layer data tuple.

        Args:
            layer (napari layer): The Napari layer to convert.
            attributes (dict | None, optional): The associated attributes for the layer. Defaults to None.

        Returns:
           Data: An instance of the Data class.
        """

        if attributes is None:
            data = layer.data
            scale = layer.scale[0]
            layer_metadata = layer.metadata['ct metadata']
        else:
            data = layer
            scale = attributes['scale'][0]
            layer_metadata = attributes['metadata']['ct metadata']

        return cls(data, scale, layer_metadata)
