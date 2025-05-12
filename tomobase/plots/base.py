





from qtpy.QtWidgets import QVBoxLayout, QWidget
import pyqtgraph as pg
import numpy as np

class BasePlotWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.plot_widget = pg.GraphicsLayoutWidget()
        self.layout.addWidget(self.plot_widget)
        self.setLayout(self.layout)

        def refresh():
            self.plot_widget.clear()
            self.plot_widget.addItem(self.plot)

class BarPlotWidget(BasePlotWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.plot = self.plot_widget.addPlot(title="Bar Plot")
        bar_item = pg.BarGraphItem(x=x, height=y, width=0.6, brush='b')
        self.plot.addItem(bar_item)

    def addData(self, df):
        y_axis = f"{df.metadata['name']} ({df.metadata['units_y']})"
        for i, row in df.iterrows():
            x = row[0]
            y = row[1]
            
            bar_item = pg.BarGraphItem(x0=x-0.3, x1=x+0.3, y0=0, y1=y, brush='b')
            self.plot.addItem(bar_item)

class HeatmapWidget(BasePlotWidget):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.plot = self.plot_widget.addPlot(title="Heatmap")
        self.image_item = pg.ImageItem(data)
        self.plot.addItem(self.image_item)
        self.plot.showGrid(x=True, y=True)
        self.plot.setAspectLocked(True)

class LineWithMarkersWidget(BasePlotWidget):
    def __init__(self, x, y, parent=None):
        super().__init__(parent)
        self.plot = self.plot_widget.addPlot(title="Line with Markers")
        self.plot.plot(x, y, pen=pg.mkPen(color='r', width=2), symbol='o', symbolSize=10, symbolBrush='b')