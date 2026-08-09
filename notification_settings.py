# notification_settings.py — Read/write notification preferences from configuration.ini
import configparser

EVENTS = [
    ("on_create_error",     "Begivenhed ikke oprettet"),
    ("on_update_error",     "Begivenhed ikke opdateret"),
    ("on_delete_error",     "Begivenhed ikke slettet"),
    ("on_person_not_found", "Person ikke fundet"),
    ("on_critical_error",   "Kritisk programfejl"),
    ("on_sync_summary",     "Sammendrag efter kørsel"),
]

METHODS = [
    ("email", "E-mail"),
    ("toast", "Toast"),
    ("none",  "Ingen"),
]

_SECTION     = "NOTIFICATIONS"
_CONFIG_FILE = "configuration.ini"

# Fejl-relaterede nøgler er slået til (e-mail) som standard, så en bruger
# ikke går glip af en fejl uden selv at have valgt det til. "Sammendrag
# efter kørsel" er derimod ekstra støj for de fleste — den skal aktivt
# vælges til.
_DEFAULT_METHODS = {
    "on_sync_summary": "none",
}


class NotificationSettings:
    """Stores a set of active methods per event key.

    Stored in configuration.ini as comma-separated values, e.g.
    ``on_create_error = email,toast``.  An empty set is stored as ``none``.
    Default for all keys is ``{'email'}``, except keys listed in
    ``_DEFAULT_METHODS`` above.
    """

    def __init__(self):
        self._cfg = configparser.ConfigParser()
        self._cfg.read(_CONFIG_FILE)
        if not self._cfg.has_section(_SECTION):
            self._cfg.add_section(_SECTION)

    def get(self, event_key: str) -> set:
        default = _DEFAULT_METHODS.get(event_key, "email")
        raw = self._cfg.get(_SECTION, event_key, fallback=default)
        if raw == "none" or not raw.strip():
            return set()
        return {m.strip() for m in raw.split(",")
                if m.strip() in ("email", "toast")}

    def set(self, event_key: str, methods: set):
        if not self._cfg.has_section(_SECTION):
            self._cfg.add_section(_SECTION)
        value = ",".join(sorted(methods)) if methods else "none"
        self._cfg.set(_SECTION, event_key, value)
        with open(_CONFIG_FILE, "w") as f:
            self._cfg.write(f)
