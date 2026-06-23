import inspect
import copy
from collections.abc import Callable

from ..environment import proxy, GPUContext, EnvironmentContext
from .task_builders import _wrap_axial, _wrap_process_context, _wrap_strip_process_context, _wrap_tuple, _wrap_use_numpy,_wrap_restore_context, _wrap_use_context, _wrap_inplace, _wrap_returns, _wrap_measurements_validate, _wrap_measurements_return, _build_decorated_function, _wrap_history

def bootstrap_procedure(func: Callable) -> Callable:
    """Initialize a registered tomography procedure."""

    kwargs = getattr(func, "_tomobase_kwargs", {})

    use_numpy = kwargs.get("use_numpy", False)
    inplace = kwargs.get("inplace", True)

    if not inspect.isfunction(func):
        raise ValueError("bootstrap_procedure can only be applied to functions for now.")

    origin = func

    params = [
        ("inplace", bool, inplace),
        ("verbose_outputs", bool, False),
        ("measurements", list | None, None),
        ("proxy", EnvironmentContext, proxy),
        ("restore_context", bool, True),
    ]

    func = _wrap_tuple(func)
    func = _wrap_measurements_return(func)
    func = _wrap_history(func)
    func = _wrap_restore_context(func)
    func = _wrap_returns(func)

    func = _wrap_measurements_validate(func)

    if use_numpy:
        func = _wrap_use_numpy(func)
    else:
        func = _wrap_use_context(func)

    func = _wrap_inplace(func)

    func = _build_decorated_function(origin, func, params)

    return func
