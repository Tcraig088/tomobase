from os import name
from tomobase.registrations.base import ItemDict
from tomobase.data import images

class DataItemDict(ItemDict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

image_datatypes_register = DataItemDict( Data=images.Image, Image=images.Image, Sinogram=images.Sinogram, Volume=images.Volume)