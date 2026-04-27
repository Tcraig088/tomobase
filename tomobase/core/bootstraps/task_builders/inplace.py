import copy

from functools import wraps

from ...base_classes import ImageAbstract
from ...log import logger

def _wrap_inplace(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.trace("Wrapped Execution: Deciding Wether to use copied or inplace data for execution")
        inplace = kwargs.pop("inplace", True)

        if not inplace:
            args_new = list(args)
            kwargs_new = dict(kwargs)
            for i, arg in enumerate(args):
                if isinstance(arg, ImageAbstract):
                    args_new[i] = copy.deepcopy(arg)

            for key, value in kwargs.items():
                if isinstance(value, ImageAbstract):
                    kwargs_new[key] = copy.deepcopy(value)
            return func(*args_new, **kwargs_new)
        else:
            return func(*args, **kwargs)
        
    return wrapper