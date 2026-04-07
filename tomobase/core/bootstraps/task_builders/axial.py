
from itertools import zip_longest

from ...data_classes import Measurement
from ...base_classes import ImageAbstract
from ...environment import proxy, GPUContext

def _wrap_axial(func):
    def wrapper(*args, **kwargs):
        axis = kwargs.get("axis", None)

        if axis is not None:
            args_i = list(args)
            kwargs_i = dict(kwargs)
            
            i_img_args = [i for i, arg in enumerate(args) if isinstance(arg, ImageAbstract)]
            key_img_kwargs = [key for key, value in kwargs.items() if isinstance(value, ImageAbstract)]
            image_list = [args[i] for i in i_img_args] + [kwargs[key] for key in key_img_kwargs]
            for i, outs in enumerate(zip_longest(*[img.split(axis) for img in image_list], fillvalue=None)):
                args_i[i_img_args] = outs[:len(i_img_args)]
                kwargs_i.update({key_img_kwargs[j]: outs[len(i_img_args) + j] for j in range(len(key_img_kwargs))})
                results_i = func(*args_i, **kwargs_i)
                if i == 0:
                    results = results_i
                else:
                    for j in range(len(results_i)):
                        if isinstance(results_i[j], ImageAbstract):
                            results[j] = results[j].insert(results_i[j], axis=axis)
                        elif isinstance(results_i[j], Measurement):
                            results[j] = results[j].insert(results_i[j])
                        else:
                            raise TypeError(f"Unsupported result type: {type(results_i[j])}")

        else:
            results = func(*args, **kwargs)

        return results
    return wrapper