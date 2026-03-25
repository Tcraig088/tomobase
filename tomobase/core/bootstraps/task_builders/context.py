
from ...data_classes import Image, Measurement
from ...environment import proxy, GPUContext

def _wrap_use_context(func):
    def wrapper(*args, **kwargs):

        context = proxy.get_context()
        for item in args:
            if isinstance(item, Image) or isinstance(item, Measurement):
                item.set_context(*context)

        for key, value in kwargs.items():
            if isinstance(value, Image) or isinstance(value, Measurement):
                value.set_context(*context)

        return func(*args, **kwargs)
    
    return wrapper


def _wrap_restore_context(func):
    def wrapper(*args, **kwargs):
        restore_context = kwargs.pop("restore_context", True)
        results = func(*args, **kwargs)
        
        if restore_context:
            for item in args:
                if isinstance(item, Image) or isinstance(item, Measurement):
                    item.set_context(GPUContext.NUMPY)

            for key, value in kwargs.items():
                if isinstance(value, Image) or isinstance(value, Measurement):
                    value.set_context(GPUContext.NUMPY)

            if not isinstance(results, tuple):
                if isinstance(results, Image) or isinstance(results, Measurement):
                    results.set_context(GPUContext.NUMPY)
                    
            else:
                for i, result in enumerate(results):
                    if isinstance(result, Image) or isinstance(result, Measurement):
                        results[i].set_context(GPUContext.NUMPY)
        return results
    return wrapper


def _wrap_use_numpy(func):
    def wrapper(*args, **kwargs):
        for item in args:
            if isinstance(item, Image) or isinstance(item, Measurement):
                item.set_context(GPUContext.NUMPY)

        for key, value in kwargs.items():
            if isinstance(value, Image) or isinstance(value, Measurement):
                value.set_context(GPUContext.NUMPY)

        return func(*args, **kwargs)
    return wrapper