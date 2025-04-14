import os
import napari

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

    @abstractmethod
    def show(self):
        pass

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

