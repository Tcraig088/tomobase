from tomobase.registrations.base import ItemDict


class PhantomItemDict(ItemDict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._hook = 'is_tomobase_phantom'
        self._folder = 'phantoms'

phantoms_register = PhantomItemDict()
phantoms_register._hook = 'is_tomobase_phantom'
phantoms_register._folder = 'phantoms'
phantoms_register.update()