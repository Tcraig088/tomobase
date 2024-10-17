import napari

from qtpy.QtWidgets import QMenu
from qtpy.QtCore import Qt

from tomobase.log import logger
from tomobase.napari.process_widgets import ProjectWidget, AlignWidget
from tomobase.registrations.processes import TOMOBASE_PROCESSES
class TomographyMenuWidget(QMenu):  
    def __init__(self, viewer: 'napari.viewer.Viewer', parent=None):
        super().__init__("Tomography", parent)
        self.menu = {}
        self.alignments = {}
        self.viewer = viewer
        
        self.menu['Configs'] = self.addAction('Configurations')
        self.menu['Alignment'] = self.addMenu('Alignment')
        for key, value in TOMOBASE_PROCESSES.alignments.items():
            logger.info(f"Key: {key}, Value: {value}")
            self.alignments[key] = self.menu['Alignment'].addAction(key)
            self.alignments[key].triggered.connect(lambda checked, k=key, v=value: self.onAlignmentTriggered(k, v))
                
        self.menu['Reconstruction'] = self.addAction('Reconstruction')
        self.menu['Forward Project'] = self.addAction('Forward Projection')
        self.menu['Post Processing'] = self.addAction('Post Processing')
        self.menu['Utilities'] = self.addAction('Utilities')
        
        
        
        self.menu['Forward Project'].triggered.connect(self.onFPTriggered)
        
    def onFPTriggered(self):
        self.viewer.window.add_dock_widget(ProjectWidget(self.viewer), name='Forward Projection', area='right')
        
    def onAlignmentTriggered(self, name, process):
        self.viewer.window.add_dock_widget(AlignWidget(name, process, self.viewer), name='Alignment: '+ name, area='right')