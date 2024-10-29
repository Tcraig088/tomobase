import napari

from qtpy.QtWidgets import QMenu
from qtpy.QtCore import Qt

from tomobase.log import logger

from tomobase.registrations.processes import TOMOBASE_PROCESSES
from tomobase.registrations.transforms import TOMOBASE_TRANSFORM_CATEGORIES

class TomographyMenuWidget(QMenu):  
    def __init__(self, viewer: 'napari.viewer.Viewer', parent=None):
        super().__init__("Tomography", parent)
        self.menu = {}
        self.viewer = viewer
        
        self.menu['Configs'] = self.addAction('Configurations')
        for key, value in TOMOBASE_TRANSFORM_CATEGORIES.items():
            self.menu[key] = {}
            self.menu[key][key] = self.addMenu(key.capitalize())
            self._current_transform = key
            self.traverseMenu(value.categories)
  
        for process_category, processes in TOMOBASE_PROCESSES.items():
            for key, value in processes.items():
                if value.widget is None:
                    widget = TOMOBASE_TRANSFORM_CATEGORIES[process_category].widget
                else:
                    widget = value.widget
                name = process_category + ' ' + key
                
                _dict = {'category': [TOMOBASE_TRANSFORM_CATEGORIES[process_category].value()], 'name': name, 'controller': value}
                self.menu[process_category][key].triggered.connect(lambda checked, w = widget, k=_dict: self.onProcessTriggered(w, k))
        
    def onProcessTriggered(self, widget, process):
        self.viewer.window.add_dock_widget(widget(process, self.viewer), name=process['name'], area='right')
        

    def traverseMenu(self, item, previous=None):
        if isinstance(item, dict):
            for key, value in item.items(): 
                if not isinstance(key, str):
                    self.traverseMenu(value)
                else:
                    if previous is None:
                        self.addMenuItem(key, ismenu=True)
                    else:
                        self.addMenuItem(key, previous, ismenu=True)
                    self.traverseMenu(value, key)
        else:
            if previous is None:
                for name in item:
                    self.addMenuItem(name)
            else:
                for name in item:
                    self.addMenuItem(name, previous)
            

    def addMenuItem(self, value, previous=None,  ismenu=False):
        if previous is None:
            index = self.menu[self._current_transform][self._current_transform]
        else:
            index = self.menu[self._current_transform][previous]
            
        if ismenu:
            self.menu[self._current_transform][value] = index.addMenu(value.capitalize())
        else:
            if isinstance(value, str):
                value = [value]
            for item in value:
                self.menu[self._current_transform][item] = index.addAction(item.capitalize())
                
        