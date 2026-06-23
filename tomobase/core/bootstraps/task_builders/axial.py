
from functools import wraps

import xarray as xr

from ...data_classes import Measurement
from ...base_classes import ImageAbstract
from ...environment import proxy, GPUContext

def _wrap_axial(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        axis = kwargs.pop("axis", None)

        if axis is None:
            return func(*args, **kwargs)

        i_img_args = [i for i, arg in enumerate(args) if isinstance(arg, ImageAbstract)]
        key_img_kwargs = [key for key, value in kwargs.items() if isinstance(value, ImageAbstract)]

        if not i_img_args and not key_img_kwargs:
            return func(*args, **kwargs)

        image_list = [args[i] for i in i_img_args]
        image_list.extend(kwargs[key] for key in key_img_kwargs)

        axis_size = image_list[0].xr.sizes[axis]
        for img in image_list[1:]:
            if img.xr.sizes[axis] != axis_size:
                raise ValueError(f"Image sizes along axis {axis!r} do not match.")

        results = None
        results_was_tuple = True

        for i, outs in enumerate(zip(*(img.split(axis) for img in image_list))):
            args_i = list(args)
            kwargs_i = dict(kwargs)

            for arg_index, image_slice in zip(i_img_args, outs):
                args_i[arg_index] = image_slice

            offset = len(i_img_args)
            for key, image_slice in zip(key_img_kwargs, outs[offset:]):
                kwargs_i[key] = image_slice

            results_i = func(*args_i, **kwargs_i)
            if not isinstance(results_i, tuple):
                results_was_tuple = False
                results_i = (results_i,)

            if i == 0:
                results = list(results_i)
                continue

            for j, result_i in enumerate(results_i):
                result = results[j]
                if isinstance(result, ImageAbstract):
                    result.xr = xr.concat([result.xr, result_i.xr], dim=axis)
                elif isinstance(result, Measurement):
                    result.stack(result_i)
                else:
                    raise TypeError(f"Unsupported result type: {type(result_i)}")

        if results_was_tuple:
            return tuple(results)
        return results[0]
    return wrapper

