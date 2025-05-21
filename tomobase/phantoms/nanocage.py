
import os 
import pickle
from tomobase.data import Volume
from tomobase.hooks import phantom_hook
from qtpy.QtWidgets import QHBoxLayout, QVBoxLayout, QComboBox, QLabel, QWidget, QFrame, QGridLayout, QPushButton, QSpinBox, QDialog
from qtpy.QtCore import Qt

@phantom_hook
def nanocage():
    path = os.path.dirname(__file__)
    path = os.path.join(path, 'nanocage.pkl')
    
    return Volume(pickle.load(open(path,'rb')))

