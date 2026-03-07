
from ...data import BaseImageModel, Analysis
from ...environment import proxy, GPUContext

def _wrap_use_numpy(func):
    def wrapper(*args, **kwargs):
        for item in args:
            if isinstance(item, BaseImageModel) or isinstance(item, Analysis):
                item.set_context(GPUContext.NUMPY)

        for key, value in kwargs.items():
            if isinstance(value, BaseImageModel) or isinstance(value, Analysis):
                value.set_context(GPUContext.NUMPY)

        results = func(*args, **kwargs)

        if not isinstance(results, tuple):
            if isinstance(results, BaseImageModel) or isinstance(results, Analysis):
                results.set_context(proxy.xupy.get_context())
        else:
            for result in results:
                if isinstance(result, BaseImageModel) or isinstance(result, Analysis):
                    result.set_context(proxy.xupy.get_context())
        
        for item in args:
            if isinstance(item, BaseImageModel) or isinstance(item, Analysis):
                item.set_context(proxy.xupy.get_context())

        for key, value in kwargs.items():
            if isinstance(value, BaseImageModel) or isinstance(value, Analysis):
                value.set_context(proxy.xupy.get_context())

        return results