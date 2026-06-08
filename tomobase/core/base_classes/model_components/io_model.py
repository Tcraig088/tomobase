import pathlib
from functools import partial

from .. import registers
from ... import log

from typing import Callable
from qtpy.QtWidgets import QApplication, QFileDialog


class IOModel():
    readers = registers.Registry(str, Callable)
    writers = registers.Registry(str, Callable)
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.readers = registers.Registry(str, Callable, parent=cls.readers)
        cls.writers = registers.Registry(str, Callable, parent=cls.writers)

    def __init__(self, data, *args, **kwargs):
        super().__init__(data, *args, **kwargs)
        
    def write(self, filename: pathlib.Path| str | None = None, **kwargs):
        """Save the data to a file."""
        if isinstance(filename, str):
            filename = pathlib.Path(filename)
            
        if filename is None:
            app = QApplication.instance() or QApplication([])
            filters = ";;".join(
                f"{ext.upper()} files (*.{ext})"
                for ext in self.writers.keys()
            )
            filename_str, _ = QFileDialog.getSaveFileName(
                None, "Save File", "", filters
            )
            if not filename_str:
                raise Exception("No file selected or file could not be found")
            filename = pathlib.Path(filename_str)
            if app is not QApplication.instance():
                app.quit()

        ext = filename.suffix.lower().lstrip(".")

        try:
            writer = self.writers[f'.{ext}']
        except KeyError:
            raise ValueError(f"The given file type {ext.upper()} is not supported.")

        writer(self, filename, **kwargs)
    
    @classmethod
    def read(cls, filename: pathlib.Path | str | None = None, **kwargs):
        """Read a dataset from a file and return a model instance."""
        if isinstance(filename, str):
            filename = pathlib.Path(filename)

        log.logger.debug(f"Attempting to load file {filename} with {cls.readers}")
        if filename is None:
            app = QApplication.instance() or QApplication([])
            filters = ";;".join(
                f"{ext.upper()} files (*{ext})"
                for ext in cls.readers.keys()
            )
            filename_str, _ = QFileDialog.getOpenFileName(
                None, "Select File", "", filters
            )
            if not filename_str:
                raise Exception("No file selected or file could not be found")
            filename = pathlib.Path(filename_str)
            
            if app is not QApplication.instance():
                app.quit()

        ext = filename.suffix.lower().lstrip(".")
        name = kwargs.get('name', filename.parent.name)
        try:
            reader = cls.readers[f'.{ext}']
        except KeyError:
            raise ValueError(f"The given file type {ext.upper()} is not supported.")

        # reader should create and return an instance of cls
        return reader(str(filename), name=name,  **kwargs)
    
