import os
import napari

from qtpy.QtWidgets import QApplication, QFileDialog
import collections
collections.Iterable = collections.abc.Iterable

from abc import ABC, abstractmethod

from tomobase.registration import TOMOBASE_ENVIRONMENT_REGISTRATION
if TOMOBASE_ENVIRONMENT_REGISTRATION.hyperspy:
    import hyperspy.api as hs

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

    def __init__(self, data, pixelsize):
        self.data = data
        self.pixelsize = pixelsize

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
    def from_layer(cls, layer):
        """Create an instance of the class from a napari layer

        Arguments:
            layer (napari.layers.Layer)
                The layer from which to create the data

        Returns:
            Data
                The data
        """
        return cls._from_napari_layer(layer)

    def show(self, viewer = None):
        """Display the data in an image viewer

        Arguments:
            viewer (napari.Viewer)
                The viewer to which to add the image, if None a new viewer will
                be created (default: None)
        """
        if viewer is None:
            viewer = napari.Viewer()
        viewer.add_image(**self._to_napari_layer())
        return viewer

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
    def _to_napari_layer(self):
        pass

    @abstractmethod
    def _from_napari_layer(layer):
        pass

    @property
    @abstractmethod
    def _writers(self):
        pass

    @property
    @abstractmethod
    def _readers(self):
        pass
