import enum
import logging
from qtpy.QtCore import QObject, Signal
import numpy as np
import pandas as pd
from tomobase.log import logger

class GPUContext(enum.Enum):
    CUPY = 1
    NUMPY = 2


class EnvironmentContext(QObject):
    context_changed = Signal(object, int)  # emits (GPUContext, device_id)
    def __init__(self):

        # Initialize QObject first
        super().__init__()

        self._cupy_checked = False
        self._cupy_available = False
        self._context = GPUContext.NUMPY  # backing field
        self._device = 0  # backing field
        self.device_count = 1

        import numpy as np
        import pandas as pd
        import scipy
        import skimage

        self._xupy = BackendProxy(lambda:np)
        self._scipy = BackendProxy(lambda:scipy)
        self._df = BackendProxy(lambda:pd)
        self._skimage = BackendProxy(lambda:skimage)

        self.check_cupy()
    
    @property
    def context(self):
        """
        Return the current computational context (GPUContext).
        """
        return self._context
    
    @context.setter
    def context(self, value: GPUContext):
        """
        Set the computational context (GPUContext).
        Emits context_changed signal only if value actually changes.
        """
        old_context = self._context
        old_device = self._device
        self._context = value
        
        # Emit only if context or device changed
        if old_context != value:
            try:
                self.context_changed.emit(self._context, self._device)
            except Exception:
                pass  # Ignore if signal system not ready
        
    @property
    def device(self):
        """
        Return the current device ID.
        """
        return self._device
    
    @device.setter
    def device(self, value: int):
        """
        Set the current device ID.
        Emits context_changed signal only if value actually changes.
        """
        old_device = self._device
        old_context = self._context
        self._device = value
        
        # Emit only if device changed
        if old_device != value:
            try:
                self.context_changed.emit(self._context, self._device)
            except Exception:
                pass  # Ignore if signal system not ready
    
    @property
    def df(self):
        """
        Return the DataFrame backend module (pandas or cudf).
        """
        return self._df

    @property
    def xupy(self):
        """
        Return the array backend module (numpy or cupy).
        """
        return self._xupy
    
    @property
    def scipy(self):
        """
        Return the scientific backend module (scipy or cupyx).
        """
        return self._scipy


    @property
    def skimage(self):
        """
        Return the scientific backend module (scipy or cupyx).
        """
        return self._skimage
    def check_cupy(self):
        if not self._cupy_checked:
            self._cupy_checked = True
            try:
                import cupy as cp
                self._cupy_available = True
                self.device_count = cp.cuda.runtime.getDeviceCount()
            except ModuleNotFoundError:
                self._cupy_available = False
                logging.warning("CUPY module not found. Please install it via Conda or pip.")
            except Exception as e:
                self._cupy_available = False
                logging.error(e)
        return self._cupy_available


    def set_context(self, context: GPUContext = GPUContext.NUMPY, device: int = 0):
        if context == GPUContext.CUPY:
            if self.check_cupy():
                import cupy as cp
                if cp.cuda.runtime.getDeviceCount() <= device:
                    logging.warning(f"No GPU available with device ID {device}")
                else:
                    self.context = GPUContext.CUPY
                    self.device = device
                    import cupyx.scipy as cupyx_scipy
                    #import cudf
                    #import cucim.skimage as skimage
                    self._xupy = BackendProxy(lambda:cp)
                    self._scipy = BackendProxy(lambda: cupyx_scipy)
                    #self._df = BackendProxy(lambda: cudf)
                    #self._skimage = BackendProxy(lambda: skimage)

        elif context == GPUContext.NUMPY:
            self.context = GPUContext.NUMPY
            self.device = device
            import numpy as np
            import scipy
            import skimage
            self._xupy = BackendProxy(lambda: np)
            self._scipy = BackendProxy(lambda: scipy)
            self._df = BackendProxy(lambda: pd)
            self._skimage = BackendProxy(lambda: skimage)

        else:
            logging.warning("Unknown context. Context unchanged.")
            return

    def get_context(self):
        return {"context": self.context, "device": self.device}


    def asdataframe(self, data, context=None, device=None):
        return data
        #TODO Implement once cudf is available on 3.11 and 3.12
        if context is None:
            context = self.context
        if device is None:
            device = self.device

        if self._cupy_available:
            #import cudf
            pass

        if isinstance(data, pd.DataFrame):
            if context == GPUContext.CUPY:
                return proxy.df.from_pandas(data)
            
            else:
                return data
        elif isinstance(data, cudf.DataFrame):
            if context == GPUContext.NUMPY:
                return data.to_pandas()
            else:
                return data
        else:
            logger.warning(f"Unsupported data conversion. Data is of type {type(data)}. No Change made.")
            return data
        
    def asarray(self, data, context=None, device=None):

        if context is None:
            context = self.context
        if device is None: #Not used atm but may in future
            device = self.device

        if self._cupy_available:
            import cupy as cp

        if isinstance(data, np.ndarray):
            if context == GPUContext.CUPY:
                return proxy.xupy.asarray(data)
            else:
                return data

        elif isinstance(data, cp.ndarray):
            if context == GPUContext.NUMPY:
                return data.get()
            else:
                return data
            
        else:
            logger.warning(f"Unsupported data conversion. Data is of type {type(data)}. No Change made.")
            return data
            
        

class BackendProxy:
    def __init__(self, context_getter):
        """
        Initialize the proxy with a function to get the current backend context.
        :param context_getter: A callable that returns the current backend module (e.g., numpy or cupy).
        """
        self._context_getter = context_getter

    def __getattr__(self, name):
        """
        Dynamically resolve attributes or submodules.
        """
        backend = self._context_getter()  # Get the current backend (numpy, cupy, scipy, or cupyx)
        attr = getattr(backend, name)  # Get the attribute from the backend

        # If the attribute is a module (e.g., scipy.ndimage), wrap it in another BackendProxy
        if isinstance(attr, type(backend)):
            return BackendProxy(lambda: getattr(self._context_getter(), name))

        return attr

_env = None

def _get_env():
    global _env
    if _env is None:
        _env = EnvironmentContext()
    return _env



class EnvironmentProxy:
    """Plain Python facade: convenient global API + exposes signals."""
    def __getattr__(self, name):
        # forward everything to the QObject instance
        return getattr(_get_env(), name)

    # Optional: make it callable if you like proxy() returning the context
    def __call__(self):
        return _get_env()


proxy = EnvironmentProxy()