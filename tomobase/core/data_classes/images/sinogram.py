
import numpy as np
import xarray as xr

from ... import registers, base_classes, get_xp

@registers.images.register(name="Sinogram")
class Sinogram(base_classes.ImageAbstract):
    """Data type for a sinogram.

    Args:
        name (str): Name of the sinogram.
        data (numpy.ndarray): Projection data.
        angles (numpy.ndarray): Projection angles in degrees.
        pixelsize (float): Pixel size. Defaults to 1.0.
        times (numpy.ndarray | None): Acquisition times. Defaults to None.
        metadata (dict): Extra metadata.

    Raises:
        ValueError: If the angle/time dimensions do not match the data.

    Returns:
        Sinogram: A sinogram object.
    """
    _allowed_dims = ['n', 'signals', 'y', 'x']
    
    def __init__(self, name, data, angles: np.ndarray, pixelsize: float = 1.0, times: np.ndarray | None = None, metadata: dict = {}, *args, **kwargs):
        """Data type for a sinogram.

        Args:
            name (str): Name of the sinogram.
            data (numpy.ndarray): Projection data.
            angles (numpy.ndarray): Projection angles in degrees.
            pixelsize (float): Pixel size. Defaults to 1.0.
            times (numpy.ndarray | None): Acquisition times. Defaults to None.
            metadata (dict): Extra metadata.

        Raises:
            ValueError: If the angle/time dimensions do not match the data.

        Returns:
            Sinogram: A sinogram object.
        """
        
               
        data = super()._construct_data_array(data, pixel_size=pixelsize)
        super().__init__(name, data, pixelsize, metadata, *args, **kwargs)

        xp = get_xp(self.xr.data)
        if times is None:
            times_data = xp.arange(self.xr.sizes['n']) + 1
        else:
            times_data = times
        if 'times' not in self.xr.coords or 'angles' not in self.xr.coords:
            len_proj = self.xr.sizes['n']
            self.xr = self.xr.assign_coords(
                n = xp.arange(len_proj),
                times = ('n', times_data),
                angles = ('n', angles)
            )
        self.coords_to_numpy()

    def sort(self, by='times'):
        """
        Sort the sinogram by a specified coordinate.
        Args:
            by (str): The coordinate to sort by. Must be one of 'times', 'angles', or 'n'. Defaults to 'times'.
        Raises:
            ValueError: If the specified coordinate is not valid.           
        """
        if by not in ['times', 'angles', 'n']:
            raise ValueError(f"Invalid sort option {by}. Valid options are 'times', 'angles', and 'n'.")
        self.xr = self.xr.sortby(by)

    def remove(self, n: list[int]):
        self.xr = self.xr.drop_sel(n=n)
        self.removed.emit()
        
    def insert(self, data, axis):
        self.xr = xr.concat([self.xr, data], dim='n')
        self.inserted.emit()

    @property
    def angles(self):
        angles =self.xr.coords['angles'].data
        if hasattr(angles, "get"):
            angles = angles.get()

        return np.asarray(angles)
    
    @angles.setter
    def angles(self, value):
        self.xr.coords["angles"] = ("n", value)

    @property
    def times(self):
        times = self.xr.coords['times'].data
        if hasattr(times, "get"):
            times = times.get()
        return np.asarray(times)
    
    @times.setter
    def times(self, value):
        self.xr.coords["times"] = ("n", value)
    
