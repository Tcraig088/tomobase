import logging
import time
import progressbar
from qtpy.QtCore import QObject, Signal
import coolname

from tomobase.registrations.base import ItemDictNonSingleton, ItemDict, Item

class ProgressBar(QObject):
    finished = Signal()
    updated  = Signal(int, str)
    started = Signal(int, str)
    maxupdated = Signal(int)

    def __init__(self):
        super().__init__()
        self.progress_bar = None
        self.start_time = None
        self.max_value = None
        self.inheritor = None

    def start(self, max_value, label='Progress'):
        self.start_time = time.time()
        self.max_value = max_value
        self.progress_bar = progressbar.ProgressBar(
        max_value=max_value,
        widgets=[
            progressbar.Percentage(), " ",
            progressbar.Bar(), " ",
            progressbar.Timer(), "",
            progressbar.ETA(), " ",
            progressbar.SimpleProgress()]
        )
        self.progress_bar.max_value = max_value
        self.progress_bar.start()
        self.started.emit(max_value, label)

    def update_max(self, max_value):
        self.progress_bar.max_value = max_value
        self.max_value = max_value
        self.maxupdated.emit(max_value)

    def finish(self):
        self.progress_bar.finish()
        self.finished.emit()

    def update(self, value):
        self.progress_bar.update(value)
        # get ETA and time progress adn time taken
        elapsed_time = time.time() - self.start_time
        if self.progress_bar.value - self.progress_bar.min_value == 0:
            eta = 0
        else:
            eta = (self.progress_bar.max_value - self.progress_bar.value)*(elapsed_time/self.progress_bar.value-self.progress_bar.min_value)
        #convert time to hours, minutes and seconds
        hours, remainder = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        msg = f'{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}'
        hours, remainder = divmod(eta, 3600)
        minutes, seconds = divmod(remainder, 60)
        msg2 = f'{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}'
        final_msg = f'Elapsed {msg} ({value})| ETA {msg2} ({self.max_value})'
        self.updated.emit(value, final_msg)

class ProgressHandler(ItemDict, QObject):
    added = Signal(str)
    added_subsignal = Signal(str, str)
    removed = Signal(str)

    def __init__(self):
        ItemDict.__init__(self)
        QObject.__init__(self)
        self.pending_registrations = {}

    def add_signal(self, signal):
        signal_key = signal.upper().replace(' ', '_')
        if signal_key in self._dict:
            pass
        else:
            self[signal] = ProgressBar()
            self.added.emit(signal)
        
        return self[signal_key]

    def add_subsignal(self, signal, subsignal=None):
        if subsignal is None:
            subsignal = coolname.generate_slug(2)

        signal_key = signal.upper().replace(' ', '_')
        if subsignal not in self._dict:
            self[subsignal] = ProgressBar()
            subsignal_key = subsignal.upper().replace(' ', '_')
            if self[signal_key].value.inheritor is None:
                self[subsignal_key].value.inheritor = signal
            else:
                self[subsignal_key].value.inheritor = self[signal_key].value.inheritor
            self.added_subsignal.emit(self[subsignal_key].value.inheritor, subsignal)
        return self[subsignal_key]

    def remove_signal(self, item):
        signal = item.name.upper().replace(' ', '_')
        if signal in self._dict:
            self[signal].value.finish()
            del self._dict[signal]
            self.removed.emit(signal)

progresshandler = ProgressHandler()  
