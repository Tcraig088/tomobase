import copy

from ...hooks import process_hook
from ...registers.categories import categories
from ...environment import proxy
from ...data import Sinogram

from magicgui.tqdm import trange, tqdm

subcategory = categories.add_category('Shift Corrections', value=6, inheritor = 'Align')
@process_hook(name='Align Sinogram XCorrelation', category=subcategory)
def align_sinogram_xcorr(sino: Sinogram, shifts=None):
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

    if shifts is None:
        shifts = proxy.xupy.zeros((sino.data.shape[0], 2))
        fft_fixed = proxy.xupy.fft.fft2(sino.data[0, :, :])
        for i in tqdm(range(sino.data.shape[0] - 1), label='Calculating shifts with cross-correlation'):
            fft_moving = proxy.xupy.fft.fft2(sino.data[i + 1, :, :])
            xcorr = proxy.xupy.fft.ifft2(proxy.xupy.multiply(fft_fixed, proxy.xupy.conj(fft_moving)))
            fft_fixed = fft_moving
            rel_shift = proxy.xupy.asarray(proxy.xupy.unravel_index(proxy.xupy.argmax(xcorr), xcorr.shape))
            shifts[i + 1, :] = shifts[i, :] + rel_shift

        shifts %= proxy.xupy.asarray(sino.data.shape[1:])[None, :]
        shifts = proxy.xupy.rint(shifts).astype(int)

    for i in tqdm(range(sino.data.shape[0]), label='Aligning sinogram with cross-correlation'):
        sino.data[i, :, :] = proxy.xupy.roll(sino.data[i, :, :], shifts[i, :], axis=(0, 1))

    return sino, shifts


@process_hook(name='Centre of Mass', category=subcategory)
def align_sinogram_center_of_mass(sino: Sinogram):
    """Align the projection images using the center of mass
    Arguments:
        sino (Sinogram): The projection data
        inplace (bool): Whether to do the alignment in-place in the input data object (default: True)
        extend_return (bool): If True, the return value will be a tuple with the offset in the second item (default: False)
    Returns:
        Sinogram: The result
        offset (xp.ndarray): The offset in pixels
    """

    offset = proxy.xupy.asarray(sino.data.shape[1:]) / 2 - proxy.scipy.ndimage.center_of_mass(proxy.xupy.sum(sino.data, axis=0))
    sino.data = proxy.xupy.shift(sino.data, (0, offset[0], offset[1]))
    return sino, offset


@process_hook(name='Weight by Angle', category=subcategory)
def weight_by_angle(sino: Sinogram):
    """Weight the sinogram by the angle
    Arguments:
        sino (Sinogram): The projection data
        inplace (bool): Whether to do the alignment in-place in the input data object (default: True)
        extend_return (bool): If True, the return value will be a tuple with the weights in the second item (default: False)
    Returns:
        Sinogram: The result
        weights (xp.ndarray): The weights in pixels
    """

    #Dont bother progress tracking for short processes
    indices = proxy.xupy.argsort(sino.angles)
    sino.angles = sino.angles[indices]
    sino.data = sino.data[indices, :, :]
    weights = proxy.xupy.ones_like(sino.angles)

    sorted_angles = copy.deepcopy(sino.angles) + 90
    n_angles = len(sorted_angles)

    for i in range(len(sorted_angles)):
        if i == 0:
            weights[i] = 0.5 * (180 - sorted_angles[n_angles - 1] + sorted_angles[i + 1])
        elif i == len(sorted_angles) - 1:
            weights[i] = 0.5 * (180 - sorted_angles[n_angles - 2] + sorted_angles[0])
        else:
            weights[i] = 0.5 * ((sorted_angles[i + 1] - sorted_angles[i]) + (sorted_angles[i] - sorted_angles[i - 1]))
    ratio = 180 / (n_angles - 1)
    weights = weights / ratio

    for i in range(sino.data.shape[0]):
        sino.data[i, :, :] = sino.data[i, :, :] * weights[i]

    return sino, weights


#@tomobase_hook_process(name='Manual Translation', category=TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value, subcategories=_subcategories)
class TranslateSinogramManual:
    def __init__(self, sino: Sinogram, inplace: bool = True):
        self.sino = sino
        self.shape = sino.data.shape
        self.inplace = inplace
        self.index = 0
        self.x = 0
        self.y = 0
        self._view()

    def _view(self):
        self.data = self.sino._transpose_to_view(use_copy=True)
        self.tick_box = widgets.Checkbox(value=False, description='Move Green')
        self.shift_box = widgets.Checkbox(value=False, description='Shift All')
        self.x_slider = widgets.IntSlider(min=-self.shape[1] // 2, max=self.shape[1] // 2, value=0, description='x')
        self.y_slider = widgets.IntSlider(min=-self.shape[2] // 2, max=self.shape[2] // 2, value=0, description='y')
        self.confirm = widgets.Button(description='Confirm')
        self.view = stackview.side_by_side(self.data[0:-2], self.data[1:-1])

        self.img_slider = self.view.children[0].children[0].children[1].children[0].children[1]
        self.index = self.img_slider.value

        self.img_slider.observe(self._on_image_change, names='value')
        self.confirm.on_click(self._on_confirm)
        self.x_slider.observe(self._on_x_change, names='value')
        self.y_slider.observe(self._on_y_change, names='value')

        self.group = widgets.VBox([self.x_slider, self.y_slider, self.view, self.tick_box, self.shift_box, self.confirm])
        display(self.group)

    def _on_confirm(self, change):
        self.sino.data = Sinogram._transpose_from_view(self.data)
        return self.sino

    def _on_image_change(self, change):
        self.index = change.new
        self.x_slider.value = 0
        self.y_slider.value = 0

    def _on_x_change(self, change):
        value = 0
        if not self.shift_box.value:
            if self.tick_box.value:
                value = 1
            x = change.new - self.x
            self.data[self.index + value, :, :] = np.roll(self.data[self.index + value, :, :], (0, x), axis=(0, 1))
            self.view.update()
            self.x = change.new
        else:
            x = change.new - self.x
            self.data[:, :, :] = np.roll(self.data[:, :, :], (0, x), axis=(1, 2))
            self.view.update()
            self.x = change.new

    def _on_y_change(self, change):
        value = 0
        if not self.shift_box.value:
            if self.tick_box.value:
                value = 1
            y = change.new - self.y
            self.data[self.index + value, :, :] = np.roll(self.data[self.index + value, :, :], (y, 0), axis=(0, 1))
            self.view.update()
            self.y = change.new
        else:
            y = change.new - self.y
            self.data[:, :, :] = np.roll(self.data[:, :, :], (y, 0), axis=(1, 2))
            self.view.update()
            self.y = change.new



