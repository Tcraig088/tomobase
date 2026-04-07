import logging

TRACE = 5
VERBOSE = 15

logging.addLevelName(TRACE, "TRACE")
logging.addLevelName(VERBOSE, "VERBOSE")

# Optional: make these available as logging.TRACE / logging.VERBOSE
logging.TRACE = TRACE
logging.VERBOSE = VERBOSE


def trace(self, message, *args, **kwargs):
    if self.isEnabledFor(TRACE):
        self._log(TRACE, message, args, **kwargs)


def verbose(self, message, *args, **kwargs):
    if self.isEnabledFor(VERBOSE):
        self._log(VERBOSE, message, args, **kwargs)


logging.Logger.trace = trace
logging.Logger.verbose = verbose


class TomobaseLogger:
    def __init__(self, name='tomobase_logger', level=logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False
        self._setup_stream_handler()

    def _setup_stream_handler(self):
        if not any(isinstance(handler, logging.StreamHandler) for handler in self.logger.handlers):
            self.handler = logging.StreamHandler()
            self.handler.setLevel(TRACE)  # allow all custom levels through
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            self.handler.setFormatter(formatter)
            self.logger.addHandler(self.handler)

    def get_logger(self):
        return self.logger

    def enable_cli(self):
        if self.handler is not None and self.handler not in self.logger.handlers:
            self.logger.addHandler(self.handler)

    def disable_cli(self):
        if self.handler is not None and self.handler in self.logger.handlers:
            self.logger.removeHandler(self.handler)

tomobase_logger = TomobaseLogger()
logger = tomobase_logger.get_logger()