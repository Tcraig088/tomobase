import numpy as np
import napari
import inspect
from qtpy.QtWidgets import QWidget, QComboBox, QLabel, QSpinBox, QHBoxLayout, QLineEdit, QVBoxLayout, QCheckBox, QPushButton, QGridLayout, QDoubleSpinBox
from qtpy.QtCore import Qt

from tomobase.log import logger
from tomobase.data import Volume, Sinogram
from tomobase.registrations.datatypes import TOMOBASE_DATATYPES
from tomobase.registrations.tiltschemes import TOMOBASE_TILTSCHEMES
from tomobase.napari.components import CollapsableWidget
from tomobase.napari.utils import get_value, get_widget
from tomobase.napari.process_widgets.process import ProcessWidget

from threading import Thread
from napari.qt.threading import thread_worker

class AlignWidget(ProcessWidget):
    def __init__(self, process:dict, viewer: 'napari.viewer.Viewer', parent=None):
        super().__init__(process=process, viewer=viewer, parent=None)
        self.name = process['name']


         


    
        
        