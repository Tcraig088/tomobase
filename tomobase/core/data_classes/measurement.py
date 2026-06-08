from dataclasses import dataclass
import collections
collections.Iterable = collections.abc.Iterable
import numpy as np

import xarray as xr

from .. import base_classes



@dataclass
class Coordinate:
    name: str
    unit: str = "a.u."
    scale: float = 1.0


class Measurement(base_classes.MeasurementAbstract):
    def __init__(
        self,
        name,
        dims,
        sample=None,
        data=None,
        domain_dims=None,
        metadata=None,
        dtype=float,
        *args,
        **kwargs,
    ):
        self.name = name
        self.metadata = metadata or {}
        self.dtype = dtype

        self.dims = self._normalize_dims(dims)

        if domain_dims is None:
            domain_dims = ()

        if isinstance(domain_dims, str):
            domain_dims = (domain_dims,)

        self.domain_dims = tuple(domain_dims)

        if data is None:
            self.xr = self._empty_dataset(dtype=dtype)
        else:
            self.xr = self._make_dataset(sample, data, dtype=dtype)

        super().__init__(name, self.xr, *args, **kwargs)

    def _normalize_dims(self, dims):
        if isinstance(dims, Coordinate):
            return (dims,)

        dims = tuple(dims)

        if all(isinstance(d, Coordinate) for d in dims):
            return dims

        if all(isinstance(row, (tuple, list)) for row in dims):
            return tuple(tuple(row) for row in dims)

        raise TypeError("dims must be a Coordinate, a sequence of Coordinates, or a 2D sequence of Coordinates.")

    @property
    def is_matrix(self):
        return len(self.dims) > 0 and isinstance(self.dims[0], tuple)

    @property
    def value_shape(self):
        if self.is_matrix:
            return (len(self.dims), len(self.dims[0]))
        return (len(self.dims),)

    def _component_names(self):
        if self.is_matrix:
            return np.asarray([[c.name for c in row] for row in self.dims], dtype=object)
        return np.asarray([c.name for c in self.dims], dtype=object)

    def _component_units(self):
        if self.is_matrix:
            return np.asarray([[c.unit for c in row] for row in self.dims], dtype=object)
        return np.asarray([c.unit for c in self.dims], dtype=object)

    def _component_scales(self):
        if self.is_matrix:
            return np.asarray([[c.scale for c in row] for row in self.dims], dtype=float)
        return np.asarray([c.scale for c in self.dims], dtype=float)

    def _value_dims_and_coords(self):
        if self.is_matrix:
            row_dim = "row"
            col_dim = "col"

            coords = {
                row_dim: np.arange(self.value_shape[0]),
                col_dim: np.arange(self.value_shape[1]),
                "component": xr.DataArray(
                    self._component_names(),
                    dims=(row_dim, col_dim),
                ),
                "unit": xr.DataArray(
                    self._component_units(),
                    dims=(row_dim, col_dim),
                ),
                "scale": xr.DataArray(
                    self._component_scales(),
                    dims=(row_dim, col_dim),
                ),
            }

            return (row_dim, col_dim), coords

        value_dim = "component"

        coords = {
            value_dim: xr.DataArray(
                self._component_names(),
                dims=(value_dim,),
            ),
            "unit": xr.DataArray(
                self._component_units(),
                dims=(value_dim,),
            ),
            "scale": xr.DataArray(
                self._component_scales(),
                dims=(value_dim,),
            ),
        }

        return (value_dim,), coords

    def _empty_dataset(self, dtype=float):
        value_dims, value_coords = self._value_dims_and_coords()

        dims = ("sample", *self.domain_dims, *value_dims)

        coords = {
            "sample": np.asarray([], dtype=object),
            **{d: np.asarray([], dtype=float) for d in self.domain_dims},
            **value_coords,
        }

        shape = (
            0,
            *[0 for _ in self.domain_dims],
            *self.value_shape,
        )

        da = xr.DataArray(
            np.empty(shape, dtype=dtype),
            dims=dims,
            coords=coords,
            name=self.name,
        )

        return xr.Dataset({self.name: da}, attrs=self.metadata)

    def _make_vector_dataset(self, sample, data, dtype=float):
        if sample is None:
            raise ValueError("sample must be provided when data is provided.")

        if hasattr(data, "__cuda_array_interface__"):
            data = data.get()

        data = np.asarray(data, dtype=dtype)

        if data.ndim != 2:
            raise ValueError(f"Vector measurement data must be 2D, got shape {data.shape}.")

        if data.shape[1] != len(self.dims):
            raise ValueError(
                f"Vector measurement has {len(self.dims)} coordinates, "
                f"but data has {data.shape[1]} columns."
            )

        sample_name = f"{sample.name}[{sample.process_name}]"
        index = np.arange(data.shape[0])

        data_vars = {}

        for j, coord in enumerate(self.dims):
            data_vars[coord.name] = xr.DataArray(
                data[None, :, j],
                dims=("sample", "index"),
                coords={
                    "sample": [sample_name],
                    "index": index,
                },
                attrs={
                    "unit": coord.unit,
                    "scale": coord.scale,
                },
            )

        return xr.Dataset(data_vars=data_vars, attrs=self.metadata)


    def _make_dataset(self, sample, data, dtype=float):
        if sample is None:
            raise ValueError("sample must be provided when data is provided.")

        if hasattr(data, "__cuda_array_interface__"):
            data = data.get()

        data = np.asarray(data, dtype=dtype)

        # Vector measurement with no sample-domain axis:
        # data shape: (N, number_of_coordinates)
        # example: columns = Angle, RMSE
        if len(self.domain_dims) == 0 and len(self.dims) > 1:
            if data.ndim == 2 and data.shape[1] == len(self.dims):
                return self._make_vector_dataset(sample, data, dtype=dtype)

        sample_name = f"{sample.name}[{sample.process_name}]"

        out_dims = ["sample"]
        coords = {"sample": [sample_name]}

        # Domain dimensions copied from the source sample.
        # This also copies coordinates attached to that dimension,
        # e.g. if domain_dims=("n",), it copies n plus times(n), angles(n), etc.
        for axis, dim in enumerate(self.domain_dims):
            if dim not in sample.xr.sizes:
                raise ValueError(f"Domain dimension {dim!r} not found in sample.")

            expected = sample.xr.sizes[dim]
            actual = data.shape[axis]

            if actual != expected:
                raise ValueError(
                    f"Data size along domain dimension {dim!r} is {actual}, "
                    f"expected {expected}."
                )

            out_dims.append(dim)

            if dim in sample.xr.coords:
                coords[dim] = sample.xr.coords[dim]
            else:
                coords[dim] = np.arange(expected)

            for coord_name, coord in sample.xr.coords.items():
                if coord.dims == (dim,) and coord_name not in coords:
                    coords[coord_name] = coord

        # Single-coordinate measurement.
        # Example:
        #   dims=Coordinate("y Offset", unit="pixels")
        #   domain_dims=("n",)
        #   data shape: (n,)
        if len(self.dims) == 1:
            coord = self.dims[0]

            expected_ndim = len(self.domain_dims)

            if data.ndim != expected_ndim:
                raise ValueError(
                    f"Data has ndim={data.ndim}, expected {expected_ndim} "
                    f"for single-coordinate measurement with domain_dims={self.domain_dims}."
                )

            da = xr.DataArray(
                data[None, ...],
                dims=tuple(out_dims),
                coords=coords,
                name=coord.name,
                attrs={
                    "unit": coord.unit,
                    "scale": coord.scale,
                },
            )

            return xr.Dataset(
                data_vars={coord.name: da},
                attrs=self.metadata,
            )

        # Multi-coordinate measurement with domain dims.
        # Example:
        #   dims=[Coordinate("shift_x"), Coordinate("shift_y")]
        #   domain_dims=("n",)
        #   data shape: (n, 2)
        if len(self.dims) > 1:
            expected_ndim = len(self.domain_dims) + 1

            if data.ndim != expected_ndim:
                raise ValueError(
                    f"Data has ndim={data.ndim}, expected {expected_ndim}. "
                    f"For {len(self.dims)} coordinates and domain_dims={self.domain_dims}, "
                    f"data should end with a coordinate/component axis of length {len(self.dims)}."
                )

            if data.shape[-1] != len(self.dims):
                raise ValueError(
                    f"Last data axis has length {data.shape[-1]}, "
                    f"expected {len(self.dims)} coordinates."
                )

            data_vars = {}

            for j, coord in enumerate(self.dims):
                data_vars[coord.name] = xr.DataArray(
                    data[..., j][None, ...],
                    dims=tuple(out_dims),
                    coords=coords,
                    attrs={
                        "unit": coord.unit,
                        "scale": coord.scale,
                    },
                )

            return xr.Dataset(
                data_vars=data_vars,
                attrs=self.metadata,
            )

        raise ValueError("Measurement must have at least one Coordinate in dims.")

    def add_data(self, sample, data):
        new_ds = self._make_dataset(sample, data, dtype=self.dtype)

        if self.xr[self.name].sizes.get("sample", 0) == 0:
            self.xr = new_ds
        else:
            self.xr = xr.concat([self.xr, new_ds], dim="sample")

        return self

    def stack(self, other):
        if self.name != other.name:
            raise ValueError(f"{self.name} != {other.name}")

        self.xr = xr.concat([self.xr, other.xr], dim="sample")
        return self