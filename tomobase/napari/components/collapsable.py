from qtpy.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QGroupBox
from qtpy.QtCore import Qt

class CollapsableWidget(QWidget):
    """A QWidget that can be collapsed and expanded for better organization of the GUI.
    
    Methods:
    
        __init__(self, title='', parent=None): Initializes the CollapsableWidget.
    """
    def __init__(self, title='', parent=None):
        """Initializes the CollapsableWidget.

        Args:
            title (str, optional): title of the widget. Defaults to ''.
            parent (_type_, optional): parent widget
        """
        super().__init__(parent)
        self._title= title
        
        self._group_box = QGroupBox(self._title, self)
        self._group_box.setCheckable(True)
        self._layout = QVBoxLayout()
        
    def setLayout(self, layout):
        """sets the layout of the widget. Inherited from QWidget.

        Args:
            layout (QWidget Layout): the layout being setup for the widget.
        """
        self._group_box.setLayout(layout)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self._group_box)
        super().setLayout(main_layout)

        self._group_box.toggled.connect(self.toggle)
        self._layout.setAlignment(Qt.AlignTop)
    
    def show(self):
        self._group_box.show()
        super().show()
        self._group_box.setChecked(False)
        
    def toggle(self, checked):
        if not checked:
            self._group_box.setMaximumHeight(13)
        else:
            self._group_box.setMaximumHeight(10000000) 
