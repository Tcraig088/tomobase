from tomobase.registrations.base import ItemDict


class DataItemDict(ItemDict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

TOMOBASE_DATATYPES = DataItemDict( IMAGE=None, SINOGRAM=None, VOLUME=None)