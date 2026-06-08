import copy

from ....core.data_classes.images import Sinogram
from ....core.data_classes import Measurement, Coordinate
from ....core import registers, progress, logger, utils, GPUContext, get_xp

subcategory = registers.categories.add_hierarchy('Shift Corrections', value=6, parent = 'Align')
@registers.procedures.register(name='Align Sinogram XCorrelation', category=subcategory)
def align_sinogram_xcorr(sino: Sinogram):
    xp = get_xp(sino.data)

    n_size = sino.xr.sizes["n"]
    shifts = xp.zeros((n_size, 2))

    dims = {"n": 0}
    if "signals" in sino.xr.dims:
        dims["signals"] = 0

    fixed = sino.xr.isel(**dims).data
    fixed = xp.nan_to_num(fixed, nan=0.0, posinf=0.0, neginf=0.0)
    fft_fixed = xp.fft.fft2(fixed)

    progress_bar = progress.new(name="Calculating shifts with cross-correlation",total=n_size - 1)
    for i in progress_bar:
        dims["n"] = i + 1

        moving = sino.xr.isel(**dims).data
        moving = xp.nan_to_num(moving, nan=0.0, posinf=0.0, neginf=0.0)
        fft_moving = xp.fft.fft2(moving)

        xcorr = xp.fft.ifft2(fft_fixed * xp.conj(fft_moving))
        xcorr_abs = xp.abs(xcorr)
        rel_shift = xp.asarray(xp.unravel_index(xp.argmax(xcorr_abs), xcorr_abs.shape))

        # Convert wraparound shifts to signed shifts
        shape = xp.asarray(xcorr_abs.shape)
        rel_shift = xp.where(rel_shift > shape // 2, rel_shift - shape, rel_shift)
        shifts[i + 1, :] = shifts[i, :] + rel_shift
        fft_fixed = fft_moving

    shifts = xp.rint(shifts).astype(int)

    # Apply shifts to all non-spatial index combinations
    non_spatial_dims = list(sino.non_spatial_dims)
    
    total, indexer = utils.iter_indexers_with_len({d: sino.xr.sizes[d] for d in non_spatial_dims}, non_spatial_dims)
    progress_bar = progress.new(name="Aligning sinogram with cross-correlation",total=total)
    for _ in progress_bar:
        idx = next(indexer)

        s1 = sino.xr.isel(idx)
        shifted = xp.roll(
            s1.data,
            shift=tuple(shifts[idx["n"], :].tolist()),
            axis=(0, 1)
        )
        sino.xr.loc[idx] = shifted
    
    shift_x = Measurement(name="Shifts X", dims=Coordinate(name="x Offset", unit="pixels"), sample=sino, data=shifts[:, 1], domain_dims=("n",))
    shift_y = Measurement(name="Shifts Y", dims=Coordinate(name="y Offset",unit="pixels"), sample=sino, data=shifts[:, 0], domain_dims=("n",))

    return sino, shift_x, shift_y


@registers.procedures.register(name='Centre of Mass', category=subcategory)
def align_sinogram_center_of_mass(sino: Sinogram):
    xp = get_xp(sino.data)
    ndimage = utils.get_module('ndimage', sino.context)
    
    
    spatial_dims = list(sino.spatial_dims)
    center = xp.asarray([sino.xr.sizes[d] // 2 for d in spatial_dims])
    offsets = xp.zeros((sino.xr.sizes['n'], 2), dtype=int)

    dims = {}
    if "signals" in sino.xr.dims:
        dims["signals"] = 0
        dims["n"] = 0
        
    progress_bar = progress.new(name="Aligning sinogram with center of mass", total=sino.xr.sizes['n'])
    for i in progress_bar:
        dims["n"] = i
        s1 = sino.xr.isel(dims)

        # compute COM for this slice
        com = xp.asarray(ndimage.center_of_mass(s1.data))
        offset = center - com
        offsets[i, 0]= int(offset[0])
        offsets[i, 1]= int(offset[1])

    
    dims = list(sino.non_spatial_dims)  
    sizes = {d: sino.xr.sizes[d] for d in dims}
    total, indexer = utils.iter_indexers_with_len(sizes, dims)
    progress_bar_signals = progress.new(name="Aligning signals to COM", total=total)
    for i in progress_bar_signals:
        idx = next(indexer)
        s1 = sino.xr.isel(idx)
        shifted = xp.roll(s1.data,shift=tuple(offsets[idx["n"], :].tolist()),axis=(0, 1))
        sino.xr.loc[idx] = shifted
    
    shift_x = Measurement(name="Shifts X", dims=Coordinate(name="x Offset", unit="pixels"), sample=sino, data=offsets[:, 1], domain_dims=("n",))
    shift_y = Measurement(name="Shifts Y", dims=Coordinate(name="y Offset",unit="pixels"), sample=sino, data=offsets[:, 0], domain_dims=("n",))

    
    return sino, shift_x, shift_y


#@registers.procedures.register(name='Align Slice (Manual)', category=subcategory)
def align_slice_manual(sino: Sinogram, slice_index: int = 0, x_shift: int=0, y_shift: int=0):
    #TODO Implement
    xp = get_xp(sino.xr.data)

    s1 = sino.xr.isel(n=slice_index)
    s1.values = xp.roll(s1.values, (y_shift, x_shift), axis=(0, 1))
    sino.xr.loc[dict(n=s1.coords["n"].item())] = s1

    return sino






