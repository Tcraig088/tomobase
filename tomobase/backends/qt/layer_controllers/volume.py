from .base import ImageAbstractController
from .. import registers
from ....core import data_classes

class VolumeController(ImageAbstractController):
    def __init__(self, model):
        super().__init__(model)

registers.controller_pairs.register()(data_classes.Volume, VolumeController)