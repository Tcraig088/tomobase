from qtpy.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QHBoxLayout, QFileDialog

class FileSaveDialog(QWidget):
    def __init__(self):
        super().__init__()
        self.label = QLabel('File:', self)
        self.line_edit = QLineEdit(self)
        self.button_file_select = QPushButton('Select File', self)
        self.button_file_select.clicked.connect(self.showFileDialog)
        self.extensions = ""
        layout = QHBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.line_edit)
        layout.addWidget(self.button_file_select)
        self.setLayout(layout)

    def set_extensions(self, **kwargs):
        for key, value in kwargs.items():
            mystring = value + " (*." + key + ");;"
            self.extensions = mystring + self.extensions
        
        
    def showFileDialog(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", self.extensions, options=options)
        if file_path:
            self.line_edit.setText(file_path)

