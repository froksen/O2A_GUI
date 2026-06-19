# -*- coding: utf-8 -*-
# ui/event_store.py — Persistent event history (max 7 days)
import json
import os
from datetime import datetime, timedelta


class EventStore:
    """
    Singleton: every sync action (oprettet/opdateret/fjernet) since startup,
    plus up to 7 days of prior history loaded from disk.
    """
    _path: str = os.path.expandvars(r"%APPDATA%\O2A\events.json")
    _records: list | None = None
    _subscribers: list = []

    # ── Internal helpers ──────────────────────────────────────────────────────

    @classmethod
    def _load(cls):
        if cls._records is None:
            try:
                with open(cls._path, encoding="utf-8") as f:
                    cls._records = json.load(f)
            except Exception:
                cls._records = []
            cls._prune()

    @classmethod
    def _save(cls):
        try:
            os.makedirs(os.path.dirname(cls._path), exist_ok=True)
            with open(cls._path, "w", encoding="utf-8") as f:
                json.dump(cls._records, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    @classmethod
    def _prune(cls):
        """Remove entries older than 7 days."""
        cutoff = (datetime.now() - timedelta(days=7)).isoformat()
        cls._records = [r for r in cls._records if r.get("timestamp", "") >= cutoff]

    # ── Public API ────────────────────────────────────────────────────────────

    @classmethod
    def append(cls, action: str, title: str, start_date: str,
               error: bool = False, volatile: bool = False,
               error_detail: str | None = None,
               log_snippet: str | None = None):
        """
        Record a sync action.
        action: "oprettet" | "opdateret" | "fjernet"
        volatile: if True, the record is kept in memory only (not saved to disk).
        error_detail: short human-readable error description shown in the event feed.
        log_snippet: relevant log lines captured during the operation.
        """
        cls._load()
        record = {
            "action":     action,
            "title":      str(title),
            "start_date": str(start_date),
            "timestamp":  datetime.now().isoformat(),
            "error":      error,
        }
        if error_detail:
            record["error_detail"] = error_detail
        if log_snippet:
            record["log_snippet"] = log_snippet
        if volatile:
            record["demo"] = True
        cls._records.append(record)
        cls._prune()
        if not volatile:
            cls._save()
        for cb in list(cls._subscribers):
            try:
                cb(record)
            except Exception:
                pass

    @classmethod
    def all(cls) -> list:
        """Return all records (excluding volatile demo entries), newest first."""
        cls._load()
        return list(reversed([r for r in cls._records if not r.get("demo")]))

    @classmethod
    def subscribe(cls, cb):
        """Register a callback invoked with the new record dict on each append."""
        cls._load()
        cls._subscribers.append(cb)
