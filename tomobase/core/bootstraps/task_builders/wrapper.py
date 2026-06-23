from functools import wraps

def wraps_tomobase(func):
    def decorator(wrapper):
        wrapper = wraps(func)(wrapper)

        if hasattr(func,"_tomobase_name"):
            setattr(wrapper, "_tomobase_name", getattr(func, "_tomobase_name"))
            
        if hasattr(func,"_tomobase_kwargs"):
            setattr(wrapper, "_tomobase_kwargs", getattr(func, "_tomobase_kwargs"))
        
        if hasattr(func,"_tomobase_category"):
            setattr(wrapper, "_tomobase_category", getattr(func, "_tomobase_category"))
            
        if hasattr(func,"_raw"):
            setattr(wrapper, "_raw", getattr(func, "_raw"))
        return wrapper

    return decorator