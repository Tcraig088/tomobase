
from ...data_classes import Measurement
from ...base_classes import ImageAbstract
from ...environment import proxy, GPUContext
from ...log import logger
from functools import wraps

def _wrap_use_context(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.trace("Wrapped Execution: Setting context to specified GPU/CPU")
        context = proxy.get_context()
        for item in args:
            if isinstance(item, ImageAbstract) or isinstance(item, Measurement):
                item.set_context(*context)

        for key, value in kwargs.items():
            if isinstance(value, ImageAbstract) or isinstance(value, Measurement):
                value.set_context(*context)

        return func(*args, **kwargs)
    
    return wrapper


def _wrap_use_numpy(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.trace("Wrapped Execution: Setting context to NUMPY")
        for item in args:
            if isinstance(item, ImageAbstract) or isinstance(item, Measurement):
                item.set_context(GPUContext.NUMPY)

        for key, value in kwargs.items():
            if isinstance(value, ImageAbstract) or isinstance(value, Measurement):
                value.set_context(GPUContext.NUMPY)

        return func(*args, **kwargs)
    return wrapper

def _wrap_restore_context(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.trace("Wrapped Execution: Restoring Original Context")
        restore_context = kwargs.pop("restore_context", True)
        results = func(*args, **kwargs)
        
        if restore_context:
            for item in args:
                if isinstance(item, ImageAbstract) or isinstance(item, Measurement):
                    item.set_context(GPUContext.NUMPY)

            for key, value in kwargs.items():
                if isinstance(value, ImageAbstract) or isinstance(value, Measurement):
                    value.set_context(GPUContext.NUMPY)

            for i, result in enumerate(results):
                if isinstance(result, ImageAbstract) or isinstance(result, Measurement):
                    results[i].set_context(GPUContext.NUMPY)
        return results
    return wrapper