from tomobase.registrations.base import ItemDict

class TiltSchemeItemDict(ItemDict): pass  
TOMOBASE_TILTSCHEMES = TiltSchemeItemDict()  
TOMOBASE_TILTSCHEMES._hook = 'is_tomobase_tiltscheme'
TOMOBASE_TILTSCHEMES._folder = 'tiltschemes'
TOMOBASE_TILTSCHEMES.update() 