from tomobase.registrations.base import ItemDict

class TiltSchemeItemDict(ItemDict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._hook = 'is_tomobase_tiltscheme'
        self._folder = 'tiltschemes'


tiltschemes_register = TiltSchemeItemDict()  
tiltschemes_register._hook = 'is_tomobase_tiltscheme'
tiltschemes_register._folder = 'tiltschemes'
tiltschemes_register.update() 