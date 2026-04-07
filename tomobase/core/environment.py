import enum
import numpy as np
from tomobase.core.log import logger
import dask.array as da


class GPUContext(enum.Enum):
    CUPY = 1
    NUMPY = 2


class EnvironmentContext():
    def __init__(self, context:GPUContext = GPUContext.NUMPY, device:int = 0):
        self._context = context
        self._device = device
        self._cupy_enabled = False
        self._available_devices:int = 1

        try:
            import cupy as cp
            self._cupy_enabled = True
        except ImportError:
            self._cupy_enabled = False

        if self._cupy_enabled:
            self._available_devices = cp.cuda.runtime.getDeviceCount()

    @property
    def context(self):
        return self._context
    
    @property
    def device(self):
        return self._device
    
    def get_context(self):
        return self._context, self._device
    
    def show_available_devices(self):
        if self._cupy_enabled:
            for i in range(self._available_devices):
                import cupy as cp
                device = cp.cuda.Device(i)
                logger.info(f"Device {i}: {device}")
        else:
            logger.info("CuPy is not enabled. No GPU devices available.")

    def set_context(self, context: GPUContext, device: int = 0, set_param=True):
        if context == GPUContext.CUPY and not self._cupy_enabled:
            logger.warning("CuPy is not enabled. Falling back to NumPy.")
            context = GPUContext.NUMPY

        if self._available_devices <= device:
            logger.warning(f"Requested device {device} is not available. Falling back to device 0.")
            device = 0


        if set_param:
            self._context = context
            self._device = device
        return context, device

    def set_array_context(self, array, current_context, current_device, context: GPUContext, device: int = 0):
        if isinstance(array.data, da.Array):
            xp = da
        else:
            xp = array.data.__array_namespace__()

        valid_state = True
        if current_context == GPUContext.CUPY:
            if xp is not cp:
                valid_state = False
            else:
                if current_device != array.device.id:
                    valid_state = False

        elif current_context == GPUContext.NUMPY:
            if xp is not np:
                valid_state = False

        if not valid_state:        
            raise ValueError(f"Array context {xp} does not match expected context {current_context} on device {current_device}")
        
        context, device = self.set_context(context, device, set_param=False)
        if context == GPUContext.CUPY:
            cp.Device(device).use()
            if xp is np:
                array = cp.asarray(array)
            else:
                if device != current_device:
                    with cp.cuda.Device(device):
                        array = array.copy()

        #elif context == GPUContext.NUMPY:
            #if xp is not np:
            #    array = array.get()
        return array
        
proxy = EnvironmentContext()