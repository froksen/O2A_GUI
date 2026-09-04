# -*- coding: utf-8 -*-
# ui/event_store.py — Persistent event history (max 7 days)
import json
import os
from datetime import datetime, timedelta

from secure_storage import protect, unprotect, is_protected


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
            cls._records = []
            try:
                with open(cls._path, encoding="utf-8") as f:
                    stored = f.read()
                if is_protected(stored):
                    cls._records = json.loads(unprotect(stored))
                # En ukrypteret fil (skrevet af en ældre version, før
                # kryptering blev indført) droppes bevidst i stedet for at
                # migreres — historikken er kun en 7-dages log, så det er
                # uden reel betydning, og filen krypteres fra næste _save().
            except Exception:
                cls._records = []
            cls._prune()

    @classmethod
    def _save(cls):
        try:
            os.makedirs(os.path.dirname(cls._path), exist_ok=True)
            payload = json.dumps(cls._records, ensure_ascii=False, indent=2)
            with open(cls._path, "w", encoding="utf-8") as f:
                f.write(protect(payload))
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
    def stats(cls) -> dict:
        """Aggregated counts across the retained history (last 7 days):
        successful oprettet/opdateret/fjernet, plus total errors."""
        cls._load()
        records = [r for r in cls._records if not r.get("demo")]
        return {
            "created": sum(1 for r in records if r["action"] == "oprettet" and not r.get("error")),
            "updated": sum(1 for r in records if r["action"] == "opdateret" and not r.get("error")),
            "deleted": sum(1 for r in records if r["action"] == "fjernet" and not r.get("error")),
            "errors":  sum(1 for r in records if r.get("error")),
        }

    @classmethod
    def subscribe(cls, cb):
        """Register a callback invoked with the new record dict on each append."""
        cls._load()
        cls._subscribers.append(cb)
