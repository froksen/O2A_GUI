import logging
import tkinter as tk
from types import SimpleNamespace


class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.messages = []

    def emit(self, record):
        self.messages.append(record.getMessage())


def build_logger(name):
    logger = logging.getLogger(name)
    logger.handlers = []
    logger.setLevel(logging.CRITICAL)
    logger.propagate = False
    handler = ListHandler()
    logger.addHandler(handler)
    return logger, handler


def test_mainwindow_init_sets_logger_before_setup(main_module, monkeypatch):
    """MainWindow.__init__ must set self.logger before it runs any of the
    setup steps that might log — otherwise those steps would crash on a
    missing logger."""
    calls = []

    for hook in ("_setup_window", "_build_ui", "initial_o2a_check", "_start_timers"):
        monkeypatch.setattr(
            main_module.MainWindow,
            hook,
            lambda self, _hook=hook: calls.append((_hook, self.logger.name)),
        )

    root = tk.Tk()
    root.withdraw()
    try:
        main_module.MainWindow(root)
    finally:
        root.destroy()

    assert calls == [
        ("_setup_window", "O2A"),
        ("_build_ui", "O2A"),
        ("initial_o2a_check", "O2A"),
        ("_start_timers", "O2A"),
    ]


def test_internet_notification_logs_every_call(main_module):
    logger, handler = build_logger("test.internet.notify")
    target = SimpleNamespace(logger=logger, _internet_error_tray_announced=False)

    main_module.MainWindow._notify_internet_connection_error(target)
    main_module.MainWindow._notify_internet_connection_error(target)

    assert handler.messages == [
        main_module.INTERNET_ERROR_MESSAGE,
        main_module.INTERNET_ERROR_MESSAGE,
    ]
    assert target._internet_error_tray_announced is True


def test_both_sync_buttons_use_central_notification_helper(main_module):
    calls = []
    target = SimpleNamespace(
        _dry_run=False,
        has_internet_connection=lambda: False,
        _notify_internet_connection_error=lambda: calls.append("notified"),
    )

    main_module.MainWindow.on_runO2A_clicked(target)
    main_module.MainWindow.on_forcerunO2A_clicked(target)

    assert calls == ["notified", "notified"]
