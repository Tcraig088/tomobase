import os
import pathlib
import copy
from abc import ABC, abstractmethod

from qtpy.QtCore import QObject, Slot
from qtpy.QtWidgets import QApplication, QFileDialog

from ..environment import GPUContext, proxy
import magicgui


from ..log import logger
class BaseDataModel(QObject):
    """Base class for GPU-backed data models with file IO."""

    # class-level registries; subclasses override/extend these
    readers: dict[str, callable] = {}
    writers: dict[str, callable] = {}

    def __init__(self, *args, **kwargs):
        """Initialize the Data object."""
        super().__init__()

        # default: follow global proxy
        self._context: GPUContext = proxy.context
        self._device: int = proxy.device
        self._global_context: bool = True
        self.global_context = True  # goes through setter, connects signals

    # ---------- global context handling ----------

    @property
    def global_context(self) -> bool:
        """Whether the data object is using the global proxy context/device."""
        return self._global_context

    @global_context.setter
    def global_context(self, value: bool):
        if self._global_context == value:
            return

        self._global_context = value
        if value:
            # follow global context: connect to proxy signal and sync now
            try:
                proxy.context_changed.connect(self._on_proxy_context_changed)
            except Exception:
                pass
            self._context = proxy.context
            self._device = proxy.device
        else:
            # stop following global context
            try:
                proxy.context_changed.disconnect(self._on_proxy_context_changed)
            except Exception:
                pass

    @Slot(object, int)
    def _on_proxy_context_changed(self, context, device):
        """Slot called when the global proxy context or device changes."""
        if not self._global_context:
            return
        # keep this object in sync with the proxy
        self.set_context(context, device)

    # ---------- IO ----------

    def to_file(self, filename: pathlib.Path | None = None, **kwargs):
        """Save the data to a file."""
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
            writer = self.writers[ext]
        except KeyError:
            raise ValueError(f"The given file type {ext.upper()} is not supported.")

        writer(self, filename, **kwargs)

    @classmethod
    @magicgui.magicgui(call_button='Load from File')
    def magicgui_from_file(cls, filename: pathlib.Path | None = None, **kwargs):
        ext = filename.suffix.lower().lstrip(".")
        if ext not in cls.readers:
            raise ValueError(f"The given file type {ext.upper()} is not supported.")
        else:          
            reader = cls.readers[ext]
            return reader(filename, **kwargs)
    
    @classmethod
    def from_file(cls, filename: pathlib.Path | None = None, **kwargs):
        """Read a dataset from a file and return a model instance."""
        logger.debug(f"Attempting to load file {filename} with {cls.readers}")
        if filename is None:
            app = QApplication.instance() or QApplication([])
            filters = ";;".join(
                f"{ext.upper()} files (*.{ext})"
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

        try:
            reader = cls.readers[ext]
        except KeyError:
            raise ValueError(f"The given file type {ext.upper()} is not supported.")

        # reader should create and return an instance of cls
        return reader(filename, **kwargs)

    # ---------- context management ----------

    @abstractmethod
    def set_context(
        self,
        context: GPUContext | None = None,
        device: int | None = None,
    ):
        """Set the computational context for the data object.

        Subclasses may extend this, but should call super().set_context(...)
        to preserve the base behaviour.
        """
        if self.global_context:
            # follow the proxy; ignore explicit context/device
            self._context = proxy.context
            self._device = proxy.device
            return

        if context is not None:
            self._context = context
        if device is not None:
            self._device = device

    # ---------- copying / deepcopying ----------

    def __copy__(self):
        """Shallow copy: new QObject, same context/device, shallow payload copy."""
        cls = self.__class__
        new = cls.__new__(cls)

        # initialise QObject part
        QObject.__init__(new)

        # copy base state
        new._context = self._context
        new._device = self._device

        # copy global_context and re-wire proxy connections as needed
        new._global_context = False  # avoid extra work in setter
        new.global_context = self._global_context

        # let subclass copy its own data payload
        new._copy_from(self)
        return new

    def __deepcopy__(self, memo):
        """Deep copy: new QObject, same context/device, deep-copied payload."""
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new

        QObject.__init__(new)

        # base state: usually you don't deepcopy GPU context/device
        new._context = self._context
        new._device = self._device

        new._global_context = False
        new.global_context = self._global_context

        new._deepcopy_from(self, memo)
        return new

    @abstractmethod
    def _copy_from(self, other: "BaseDataModel"):
        """Copy this model's payload (shallow) from another instance.

        BaseDataModel already handled QObject + context/device; subclasses should
        implement copying of their actual data (arrays, metadata, etc.).
        """
        raise NotImplementedError

    @abstractmethod
    def _deepcopy_from(self, other: "BaseDataModel", memo: dict):
        """Deep-copy this model's payload from another instance.

        Use copy.deepcopy(..., memo) on your own attributes here.
        """
        raise NotImplementedError
