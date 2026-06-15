import itertools
import numpy as np


from ..core.environment import GPUContext

def iter_indexers_with_len(shape: dict[str, int], dims: list[str]):
    """Creates a generator that yields all permutations of the specified dimensions. This allows user to iterate over all combinations of the specified dimensions in a multi-dimensional array or dataset.

    Args:
        shape (dict[str, int]): A dictionary mapping dimension names to their sizes.
        dims (list[str]): A list of dimension names to iterate over.

    Returns:
        tuple[int, generator[dict[str, int]]]: A tuple containing the total number of combinations and a generator that yields dictionaries mapping dimension names to their current values.

    """
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
        