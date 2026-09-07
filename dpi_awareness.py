# -*- coding: utf-8 -*-
# dpi_awareness.py — Gør processen DPI-bevidst på Windows, FØR noget
# tkinter-vindue oprettes. Uden dette skalerer Windows selve vinduet op som
# et bitmap på skærme med skaleringsfaktor over 100% (meget almindeligt på
# bærbare), hvilket gør tekst og widgets slørede — med DPI-awareness beder
# appen i stedet Windows om de rigtige pixelmål, og tegner selv skarpt.
#
# Skal kaldes tidligst muligt i hver proces der opretter et tk.Tk()-vindue
# (main.pyw og launcher.pyw er separate processer, så begge skal kalde den).
import ctypes


def enable():
    """Bedste tilgængelige DPI-awareness-niveau, ældste Windows-API sidst.
    Fejler stille hvis intet niveau er tilgængeligt (fx ikke-Windows) — det
    er kun en visuel forbedring, aldrig noget appen skal stoppe for."""
    try:
        # PROCESS_PER_MONITOR_DPI_AWARE — korrekt skalering selv når
        # vinduet flyttes mellem skærme med forskellig DPI (Windows 8.1+).
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return
    except Exception:
        pass
    try:
        # PROCESS_SYSTEM_DPI_AWARE — skarpt, men opdaterer ikke ved flytning
        # mellem skærme med forskellig DPI (Windows 8.1+).
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        return
    except Exception:
        pass
    try:
        # Ældste API (Windows Vista+) — bedre end ingenting.
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass
