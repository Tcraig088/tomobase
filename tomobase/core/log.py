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


class Log_Handler:
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

tomobase_logger = Log_Handler()
logger = tomobase_logger.get_logger()
""" 
Python log module instance for tomobase. Provides custom log levels TRACE and VERBOSE, and a Log_Handler class to manage logging configuration. 
The logger instance can be used throughout the tomobase codebase for consistent logging.

By convention:\n
- Use logger.trace() for very detailed debugging information, typically only useful structural developement lower than debug.\n
- Use logger.debug() for general debugging information that may be useful during development of tomographic tools.\n
- Use logger.verbose() for detailed information that is meant to be accessible to users on request.\n
- Use logger.info() for general informational messages about the progress of operations.\n
- Use logger.warning() for situations that are unexpected but do not prevent the program from functioning.\n
- Beyond this point errors should throw exceptions\n
"""