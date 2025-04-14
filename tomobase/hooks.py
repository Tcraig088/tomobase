import types
import copy
import inspect
from copy import deepcopy
from tomobase.log import logger
import re
from functools import wraps
from tomobase.registrations.environment import xp, GPUContext
from tomobase.data.base import Data
from inspect import signature, Parameter


def tomobase_hook_tiltscheme(name: str):
    """a decorator used to mark a class as a tiltscheme. The class is either a standard class used to define the tiltscheme or a QWidget used to attach to napari. 
    see the plugins tutorial for more information on how to use this decorator. returns a decorated class

    Args:
        name (str): the name of the tilt scheme. Should be readable casing and spaces. 
    """
    def decorator(cls):
        cls.tomobase_name = name
        cls.is_tomobase_tiltscheme = True
        return cls
    return decorator

def tomobase_hook_process(**kwargs):
    """A decorator used to mark a function or class as a tomography process. The function or class is either a standard function or class used to define the process or a QWidget used to attach to napari.
    Args:
        name (str): the name of the process. Should be readable casing and spaces.
        category (enum.TransformCategory or List[enum.TransformCategory]): the category of the process. Should be a member of the TransformCategories enum.
        includes (list[enum.DataModules]): a list of data types that the process can handle. Either Numpy Cupy or Torch.
        excludes (list[enum.DataModules]): a list of strings that define the data types that the process cannot handle. Cannot define both includes and excludes
        subcategories (dict(enum.TransformCategory,[list[str]])): a list of strings that define the subcategories of the process. Used when adding the process to the napari menu.
    """
    use_numpy = kwargs.get("use_numpy", False)
    isquantification = kwargs.get("isquantification", False)
    def decorator(obj):
        if inspect.isfunction(obj):
            if isquantification:
                wrapper = _quantification_wrapper(obj, use_numpy)
                wrapper.isquantification = True
            else:
                wrapper = _function_wrapper(obj, use_numpy)
            pass
        obj = _registration(wrapper, **kwargs)
        return obj
    return decorator


def _quantification_wrapper(func, use_numpy):
    original_sig = signature(func)
    params = list(original_sig.parameters.values())
    params = [param for param in params if param.name != "object"]
    params.append(Parameter("kwargs", kind=Parameter.VAR_KEYWORD))
    params.append(Parameter("units", kind=Parameter.KEYWORD_ONLY, default=use_numpy, annotation=str))
    params.append(Parameter("inplace", kind=Parameter.KEYWORD_ONLY, default=True, annotation=bool))
    params.append(Parameter("verbose_outputs", kind=Parameter.KEYWORD_ONLY, default=False, annotation=bool))
    
    
    params = sorted(
        params,
        key=lambda p: (
            0 if p.kind == Parameter.POSITIONAL_ONLY else
            1 if p.kind == Parameter.POSITIONAL_OR_KEYWORD else
            2 if p.kind == Parameter.VAR_POSITIONAL else
            3 if p.kind == Parameter.KEYWORD_ONLY else
            4  # Parameter.VAR_KEYWORD
        )
    )
    new_sig = original_sig.replace(parameters=params)

    @wraps(func)
    def wrapper(*args, units:str='a.u.', inplace:bool=True, verbose_outputs:bool=False, **kwargs):
        if use_numpy:
            xp.set_context(GPUContext.NUMPY, 0)
        context = xp.get_context()
        for arg in args:
            if isinstance(arg, Data):
                if not inplace:
                    arg = deepcopy(arg)
                arg.set_context()
        for key, value in kwargs.items():
            if isinstance(value, Data):
                if not inplace:
                    kwargs[key] = deepcopy(value)
                kwargs[key].set_context()
        results =  func(*args, **kwargs)
        xp.set_context(context)
        if isinstance(results, tuple) and verbose_outputs == False:
            return results[0]
        else:
            return results
    wrapper.__signature__ = new_sig
    return wrapper

def _function_wrapper(func, use_numpy):
    original_sig = signature(func)
    params = list(original_sig.parameters.values())
    params.append(Parameter("inplace", kind=Parameter.KEYWORD_ONLY, default=True, annotation=bool))
    params.append(Parameter("verbose_outputs", kind=Parameter.KEYWORD_ONLY, default=False, annotation=bool))
    params = sorted(
        params,
        key=lambda p: (
            0 if p.kind == Parameter.POSITIONAL_ONLY else
            1 if p.kind == Parameter.POSITIONAL_OR_KEYWORD else
            2 if p.kind == Parameter.VAR_POSITIONAL else
            3 if p.kind == Parameter.KEYWORD_ONLY else
            4  # Parameter.VAR_KEYWORD
        )
    )
    new_sig = original_sig.replace(parameters=params)

    @wraps(func)
    def wrapper(*args, inplace:bool=True, verbose_outputs:bool=False, **kwargs):
        if use_numpy:
            xp.set_context(GPUContext.NUMPY, 0)
        context = xp.get_context()
        for arg in args:
            if isinstance(arg, Data):
                if not inplace:
                    arg = deepcopy(arg)
                arg.set_context()
        for key, value in kwargs.items():
            if isinstance(value, Data):
                if not inplace:
                    kwargs[key] = deepcopy(value)
                kwargs[key].set_context()
        results =  func(*args, **kwargs)
        xp.set_context(context)
        if isinstance(results, tuple) and verbose_outputs == False:
            return results[0]
        else:
            return results
    wrapper.__signature__ = new_sig
    return wrapper



def _registration(obj, **kwargs):
    obj.tomobase_name = kwargs.get("name", obj.__name__)
    obj.is_tomobase_process = True
    obj.tomobase_category = kwargs.get("category", None)
    obj.tomobase_subcategories = deepcopy(kwargs.get("subcategories", []))
    if obj.tomobase_category is None:
        raise ValueError("category is required")
    
    if obj.__name__ == obj.tomobase_name:
        obj.tomobase_name = deepcopy(obj.__name__)
        obj.tomobase_name = obj.tomobase_name.replace('_', ' ').title()
        if inspect.isclass(obj):
            text = obj.tomobase_name
            obj.tomobase_name = re.sub(r'(?<!^)(?=[A-Z])', ' ', text)

    obj.tomobase_subcategories.append(obj.tomobase_name)    
    return obj


def tomobase_class_method(**kwargs):
    def decorator(func):
        for name, obj in inspect.getmembers(func):
            func.process_step = kwargs.get("step", "pre") # can be pre or final
            func.process_order = kwargs.get("order", 0)
        return func
    return decorator



