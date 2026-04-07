import pytest
import numpy as np
import itertools

from tomobase.domain import phantoms, procedures
from tomobase.core.data_classes import tiltschemes

@pytest.fixture
def get_volume():
    return phantoms.get_nanocage()

@pytest.fixture
def get_sinogram():
    volume = phantoms.get_nanocage()
    grs = tiltschemes.GRS()
    grs.generate_angles_from_slice(slice(0, 100))
    
    sino = procedures.project(volume, grs.angles)
    return sino
