from IPython import display
from ipywidgets import VBox, HBox, Accordion, Label, Output, ToggleButtons, IntSlider, Dropdown, Checkbox, FloatRangeSlider
import pyvista as pv
import numpy as np
import itertools
from ....core import data_classes



class VolumeInfoWidget(Accordion):
    def __init__(self, volume_widget, **kwargs):
        super().__init__(**kwargs)

        self.volume_widget = volume_widget

        self.colormap_dropdown = Dropdown(
            options=[
                "gray",
                "bone",
                "viridis",
                "plasma",
                "inferno",
                "magma",
                "cividis",
                "jet",
            ],
            value=getattr(volume_widget, "colormap", "gray"),
            description="Colormap:",
        )

        self.opacity_dropdown = Dropdown(
            options=[
                ("linear", "linear"),
                ("linear_r", "linear_r"),
                ("geom", "geom"),
                ("geom_r", "geom_r"),
                ("sigmoid", "sigmoid"),
                ("sigmoid_r", "sigmoid_r"),
                ("sigmoid_6", "sigmoid_6"),
                ("sigmoid_6_r", "sigmoid_6_r"),
            ],
            value=getattr(volume_widget, "opacity", "linear"),
            description="Opacity:",
        )
        self.shade_checkbox = Checkbox(
            value=getattr(volume_widget, "shade", True),
            description="Shade",
        )
        self.clim_range = FloatRangeSlider(
            value=(0.0, 1.0),
            min=-1.0, 
            max=2.0,
            description="Color Limits:",
            continuous_update=True,
        )

        body = VBox([self.colormap_dropdown, self.opacity_dropdown, self.shade_checkbox, self.clim_range])
        self.children = (body,)
        self.set_title(0, "Volume Info")


        self.colormap_dropdown.observe(self._on_change, names="value")
        self.opacity_dropdown.observe(self._on_change, names="value")
        self.shade_checkbox.observe(self._on_change, names="value")
        self.clim_range.observe(self._on_change, names="value")
        
    def _on_change(self, change):
        if change.get("name") != "value":
            return

        self.volume_widget.colormap = self.colormap_dropdown.value
        self.volume_widget.opacity = self.opacity_dropdown.value
        self.volume_widget.shade = self.shade_checkbox.value
        self.volume_widget.clim = self.clim_range.value
        self.volume_widget._refresh_volume_only()


@data_classes.images.Volume.ipywidgets.register(name="volume view")
class ImageVolumeWidget(VBox):
    def __init__(self, image: data_classes.images.Volume, **kwargs):
        super().__init__(**kwargs)
        self.layout.width = "800px"
        self.plotter = None
        self.volume_actor = None
        self.image = image
        self.slider = {}
        self.colormap = "cividis"
        self.clim = (0.0, 1.0)
        self.shade = True
        self.opacity = "sigmoid_6"
        self.buttons = None
        self.image_view = None

        # Dims that should not be used as volume axes by default.
        # They will instead be controlled by sliders if present.
        self._blocked_view_dims = {"signals", "n"}

        # Hook image events once.
        image.data_refreshed.connect(self.remake_widget, weak=False)
        image.data_appended.connect(self.remake_widget, weak=False)
        image.data_removed.connect(self.remake_widget, weak=False)

        self.remake_widget()

    def _view_dims(self):
        return [d for d in self.image.data.dims if d not in self._blocked_view_dims]

    def _triplets(self):
        view_dims = self._view_dims()
        return list(itertools.combinations(view_dims, 3))

    def _current_selected_dims(self):
        if self.buttons is None or self.buttons.value is None:
            triplets = self._triplets()
            if not triplets:
                raise ValueError("Need at least three valid view dimensions to display a volume.")
            return triplets[0]
        return self.buttons.value

    def _current_slider_values(self):
        return {d: w.value for d, w in self.slider.items()}

    def _build_current_volume(self):
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

        # Reorder into the displayed volume axis order.
        view = data.isel(indexers).transpose(*selected_dims)
        arr = np.asarray(view.values)

        if arr.ndim != 3:
            raise ValueError(f"Expected a 3D array for volume display, got shape {arr.shape}")

        return arr

    def _normalize_volume(self, arr3d):
        arr = np.asarray(arr3d)

        if arr.ndim != 3:
            raise ValueError(f"Expected a 3D array for display, got shape {arr.shape}")

        arr = arr.astype(np.float32, copy=False)
        arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)

        vmin = float(arr.min())
        vmax = float(arr.max())

        if vmax > vmin:
            arr = (arr - vmin) / (vmax - vmin)
        else:
            arr = np.zeros_like(arr, dtype=np.float32)

        return arr

    def _make_sliders_for_selection(self, selected_dims, old_values=None):
        old_values = old_values or {}
        sliders = {}

        for d in self.image.data.dims:
            if d not in selected_dims:
                max_index = self.image.data.sizes[d] - 1
                value = min(old_values.get(d, max_index // 2), max_index)

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

    def _render_volume(self):
        arr3d = self._build_current_volume()
        arr3d = self._normalize_volume(arr3d)

        pv.set_jupyter_backend("trame")

        if self.plotter is None:
            self.image_view.clear_output(wait=True)
            with self.image_view:
                self.plotter = pv.Plotter(notebook=True)
                self.volume_actor = self.plotter.add_volume(
                    arr3d,
                    cmap=self.colormap,
                    opacity=self.opacity,
                    clim = self.clim,
                    shade=self.shade,
                )
                self.plotter.show()
        else:
            self.plotter.clear_actors()
            self.volume_actor = self.plotter.add_volume(
                arr3d,
                cmap=self.colormap,
                opacity=self.opacity,
                clim = self.clim,
                shade=self.shade,
            )
            self.plotter.render()
            
    def _refresh_volume_only(self):
        self._render_volume()

    def remake_widget(self, sender=None, **kwargs):
        """
        Rebuild the whole widget. Safe to call:
        - at init
        - after data_refreshed / data_appended / data_removed
        - manually
        """
        triplets = self._triplets()
        if not triplets:
            raise ValueError("Need at least three valid view dimensions to display a volume.")

        old_selected = None
        old_slider_values = {}

        if self.buttons is not None:
            old_selected = self.buttons.value

        if self.slider:
            old_slider_values = self._current_slider_values()

        if old_selected not in triplets:
            old_selected = triplets[0]

        labels = [f"{a}{b}{c}" for a, b, c in triplets]

        self.buttons = ToggleButtons(
            options=[(label, triplet) for label, triplet in zip(labels, triplets)],
            description="View:",
            value=old_selected,
        )
        self.buttons.observe(self.update_image, names="value")

        self.slider = self._make_sliders_for_selection(old_selected, old_slider_values)

        # Build volume widget from current state
        if self.image_view is None:
            self.image_view = Output()
        self._refresh_volume_only()

        self.children = (self.buttons, self.image_view, *self.slider.values())

    def update_image(self, change):
        """
        Handles:
        - slider changes: only refresh volume
        - button changes: rebuild sliders + refresh volume
        """
        owner = change.get("owner", None)
        name = change.get("name", None)

        if name != "value":
            return

        # If the view triplet changed, the controlled axes changed too,
        # so rebuild the slider set while preserving any matching values.
        if owner is self.buttons:
            old_slider_values = self._current_slider_values()
            selected_dims = self.buttons.value

            self.slider = self._make_sliders_for_selection(selected_dims, old_slider_values)
            self.children = (self.buttons, self.image_view, *self.slider.values())
            self._refresh_volume_only()
            return

        # Otherwise it was a slider move.
        self._refresh_volume_only()


