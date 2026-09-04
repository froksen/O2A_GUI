# -*- coding: utf-8 -*-
# secure_storage.py — Kryptering af lokalt gemte data (Windows DPAPI)
#
# Bruges til at kryptere personoplysninger, der ligger i almindelige
# tekstfiler (configuration.ini, personer.csv), så de ikke ligger i
# klartekst på disken. Krypteringsnøglen er bundet til den aktuelle
# Windows-brugers login (DPAPI) — der er ingen ekstra hemmelighed for
# brugeren at opbevare, og kun samme Windows-bruger på samme maskine
# kan dekryptere igen.
import base64
import logging

import win32crypt

logger = logging.getLogger('O2A')

# Præfiks der markerer en værdi som krypteret af denne modul, så en
# allerede-krypteret værdi kan skelnes fra en ældre klartekst-værdi
# uden at skulle forsøge at dekryptere den først.
_PREFIX = "dpapi1:"


def is_protected(value: str) -> bool:
    """True hvis værdien allerede er krypteret af protect()."""
    return bool(value) and value.startswith(_PREFIX)


def protect(value: str) -> str:
    """Krypterer en tekststreng til den aktuelle Windows-brugers DPAPI-nøgle.

    Tomme værdier krypteres ikke (der er intet at beskytte). Hvis
    kryptering fejler af en eller anden grund, logges det og værdien
    returneres ukrypteret, så programmet fortsat kan fungere frem for
    at crashe på at gemme en indstilling.
    """
    if not value:
        return value
    try:
        encrypted = win32crypt.CryptProtectData(
            value.encode("utf-8"), None, None, None, None, 0)
        return _PREFIX + base64.b64encode(encrypted).decode("ascii")
    except Exception as e:
        logger.warning("Kunne ikke kryptere lokale data (DPAPI): %s", e)
        return value


def unprotect(value: str) -> str:
    """Dekrypterer en værdi krypteret af protect().

    Værdier der ikke bærer protect()'s præfiks (fx data skrevet af en
    ældre version af programmet, før kryptering blev indført) betragtes
    som allerede klartekst og returneres uændret — det er den transparente
    migrering: næste gang værdien gemmes, bliver den krypteret.
    """
    if not is_protected(value):
        return value
    try:
        raw = base64.b64decode(value[len(_PREFIX):])
        _, decrypted = win32crypt.CryptUnprotectData(raw, None, None, None, 0)
        return decrypted.decode("utf-8")
    except Exception as e:
        logger.warning("Kunne ikke dekryptere gemte data — bruger rå værdi: %s", e)
        return value
