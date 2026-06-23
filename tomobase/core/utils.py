import itertools
import numpy as np

import astra
import numpy as np

from ..core.data_classes.images import Sinogram, Volume
from ..core.base_classes import ImageAbstract, TiltSchemeCursor
from ..core import proxy, GPUContext, utils, logger, get_xp

def iter_indexers_with_len(shape: dict[str, int], dims: list[str]):
    """Creates a generator that yields all permutations of the specified dimensions. This allows user to iterate over all combinations of the specified dimensions in a multi-dimensional array or dataset.

    Args:
        shape (dict[str, int]): A dictionary mapping dimension names to their sizes.
        dims (list[str]): A list of dimension names to iterate over.

    Returns:
        tuple[int, generator[dict[str, int]]]: A tuple containing the total number of combinations and a generator that yields dictionaries mapping dimension names to their current values.

    """
    total = 1
    for d in dims:
        total *= shape[d]

    def gen():
        ranges = [range(shape[d]) for d in dims]
        for values in itertools.product(*ranges):
            yield dict(zip(dims, values))

    return total, gen()

def get_module(name, context=None):
    if context == GPUContext.CUPY:
        match name:
            case 'ndimage':
                import cupyx.scipy.ndimage as module
                return module
            case _:
                raise ValueError(f"Module {name} not found for context {context}")
    else:
        match name:
            case 'ndimage':
                import scipy.ndimage as module
                return module
            case _:
                raise ValueError(f"Module {name} not found for context {context}")
            
            
def format_before_projection(image:ImageAbstract, angles=None, default_value=0.0):
    """Format the Volume or Sinogram to the necessary shape for projection operations for astra.
    Either a Volume or a Sinogram can be provided as input. If a Volume is provided, a Sinogram will be created with the specified angles. If a Sinogram is provided, a Volume will be created with the same shape as the Sinogram.
    The default value is used to fill the newly created image. The angles are expected to be in degrees and will be converted to radians for the projection operations.

    Args:
        image (ImageAbstract): The input image, either a Volume or a Sinogram.
        angles (TiltSchemeCursor|xp.ndarray|None, optional): The angles for projection. Defaults to None.
        default_value (float, optional): The default value to fill in the formatted image. Defaults to 0.0.


    Raises:
        ValueError: _angles_ must be provided for forward projection when a Volume is provided.
        ValueError: _image_ must be either a Volume or a Sinogram.

    Returns:
        tuple[Sinogram, Volume, xp.ndarray]: A tuple containing the formatted Sinogram, Volume, and angles in radians.
    """
    xp = get_xp(image.data)
    y, x = image.xr.sizes['y'], image.xr.sizes['x']
    if isinstance(image, Volume):
        volume = image
        z = volume.xr.sizes['z']
                   
        if angles is None:
            raise ValueError("Angles must be provided for forward projection.")
        
        if isinstance(angles, TiltSchemeCursor):
            angles = xp.array(angles.angles)
        angles = xp.asarray(angles)
        
        sinogram = Sinogram.array_like(image, values=default_value, n=len(angles)).set_context(image.context, image.device)
        sinogram.angles = angles
        sinogram.times = xp.arange(len(angles)) + 1

    
    elif isinstance(image, Sinogram):
        sinogram = image
        z = sinogram.xr.sizes['x']
        volume = Volume.array_like(image, values=default_value, z=z).set_context(image.context, image.device)

        angles = xp.array(sinogram.angles)
    
    else:   
        raise ValueError("Input image must be either a Volume or a Sinogram.")    
    if hasattr(image.xr.data, "__cuda_array_interface__"):
        angles = angles.get()
    
    angles = angles * np.pi / 180  
    sinogram = sinogram.transpose("y","n", "x")
    volume = volume.transpose("y", "z", "x")

    sinogram.xr.data = sinogram.xr.data.astype(xp.float32)
    volume.xr.data = volume.xr.data.astype(xp.float32)
    return sinogram, volume, angles

def format_after_projection(sinogram:Sinogram, volume:Volume):
    """Format the Volume and Sinogram back to their original shapes after projection operations.
    
    Args:
        sinogram (Sinogram): The formatted Sinogram.
        volume (Volume): The formatted Volume.

    Returns:
        tuple[Sinogram, Volume]: A tuple containing the Sinogram and Volume in their original shapes.
    """
    volume = volume.transpose("x", "y", "z")
    sinogram = sinogram.transpose("n", "y", "x")
    return sinogram, volume


def _create_astra_2d_geom(volume:Volume, angles, use_gpu=False):
    x, y, z = volume.xr.sizes['x'], volume.xr.sizes['y'], volume.xr.sizes['z']
    proj_geom = astra.creators.create_proj_geom('parallel', 1, max(x, z), angles)
    vol_geom = astra.creators.create_vol_geom(max(x, z), max(x, z))
    if use_gpu:
        proj_id = astra.creators.create_projector('cuda', proj_geom, vol_geom)
    else:
        proj_id = astra.creators.create_projector('linear', proj_geom, vol_geom)
    return proj_id, proj_geom, vol_geom


def _create_astra_3d_geom(volume:Volume, angles, use_gpu=False):
    x, y, z = volume.xr.sizes['x'], volume.xr.sizes['y'], volume.xr.sizes['z']
    proj_geom = astra.creators.create_proj_geom('parallel3d', 1, 1, max(x, z), max(x, z), angles)
    vol_geom = astra.creators.create_vol_geom(max(x, z), max(x, z), y)
    if use_gpu:
        proj_id = astra.creators.create_projector('cuda3d', proj_geom, vol_geom)
    else:
        raise NotImplementedError("ASTRA does not support linear 3D projection without GPU")
    return proj_id, proj_geom, vol_geom

class Projector:
    """A class to handle forward and back projection operations using the ASTRA toolbox.
    This class initializes the necessary geometries and configurations for performing forward and back projection operations on a given Volume and Sinogram. It supports both 2D and 3D projections, as well as GPU acceleration if available.
    
    Args:
        sinogram (Sinogram): The sinogram object containing projection angles.
        volume (Volume): The volume object to be projected.
        angles (xp.ndarray): The angles for projection in radians.
        use_3D (bool, optional): Whether to use 3D projection. Defaults to True.
    """
    def __init__(self, sinogram, volume, angles, use_3D=True):
        self.loopdims = list(volume.non_spatial_dims)
        self.use_gpu = False
        self.xp = get_xp(sinogram.data)
        if sinogram.context == GPUContext.CUPY:
            self.use_gpu = True
        
        self.use_3D = use_3D
        if sinogram.xr.sizes['y'] == 1:
            self.use_3D = False
        
        self.algorithms = {}
        validations = (self.use_3D, self.use_gpu)
        match validations:
            case (True, True):
                self.proj_id, self.proj_geom, self.vol_geom = _create_astra_3d_geom(volume, angles, use_gpu=self.use_gpu)
                self.range_shape = (sinogram.xr.sizes['y'], sinogram.xr.sizes['n'], sinogram.xr.sizes['x'])
                self.domain_shape = (volume.xr.sizes['y'], sinogram.xr.sizes['x'], sinogram.xr.sizes['x'])
                self.linker = astra.data3d
                self.deleter = astra.projector3d
                self.algorithms["FP"] = 'FP3D_CUDA'
                self.algorithms["BP"] = 'BP3D_CUDA'
            case (False, False) | (True, False):
                if "y" in volume.xr.dims:
                    self.loopdims.append("y")
                self.proj_id, self.proj_geom, self.vol_geom = _create_astra_2d_geom(volume, angles, use_gpu=self.use_gpu)
                self.range_shape = (sinogram.xr.sizes['n'], sinogram.xr.sizes['x'])
                self.domain_shape = (sinogram.xr.sizes['x'], sinogram.xr.sizes['x'])
                self.linker = astra.data2d
                self.deleter = astra.projector
                self.algorithms["FP"] = 'FP'
                self.algorithms["BP"] = 'BP'
                self.algorithms["projector"] = self.proj_id

            case (False, True):
                if "y" in volume.xr.dims:
                    self.loopdims.append("y")
                volume_slice = volume.xr.isel(y=slice(0, 1))
                self.proj_id, self.proj_geom, self.vol_geom = _create_astra_3d_geom(volume_slice, angles, use_gpu=self.use_gpu)  
                self.range_shape = (1, sinogram.xr.sizes['n'], sinogram.xr.sizes['x'])
                self.domain_shape = (1, sinogram.xr.sizes['x'], sinogram.xr.sizes['x'])
                self.linker = astra.data3d
                self.deleter = astra.projector3d
                self.algorithms["FP"] = 'FP3D_CUDA'
                self.algorithms["BP"] = 'BP3D_CUDA'
        
        
            
    def __call__(self, x, y=None):
        """Performs the forward projection operation.

        Args:
            x (xp.ndarray): The input volume data.
            y (xp.ndarray|None, optional): The output sinogram data. Defaults to None.

        Returns:
            xp.ndarray: The resulting sinogram data.
        """

        x = self.xp.ascontiguousarray(x, dtype=self.xp.float32)
        vol_id = self.linker.link('-vol', self.vol_geom, x)
        if y is None:
            y = self.xp.zeros(self.range_shape, dtype=x.dtype)
        y = self.xp.ascontiguousarray(y, dtype=self.xp.float32)
        sino_id = self.linker.link('-sino', self.proj_geom, y)
        
        cfg = astra.astra_dict(self.algorithms["FP"])
        if "projector" in self.algorithms:
            cfg['ProjectorId'] = self.algorithms["projector"]
        cfg['ProjectionDataId'] = sino_id
        cfg['VolumeDataId'] = vol_id
        alg_id = astra.algorithm.create(cfg)
        astra.algorithm.run(alg_id)
        
        astra.algorithm.delete(alg_id)
        self.linker.delete(sino_id)
        self.linker.delete(vol_id)
        return y
    
    def T(self, y, x=None):
        """Performs the backprojection operation.

        Args:
            y (xp.ndarray): The input sinogram data.
            x (xp.ndarray|None, optional): The output volume data. Defaults to None.

        Returns:
            xp.ndarray: The resulting volume data.
        """
        y = self.xp.ascontiguousarray(y, dtype=self.xp.float32)
        sino_id = self.linker.link('-sino', self.proj_geom, y)
        if x is None:
            x = self.xp.zeros(self.domain_shape, dtype=y.dtype)
        x = self.xp.ascontiguousarray(x, dtype=self.xp.float32)
        vol_id = self.linker.link('-vol', self.vol_geom, x)
        
        cfg = astra.astra_dict(self.algorithms["BP"])
        if "projector" in self.algorithms:
            cfg['ProjectorId'] = self.algorithms["projector"]
        cfg['ProjectionDataId'] = sino_id
        cfg['ReconstructionDataId'] = vol_id
        alg_id = astra.algorithm.create(cfg)
        
        astra.algorithm.run(alg_id)
        
        astra.algorithm.delete(alg_id)
        self.linker.delete(vol_id)
        self.linker.delete(sino_id)
        return x
    
    def get_iterators(self, volume):
        return utils.iter_indexers_with_len({d: volume.xr.sizes[d] for d in self.loopdims}, self.loopdims)
    
    def delete(self):
        self.deleter.delete(self.proj_id)
        astra.clear()
        
def get_weights(sinogram: Sinogram, weighted: bool, projector:Projector|None=None):
    """Weights projection angles based on their spacing.

    Args:
        sinogram (Sinogram): The sinogram object containing projection angles.
        weighted (bool): Whether to weight the projection angles based on their spacing.
        projector (Projector|None, optional): The projector object. Defaults to None.

    Returns:
        xp.ndarray: The weights for each projection angle.
    """
    
    xp = get_xp(sinogram.data)
    weights = xp.ones_like(sinogram.angles)
    if weighted == True:
        idx = xp.argsort(sinogram.angles)
        sorted_angles = xp.take(sinogram.angles, idx) + 90
        n_angles = len(sorted_angles)
        for i in range(len(sorted_angles)):
            if i == 0:
                weights[idx[i]] = 0.5*(180 - sorted_angles[n_angles-1] + sorted_angles[i+1])
            elif i == len(sorted_angles)-1:
                weights[idx[i]] = 0.5*(180 - sorted_angles[n_angles-2] + sorted_angles[0])
            else:
                weights[idx[i]] = 0.5*((sorted_angles[i+1] - sorted_angles[i]) + (sorted_angles[i] - sorted_angles[i-1]))
        ratio = 180/(n_angles-1)
        weights = weights/ratio
    
    
    if projector is None:
        return weights

    if len(projector.range_shape) == 3:
        weights = weights[None, :, None]
    else:
        weights = weights[:,None]
    return weights
        