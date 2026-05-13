import itertools
import numpy as np


from ..core.environment import GPUContext

def iter_indexers_with_len(shape, dims):
    total = 1
    for d in dims:
        total *= shape[d]

    def gen():
        ranges = [range(shape[d]) for d in dims]
        for values in itertools.product(*ranges):
            yield dict(zip(dims, values))

    return total, gen()

def get_module(name, context=None):
    if context == GPUContext.CUPY:
        match name:
            case 'ndimage':
                import cupyx.scipy.ndimage as module
                return module
            case _:
                raise ValueError(f"Module {name} not found for context {context}")
    else:
        match name:
            case 'ndimage':
                import scipy.ndimage as module
                return module
            case _:
                raise ValueError(f"Module {name} not found for context {context}")
        