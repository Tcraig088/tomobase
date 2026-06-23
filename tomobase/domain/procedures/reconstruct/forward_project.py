import astra
import numpy as np
from typing import Union, Tuple


from .geometries import _create_astra_2d_geom, format_before_projection, format_after_projection, Projector

from ....core import registers, progress, proxy, GPUContext
from ....core.data_classes.images import Volume, Sinogram
from ....core.base_classes import TiltSchemeCursor, ImageAbstract
from ....core import utils

print('type tester', type(Sinogram), type(Volume), type(ImageAbstract))

@registers.procedures.register(name='Astra Slice Project', category=registers.categories['Project'], use_numpy=True)
def astra_project(volume:Volume, angles:Union[TiltSchemeCursor, np.ndarray]):
    """Create a sinogram from a volume using forward projection. The GPU Context is overriden due to underlying astra gpu usage. 
    Args:
        volume (Volume): The input volume to be projected.
        angles (Union[Tuple[TiltSchemeAbstract, slice], np.ndarray]): The angles at which to project the volume. Can be a TiltSchemeAbstract with a slice of angles or a numpy array of angles.
        use_gpu (bool): Whether to use GPU for projection. Default is True.
    Returns:
        Sinogram: The resulting sinogram.

    """
    sinogram, volume, angles = format_before_projection(volume, angles)
    proj_id = _create_astra_2d_geom(volume, angles)
    
    progress_bar = progress.new(name="Forward projecting", total=volume.xr.sizes['y'])
    for i in progress_bar:
        img = volume.xr.isel(y=i).data
        sino_id, sino_slice = astra.creators.create_sino(img, proj_id)
        sinogram.xr.loc[dict(y=i)] = sino_slice
        astra.astra.delete(sino_id)
    
    sinogram, volume = format_after_projection(sinogram, volume)
    astra.astra.delete(proj_id)
    return sinogram


@registers.procedures.register(name="forward project", category=registers.categories["Project"])
def forward_project(volume: Volume, angles: Union[TiltSchemeCursor, np.ndarray], use_3D: bool = True, **kwargs):
    sinogram, volume, angles = format_before_projection(volume, angles)
    A = Projector(sinogram, volume, angles, use_3D=use_3D)

    total, indices = A.get_iterators(volume)
    progress_bar = progress.new(name="Forward projecting", total=total)
    for _ in progress_bar:
        idx = next(indices)
        vol_slice = volume.xr.isel(idx).data
        sino_slice = A(vol_slice)
        sinogram.xr.isel(idx).data[...] = sino_slice

    sinogram, volume = format_after_projection(sinogram, volume)
    A.delete()

    return sinogram