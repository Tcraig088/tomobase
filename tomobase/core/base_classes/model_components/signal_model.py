
import copy
from blinker import Signal

class SignalModel():

    def __init__(self, data, *args, **kwargs):
        """Initialize the Data object."""
        super().__init__(*args, **kwargs)

        self.data_refreshed = Signal()
        self.data_appended = Signal()
        self.data_removed = Signal()

    def refresh(self):
        """Refresh the data."""
        self.data_refreshed.send(self)

    def append(self, item):
        """Append an item to the data."""
        self.data_appended.send(self, item=item)

    def remove(self, item):
        """Remove an item from the data."""
        self.data_removed.send(self, item=item)
        
