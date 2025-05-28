from tomobase.registrations.base import ItemDict


class PhantomItemDict(ItemDict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._hook = 'is_tomobase_phantom'
        self._folder = 'phantoms'

TOMOBASE_PHANTOMS = PhantomItemDict()
TOMOBASE_PHANTOMS._hook = 'is_tomobase_phantom'
TOMOBASE_PHANTOMS._folder = 'phantoms'
TOMOBASE_PHANTOMS.update()