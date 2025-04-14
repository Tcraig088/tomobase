import logging

class TomobaseLogger:
    def __init__(self, name='tomobase_logger', level=logging.DEBUG):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False  # Prevent duplicate logs
        self._setup_stream_handler()

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
 


