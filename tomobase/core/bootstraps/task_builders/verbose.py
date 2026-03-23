
def _wrap_verbose(func):
    def wrapper(*args, **kwargs):
        verbose_outputs = kwargs.pop("verbose_outputs", False)
        results = func(*args, **kwargs)

        if not isinstance(results, tuple):
            results = (results,)

        if verbose_outputs:
            return results
        else:
            return results[0]
    return wrapper