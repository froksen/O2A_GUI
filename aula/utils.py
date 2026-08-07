"""Delte hjælpefunktioner til Aula-integrationen (URL-oprydning, dag-masker)."""

import itertools
import re
from pathlib import Path


def get_program_version() -> str | None:
    """Seneste git-commit-dato som versionsstreng, ellers fallback til version.txt."""
    base_dir = Path(__file__).resolve().parent.parent
    try:
        import git
        import datetime as dt

        repo = git.Repo(base_dir, search_parent_directories=True)
        commit_dt = dt.datetime.fromtimestamp(repo.head.commit.committed_date)
        return commit_dt.strftime("%d-%m-%Y %H:%M")
    except Exception:
        version_file = base_dir / "version.txt"
        if version_file.is_file():
            return version_file.read_text(encoding="utf-8").strip() or None
        return None

_TEAMS_MEETING_PATTERN = (
    r"Klik her for at deltage i mødet <https://teams\.microsoft\.com/l/meetup-join/.*"
)
_TEAMS_KNOW_MORE_PATTERN = r"Få mere at vide <https://aka\.ms/JoinTeamsMeeting"
_TEAMS_MEETING_OPTIONS_PATTERN = (
    r"Mødeindstillinger <https://teams\.microsoft\.com/meetingOptions.*"
)
_TEAMS_JOIN_LINK_PATTERN = r"https://teams\.microsoft\.com/l/meetup-join"
_URL_PATTERN = (
    r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
)


def teams_url_fixer(text):
    """Erstatter Teams-mødetekster fra Outlook med klikbare HTML-links."""
    teams_meeting = re.search(_TEAMS_MEETING_PATTERN, text)
    know_more = re.search(_TEAMS_KNOW_MORE_PATTERN, text)
    meeting_options = re.search(_TEAMS_MEETING_OPTIONS_PATTERN, text)

    if teams_meeting:
        url = re.search(_URL_PATTERN, teams_meeting.group(0)).group(0).replace(">", "")
        text = re.sub(
            _TEAMS_MEETING_PATTERN,
            f'<p><a href="{url}" target="_blank" rel="noopener">Klik her for at deltage i mødet</a></p>',
            text,
        )

    if know_more:
        url = re.search(_URL_PATTERN, know_more.group(0)).group(0).replace(">", "")
        text = re.sub(
            _TEAMS_KNOW_MORE_PATTERN,
            f'<a href="{url}" target="_blank" rel="noopener">Få mere at vide</a>',
            text,
        )

    if meeting_options:
        url = (
            re.search(_URL_PATTERN, meeting_options.group(0)).group(0).replace(">", "")
        )
        text = re.sub(
            _TEAMS_MEETING_OPTIONS_PATTERN,
            f'<a href="{url}" target="_blank" rel="noopener">Mødeindstillinger</a>',
            text,
        )

    return text


def url_fixer(text):
    """Fjerner < > omkring Teams-join-links og gør almindelige URL'er klikbare."""
    if re.search(_TEAMS_JOIN_LINK_PATTERN, text):
        text = text.replace("<", "").replace(">", "")

    for url in re.findall(_URL_PATTERN, text):
        text = re.sub(
            re.escape(url),
            f'<a href="{url}" target="_blank" rel="noopener">{url}</a>',
            text,
        )
    return text


# Outlook DayOfWeekMask-bitværdier (se olDaysOfWeek i Outlook-objektmodellen)
_OL_MONDAY = 2
_OL_TUESDAY = 4
_OL_WEDNESDAY = 8
_OL_THURSDAY = 16
_OL_FRIDAY = 32
_OL_SATURDAY = 64
_OL_SUNDAY = 1

_DAY_NAMES = {
    _OL_SUNDAY: "sunday",
    _OL_MONDAY: "monday",
    _OL_TUESDAY: "tuesday",
    _OL_WEDNESDAY: "wednesday",
    _OL_THURSDAY: "thursday",
    _OL_FRIDAY: "friday",
    _OL_SATURDAY: "saturday",
}


def calculate_day_of_the_week_mask():
    """Bygger alle kombinationer af ugedage med deres Outlook-bitsum.

    Bruges til at slå en DayOfWeekMask-sum op og finde de(n) tilhørende
    ugedag(e) — se get_day_of_the_week_mask i aula_calendar.py.
    """
    days_list = [
        _OL_MONDAY,
        _OL_TUESDAY,
        _OL_WEDNESDAY,
        _OL_THURSDAY,
        _OL_FRIDAY,
        _OL_SATURDAY,
        _OL_SUNDAY,
    ]

    data = []
    for size in range(len(days_list) + 1):
        for subset in itertools.combinations(days_list, size):
            data.append(
                {
                    "days_integer": subset,
                    "days_string": [_DAY_NAMES[day] for day in subset],
                    "sum": sum(subset),
                }
            )

    return data
