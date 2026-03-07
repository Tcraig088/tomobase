from itertools import zip_longest
import inspect
import functools
from copy import deepcopy

import re
from functools import wraps
from tomobase.environment import proxy, GPUContext
from tomobase.data import BaseImageModel, Analysis, analysis
from inspect import signature, Parameter
from typing import Union, get_args
from collections.abc import Callable, Iterable
import makefun


from ..log import logger

def _build_process_signature(func, enable_measurements, enable_axial):
    original_sig = signature(func)
    params = list(original_sig.parameters.values())

    # Add inplace and verbose_outputs as keyword-only parameters
    params.append(Parameter("inplace", kind=Parameter.KEYWORD_ONLY, default=True, annotation=bool))
    params.append(Parameter("verbose_outputs", kind=Parameter.KEYWORD_ONLY, default=False, annotation=bool))
    if enable_measurements:
        params.append(Parameter("measurements", kind=Parameter.KEYWORD_ONLY, default=[], annotation=list))
    if enable_axial:
        params.append(Parameter("axial", kind=Parameter.KEYWORD_ONLY, default=False, annotation=bool))

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
    return original_sig.replace(parameters=params)

def _apply_signature(func, decorated_func, new_sig):
    new_func = makefun.with_signature(new_sig)(functools.wraps(func)(decorated_func))
    return new_func







def wrapper(*args, **kwargs):
    hint = wrapper.__annotations__
    count_measurements = get_args(hint['return']).count(Analysis) if 'return' in hint else 0

    # set wrapper common atributes for registered processes
    inplace = kwargs.pop("inplace", True)
    verbose_outputs = kwargs.pop("verbose_outputs", False)
    measurements = kwargs.pop("measurements", [])
    axial = kwargs.pop("axial", -1)

        if len(measurements) > count_measurements:
            raise ValueError(f"Too many measurements provided. Expected at most {count_measurements} but got {len(measurements)}")

        i_img_args, i_measurements_args = _get_indices(args)
        key_img_kwargs, key_measurements_kwargs = _get_indices(kwargs)

        # Sets the context to numpy if use_numpy is True. This allows the process to run on CPU even if the input data is on GPU. 
        if use_numpy:
            for i in i_img_args:
                args[i].set_context(GPUContext.NUMPY)
            for key in key_img_kwargs:
                kwargs[key].set_context(GPUContext.NUMPY)
            for i in i_measurements_args:
                args[i].set_context(GPUContext.NUMPY)
            for key in key_measurements_kwargs:
                kwargs[key].set_context(GPUContext.NUMPY)
            for measurement in measurements:
                measurement.set_context(GPUContext.NUMPY)
        
        # Populate entry function args and kwargs depending on using inplace memory or not
        if inplace:
           args_new = args
           kwargs_new = kwargs 
        else:
            args_new = list(args)
            kwargs_new = dict(kwargs)
            for i in i_img_args:
                args_new[i] = deepcopy(args[i])
            for key in key_img_kwargs:
                kwargs_new[key] = deepcopy(kwargs[key])

        if axial != -1:
            gens_args = [args_new[i].split(axis=axial) for i in i_img_args] 
            gens_kwargs = [kwargs_new[key].split(axis=axial) for key in key_img_kwargs]
            results = None
            for i, outs in enumerate(zip_longest(*gens_args, *gens_kwargs, fillvalue=None)):
                args_i = list(args_new)
                kwargs_i = dict(kwargs_new)
                for j, out in enumerate(outs[:len(gens_args)]):
                    if out is not None:
                        args_i[i_img_args[j]] = out
                for j, out in enumerate(outs[len(gens_args):]):
                    if out is not None:
                        kwargs_i[key_img_kwargs[j]] = out

                results_i = func(*args_i, **kwargs_i)
                if results is None:
                    results = results_i
                else:
                    results = _merge_results(results, results_i, axial)
    
        else:
            results = func(*args_new, **kwargs_new)

        if not isinstance(results, Iterable):
            results = [results]

        i = 0
        for j, item in enumerate(results):
            if isinstance(item, Analysis):
                results[j] = measurements[i].stack(item)
                i += 1

        if use_numpy:
            for i in i_img_args:
                args[i].set_context(proxy.xupy.get_context())
            for key in key_img_kwargs:
                kwargs[key].set_context(proxy.xupy.get_context())
            for i in i_measurements_args:
                args[i].set_context(proxy.xupy.get_context())
            for key in key_measurements_kwargs:
                kwargs[key].set_context(proxy.xupy.get_context())
            for measurement in measurements:
                measurement.set_context(proxy.xupy.get_context())

            for i in range(len(results)):
                if isinstance(results[i], BaseImageModel):
                    results[i].set_context(proxy.xupy.get_context())
                elif isinstance(results[i], Analysis):
                    results[i].set_context(proxy.xupy.get_context())
        
        #TODO The generate_slug for the process name should be moved to the copy function
        if not verbose_outputs:
            return results[0]
        else:
            return results

    return wrapper

