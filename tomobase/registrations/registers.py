from tomobase.registrations.environment import EnvironmentRegistration
from tomobase.registrations.datatypes import DataItemDict
from tomobase.napari.layer_widgets.sinogram import SinogramDataWidget
from tomobase.napari.layer_widgets.image import ImageDataWidget
from tomobase.napari.layer_widgets.volume import VolumeDataWidget

TOMOBASE_DATATYPES = DataItemDict( IMAGE=ImageDataWidget, SINOGRAME=SinogramDataWidget, VOLUME=VolumeDataWidget)
TOMOBASE_ENVIRONMENT_REGISTRATION = EnvironmentRegistration()