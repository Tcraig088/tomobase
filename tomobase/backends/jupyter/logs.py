import logging
import ipywidgets as widgets
from IPython.display import display

from ...core.log import tomobase_logger, logger

class OutputWidgetHandler(logging.Handler):
    def __init__(self, output_widget):
        super().__init__()
        self.output_widget = output_widget

    def emit(self, record):
        try:
            msg = self.format(record)
            self.output_widget.append_stdout(msg + "\n")
        except Exception:
            self.handleError(record)


class LogWidget:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is not None:
            raise RuntimeError("Only one LogWidget instance is allowed.")
        instance = super().__new__(cls)
        cls._instance = instance
        return instance

    def __init__(self):
        

        if getattr(self, "_initialized", False):
            return

        self.tomobase_logger = tomobase_logger
        self.logger = self.tomobase_logger.get_logger()

        self.output = widgets.Output(
            layout=widgets.Layout(
                border='1px solid #999',
                height='300px',
                overflow='auto',
                width='100%'
            )
        )

        self.close_button = widgets.Button(
            description='Close log',
            button_style='warning',
            icon='times'
        )
        self.clear_button = widgets.Button(
            description='Clear',
            button_style='',
            icon='trash'
        )

        self.close_button.on_click(self._handle_close_clicked)
        self.clear_button.on_click(self._handle_clear_clicked)

        self.container = widgets.VBox([
            widgets.HBox([self.clear_button, self.close_button]),
            self.output
        ])

        self.widget_handler = OutputWidgetHandler(self.output)
        self.widget_handler.setLevel(logging.TRACE)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.widget_handler.setFormatter(formatter)

        self.is_open = False
        self._initialized = True

    def open(self):
        if self.is_open:
            display(self.container)
            return

        self.tomobase_logger.disable_cli()

        if self.widget_handler not in self.logger.handlers:
            self.logger.addHandler(self.widget_handler)

        self.is_open = True
        display(self.container)

    def close(self):
        if not self.is_open:
            return

        if self.widget_handler in self.logger.handlers:
            self.logger.removeHandler(self.widget_handler)

        self.tomobase_logger.enable_cli()
        self.output.close()
        self.container.close()

        self.is_open = False
        LogWidget._instance = None

    def clear(self):
        self.output.clear_output()

    def _handle_close_clicked(self, _):
        self.close()

    def _handle_clear_clicked(self, _):
        self.clear()
        
def display_log():
    log_widget = LogWidget()
    log_widget.open()