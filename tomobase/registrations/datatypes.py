from os import name
from ..data import *
from .base import ItemDict


class DataItemDict(ItemDict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

image_datatypes_register = DataItemDict( Data=ImageAbstract, Image=Image, Sinogram=Sinogram, Volume=Volume)