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


# ── Loginmetode-valg til UI'ens IDP-vælgere (unilogin-dialog og opsætningsguide) ──
UNILOGIN_OPTION = ("UniLogin (STIL)", "")          # (visningsnavn, idp_id)
IDP_OPTIONS = [UNILOGIN_OPTION] + [
    (idp["display_name"], idp["id"]) for idp in LOCAL_IDPS
]
IDP_DISPLAY_LABELS = [opt[0] for opt in IDP_OPTIONS]


def idp_id_to_display(idp_id: str) -> str:
    for display, value in IDP_OPTIONS:
        if value == idp_id:
            return display
    return UNILOGIN_OPTION[0]


def display_to_idp_id(display: str) -> str:
    for disp, value in IDP_OPTIONS:
        if disp == display:
            return value
    return ""
