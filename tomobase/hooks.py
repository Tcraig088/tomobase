
def tomobase_hook_tiltscheme(name):
    def decorator(cls):
        cls.tomobase_name = name
        cls.is_tomobase_tiltscheme = True
        return cls
    return decorator