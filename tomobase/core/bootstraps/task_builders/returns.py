

from functools import wraps
from itertools import zip_longest
import random
from ...data_classes import Measurement
from ...base_classes import ImageAbstract
from ...environment import proxy, GPUContext
from ...log import logger

from .wrapper import wraps_tomobase

def is_array_like(x):
    return hasattr(x, "shape") and hasattr(x, "dtype")

def _wrap_tuple(func):
    """
    A wrapper function that ensures the output of the decorated function is always a tuple. If the output is not a tuple, it will be converted to a tuple with a single element. Useful for later data processing.
    Args:
        func (callable): The function to be decorated.
        
        Returns:
            callable: The decorated function that always returns a tuple.
    """
    @wraps_tomobase(func)
    def wrapper(*args, **kwargs):
        kwargs.pop("proxy", None)
        logger.trace("Wrapped Execution: Packing Results into tuple")
        results = func(*args, **kwargs)
        if not isinstance(results, tuple):
            results = (results,)
        return results
    return wrapper

def _wrap_returns(func):
    """
    A wrapper function that controls the verbosity of the function's output. If verbose_outputs is True, the function returns all results as a tuple. If False, it returns only the first result.
    Args:
        func (callable): The function to be decorated.
        
        Returns:
            callable: The decorated function that respects the verbose_outputs flag.
    """
    @wraps_tomobase(func)
    def wrapper(*args, **kwargs):
        logger.trace("Wrapped Execution: Unpacking tuple")
        verbose_outputs = kwargs.pop("verbose_outputs", False)
        results = func(*args, **kwargs)

        if verbose_outputs:
            if len(results)==1:
                return results[0]
            return results
        else:
            return results[0]
    return wrapper


def _wrap_history(func):
    """
    A wrapper function that records the computational history of the function's execution. It stores the input arguments and their types in the metadata of the resulting ImageAbstract objects.
    Args:
        func (callable): The function to be decorated.
        
        Returns:
            callable: The decorated function that records computational history.
    """
    @wraps_tomobase(func)
    def wrapper(*args, **kwargs):
        logger.trace("Wrapped Execution: Creating Event History")
        results = func(*args, **kwargs)
        
        _history = {}
        his_kwargs = dict(kwargs)
        his_kwargs.pop("measurements", None)
        for key, value in his_kwargs.items():
            if isinstance(value, ImageAbstract):
                his_kwargs[key] = f'{value.name}[{value.process_name}]'
            elif isinstance(value, Measurement):
                his_kwargs[key] = f'{value.name}'
            elif is_array_like(value):
                his_kwargs[key] = f'array[{value.shape}]'
            else:
                his_kwargs[key] = str(value)
            

        _history[func.__name__] = his_kwargs
        
        for result in results:
            if isinstance(result, ImageAbstract):
                if "Computational History" not in result.metadata:
                    result.metadata["Computational History"] = _history
                else:
                    if func.__name__ not in result.metadata["Computational History"]:
                        result.metadata["Computational History"][func.__name__] = his_kwargs
                    else:
                        result.metadata["Computational History"][f"{func.__name__}_{random.randint(0, 256)}"] = his_kwargs

        return results
    return wrapper