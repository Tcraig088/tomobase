

from ....core import registers

from qtpy.QtCore import QObject, Signal

class QtRegistryBridge(QObject):
    added = Signal(object, object)
    removed = Signal(object, object)
    renamed = Signal(object, object, object)
    updated = Signal(object, object, object)

    def __init__(self, registry, parent=None):
        super().__init__(parent)
        self.registry = registry

        registry.added.connect(self._on_added, weak=False)
        registry.removed.connect(self._on_removed, weak=False)
        registry.renamed.connect(self._on_renamed, weak=False)
        registry.updated.connect(self._on_updated, weak=False)

    def _on_added(self, sender, key, value):
        self.added.emit(key, value)

    def _on_removed(self, sender, key, old_value):
        self.removed.emit(key, old_value)

    def _on_renamed(self, sender, old_key, new_key, value):
        self.renamed.emit(old_key, new_key, value)

    def _on_updated(self, sender, key, old_value, new_value):
        self.updated.emit(key, old_value, new_value)


qt_phantoms = QtRegistryBridge(registers.phantoms)
qt_image_types = QtRegistryBridge(registers.image_types)
qt_tiltschemes = QtRegistryBridge(registers.tiltschemes)
qt_processes = QtRegistryBridge(registers.procedures)
qt_categories = QtRegistryBridge(registers.categories)