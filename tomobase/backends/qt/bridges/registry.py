

from ....core import registers

from qtpy.QtCore import QObject, Signal

class QtRegistryBridge(QObject):
    """ A class to bridge blinker event to qt allowing them to be used with Qt threading and 

    Attributes:
        added (Signal): Signal emitted when an item is added to the registry. Emits the key and value of the added item.
        removed (Signal): Signal emitted when an item is removed from the registry. Emits the key and old value of the removed item.
        renamed (Signal): Signal emitted when an item is renamed in the registry. Emits the old key, new key, and value of the renamed item.
        updated (Signal): Signal emitted when an item is updated in the registry. Emits the key, old value, and new value of the updated item.
        
    Args:
        QObject (_type_): _description_
    """
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