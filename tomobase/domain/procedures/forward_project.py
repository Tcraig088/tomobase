import astra
import numpy as np
from typing import Union, Tuple

from ...utils import _create_projector

from ...core import registers, progress
from ...core.data_classes.images import Volume, Sinogram
from ...core.base_classes import TiltSchemeCursor




from magicgui import magicgui
from magicgui.tqdm import trange


@registers.procedures.register(name='Project', category=registers.categories['Project'], use_numpy=True)
def project(volume:Volume, angles:Union[TiltSchemeCursor, np.ndarray], use_gpu:bool=True):
    """Create a sinogram from a volume using forward projection. The GPU Context is overriden due to underlying astra gpu usage. 
    Args:
        volume (Volume): The input volume to be projected.
        angles (Union[Tuple[TiltSchemeAbstract, slice], np.ndarray]): The angles at which to project the volume. Can be a TiltSchemeAbstract with a slice of angles or a numpy array of angles.
        use_gpu (bool): Whether to use GPU for projection. Default is True.
    Returns:
        Sinogram: The resulting sinogram.

    """
    if isinstance(angles, TiltSchemeCursor):
        angles = np.array(angles.angles)
        
    data = volume.data.transpose("z", "y", "x").values
    angles = np.asarray(angles)
    use_gpu = use_gpu and astra.use_cuda()

    z, y, x = data.shape
    proj_id = _create_projector(x, y, angles, use_gpu)

    sino = np.empty((z, len(angles), max(x, y)))
    
    progress_bar = progress.new(name="Forward projecting", total=z)
    for i in progress_bar:
        sino_id, sino[i, :, :] = astra.creators.create_sino(data[i, :, :], proj_id)
        astra.astra.delete(sino_id)

    sinogram = Sinogram(volume.name, np.transpose(sino, (1,0,2)), angles, volume.pixel_size)  # ASTRA gives (z, n, d)
    astra.astra.delete(proj_id)
    return sinogram