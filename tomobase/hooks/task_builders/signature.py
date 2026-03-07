
import makefun
import functools
import inspect 

def _build_decorated_function(func, wrapper, new_params):
    original_sig = inspect.signature(func)
    params = list(original_sig.parameters.values())

    # Add inplace and verbose_outputs as keyword-only parameters
    for name, annotation, default in new_params:
        params.append(inspect.Parameter(name,
                                kind=inspect.Parameter.KEYWORD_ONLY, 
                                default=default,
                                annotation=annotation))

    # Sort parameters so keyword-only are last
    params = sorted(
        params,
        key=lambda p: (
            0 if p.kind == inspect.Parameter.POSITIONAL_ONLY else
            1 if p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD else
            2 if p.kind == inspect.Parameter.VAR_POSITIONAL else
            3 if p.kind == inspect.Parameter.KEYWORD_ONLY else
            4
        )
    )
    new_sig = original_sig.replace(parameters=params)
    new_func = makefun.with_signature(new_sig)(functools.wraps(func)(wrapper))
    return new_func