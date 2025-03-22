import logging
import time
import progressbar
from qtpy.QtCore import QObject, Signal


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
        final_msg = f'Elapsed time: {msg} | ETA: {msg2}'
        self.updated.emit(value, final_msg)


class TomobaseLogger:
    def __init__(self, name='tomobase_logger', level=logging.DEBUG):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False  # Prevent duplicate logs
        self._setup_stream_handler()
        self.progress_bar = ProgressBar()

    def _setup_stream_handler(self):
        if not any(isinstance(handler, logging.StreamHandler) for handler in self.logger.handlers):
            handler = logging.StreamHandler()
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def get_logger(self):
        return self.logger

tomobase_logger = TomobaseLogger()   
logger = tomobase_logger.get_logger()
 


