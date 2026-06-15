
from ipywidgets import VBox, HBox, Accordion, Label, Output, Image, IntSlider, ToggleButtons, GridBox, Layout

from ...core.base_classes import ImageAbstract

from traitlets import link


class SliceGrid(GridBox):
    """A grid of slice views for multiple images.
    """
    
    def __init__(self, images, columns=2, **kwargs):
        """Initialize the SliceGrid widget.

        Args:
            images (list of ImageAbstract): A list of images to display in the grid.
            columns (int, optional): Number of columns in the grid. Defaults to 2.
        """
        self.images = list(images)
        self.widgets = [img.interactive.slice_view() for img in self.images]

        super().__init__(
            children=tuple(self.widgets),
            layout=Layout(
                display="grid",
                grid_template_columns=" ".join(["1fr"] * columns),
                grid_gap="12px",
            ),
            **kwargs,
        )

        self._syncing = False
        self._attach_all()

    def _attach_all(self):
        for widget in self.widgets:
            widget.buttons.observe(self._on_buttons_changed, names="value")

            for dim, slider in widget.slider.items():
                slider.observe(self._on_slider_changed, names="value")

    def _reattach_slider_observers(self):
        for widget in self.widgets:
            for dim, slider in widget.slider.items():
                slider.observe(self._on_slider_changed, names="value")

    def _on_buttons_changed(self, change):
        if self._syncing or change["name"] != "value":
            return

        source = change["owner"]
        new_value = change["new"]

        self._syncing = True
        try:
            for widget in self.widgets:
                if widget.buttons is not source:
                    valid_values = [v for _, v in widget.buttons.options]
                    if new_value in valid_values:
                        widget.buttons.value = new_value

            # Button changes rebuild sliders inside ImageSliceWidget,
            # so attach observers to the new slider objects.
            self._reattach_slider_observers()

        finally:
            self._syncing = False

    def _on_slider_changed(self, change):
        if self._syncing or change["name"] != "value":
            return

        source_slider = change["owner"]
        new_value = change["new"]

        # Find which dimension this slider belongs to.
        source_dim = None
        for widget in self.widgets:
            for dim, slider in widget.slider.items():
                if slider is source_slider:
                    source_dim = dim
                    break
            if source_dim is not None:
                break

        if source_dim is None:
            return

        self._syncing = True
        try:
            for widget in self.widgets:
                if source_dim in widget.slider:
                    slider = widget.slider[source_dim]
                    slider.value = min(max(new_value, slider.min), slider.max)
        finally:
            self._syncing = False