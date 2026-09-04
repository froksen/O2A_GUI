# -*- coding: utf-8 -*-
# app_paths.py — Centrale filstier for brugerdata, og migrering fra den
# gamle placering (programmappen) til den nye (%APPDATA%\O2A).
#
# configuration.ini og personer(_ignorer).csv lå oprindeligt i selve
# programmappen. De er flyttet til %APPDATA%\O2A for at samle dem med
# events.json, aula_event_cache.json og logfilerne ét sted — og for at
# undgå at krypterede, personfølsomme filer ligger et sted der kan blive
# kopieret, delt eller lagt på et netværksdrev sammen med selve programmet.
#
# Ingen tredjeparts-afhængigheder her med vilje: launcher.pyw importerer
# dette modul, før venv'et overhovedet er sat op.
import os
import shutil

APPDATA_DIR = os.path.expandvars(r"%APPDATA%\O2A")
PROGRAM_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE            = os.path.join(APPDATA_DIR, "configuration.ini")
PEOPLE_CSV_FILE        = os.path.join(APPDATA_DIR, "personer.csv")
PEOPLE_IGNORE_CSV_FILE = os.path.join(APPDATA_DIR, "personer_ignorer.csv")


def migrate_legacy_file(filename: str, new_path: str) -> None:
    """Flytter en fil fra den gamle placering (programmappen) til den nye,
    hvis den nye endnu ikke findes. Kaldes ved hver indlæsning — no-op så
    snart filen er flyttet, så eksisterende brugere ikke mærker noget til
    flytningen."""
    if os.path.exists(new_path):
        return
    old_path = os.path.join(PROGRAM_DIR, filename)
    if not os.path.exists(old_path):
        return
    try:
        os.makedirs(os.path.dirname(new_path), exist_ok=True)
        shutil.move(old_path, new_path)
    except Exception:
        pass
