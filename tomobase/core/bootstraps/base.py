import inspect
import copy
from collections.abc import Callable

from ..environment import proxy, GPUContext, EnvironmentContext
from .task_builders import _wrap_axial, _wrap_process_context, _wrap_strip_process_context, _wrap_tuple, _wrap_use_numpy,_wrap_restore_context, _wrap_use_context, _wrap_inplace, _wrap_returns, _wrap_measurements_validate, _wrap_measurements_return, _build_decorated_function, _wrap_history

def bootstap_procedure(**kwargs) -> Callable:
    """A decorator used to mark a function or class as a tomography procedure. The function or class is either a standard function or class used to define the procedure or a QWidget used to attach to napari.
    
    This converts a function from
    
    ```python
    def my_procedure(args, kwargs) -> np.ndarray:
        # do something with data
        return data
    ```
    
    ```python
    def my_procedure(args, kwargs, inplace: bool = True, verbose_outputs: bool = False, measurements: list | None = None, proxy: EnvironmentContext = proxy, restore_context: bool = True) -> np.ndarray:
        # do something with data
        return data
    ```
    
    Args:
        name (str): the name of the procedure. Should be readable casing and spaces.
        use_numpy (bool, optional): overrides the default behavior of EnvironmentContext to always set the context to Numpy useful when the function uses some library that is not compatible with this library
        inplace (bool, optional): whether the procedure modifies the input data in place. Defaults to True.
    """
    use_numpy = kwargs.get("use_numpy", False)
    inplace = kwargs.get("inplace", True)
    
    def decorator(func):
        if inspect.isfunction(func):
            origin =  func
           
            params = [
                ("inplace", bool, inplace),
                ("verbose_outputs", bool, False),
                ("measurements", list | None, None),
                ("proxy", EnvironmentContext, proxy),
                ("restore_context", bool, True),
            ]
            #if enable_axial:
                #func = _wrap_axial(func)
                #params.append(("axial", int, -1))
            
            
            #func = _wrap_strip_process_context(func)
            #Be careful of the execution order
            #Things happen in the reverse order they are defined
            # However post execution steps are double reversed because the previous function is called in the new one 
            
            #post execution steps: execution order tuple -> returns
            func = _wrap_tuple(func) # should be executedc before any process that works with returns
            func = _wrap_measurements_return(func)
            func = _wrap_history(func)
            func = _wrap_restore_context(func)
            func = _wrap_returns(func)
            
            #pre execution steps: execution order inplace -> validate
            func = _wrap_measurements_validate(func)
            if use_numpy:
                func = _wrap_use_numpy(func)
            else:
                func = _wrap_use_context(func)
            func = _wrap_inplace(func)
            #func = _wrap_process_context(func, default_inplace=inplace)
            func = _build_decorated_function(origin, func, params)
            
        else:
            raise ValueError("The process_hook decorator can only be applied to functions for now.")
        return func
    return decorator
