from qtpy.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QGroupBox
from qtpy.QtCore import Qt

class CollapsableWidget(QWidget):
    def __init__(self, parent=None, title=''):
        super().__init__(parent)
        self.title= title
        
        self.group_box = QGroupBox(self.title, self)
        self.group_box.setCheckable(True)
        self.layout = QVBoxLayout()
        
    def setLayout(self, layout):
        self.group_box.setLayout(layout)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.group_box)
        super().setLayout(main_layout)

        self.group_box.toggled.connect(self.toggle)
        self.layout.setAlignment(Qt.AlignTop)
    
    def show(self):
        self.group_box.show()
        super().show()
        self.group_box.setChecked(False)
        
    def toggle(self, checked):
        if not checked:
            self.group_box.setMaximumHeight(13)
        else:
            self.group_box.setMaximumHeight(10000000) 
