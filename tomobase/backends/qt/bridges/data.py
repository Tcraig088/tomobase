from qtpy.QtCore import QObject, Signal


class QtDataBridge(QObject):
    data_refreshed = Signal()
    data_appended = Signal(object)
    data_removed = Signal(object)

    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
        self._connections = []

        model.data_refreshed.connect(self._on_data_refreshed, weak=False)
        model.data_appended.connect(self._on_data_appended, weak=False)
        model.data_removed.connect(self._on_data_removed, weak=False)

        self._connections.extend([
            (model.data_refreshed, self._on_data_refreshed),
            (model.data_appended, self._on_data_appended),
            (model.data_removed, self._on_data_removed),
        ])

    def _on_data_refreshed(self, sender):
        self.data_refreshed.emit()

    def _on_data_appended(self, sender, item):
        self.data_appended.emit(item)

    def _on_data_removed(self, sender, item):
        self.data_removed.emit(item)

    def disconnect(self):
        for sig, callback in self._connections:
            sig.disconnect(callback)
        self._connections.clear()