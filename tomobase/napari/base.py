import napari

from qtpy.QtWidgets import QMenu
from qtpy.QtCore import Qt

from tomobase.napari.process_widgets import ProjectWidget
class TomographyMenuWidget(QMenu):  
    def __init__(self, viewer: 'napari.viewer.Viewer', parent=None):
        super().__init__("Tomography", parent)
        self.actions = {}
        self.viewer = viewer
        
        self.actions['Configs'] = self.addAction('Configurations')
        self.actions['Alignment'] = self.addAction('Alignment')
        self.actions['Reconstruction'] = self.addAction('Reconstruction')
        self.actions['Forward Project'] = self.addAction('Forward Projection')
        self.actions['Post Processing'] = self.addAction('Post Processing')
        self.actions['Utilities'] = self.addAction('Utilities')

        self.actions['Forward Project'].triggered.connect(self.onFPTriggered)
        
    def onFPTriggered(self):
        self.viewer.window.add_dock_widget(ProjectWidget(self.viewer), name='Forward Projection', area='right')