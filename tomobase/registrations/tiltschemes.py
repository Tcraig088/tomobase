from tomobase.registrations.base import ItemDict

class TiltSchemeItemDict(ItemDict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._hook = 'is_tomobase_tiltscheme'
        self._folder = 'tiltschemes'


TOMOBASE_TILTSCHEMES = TiltSchemeItemDict()  
TOMOBASE_TILTSCHEMES._hook = 'is_tomobase_tiltscheme'
TOMOBASE_TILTSCHEMES._folder = 'tiltschemes'
TOMOBASE_TILTSCHEMES.update() 