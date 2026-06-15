import xarray as xr


class SliceModel():
    def __init__(self, data, *args, **kwargs):
        super().__init__(data, *args, **kwargs)
    
    def apply_kernel(self, kernel, input_core_dims, output_core_dims=None, **kwargs):
        if output_core_dims is None:
            output_core_dims = input_core_dims

        out = xr.apply_ufunc(
            kernel,
            self.data,
            input_core_dims=[input_core_dims],
            output_core_dims=[output_core_dims],
            vectorize=True,
            kwargs=kwargs,
            dask="parallelized",
            output_dtypes=[self.data.dtype],
        )
        return self.with_data(out)
    
    def apply_per_dim(self, dim, fn):
        pieces = []
        for i in range(self.data.sizes[dim]):
            sub = self.with_data(self.data.isel({dim: i}))
            out = fn(sub)
            pieces.append(out)

        if not all(isinstance(p, ImageAbstract) for p in pieces):
            raise TypeError("apply_per_dim expects fn to return ImageAbstract")

        combined = xr.concat([p.data for p in pieces], dim=dim)
        return self.with_data(combined)
    
    