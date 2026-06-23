from ...base_classes import ImageAbstract
from ...environment import GPUContext
from ...log import logger
from ..process_variables import ProcessVariables
from ...environment import proxy
from functools import wraps

from .wrapper import wraps_tomobase


def _wrap_strip_process_context(func):
    @wraps_tomobase(func)
    def wrapper(*args, **kwargs):
        kwargs.pop("__tomobase_context_key__", None)
        return func(*args, **kwargs)

    return wrapper


def _wrap_process_context(func, *, default_inplace=True, default_proxy=proxy):
    @wraps_tomobase(func)
    def wrapper(*args, **kwargs):
        ctx = ProcessVariables(
            inplace=kwargs.pop("inplace", default_inplace),
            verbose_outputs=kwargs.pop("verbose_outputs", False),
            measurements=kwargs.pop("measurements", None),
            proxy=kwargs.pop("proxy", default_proxy),
            restore_context=kwargs.pop("restore_context", True),
        )

        kwargs["__tomobase_context_key__"] = ctx
        return func(*args, **kwargs)

    return wrapper

def _wrap_use_context(func):
    @wraps_tomobase(func)
    def wrapper(*args, **kwargs):
        logger.trace("Wrapped Execution: Setting context to specified GPU/CPU")
        proxy = kwargs.get("proxy", None)
        context = proxy.get_context()
        for item in args:
            if isinstance(item, ImageAbstract):
                item.set_context(*context)

        for key, value in kwargs.items():
            if isinstance(value, ImageAbstract):
                value.set_context(*context)

        return func(*args, **kwargs)
    
    return wrapper


def _wrap_use_numpy(func):
    @wraps_tomobase(func)
    def wrapper(*args, **kwargs):
        logger.trace("Wrapped Execution: Setting context to NUMPY")
        for item in args:
            if isinstance(item, ImageAbstract):
                item.set_context(GPUContext.NUMPY)

        for key, value in kwargs.items():
            if isinstance(value, ImageAbstract):
                value.set_context(GPUContext.NUMPY)

        return func(*args, **kwargs)
    return wrapper

def _wrap_restore_context(func):
    @wraps_tomobase(func)
    def wrapper(*args, **kwargs):
        logger.trace("Wrapped Execution: Restoring Original Context")
        proxy = kwargs.get("proxy", None)
        restore_context = kwargs.pop("restore_context", True)
        results = func(*args, **kwargs)
        
        if restore_context:
            for item in args:
                if isinstance(item, ImageAbstract):
                    item.set_context(GPUContext.NUMPY)

            for key, value in kwargs.items():
                if isinstance(value, ImageAbstract):
                    value.set_context(GPUContext.NUMPY)

            for i, result in enumerate(results):
                if isinstance(result, ImageAbstract):
                    results[i].set_context(GPUContext.NUMPY)
        return results
    return wrapper