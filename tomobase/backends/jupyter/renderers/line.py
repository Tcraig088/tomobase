
import numpy as np
import ipywidgets as widgets
from ipywidgets import HBox, VBox, Output, Accordion
from IPython.display import display, clear_output

from ....core import base_classes


class AxisWidget(Accordion):
    def __init__(self, axis_name, data, **kwargs):
        self.data = data
        self.select = widgets.Dropdown(description="axis", options=[None], value=None)
        self.log_scale = widgets.Checkbox(description="Log Scale", value=False)
        self.limits = widgets.FloatRangeSlider(description="Limits", value=(0.0, 1.0), min=0.0, max=1.0)
        self.get_options()
        
        super().__init__(children=[VBox([self.select, self.log_scale, self.limits])], titles=[axis_name], **kwargs)

    def get_options(self):
        names = []
        ds = self.data.xr
        names.extend(list(ds.data_vars))
        names.extend(list(ds.coords))
        names = list(dict.fromkeys(names))
        value = self.select.value
        self.select.options = names
        if value in names:
            self.select.value = value
        else:
            self.select.value = names[0]
            self.set_limits()
            
    def set_limits(self):
        ds = self.data.xr
        var = ds[self.select.value]

        if np.issubdtype(var.dtype, np.number):
            vmin = float(var.min())
            vmax = float(var.max())
            if vmin == vmax:
                vmax = vmin + 1e-9

            if self.log_scale.value:
                vmin = max(vmin, 1e-9)

                self.limits.min = vmin * 0.5
                self.limits.max = vmax * 2
            else:
                span = vmax - vmin
                self.limits.min = vmin - span * 0.5
                self.limits.max = vmax + span * 0.5
            self.limits.value = (vmin, vmax)
            
            

class LineInfoWidget(VBox):
    def __init__(self, data):
        self.data = data
        self.x_axis = AxisWidget("X Axis", self.data)
        self.y_axis = AxisWidget("Y Axis", self.data)
        self.by = widgets.Dropdown(description="Group By", options=["sample"], value="sample")
        self.get_options()
        super().__init__(children=[self.x_axis, self.y_axis, self.by])
        
    def get_options(self):
        ds = self.data.xr
        self.x_axis.get_options()
        self.y_axis.get_options()
        
        names = []
        names.extend(list(ds.data_vars))
        names.extend(list(ds.coords))
        names = list(dict.fromkeys(names))
        value = self.by.value
        self.by.options = names
        if value in names:
            self.by.value = value
        elif "sample" in names:
            self.by.value = "sample"
        else:
            self.by.value = names[0]
        return names
        
class LinePlotWidget(VBox):
    def __init__(self, data):
        self.data = data
        self.plot_out = Output()
        super().__init__(children=[self.plot_out])

    def update_plot(self, info_widget):
        ds = self.data.xr
        xlim, ylim = info_widget.x_axis.limits.value, info_widget.y_axis.limits.value

        plot_kwargs = {
            "x": info_widget.x_axis.select.value,
            "logx": info_widget.x_axis.log_scale.value,
            "logy": info_widget.y_axis.log_scale.value,
        }

    
        by = info_widget.by.value
        if by is not None:
            plot_kwargs["by"] = by

        if xlim is not None:
            plot_kwargs["xlim"] = xlim

        if ylim is not None:
            plot_kwargs["ylim"] = ylim

        with self.plot_out:
            clear_output(wait=True)

            try:
                display(ds[info_widget.y_axis.select.value].hvplot.line(**plot_kwargs))
            except Exception as e:
                raise Exception(f"Error plotting line plot: {type(e).__name__}: {e}")



@base_classes.MeasurementAbstract.ipywidgets.register(name="line plot")
class LineWidget(HBox):
    def __init__(self, measurement: base_classes.MeasurementAbstract, **kwargs):
        super().__init__(**kwargs)
        self.data = measurement
        self.info_widget = LineInfoWidget(self.data)
        self.plot_widget = LinePlotWidget(self.data)
        
        self.children = [self.plot_widget, self.info_widget]
        self._update_plot()
        
        self.data.data_refreshed.connect(self._remake_widget, weak=False)
        self.data.data_appended.connect(self._remake_widget, weak=False)
        self.data.data_removed.connect(self._remake_widget, weak=False)

        self.info_widget.x_axis.select.observe(self._update_plot)
        self.info_widget.x_axis.log_scale.observe(self._update_plot)
        self.info_widget.x_axis.limits.observe(self._update_plot)
        
        self.info_widget.y_axis.select.observe(self._update_plot)
        self.info_widget.y_axis.log_scale.observe(self._update_plot)
        self.info_widget.y_axis.limits.observe(self._update_plot)
        
        self.info_widget.by.observe(self._update_plot)
        
    def _update_plot(self, *args, **kwargs):
        self.plot_widget.update_plot(self.info_widget)

    def _remake_widget(self, *args, **kwargs):
        self.info_widget.get_options()
        self._update_plot()


