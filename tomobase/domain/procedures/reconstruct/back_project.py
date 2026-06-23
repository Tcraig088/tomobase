import astra
import numpy as np
from copy import deepcopy

from skimage.restoration import denoise_tv_chambolle

from .geometries import _get_weights, _circle_mask, _create_astra_2d_geom, format_before_projection, format_after_projection, Projector
from ....core.data_classes.images import Volume, Sinogram
from ....core.registers import categories, procedures

from ....core import  logger, progress, proxy, GPUContext, utils, get_xp



@procedures.register(name='TVM', category=categories['Reconstruct'])
def reconstruct_tvm(sinogram: Sinogram, iterations: int=100, tv_weight: float=1e-3,
                    tv_iters: int=10, weighted: bool=True, use_3D: bool=True):
    xp = get_xp(sinogram.data)
    sinogram, volume, angles = format_before_projection(sinogram)
    A = Projector(sinogram, volume, angles, use_3D=use_3D)

    R = 1 / A(xp.ones(A.domain_shape))
    C = 1 / A.T(xp.ones(A.range_shape))
    R = xp.minimum(R, 1 / 10**-6)
    C = xp.minimum(C, 1 / 10**-6)

    weights = _get_weights(sinogram, weighted, A)

    progress_bar_iter = progress.new(name="Iterative Back Projection", total=iterations)
    for i in progress_bar_iter:
        total, indices = A.get_iterators(volume)
        progress_bar_dim = progress.new(name="Slice Wise Back Projection", total=total)
        for _ in progress_bar_dim:
            idx = next(indices)
            vol_slice = volume.xr.isel(idx).data
            sino_slice = sinogram.xr.isel(idx).data * weights

            # SIRT gradient step
            volume.xr.isel(idx).data[...] += C * A.T(R * (sino_slice - (A(vol_slice) * weights)))

            # TV proximal step (Chambolle's algorithm)
            vol_slice = volume.xr.isel(idx).data
            tau = 1.0 / (4 * vol_slice.ndim)
            p = xp.zeros((*vol_slice.shape, vol_slice.ndim), dtype=vol_slice.dtype)
            for _ in range(tv_iters):
                div_p = _divergence(p, xp)
                grad_arg = _gradient(vol_slice - tv_weight * div_p, xp)
                p_new = p + tau * grad_arg
                norms = xp.maximum(1.0, xp.sqrt((p_new**2).sum(axis=-1, keepdims=True)))
                p = p_new / norms
            volume.xr.isel(idx).data[...] = vol_slice - tv_weight * _divergence(p, xp)

    sinogram, volume = format_after_projection(sinogram, volume)
    A.delete()
    return volume


def _gradient(arr, xp):
    """Forward differences gradient, output shape (*arr.shape, arr.ndim)."""
    grads = []
    for ax in range(arr.ndim):
        g = xp.zeros_like(arr)
        slc_fwd = [slice(None)] * arr.ndim
        slc_cur = [slice(None)] * arr.ndim
        slc_fwd[ax] = slice(1, None)
        slc_cur[ax] = slice(None, -1)
        g[tuple(slc_cur)] = arr[tuple(slc_fwd)] - arr[tuple(slc_cur)]
        grads.append(g)
    return xp.stack(grads, axis=-1)


def _divergence(p, xp):
    """Backward differences divergence of a vector field p (*shape, ndim)."""
    div = xp.zeros(p.shape[:-1], dtype=p.dtype)
    for ax in range(p.shape[-1]):
        comp = p[..., ax]
        d = xp.zeros_like(comp)
        slc_fwd = [slice(None)] * comp.ndim
        slc_cur = [slice(None)] * comp.ndim
        slc_last = [slice(None)] * comp.ndim
        slc_prev = [slice(None)] * comp.ndim
        slc_fwd[ax]  = slice(1, None)
        slc_cur[ax]  = slice(None, -1)
        slc_last[ax] = slice(-1, None)
        slc_prev[ax] = slice(-2, -1)
        d[tuple(slc_fwd)] = comp[tuple(slc_fwd)] - comp[tuple(slc_cur)]
        slc_first = [slice(None)] * comp.ndim
        slc_first[ax] = slice(0, 1)
        d[tuple(slc_first)] = comp[tuple(slc_first)]
        d[tuple(slc_last)]  = -comp[tuple(slc_prev)]
        div += d
    return div

@procedures.register(name='MLEM', category=categories['Reconstruct'], inplace=False)
def reconstruct_mlem(sinogram:Sinogram, iterations:int=15, weighted:bool=True, use_3D:bool=True, **kwargs):
    xp = get_xp(sinogram.data)
    sinogram, volume, angles = format_before_projection(sinogram, default_value=1.0)
    A = Projector(sinogram, volume, angles, use_3D=use_3D)
    
    eps = 10**-6
    weights = _get_weights(sinogram, weighted, A)
    sensitivity = xp.maximum(A.T(xp.ones(A.range_shape)), eps)
    
    progress_bar_iter = progress.new(name="Iterative Back Projection", total=iterations)
    for i in progress_bar_iter:
        total, indices = A.get_iterators(volume)
        progress_bar_dim = progress.new(name="Slice Wise Back Projection", total=total)
        for _ in progress_bar_dim:
            idx = next(indices)
            vol_slice = volume.xr.isel(idx).data
            sino_predicted = xp.maximum(A(vol_slice) * weights, eps)
            sino_slice = sinogram.xr.isel(idx).data * weights
            
            ratio = sino_slice / sino_predicted
            correction = A.T(ratio)/sensitivity
            correction = xp.maximum(correction, eps)
            volume.xr.isel(idx).data[...] *= correction

    sinogram, volume = format_after_projection(sinogram, volume)
    A.delete()
    return volume

@procedures.register(name='WBP', category=categories['Reconstruct'], inplace=False)
def reconstruct_wbp(sinogram:Sinogram, weighted:bool=False, use_3D:bool=True):
    xp = get_xp(sinogram.data)
    sinogram, volume, angles = format_before_projection(sinogram)
    A = Projector(sinogram, volume, angles, use_3D=use_3D)
    

    weights = _get_weights(sinogram, weighted, A)

    total, indices = A.get_iterators(volume)
    progress_bar_dim = progress.new(name="Slice Wise Back Projection", total=total)
    for _ in progress_bar_dim:
        idx = next(indices)
        sino_slice = sinogram.xr.isel(idx).data * weights
        volume.xr.isel(idx).data[...] = A.T(sino_slice)
            
    sinogram, volume = format_after_projection(sinogram, volume)
    A.delete()
    return volume


@procedures.register(name='SIRT', category=categories['Reconstruct'], inplace=False)
def reconstruct_sirt(sinogram:Sinogram, iterations:int=100, weighted:bool=True, use_3D:bool=True):
    xp = get_xp(sinogram.data)
    sinogram, volume, angles = format_before_projection(sinogram)
    A = Projector(sinogram, volume, angles, use_3D=use_3D)
    
    R = 1/A(xp.ones(A.domain_shape))
    C = 1/A.T(xp.ones(A.range_shape))
    R = xp.minimum(R, 1 / 10**-6)
    C = xp.minimum(C, 1 / 10**-6)
    

    weights = _get_weights(sinogram, weighted, A)

    progress_bar_iter = progress.new(name="Iterative Back Projection", total=iterations)
    for i in progress_bar_iter:
        total, indices = A.get_iterators(volume)
        progress_bar_dim = progress.new(name="Slice Wise Back Projection", total=total)
        for _ in progress_bar_dim:
            idx = next(indices)
            vol_slice = volume.xr.isel(idx).data
            sino_slice = sinogram.xr.isel(idx).data * weights
            volume.xr.isel(idx).data[...] += C*A.T(R*(sino_slice - (A(vol_slice)*weights)))
    
    sinogram, volume = format_after_projection(sinogram, volume)
    A.delete()
    return volume
    
@procedures.register(name='Astra', category=categories['Reconstruct'], inplace=False, use_numpy=True)
def astra_reconstruct(sino:Sinogram, iterations:int=100):
    """Reconstruct a volume from a given sinogram.

    Arguments:
        sinogram (Sinogram)
            The projection data
        method (str)
            The reconstruction algorithm; supported algorithms are: `'bp'`,
            `'fbp'`, `'sirt'`, `'em'`, `'sart'` and `'cgls'`
        iterations (int)
            The number of iterations when using an iterative reconstructor,
            leaving this at None will select the default number of iterations
            for the given algorithm (default: None)
        use_gpu (bool)
            Use a GPU if it is available (default: True)
        mask (numpy.ndarray)
            Boolean mask that indicates which voxels should be used in the
            reconstruction (default: None)

    Returns:
        Volume
            The reconstructed volume
    """
    
    sino, volume, angles = format_before_projection(sino)
    iterations = 100
    use_gpu = False
    if proxy.context == GPUContext.CUPY:
        use_gpu = True
        if not astra.use_cuda():
            raise RuntimeError("CUDA is not available, cannot use GPU for reconstruction.")
    
    method = 'SIRT_CUDA' if use_gpu else 'SIRT'
    proj_id = _create_astra_2d_geom(volume, angles)
    
    R = np.ones((sino.xr.sizes['n'], sino.xr.sizes['x']))
    C = np.ones((volume.xr.sizes['x'], volume.xr.sizes['x']))
    progress_bar = progress.new(name="Back projecting", total=volume.xr.sizes['y'])
    for i in progress_bar:
        sino_slice = sino.xr.isel(y=i).data
        vol_id, vol_slice = astra.creators.create_reconstruction(method, proj_id, sino_slice, iterations)
        volume.xr.loc[dict(y=i)] = vol_slice
        astra.astra.delete(vol_id)
    sino, volume = format_after_projection(sino, volume)
    astra.astra.delete(vol_id)
    return volume

