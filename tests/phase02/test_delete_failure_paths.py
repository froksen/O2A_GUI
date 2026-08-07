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


def test_delete_and_update_callers_treat_false_as_failure(main_module):
    logger, handler = build_logger("test.delete_update_callers")
    target = SimpleNamespace(logger=logger)

    aula_events = {
        "delete-id": {
            "appointmentitem": SimpleNamespace(
                subject="AULA event", aula_id="delete-1"
            ),
        },
        "update-id": {
            "appointmentitem": SimpleNamespace(
                subject="Outlook event", aula_id="update-1"
            ),
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
        def deleteEvent(self, _event_id):
            return False

        def convert_outlook_appointmentitem_to_aula_event(self, _event):
            return converted_event

        def get_atendees_ids(self, event):
            return event

        def updateEvent(self, _event):
            return False

    calendar = FakeCalendar()

    main_module.MainWindow._MainWindow__delete_aula_events(
        target,
        aula_calendar=calendar,
        event_ids_to_delete=["delete-id"],
        aula_events=aula_events,
    )
    errors = main_module.MainWindow._MainWindow__update_aula_events(
        target,
        aula_calendar=calendar,
        identical_events_id=["update-id"],
        outlook_events=outlook_events,
        aula_events=aula_events,
        force_update=True,
    )

    assert errors == [converted_event]
    assert "  STATUS: Fjernelse lykkedes" not in handler.messages
    assert "  STATUS: Opdatering lykkedes" not in handler.messages
    assert "  STATUS: Fjernelse mislykkedes" in handler.messages
    assert "  STATUS: Opdatering mislykkedes" in handler.messages
