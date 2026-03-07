import inspect
import copy
from collections.abc import Callable

from .utils import _process_registration
from .task_builders import _wrap_axial, _wrap_use_numpy, _wrap_inplace, _wrap_verbose, _wrap_measure, _build_decorated_function

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
def process_hook(**kwargs) -> Callable:
    """A decorator used to mark a function or class as a tomography process. The function or class is either a standard function or class used to define the process or a QWidget used to attach to napari.
    Args:
        name (str): the name of the process. Should be readable casing and spaces.
        category (enum.TransformCategory or List[enum.TransformCategory]): the category of the process. Should be a member of the TransformCategories enum.
        includes (list[enum.DataModules]): a list of data types that the process can handle. Either Numpy Cupy or Torch.
        excludes (list[enum.DataModules]): a list of strings that define the data types that the process cannot handle. Cannot define both includes and excludes
        subcategories (dict(enum.TransformCategory,[list[str]])): a list of strings that define the subcategories of the process. Used when adding the process to the napari menu.
    """
    use_numpy = kwargs.get("use_numpy", False)
    enable_axial = kwargs.get("enable_axial", False)
    
    def decorator(func):
        if inspect.isfunction(func):
            origin =  func
            params = [("inplace", bool, True), ("verbose_outputs", bool, False), ("measurements", list | None, None)]
            
            if enable_axial:
                func = _wrap_axial(func)
                params.append(("axial", int, -1))
            func = _wrap_measure(func)
            if use_numpy:
                func = _wrap_use_numpy(func)
            func = _wrap_inplace(func)
            func = _wrap_verbose(func)

            func = _build_decorated_function(origin, func, params)
            
        else:
            raise ValueError("The process_hook decorator can only be applied to functions for now.")


        func.tomobase_name = kwargs.get("name", func.__name__)
        func.is_tomobase_process = True
        func.tomobase_category = kwargs.get("category", 0)

        if func.__name__ == func.tomobase_name:
            func.tomobase_name = copy.deepcopy(func.__name__)
            func.tomobase_name = func.tomobase_name.replace('_', ' ').title()
        return func
        
    return decorator
