
from .. import registers
from .base import ImageAbstractController
from ....core import data_classes


class SinogramController(ImageAbstractController):
    def __init__(self, model):
        super().__init__(model)

registers.controller_pairs.register()(data_classes.Sinogram, SinogramController)