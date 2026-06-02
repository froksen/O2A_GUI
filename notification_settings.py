# notification_settings.py — Read/write notification preferences from configuration.ini
import configparser
import os

EVENTS = [
    ("on_create_error",     "Begivenhed ikke oprettet"),
    ("on_update_error",     "Begivenhed ikke opdateret"),
    ("on_delete_error",     "Begivenhed ikke slettet"),
    ("on_person_not_found", "Person ikke fundet"),
]

METHODS = [
    ("email", "E-mail"),
    ("toast", "Toast"),
    ("none",  "Ingen"),
]

_SECTION      = "NOTIFICATIONS"
_CONFIG_FILE  = "configuration.ini"
_DEFAULT      = "email"


class NotificationSettings:
    def __init__(self):
        self._cfg = configparser.ConfigParser()
        self._cfg.read(_CONFIG_FILE)
        if not self._cfg.has_section(_SECTION):
            self._cfg.add_section(_SECTION)

    def get(self, event_key: str) -> str:
        return self._cfg.get(_SECTION, event_key, fallback=_DEFAULT)

    def set(self, event_key: str, method: str):
        if not self._cfg.has_section(_SECTION):
            self._cfg.add_section(_SECTION)
        self._cfg.set(_SECTION, event_key, method)
        with open(_CONFIG_FILE, "w") as f:
            self._cfg.write(f)
