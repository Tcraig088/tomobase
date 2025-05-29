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
from typing import Union
from collections.abc import Iterable


def phantom_hook(name:str=''):

    """a decorator used to mark a function as a tomography process. The function is either a standard function used to define the process or a QWidget used to attach to napari. 
    see the plugins tutorial for more information on how to use this decorator. returns a decorated function

    Args:
        name (str): the name of the process. Should be readable casing and spaces. 
    """
    def decorator(func):
        local_name = name
        if local_name == '':
            local_name = func.__name__.replace('_', ' ')
        func.tomobase_name = local_name
        func.is_tomobase_phantom = True

        return func
    return decorator

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
    units = kwargs.get("units", None)
    def decorator(obj):
        if inspect.isfunction(obj):
                wrapper = _function_wrapper(obj, use_numpy, isquantification, units)
        obj = _registration(wrapper, **kwargs)
        return obj
    return decorator


def _function_wrapper(func, use_numpy, isquantification, units=None):
    original_sig = signature(func)
    params = list(original_sig.parameters.values())

    if isquantification:
        for i, param in enumerate(params):
            if param.name != "reference":
                if isinstance(param.annotation, type) and issubclass(param.annotation, Data):
                    params[i] = param.replace(annotation=dict[str, Data])
                    object_name = param.name

    params.append(Parameter("inplace", kind=Parameter.KEYWORD_ONLY, default=True, annotation=bool))
    params.append(Parameter("verbose_outputs", kind=Parameter.KEYWORD_ONLY, default=False, annotation=bool))
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

    @wraps(func)
    def wrapper(*args, inplace:bool=True, verbose_outputs:bool=False, **kwargs):
        if use_numpy:
            xp.set_context(GPUContext.NUMPY, 0)
        context = xp.get_context()
        for key, value in kwargs.items():
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    if isinstance(subvalue, Data):
                        if not inplace:
                            subvalue = deepcopy(subvalue)
                        subvalue.set_context()
            if isinstance(value, Data):
                if not inplace:
                    kwargs[key] = deepcopy(value)
                kwargs[key].set_context()
                
        if isquantification:
            results = _quantify(func, object_name, units, *args, **kwargs)     
        else:
            results =  func(*args, **kwargs)
        xp.set_context(context)
        if isinstance(results, tuple) and verbose_outputs == False:
            return results[0]
        else:
            return results
    wrapper.__signature__ = new_sig
    return wrapper

def _quantify(func, object_name, units, *args, **kwargs):
    object = kwargs.pop(object_name, None)
    if not isinstance(object, dict):
        object = {object_name: object}

    results_list = []
    names = [name.replace("_", " ") for name in object.keys()]
    for key, value in object.items():
        kwargs[object_name] = value
        output = func(*args, **kwargs)
        kwargs.pop(object_name, None)
        if not isinstance(output, tuple):
            output = (output,)

        results_list.append(output)       
        results_list = list(zip(*results_list))
            
        df = xp.df.DataFrame({})
        first_outputs = results_list.pop(0)
        if isinstance(first_outputs[0], xp.df.DataFrame):
            for i, output in enumerate(first_outputs):
                first_outputs[i].columns = [names[i]+"_x", names[i]+"_y"]
                df = xp.df.concat([df, first_outputs[i]], axis=1)
                df.metadata = {}
        if isinstance(first_outputs[0], xp.xupy.ndarray):
            df = xp.df.DataFrame({'x':names, 'y':first_outputs} )
            df.metadata ={}
        else:
            df = xp.df.DataFrame({'x':names, 'y':first_outputs} )
            df.metadata = {}
                
        df.metadata['data type'] = type(value).__name__
        if units is not None:
            if isinstance(units, str):
                df.metadata['unit_x'] = "(a.u.)"
                df.metadata['unit_y'] = units
            elif isinstance(units, dict):
                df.metadata['unit_x'] = units['x']
                df.metadata['unit_y'] = units['y']
            else:
                raise ValueError("units must be a string or a dict with x and y keys")
        return df, *results_list

def _registration(obj, **kwargs):
    obj.tomobase_name = kwargs.get("name", obj.__name__)
    obj.is_tomobase_process = True
    obj.tomobase_category = kwargs.get("category", None)
    obj.tomobase_subcategories = deepcopy(kwargs.get("subcategories", []))
    obj.tomobase_quantification = kwargs.get("isquantification", False)
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



