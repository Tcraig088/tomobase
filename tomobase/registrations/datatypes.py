from os import name
from tomobase.registrations.base import ItemDict


class DataItemDict(ItemDict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_class(self, type_id):
        name = TOMOBASE_DATATYPES.loc(type_id).name

        import tomobase.data
        return getattr(tomobase.data, name, None)
    
        return self.get(type_id)

TOMOBASE_DATATYPES = DataItemDict( Data=None, Image=None, Sinogram=None, Volume=None)