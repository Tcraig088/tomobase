import copy
import scipy

from magicgui.tqdm import trange, tqdm

from ....core.data_classes.images import Sinogram
from ....core import registers, progress

subcategory = registers.categories.add_hierarchy('Shift Corrections', value=6, parent = 'Align')
@registers.procedures.register(name='Align Sinogram XCorrelation', category=subcategory)
def align_sinogram_xcorr(sino: Sinogram):
    """Align the projection images using cross-correlation
    Arguments:
        sino (Sinogram): The projection data
        inplace (bool): Whether to do the alignment in-place in the input data object (default: True)
        shifts (np.ndarray): A list of shifts to apply in pixels, if None is given it will be calculated (default: None)
        extend_return (bool): If True, the return value will be a tuple with the shifts in the second item (default: False)
    Returns:
        Sinogram: The result
        shifts (xp.ndarray): The shifts in pixels
    """
    xp = sino.data.values.__array_namespace__()

    shifts = xp.zeros((sino.data.shape[0], 2))
    fft_fixed = xp.fft.fft2(sino.data[0, :, :])

    progress_bar = progress.new(name="Calculating shifts with cross-correlation", total=sino.data.sizes['n'] - 1)
    for i in progress_bar:
        s1 = sino.data.isel(n=i)
        s2 = sino.data.isel(n=i + 1)

        fft_moving = xp.fft.fft2(s2.values)
        xcorr = xp.fft.ifft2(xp.multiply(fft_fixed, xp.conj(fft_moving)))
        fft_fixed = fft_moving

        rel_shift = xp.asarray(xp.unravel_index(xp.argmax(xcorr), xcorr.shape))
        shifts[i + 1, :] = shifts[i, :] + rel_shift


    spatial_dims = [d for d in sino.data.dims if d != "n"]
    sizes = xp.asarray([sino.data.sizes[d] for d in spatial_dims])[None, :]
    shifts %= sizes
    shifts = xp.rint(shifts).astype(int)

    progress_bar = progress.new(name="Aligning sinogram with cross-correlation", total=sino.data.sizes['n'])
    for i in progress_bar:
        s1 = sino.data.isel(n=i)
        s1.values = xp.roll(s1.values, shifts[i, :], axis=(0, 1))
        sino.data.loc[dict(n=s1.coords["n"].item())] = s1

    return sino, shifts


@registers.procedures.register(name='Centre of Mass', category=subcategory)
def align_sinogram_center_of_mass(sino: Sinogram):
    xp = sino.data.values.__array_namespace__()

    spatial_dims = [d for d in sino.data.dims if d != "n"]
    summed = sino.data.sum(dim="n")

    center = xp.asarray([sino.data.sizes[d] / 2 for d in spatial_dims])
    com = xp.asarray(scipy.ndimage.center_of_mass(summed.values))
    offset = center - com

    # build shift tuple in actual xarray dimension order
    shift_by_dim = {
        "n": 0,
        spatial_dims[0]: float(offset[0]),
        spatial_dims[1]: float(offset[1]),
    }

    shift_tuple = tuple(shift_by_dim[d] for d in sino.data.dims)

    sino.data.values = scipy.ndimage.shift(
        sino.data.values,
        shift_tuple
    )

    return sino, offset









