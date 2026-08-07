import logging
from types import SimpleNamespace


class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.messages = []

    def emit(self, record):
        self.messages.append(record.getMessage())


def build_notification_target(logger):
    target = SimpleNamespace(
        logger=logger,
        _internet_error_channels=("gui", "tray"),
        _internet_error_tray_announced=False,
    )
    return target


def test_mainwindow_init_sets_logger_before_setup_gui(main_module, monkeypatch, qapp):
    def fake_setup_ui(self, _window):
        self.runFrequency = SimpleNamespace(value=lambda: 1)

    def fake_setup_gui(self):
        assert self.logger.name == "O2A"

    monkeypatch.setattr(main_module.MainWindow, "setupUi", fake_setup_ui)
    monkeypatch.setattr(main_module.MainWindow, "setup_gui", fake_setup_gui)
    monkeypatch.setattr(
        main_module.MainWindow, "initialize_run_frequency_timer", lambda self: None
    )
    monkeypatch.setattr(
        main_module.MainWindow, "initialize_countdown_timer", lambda self: None
    )
    monkeypatch.setattr(main_module.MainWindow, "initial_o2a_check", lambda self: None)

    window = main_module.MainWindow()
    window.close()


def test_internet_notification_logs_every_time_but_tray_only_once(
    main_module, monkeypatch, tray_spy
):
    logger = logging.getLogger("test.internet.notify")
    logger.handlers = []
    logger.setLevel(logging.CRITICAL)
    logger.propagate = False
    handler = ListHandler()
    logger.addHandler(handler)

    target = build_notification_target(logger)
    monkeypatch.setattr(main_module, "get_tray_icon", lambda: tray_spy)

    main_module.MainWindow._notify_internet_connection_error(target)
    main_module.MainWindow._notify_internet_connection_error(target)

    assert handler.messages == [
        main_module.INTERNET_ERROR_MESSAGE,
        main_module.INTERNET_ERROR_MESSAGE,
    ]
    assert tray_spy.messages == [
        (main_module.INTERNET_ERROR_TITLE, main_module.INTERNET_ERROR_MESSAGE),
    ]


def test_success_resets_tray_throttle(main_module, monkeypatch, tray_spy):
    logger = logging.getLogger("test.internet.reset")
    logger.handlers = []
    logger.setLevel(logging.CRITICAL)
    logger.propagate = False
    logger.addHandler(ListHandler())

    target = build_notification_target(logger)
    target._reset_internet_error_notifications = lambda: (
        main_module.MainWindow._reset_internet_error_notifications(target)
    )
    monkeypatch.setattr(main_module, "get_tray_icon", lambda: tray_spy)

    main_module.MainWindow._notify_internet_connection_error(target)
    main_module.MainWindow._handle_sync_result(target, True)
    main_module.MainWindow._notify_internet_connection_error(target)

    assert tray_spy.messages == [
        (main_module.INTERNET_ERROR_TITLE, main_module.INTERNET_ERROR_MESSAGE),
        (main_module.INTERNET_ERROR_TITLE, main_module.INTERNET_ERROR_MESSAGE),
    ]


def test_both_sync_buttons_use_central_notification_helper(main_module):
    calls = []
    target = SimpleNamespace(
        has_internet_connection=lambda: False,
        _notify_internet_connection_error=lambda: calls.append("notified"),
    )

    main_module.MainWindow.on_runO2A_clicked(target)
    main_module.MainWindow.on_forcerunO2A_clicked(target)

    assert calls == ["notified", "notified"]
