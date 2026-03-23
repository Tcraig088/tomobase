import copy

from ....data import Image

def _wrap_inplace(func):
    def wrapper(*args, **kwargs):
        inplace = kwargs.pop("inplace", True)

        if not inplace:
            args_new = list(args)
            kwargs_new = dict(kwargs)
            for i, arg in enumerate(args):
                if isinstance(arg, Image):
                    args_new[i] = copy.deepcopy(arg)

            for key, value in kwargs.items():
                if isinstance(value, Image):
                    kwargs_new[key] = copy.deepcopy(value)
            return func(*args_new, **kwargs_new)
        else:
            return func(*args, **kwargs)
        
    return wrapper