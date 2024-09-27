from qtpy.QtWidgets import QMenu
from qtpy.QtCore import Qt
   
class TomographyMenuWidget(QMenu):  
    def __init__(self, parent=None):
        super().__init__("Tomography", parent)
        self.actions = {}
        
        self.actions['Configs'] = self.addAction('Configurations')
        self.actions['Alignment'] = self.addAction('Alignment')
        self.actions['Reconstruction'] = self.addAction('Reconstruction')
        self.actions['Forward Project'] = self.addAction('Forward Projection')
        self.actions['Post Processing'] = self.addAction('Post Processing')
        self.actions['Utilities'] = self.addAction('Utilities')
