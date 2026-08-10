# -*- coding: utf-8 -*-
# aula/aula_event_cache.py — Persistent, lokal cache af AULA-begivenheders
# vandmærke (Outlook GlobalAppointmentID + LastModificationTime) og øvrige
# felter, så en synk ikke behøver hente fulde detaljer for hver eneste
# begivenhed hver eneste kørsel — det var det, der fik en normal kørsel til
# at tage op mod 8 timer.
#
# PÅLIDELIGHED FREM FOR HASTIGHED:
# Cachen bruges KUN til at undgå at genhente detaljer for begivenheder der
# allerede kendes. Den bruges ALDRIG til at afgøre om en begivenhed stadig
# findes i Aula — det tjekkes hver eneste kørsel mod en frisk liste fra Aula
# (se AulaCalendar.getEvents/getEventsByProfileIdsAndResourceIds). En
# begivenhed der er slettet i Aula siden sidst, forsvinder derfor korrekt fra
# synkroniseringen uanset hvad der (endnu) står i cachen — og fjernes samtidig
# fra selve cachen (prune_to). Vandmærket i en begivenhed O2A selv har
# oprettet ændrer sig kun når O2A selv skriver til den, så det er trygt at
# genbruge så længe begivenheden stadig findes.
import json
import os


class AulaEventCache:
    """Singleton, samme mønster som ui/event_store.py — gemt i
    %APPDATA%\\O2A, altså kun tilgængeligt for den Windows-bruger der er
    logget ind (samme sted som events.json og logfilerne), aldrig i selve
    programmappen."""

    _path: str = os.path.expandvars(r"%APPDATA%\O2A\aula_event_cache.json")
    _VERSION = 1
    _entries: dict | None = None  # {str(aula_event_id): {title, start, end, location, global_id, lmt}}

    # ── Internal helpers ──────────────────────────────────────────────────────

    @classmethod
    def _load(cls):
        if cls._entries is not None:
            return
        try:
            with open(cls._path, encoding="utf-8") as f:
                data = json.load(f)
            cls._entries = data.get("entries", {}) if data.get("version") == cls._VERSION else {}
        except Exception:
            cls._entries = {}

    @classmethod
    def _save(cls):
        try:
            os.makedirs(os.path.dirname(cls._path), exist_ok=True)
            with open(cls._path, "w", encoding="utf-8") as f:
                json.dump({"version": cls._VERSION, "entries": cls._entries}, f, ensure_ascii=False)
        except Exception:
            pass  # cachen er et hastighedstiltag — en skrivefejl her må aldrig vælte en synk

    # ── Public API ────────────────────────────────────────────────────────────

    @classmethod
    def get(cls, event_id) -> dict | None:
        cls._load()
        return cls._entries.get(str(event_id))

    @classmethod
    def put(cls, event_id, entry: dict):
        cls._load()
        cls._entries[str(event_id)] = entry
        cls._save()

    @classmethod
    def prune_to(cls, valid_event_ids) -> int:
        """Fjerner cache-poster for begivenheder der ikke længere findes i
        Aula (fx slettet siden sidst) — kaldes efter hver synk med den
        friske liste af begivenheds-id'er fra Aula. Returnerer antal fjernede
        poster."""
        cls._load()
        valid = {str(i) for i in valid_event_ids}
        stale = [k for k in cls._entries if k not in valid]
        for k in stale:
            del cls._entries[k]
        if stale:
            cls._save()
        return len(stale)

    @classmethod
    def count(cls) -> int:
        cls._load()
        return len(cls._entries)

    @classmethod
    def clear(cls):
        """Tømmer hele cachen. Brugt af 'Tving fuld synkronisering' og af
        'Ryd cache'-knappen på Avanceret-siden, hvis brugeren har mistanke
        om at noget er forkert — den simple, altid-troværdige løsning er at
        starte cachen helt forfra."""
        cls._entries = {}
        cls._save()
