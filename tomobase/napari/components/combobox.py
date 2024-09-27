from qtpy.QtCore import Qt
from qtpy.QtGui import QStandardItemModel, QStandardItem
from qtpy.QtWidgets import QComboBox, QStyledItemDelegate, QVBoxLayout, QWidget, QPushButton, QListView

class CheckableComboBox(QComboBox):
    class Delegate(QStyledItemDelegate):
        def sizeHint(self, option, index):
            size = super().sizeHint(option, index)
            size.setHeight(20)
            return size

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditable(False)  # Make the combo box non-editable
        self.setInsertPolicy(QComboBox.NoInsert)
        self.setItemDelegate(CheckableComboBox.Delegate())
        self.setView(QListView())
        self.view().pressed.connect(self.handleItemPressed)
        self.model = QStandardItemModel(self)
        self.setModel(self.model)

    def addItem(self, text):
        item = QStandardItem(text)
        item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        item.setData(Qt.Unchecked, Qt.CheckStateRole)
        self.model.appendRow(item)

    def handleItemPressed(self, index):
        item = self.model.itemFromIndex(index)
        if item.checkState() == Qt.Checked:
            item.setCheckState(Qt.Unchecked)
        else:
            item.setCheckState(Qt.Checked)
        self.updateDisplayText()

    def updateDisplayText(self):
        checked_items = []
        for index in range(self.model.rowCount()):
            item = self.model.item(index)
            if item.checkState() == Qt.Checked:
                checked_items.append(item.text())
        self.setCurrentText(", ".join(checked_items))  # Update the display text



