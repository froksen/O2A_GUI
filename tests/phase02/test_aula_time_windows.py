import datetime as dt
import logging

from aula.aula_calendar import AulaCalendar


def build_calendar():
    calendar = AulaCalendar.__new__(AulaCalendar)
    calendar.logger = logging.getLogger("test.aula_calendar")
    calendar._profile_id = 1
    calendar._profile_institution_code = 2
    return calendar


def test_lookup_formatter_covers_2026_dst_boundaries():
    calendar = build_calendar()

    assert (
        calendar._format_lookup_datetime(dt.datetime(2026, 3, 28, 12, 0, 0))
        == "2026-03-28T12:00:00+01:00"
    )
    assert (
        calendar._format_lookup_datetime(dt.datetime(2026, 3, 29, 12, 0, 0))
        == "2026-03-29T12:00:00+02:00"
    )
    assert (
        calendar._format_lookup_datetime(dt.datetime(2026, 7, 15, 12, 0, 0))
        == "2026-07-15T12:00:00+02:00"
    )
    assert (
        calendar._format_lookup_datetime(dt.datetime(2026, 10, 25, 12, 0, 0))
        == "2026-10-25T12:00:00+01:00"
    )


def test_getevents_uses_dynamic_offsets_per_lookup_window(monkeypatch):
    calendar = build_calendar()
    captured_windows = []

    def capture_institution(profile_id, institution_code, start_text, end_text):
        captured_windows.append((start_text, end_text))
        return []

    monkeypatch.setattr(calendar, "getEventsForInstitutions", capture_institution)
    monkeypatch.setattr(
        calendar, "getEventsByProfileIdsAndResourceIds", lambda *args: []
    )
    monkeypatch.setattr("aula.aula_calendar.time.sleep", lambda *_args: None)

    calendar.getEvents(
        startDatetime=dt.datetime(2026, 3, 29, 12, 0, 0),
        endDatetime=dt.datetime(2026, 10, 25, 12, 0, 0),
    )

    assert captured_windows[0] == (
        "2026-03-29T12:00:00+02:00",
        "2026-04-29T12:00:00+02:00",
    )
    assert captured_windows[-1] == (
        "2026-09-29T12:00:00+02:00",
        "2026-10-25T12:00:00+01:00",
    )
