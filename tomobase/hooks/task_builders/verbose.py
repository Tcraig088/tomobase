
def _wrap_verbose(func):
    def wrapper(*args, **kwargs):
        extend_returns = kwargs.get("extend_returns", False)
        results = func(*args, **kwargs)

        if not isinstance(results, tuple):
            results = (results,)

        if extend_returns:
            return results
        else:
            return results[0]
    return wrapper