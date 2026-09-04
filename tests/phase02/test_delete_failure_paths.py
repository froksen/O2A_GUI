import logging
import datetime as dt
from types import SimpleNamespace

from aula.aula_calendar import AulaCalendar


class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.messages = []

    def emit(self, record):
        self.messages.append(record.getMessage())


def build_logger(name):
    logger = logging.getLogger(name)
    logger.handlers = []
    logger.setLevel(logging.INFO)
    logger.propagate = False
    handler = ListHandler()
    logger.addHandler(handler)
    return logger, handler


def test_delete_event_returns_false_without_nameerror_on_failure():
    logger, handler = build_logger("test.delete_event")

    calendar = AulaCalendar.__new__(AulaCalendar)
    calendar.logger = logger
    calendar._aula_api_url = "https://example.invalid/api"
    calendar._session = SimpleNamespace(
        post=lambda *_args, **_kwargs: SimpleNamespace(
            json=lambda: {"status": {"message": "ERROR"}}
        )
    )

    result = calendar.deleteEvent("event-1")

    assert result is False
    assert handler.messages == ["Begivenheden blev IKKE fjernet!"]


def test_delete_and_update_single_event_treat_false_as_failure(mainwindow_module, monkeypatch):
    """__delete_aula_events/__update_aula_events (bulk loops) blev i en
    senere refaktorering splittet op i per-begivenhed metoder
    (__delete_single_event/__update_single_event, kaldt fra
    __run_write_operations for hver begivenhed for sig) — denne test er
    opdateret til at kalde de nuværende metoder direkte."""
    import ui.event_store as event_store_module

    logger, handler = build_logger("test.delete_update_single")

    # __delete_single_event/__update_single_event skriver til den ægte,
    # delte EventStore (events.json på disk) — stubbes ud så testkørslen
    # ikke rører brugerens rigtige historik.
    appended = []
    monkeypatch.setattr(
        event_store_module.EventStore, "append",
        classmethod(lambda cls, *args, **kwargs: appended.append((args, kwargs))))

    target = SimpleNamespace(
        logger=logger,
        _dry_run=False,
        update_sync_step=lambda text: None,
    )

    aula_events = {
        "delete-id": {
            "appointmentitem": SimpleNamespace(
                subject="AULA event", aula_id="delete-1",
                start=dt.datetime(2026, 3, 18, 8, 0, 0)),
        },
        "update-id": {
            "appointmentitem": SimpleNamespace(subject="Outlook event", aula_id="update-1"),
            "outlook_LastModificationTime": "older",
        },
    }
    outlook_events = {
        "update-id": {
            "appointmentitem": SimpleNamespace(
                ReminderMinutesBeforeStart=5,
                start=dt.datetime(2026, 3, 18, 10, 0, 0),
                LastModificationTime=dt.datetime(2026, 3, 18, 9, 0, 0),
            )
        }
    }

    converted_event = SimpleNamespace(
        start_date_time="2026-03-18T08:00:00+01:00",
        outlook_last_modification_time="newer",
        creation_or_update_errors=SimpleNamespace(
            event_not_update_or_created=False,
            attendees_not_found=[],
        ),
    )

    class FakeCalendar:
        def deleteEvent(self, _aula_id):
            return False

        def convert_outlook_appointmentitem_to_aula_event(self, _event):
            return converted_event

        def get_atendees_ids(self, event):
            return event

        def updateEvent(self, _event):
            return False

    calendar = FakeCalendar()
    MainWindow = mainwindow_module.MainWindow

    delete_result = MainWindow._MainWindow__delete_single_event(
        target, calendar, "delete-id", aula_events, 1, 1)
    update_result = MainWindow._MainWindow__update_single_event(
        target, calendar, "update-id", outlook_events, aula_events,
        force_update=True, index=1, total=1)

    assert delete_result is not None
    assert delete_result.creation_or_update_errors.event_not_deleted is True
    assert update_result is converted_event
    assert converted_event.creation_or_update_errors.event_not_update_or_created is True

    assert "  STATUS: Fjernelse lykkedes" not in handler.messages
    assert "  STATUS: Opdatering lykkedes" not in handler.messages
    assert "  STATUS: Fjernelse mislykkedes" in handler.messages
    assert "  STATUS: Opdatering mislykkedes" in handler.messages
