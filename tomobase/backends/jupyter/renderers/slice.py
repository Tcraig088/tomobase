from PIL import Image as PILImage
import numpy as np
import io
import itertools

from ipywidgets import VBox, HBox, Accordion, Label, Output, Image, IntSlider, ToggleButtons
import pyvista as pv

from ....core import base_classes


class SliceInfoWidget(Accordion):
    def __init__(self, image, widget, **kwargs):
        super().__init__(**kwargs)

        self.image = image
        self.widget = widget

        self.body = VBox()
        self.children = (self.body,)
        self.set_title(0, "Slice Info")

        self._rows = {}
        self._observed_sliders = set()

        image.data_refreshed.connect(self._on_data_changed, weak=False)
        image.data_appended.connect(self._on_data_changed, weak=False)
        image.data_removed.connect(self._on_data_changed, weak=False)

        self.sync()

        self.widget.buttons.observe(self._on_data_changed, names="value")
        
    def _make_dim_box(self, dim):
        title = Label()
        coord_box = VBox()
        box = VBox([title, coord_box])

        self._rows[dim] = {
            "title": title,
            "coord_box": coord_box,
            "coord_labels": [],
            "box": box,
        }
        return box

    def _coords_for_dim_index(self, dim, i):
        out = []
        data = self.image.data

        for coord_name, coord in data.coords.items():
            if coord.dims == (dim,):
                out.append((coord_name, coord.values[i]))

        if not out:
            out.append(("index", i))

        return out

    def _format_value(self, value):
        if isinstance(value, np.generic):
            value = value.item()

        if isinstance(value, float):
            return f"{value:.6g}"

        return str(value)

    def _ensure_coord_labels(self, dim, n):
        row = self._rows[dim]
        labels = row["coord_labels"]

        while len(labels) < n:
            labels.append(Label())

        row["coord_box"].children = tuple(labels[:n])

    def _refresh_dim(self, dim):
        slider = self.widget.slider[dim]
        idx = slider.value
        coords = self._coords_for_dim_index(dim, idx)

        row = self._rows[dim]
        row["title"].value = f"{dim}: index {idx}"

        self._ensure_coord_labels(dim, len(coords))

        for label, (coord_name, value) in zip(row["coord_labels"], coords):
            label.value = f"{coord_name}: {self._format_value(value)}"

    def refresh(self, change=None):
        dims = list(self.widget.slider.keys())

        if set(dims) != set(self._rows.keys()):
            self._rows = {}
            self.body.children = tuple(self._make_dim_box(dim) for dim in dims)

        for dim in dims:
            self._refresh_dim(dim)

    def attach_slider_observers(self):
        for dim, slider in self.widget.slider.items():
            sid = id(slider)
            if sid not in self._observed_sliders:
                slider.observe(self.refresh, names="value")
                self._observed_sliders.add(sid)

    def sync(self):
        self.attach_slider_observers()
        self.refresh()

    def _on_data_changed(self, sender=None, **kwargs):
        self.sync()


@base_classes.ImageAbstract.ipywidgets.register(name="slice view")
class ImageSliceWidget(VBox):
    def __init__(self, image: base_classes.ImageAbstract, **kwargs):
        super().__init__(**kwargs)
        self.layout.width = "600px"
        self.image = image
        self.slider = {}
        self.buttons = None
        self.image_view = None

        # Hook image events once. Blinker signals can connect callables directly. :contentReference[oaicite:0]{index=0}
        image.data_refreshed.connect(self.remake_widget, weak=False)
        image.data_appended.connect(self.remake_widget, weak=False)
        image.data_removed.connect(self.remake_widget, weak=False)

        self.remake_widget()

    def _view_dims(self):
        return [d for d in self.image.data.dims if d != "signals"]

    def _pairs(self):
        view_dims = self._view_dims()
        return list(itertools.combinations(view_dims, 2))

    def _current_selected_dims(self):
        if self.buttons is None or self.buttons.value is None:
            pairs = self._pairs()
            if not pairs:
                raise ValueError("Need at least two non-'signals' dimensions to display an image.")
            return pairs[0]
        return self.buttons.value

    def _current_slider_values(self):
        return {d: w.value for d, w in self.slider.items()}

    def _make_png_bytes(self, arr2d):
        arr = np.asarray(arr2d)

        if arr.ndim != 2:
            raise ValueError(f"Expected a 2D array for display, got shape {arr.shape}")

        # Convert to float32, sanitize, then scale to uint8 for PNG display.
        arr = arr.astype(np.float32, copy=False)
        arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)

        vmin = float(arr.min())
        vmax = float(arr.max())

        if vmax > vmin:
            arr = (arr - vmin) / (vmax - vmin)
        else:
            arr = np.zeros_like(arr, dtype=np.float32)

        arr_u8 = (255 * arr).astype(np.uint8)

        buf = io.BytesIO()
        PILImage.fromarray(arr_u8).save(buf, format="PNG")
        return buf.getvalue()

    def _build_current_slice(self):
        data = self.image.data
        selected_dims = self._current_selected_dims()

        # Slice every non-view dimension using current sliders.
        indexers = {}
        for d in data.dims:
            if d not in selected_dims:
                if d in self.slider:
                    indexers[d] = self.slider[d].value
                else:
                    indexers[d] = 0

        # isel indexes by dimension name; transpose reorders into display order. :contentReference[oaicite:1]{index=1}
        view = data.isel(indexers).transpose(*selected_dims)

        # At this point it should be 2D
        return view.values

    def _refresh_image_only(self):
        arr2d = self._build_current_slice()
        self.image_view.value = self._make_png_bytes(arr2d)

    def _make_sliders_for_selection(self, selected_dims, old_values=None):
        old_values = old_values or {}
        sliders = {}
        _coord_dict  = {}
        for d in self.image.data.dims:
            if d not in selected_dims:
                max_index = self.image.data.sizes[d] - 1
                value = min(old_values.get(d, max_index//2), max_index)

                sliders[d] = IntSlider(
                    value=value,
                    min=0,
                    max=max_index,
                    step=1,
                    description=d,
                    continuous_update=True,
                )
                sliders[d].observe(self.update_image, names="value")

        return sliders

    def remake_widget(self, sender=None, **kwargs):
        """
        Rebuild the whole widget. Safe to call:
        - at init
        - after data_refreshed / data_appended / data_removed
        - manually
        """
        pairs = self._pairs()
        if not pairs:
            raise ValueError("Need at least two non-'signals' dimensions to display an image.")

        old_selected = None
        old_slider_values = {}

        if self.buttons is not None:
            old_selected = self.buttons.value

        if self.slider:
            old_slider_values = self._current_slider_values()

        if old_selected not in pairs:
            old_selected = pairs[0]

        labels = [f"{a}{b}" for a, b in pairs]

        self.buttons = ToggleButtons(
            options=[(label, pair) for label, pair in zip(labels, pairs)],
            description="View:",
            value=old_selected,
        )
        self.buttons.observe(self.update_image, names="value")

        self.slider = self._make_sliders_for_selection(old_selected, old_slider_values)

        # Build image widget from current state
        initial_slice = self._build_current_slice()
        self.image_view = Image(
            value=self._make_png_bytes(initial_slice),
            format="png",
        )

        self.children = (self.buttons, self.image_view, *self.slider.values())

    def update_image(self, change):
        """
        Handles:
        - slider changes: only refresh image
        - button changes: rebuild sliders + refresh image
        """
        owner = change.get("owner", None)
        name = change.get("name", None)

        if name != "value":
            return

        # If the view pair changed, the controlled axes changed too,
        # so rebuild the slider set while preserving any matching values.
        if owner is self.buttons:
            old_slider_values = self._current_slider_values()
            selected_dims = self.buttons.value

            self.slider = self._make_sliders_for_selection(selected_dims, old_slider_values)
            self.children = (self.buttons, self.image_view, *self.slider.values())
            self._refresh_image_only()
            return

        # Otherwise it was a slider move.
        self._refresh_image_only()
        



