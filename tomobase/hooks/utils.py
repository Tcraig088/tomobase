import inspect
import copy
import re



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



def _process_registration(obj, **kwargs):
    obj.tomobase_name = kwargs.get("name", obj.__name__)
    obj.is_tomobase_process = True
    obj.tomobase_category = kwargs.get("category", 0)

    if obj.__name__ == obj.tomobase_name:
        obj.tomobase_name = copy.deepcopy(obj.__name__)
        obj.tomobase_name = obj.tomobase_name.replace('_', ' ').title()
        if inspect.isclass(obj):
            text = obj.tomobase_name
            obj.tomobase_name = re.sub(r'(?<!^)(?=[A-Z])', ' ', text) 
    return obj


def _get_indices(items):
    img_indices = []
    measurements_indices = []
    if isinstance(items, Iterable) and not isinstance(items, dict):
        for i, item in enumerate(items):
            if isinstance(item, BaseImageModel):
                img_indices.append(i)
            elif isinstance(item, Analysis):
                measurements_indices.append(i)
        return img_indices, measurements_indices
    elif isinstance(items, dict):
        for key, item in items.items():
            if isinstance(item, BaseImageModel):
                img_indices.append(key)
            elif isinstance(item, Analysis):
                measurements_indices.append(key)
        return img_indices, measurements_indices

def _merge_results(results1, results2, axis):
    if not isinstance(results1, Iterable):
        results1 = [results1]
        results2 = [results2]
    
    final_results = []
    for r1, r2 in zip_longest(results1, results2, fillvalue=None):
        if r1 is None:
            final_results.append(r2)
        elif r2 is None:
            final_results.append(r1)
        elif isinstance(r1, BaseImageModel) and isinstance(r2, BaseImageModel):
            final_results.append(r1.stack(r2, axis=axis))
        elif isinstance(r1, Analysis) and isinstance(r2, Analysis):
            final_results.append(r1.stack(r2))
        else:
            if isinstance(r1, list):
                r1.append(r2)
                final_results.append(r1)
            elif type(r1) is type(r2):
                final_results.append([r1, r2])
            else:
                raise ValueError(f"Cannot merge results of type {type(r1)} and {type(r2)}")
    return final_results