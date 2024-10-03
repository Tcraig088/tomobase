import numpy as np
from tomondt.plugins.decorators import *

from qtpy.QtWidgets import QHBoxLayout, QVBoxLayout, QComboBox, QLabel, QWidget, QFrame, QGridLayout, QPushButton, QSpinBox, QDialog
from PyQt5.QtCore import Qt

@NDtFunc(htype='Phantom', name='rod')
def load_rod(dim=512,length=300,radius=100,proportion=0.5,intensity=0.3):
    pradius = 2*(radius/dim)
    obj = np.zeros((dim,dim,dim),dtype=np.float32)
    img = np.zeros((dim,dim),dtype=np.float32)
    x = np.linspace(-1, 1, dim)
    y = np.linspace(-1, 1, dim)
    z = np.linspace(-1, 1, dim)

    X, Y = np.meshgrid(x, y)
    disk1= (X**2 + Y**2) <= pradius**2
    dissk2 = (X**2 + Y**2) <= (pradius*proportion)**2
    img[disk1>0] = intensity
    img[dissk2>0] = 1

    L = length - 2*radius
    #L =length
    z1, z2 = dim//2 - L//2, dim//2 + L//2
    for i in range(dim):
        if i >= z1 and i <= z2:
            obj[:,:,i] = img

    sphere = np.zeros((dim,dim,dim),dtype=np.float32)
    X,Y,Z = np.meshgrid(x,y,z)
    sphere1 = (X**2 + Y**2 + Z**2) <= pradius**2
    a,b,c = pradius*proportion, pradius*proportion, pradius
    sphere2 = ((X**2)/(a**2) + (Y**2)/(b**2) + (Z**2)/(c**2)) <= 1
    sphere[sphere1>0] = intensity
    sphere[sphere2>0] = 1

    y1,y2 = dim//2 + radius, dim//2 - radius
    xz1,xz2 = dim//2 - radius, dim//2 + radius
    top_limit,bottom_limit  = z2+radius, z1-radius
    obj[xz1:xz2, xz1:xz2, z2:top_limit] = sphere[xz1:xz2, xz1:xz2, dim//2:y1] 
    obj[xz1:xz2, xz1:xz2, bottom_limit:z1] = sphere[xz1:xz2, xz1:xz2, y2:dim//2]
    return obj

@NDtWidget(htype='Phantom', name='rod', exec_method = 'get_volume')
class RodWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Create the layout
        self.layout = QHBoxLayout()
        
        # Create the buttons and spin boxes
        self.dimSpinBox = QSpinBox()
        self.lengthSpinBox = QSpinBox()
        self.radiusSpinBox = QSpinBox()
        self.proportionSpinBox = QSpinBox()
        self.intensitySpinBox = QSpinBox()

        # Add the widgets to the layout
        self.layout.addWidget(QLabel("Dimension:"))
        self.layout.addWidget(self.dimSpinBox)
        self.layout.addWidget(QLabel("Length:"))
        self.layout.addWidget(self.lengthSpinBox)
        self.layout.addWidget(QLabel("Radius:"))
        self.layout.addWidget(self.radiusSpinBox)
        self.layout.addWidget(QLabel("Proportion:"))
        self.layout.addWidget(self.proportionSpinBox)
        self.layout.addWidget(QLabel("Intensity:"))
        self.layout.addWidget(self.intensitySpinBox)

        self.layout.setAlignment(Qt.AlignTop)
        self.setLayout(self.layout)
        self.show()
        
    def get_volume(self):
        dim = self.dimSpinBox.value()
        length = self.lengthSpinBox.value()
        radius = self.radiusSpinBox.value()
        proportion = self.proportionSpinBox.value()
        intensity = self.intensitySpinBox.value()
        return load_rod(dim,length,radius,proportion,intensity)