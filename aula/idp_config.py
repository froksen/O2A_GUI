# -*- coding: utf-8 -*-
# aula/idp_config.py — Registrering af kendte lokale IDPer (UniLogin broker)
#
# Tilføj nye IDPer ved at indsætte et nyt dict i LOCAL_IDPS.
# 'id'           → selectedIdp-værdien der sendes til UniLogin-brokeren
# 'display_name' → Navn vist i brugergrænsefladen

LOCAL_IDPS = [
    {
        "id": "os2faktor-sonderborg",
        "display_name": "Sønderborg Kommune - Lærer",
    },
]

IDP_DISPLAY_NAMES = {idp["id"]: idp["display_name"] for idp in LOCAL_IDPS}


def get_idp_by_id(idp_id: str) -> dict | None:
    for idp in LOCAL_IDPS:
        if idp["id"] == idp_id:
            return idp
    return None
