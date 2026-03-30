
import inspect
import magicgui
from typing import Iterable

from collections.abc import Iterable 
import inspect
import functools
from napari.qt.threading import thread_worker

from ....core import registers, logger
from .. import registers

from .gui import magicgui_builder


def _wrap_threader(func):
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        
        
        return wrapper
    return wrapper

def build_process_widget(process, viewer):
    sig = inspect.signature(process)

    # ---- threaded wrapper with same signature ----
    @functools.wraps(process)
    def threaded_process(*args, **kwargs):
        gui = threaded_process._gui  # injected after gui is created

        # 2) disable call button while running
        if gui.call_button is not None:
            gui.call_button.native.setEnabled(False)

        # (optional) set a status in napari
        viewer.status = f"Running: {process.__name__}"

        def _reenable():
            if gui.call_button is not None:
                gui.call_button.native.setEnabled(True)
            viewer.status = ""

        @thread_worker
        def work():
            # 1) runs in a background thread
            logger.debug(f"Starting process: {process.__name__} with args: {args} and kwargs: {kwargs}")
            return process(*args, **kwargs)

        worker = work()

        # returned runs on main thread
        @worker.returned.connect
        def _on_returned(result):
            process_names = [item.model.process_name for item in model_controllers.values()]
            if not isinstance(result, Iterable):
                result = [result]
            for item in result:
                logger.debug(f"Process returned: {item}")
                if type(item) in registers.image_types.values() and item.process_name not in process_names:
                    logger.debug(f"Registering new model from process: {item.process_name}")
                    get_image_controller(item)

        @worker.errored.connect
        def _on_error(err):
            # err is an Exception (or a NapariError-like wrapper depending on version)
            logger.exception("Process errored", exc_info=err)
            _reenable()

        @worker.finished.connect
        def _on_finished():
            _reenable()

        worker.start()
        return None  # important: do not block magicgui

    # force wrapper to present the same signature to magicgui
    threaded_process = custom_magicgui_hook(threaded_process)
    threaded_process.__signature__ = sig  # type: ignore[attr-defined]
    gui = magicgui.magicgui(threaded_process, call_button=True, auto_call=False, **threaded_process._magicgui)
    threaded_process._gui = gui  # inject reference so wrapper can disable the button

    viewer.window.add_dock_widget(gui, area="right")