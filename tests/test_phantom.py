
import pytest

from tomobase.core.data_classes import images, tiltschemes
from tomobase.domain import phantoms

import numpy as np

def test_phantoms():
    """test phantoms are imported correctly and are type correct
    currently tests 3 phantoms nanocage, nanorod and nanocube
    """
    phantom = phantoms.get_nanocage()
    assert phantom.xr.shape == (307, 307, 307)
    assert phantom.pixelsize == 1.0
    assert np.isclose(np.max(phantom.xr), 1.0, atol=1e4)
    assert isinstance(phantom, Volume)
    
    phantom = get_nanorod()
    assert phantom.data.shape == (512, 512, 512)
    assert phantom.pixelsize == 1.0
    assert np.isclose(np.max(phantom.data), 1.0, atol=1e4)
    assert isinstance(phantom, Volume)

    phantom = get_nanocube()
    assert phantom.data.shape == (512, 512, 512)
    assert phantom.pixelsize == 1.0
    assert np.isclose(np.max(phantom.data), 1.0, atol=1e4)
    assert isinstance(phantom, Volume)
    
    
