"""Midlertidige miljøfejl (netværk/DNS og Outlook der ikke svarer via COM)
skal håndteres venligt — ikke som kritiske programfejl med fejlmail."""
import logging
from types import SimpleNamespace

import pytest
import requests


# ── Outlook: connect_outlook ────────────────────────────────────────────────

class _FakeOutlook:
    def __init__(self, fail):
        self._fail = fail

    def GetNamespace(self, name):
        if self._fail:
            raise AttributeError("Outlook.Application.GetNamespace")
        return "MAPI-NS"


def test_connect_outlook_retries_then_succeeds(monkeypatch):
    import outlookmanager
    results = iter([True, True, False])  # fejler to gange, lykkes tredje gang
    monkeypatch.setattr(outlookmanager.win32com.client, "Dispatch",
                        lambda _name: _FakeOutlook(next(results)))
    sleeps = []
    monkeypatch.setattr(outlookmanager.time, "sleep", sleeps.append)

    outlook, ns = outlookmanager.connect_outlook(attempts=4, first_delay=2.0)

    assert ns == "MAPI-NS"
    assert sleeps == [2.0, 4.0]


def test_connect_outlook_raises_unavailable_after_last_attempt(monkeypatch):
    import outlookmanager
    monkeypatch.setattr(outlookmanager.win32com.client, "Dispatch",
                        lambda _name: _FakeOutlook(True))
    monkeypatch.setattr(outlookmanager.time, "sleep", lambda _s: None)

    with pytest.raises(outlookmanager.OutlookUnavailableError) as exc_info:
        outlookmanager.connect_outlook(attempts=3)

    assert isinstance(exc_info.value.__cause__, AttributeError)


# ── Aula: login ved netværksfejl ────────────────────────────────────────────

def test_login_marks_dns_failure_as_network_error(monkeypatch):
    from aula.aula_connection import AulaConnection

    def _fail(*_args, **_kwargs):
        req = requests.Request("POST", "https://adgang-idp.sonderborg.dk/sso/saml/login").prepare()
        raise requests.exceptions.ConnectionError("Failed to resolve", request=req)

    conn = AulaConnection()
    monkeypatch.setattr(conn.session, "get", _fail)

    status = conn.login("bruger", "kode", idp_id="some_idp")

    assert status.status is False
    assert status.network_error is True
    assert status.error_messages == ["Ingen forbindelse til adgang-idp.sonderborg.dk"]


# ── MainWindow._run_sync ────────────────────────────────────────────────────

def _sync_target(update_calendar, calls):
    logger = logging.getLogger("test.environment_errors")
    logger.handlers = []
    logger.propagate = False
    return SimpleNamespace(
        logger=logger,
        _stop_requested=None,
        _internet_error_tray_announced=False,
        _outlook_error_announced=False,
        update_calendar=update_calendar,
        toggle_gui=lambda enabled: None,
        _clear_sync_step=lambda: None,
        root=SimpleNamespace(after=lambda _delay, fn: fn()),
        _dispatch_critical_error_notification=lambda tb: calls.append("critical"),
        _notify_outlook_unavailable=lambda e: calls.append("outlook"),
        _notify_internet_connection_error=lambda: calls.append("internet"),
    )


def test_run_sync_outlook_unavailable_is_not_critical(mainwindow_module):
    from outlookmanager import OutlookUnavailableError
    calls = []

    def _raise(_force):
        raise OutlookUnavailableError("Outlook svarer ikke")

    mainwindow_module.MainWindow._run_sync(_sync_target(_raise, calls), False)

    assert calls == ["outlook"]


def test_run_sync_network_error_is_not_critical(mainwindow_module):
    calls = []

    def _raise(_force):
        raise requests.exceptions.ConnectionError("Failed to resolve")

    mainwindow_module.MainWindow._run_sync(_sync_target(_raise, calls), False)

    assert calls == ["internet"]


def test_run_sync_unexpected_error_still_critical(mainwindow_module):
    calls = []

    def _raise(_force):
        raise ValueError("programfejl")

    mainwindow_module.MainWindow._run_sync(_sync_target(_raise, calls), False)

    assert calls == ["critical"]


def test_notify_outlook_unavailable_toasts_only_once(mainwindow_module, monkeypatch):
    import notification_settings
    monkeypatch.setattr(notification_settings.NotificationSettings, "get",
                        lambda self, key: {"toast", "email"})
    toasts = []
    logger = logging.getLogger("test.environment_errors.toast")
    logger.handlers = []
    logger.propagate = False
    target = SimpleNamespace(logger=logger, _outlook_error_announced=False,
                             show_toast=lambda title, msg: toasts.append(title))

    mainwindow_module.MainWindow._notify_outlook_unavailable(target, Exception("x"))
    mainwindow_module.MainWindow._notify_outlook_unavailable(target, Exception("x"))

    assert len(toasts) == 1
