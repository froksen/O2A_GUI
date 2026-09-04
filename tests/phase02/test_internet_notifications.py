import logging
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


def test_notify_internet_connection_error_logs_every_time_and_sets_flag(mainwindow_module):
    """_notify_internet_connection_error har ikke længere sit eget
    tray-kald (tray-integrationen sker nu via show_toast/on_tray_text_updated,
    tilkoblet udefra af main.pyw) — den logger fejlen og sætter
    _internet_error_tray_announced, som andre dele af programmet kan læse.
    Testen dækker derfor det, metoden rent faktisk gør i dag."""
    logger, handler = build_logger("test.internet.notify")
    target = SimpleNamespace(logger=logger, _internet_error_tray_announced=False)

    mainwindow_module.MainWindow._notify_internet_connection_error(target)
    mainwindow_module.MainWindow._notify_internet_connection_error(target)

    assert handler.messages == [
        mainwindow_module.INTERNET_ERROR_MESSAGE,
        mainwindow_module.INTERNET_ERROR_MESSAGE,
    ]
    assert target._internet_error_tray_announced is True


def test_run_sync_resets_tray_flag_on_success(mainwindow_module):
    """En vellykket synkronisering nulstiller _internet_error_tray_announced
    (mainwindow.py, _run_sync) — svarer til den gamle
    _reset_internet_error_notifications/_handle_sync_result, som ikke
    findes som separate metoder længere; logikken sidder i dag direkte i
    _run_sync."""
    logger, _handler = build_logger("test.internet.reset")
    calls = []
    target = SimpleNamespace(
        logger=logger,
        _stop_requested=None,
        _internet_error_tray_announced=True,
        update_calendar=lambda force_update: True,
        toggle_gui=lambda enabled: calls.append(("toggle_gui", enabled)),
        _clear_sync_step=lambda: calls.append(("clear_sync_step",)),
        root=SimpleNamespace(after=lambda _delay, fn: fn()),
    )

    mainwindow_module.MainWindow._run_sync(target, False)

    assert target._internet_error_tray_announced is False
    assert ("clear_sync_step",) in calls


def test_both_sync_buttons_notify_and_stop_without_internet(mainwindow_module):
    calls = []
    target = SimpleNamespace(
        _sync_in_progress=False,
        _dry_run=False,
        _stop_requested=None,
        has_internet_connection=lambda: False,
        _notify_internet_connection_error=lambda: calls.append("notified"),
    )

    mainwindow_module.MainWindow.on_runO2A_clicked(target)
    mainwindow_module.MainWindow.on_forcerunO2A_clicked(target)

    assert calls == ["notified", "notified"]
