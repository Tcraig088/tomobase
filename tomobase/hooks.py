import types
import copy
import inspect
import functools
from copy import deepcopy

import re
from functools import wraps
from tomobase.environment import proxy, GPUContext
from tomobase.data import BaseImageModel
from inspect import signature, Parameter
from typing import Union
from collections.abc import Callable, Iterable
import makefun
import coolname

from .log import logger

def phantom_hook(name:str| None= None) -> Callable:
    #use sphynx style
    """
    A decorator used to mark a function as a phantom. The function must return a Volume class.
    
    Args:
        name (str | None): The name of the phantom. Should be human readable casing.
    
    Returns:
        Callable: The decorated function.
    """
    def decorator(func):
        hook_name = name if name is not None else func.__name__.replace('_', ' ')
        func.tomobase_name = name
        func.is_tomobase_phantom = True

        return func
    
    return decorator

def tiltscheme_hook(name: str) -> Callable:
    """
    A decorator used to mark a class as a tiltscheme. The class must be a child of the TiltScheme class.

    :param name: the name of the tilt scheme. Should be human readable casing.
    :type name: str
    :return: the decorated class
    :rtype: Callable
    """
    def decorator(cls):
        #TODO: Check if the class is a child of the TiltScheme class
        cls.tomobase_name = name
        cls.is_tomobase_tiltscheme = True
        return cls
    return decorator

def process_hook(**kwargs):
    """A decorator used to mark a function or class as a tomography process. The function or class is either a standard function or class used to define the process or a QWidget used to attach to napari.
    Args:
        name (str): the name of the process. Should be readable casing and spaces.
        category (enum.TransformCategory or List[enum.TransformCategory]): the category of the process. Should be a member of the TransformCategories enum.
        includes (list[enum.DataModules]): a list of data types that the process can handle. Either Numpy Cupy or Torch.
        excludes (list[enum.DataModules]): a list of strings that define the data types that the process cannot handle. Cannot define both includes and excludes
        subcategories (dict(enum.TransformCategory,[list[str]])): a list of strings that define the subcategories of the process. Used when adding the process to the napari menu.
    """
    use_numpy = kwargs.get("use_numpy", False)
    def decorator(obj):
        if inspect.isfunction(obj):
                wrapper = _function_wrapper(obj, use_numpy)
        obj = _registration(wrapper, **kwargs)
        return obj
    return decorator


def _function_wrapper(func, use_numpy):
    original_sig = signature(func)
    params = list(original_sig.parameters.values())

    # Add inplace and verbose_outputs as keyword-only parameters
    params.append(Parameter("inplace", kind=Parameter.KEYWORD_ONLY, default=True, annotation=bool))
    params.append(Parameter("verbose_outputs", kind=Parameter.KEYWORD_ONLY, default=False, annotation=bool))

    # Sort parameters so keyword-only are last
    params = sorted(
        params,
        key=lambda p: (
            0 if p.kind == Parameter.POSITIONAL_ONLY else
            1 if p.kind == Parameter.POSITIONAL_OR_KEYWORD else
            2 if p.kind == Parameter.VAR_POSITIONAL else
            3 if p.kind == Parameter.KEYWORD_ONLY else
            4
        )
    )

    new_sig = original_sig.replace(parameters=params)
     

    @makefun.with_signature(new_sig)
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        inplace = kwargs.pop("inplace", True)
        verbose_outputs = kwargs.pop("verbose_outputs", False)
        logger.debug(f"Running process {func.__name__} with inplace={inplace} and verbose_outputs={verbose_outputs}")
        logger.debug(f"Arguments: {args}, {kwargs}")
        if use_numpy:
            proxy.set_context(GPUContext.NUMPY, 0)
        context = proxy.get_context()
        for key, value in kwargs.items():
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    if isinstance(subvalue, BaseImageModel):
                        if not inplace:
                            subvalue = deepcopy(subvalue)
                        subvalue.set_context()
            if isinstance(value, BaseImageModel):
                if not inplace:
                    kwargs[key] = deepcopy(value)
                kwargs[key].set_context()
        results = func(*args, **kwargs)
        proxy.set_context(context)
        
        if not isinstance(results, Iterable):
            results = [results]
            
        for item in results:
            if isinstance(item, BaseImageModel) and not inplace:
                item.process_name = coolname.generate_slug(2)
        if not verbose_outputs:
            return results[0]
        else:
            return results

    return wrapper

def _registration(obj, **kwargs):
    obj.tomobase_name = kwargs.get("name", obj.__name__)
    obj.is_tomobase_process = True
    obj.tomobase_category = kwargs.get("category", 0)
    obj.tomobase_quantification = kwargs.get("isquantification", False)

    if obj.__name__ == obj.tomobase_name:
        obj.tomobase_name = deepcopy(obj.__name__)
        obj.tomobase_name = obj.tomobase_name.replace('_', ' ').title()
        if inspect.isclass(obj):
            text = obj.tomobase_name
            obj.tomobase_name = re.sub(r'(?<!^)(?=[A-Z])', ' ', text)
  
    return obj


def class_process(**kwargs):
    def decorator(func):
        for name, obj in inspect.getmembers(func):
            func.process_step = kwargs.get("step", "pre") # can be pre or final
            func.process_order = kwargs.get("order", 0)
        return func
    return decorator



