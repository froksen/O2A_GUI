# -*- coding: utf-8 -*-
# ui/konto_view.py — Konto (account) view
import tkinter as tk
from theme import BG, PANEL, LINE, TEXT, DIM, FAINT, ACCENT, SUBTLE, HARD


class KontoView(tk.Frame):
    """Shows the currently configured Aula account and allows reconfiguration."""

    def __init__(self, parent, controller, fonts):
        super().__init__(parent, bg=BG)
        self._controller = controller
        self._fonts = fonts
        self._build()

    def _build(self):
        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=40, pady=(28, 20))

        tk.Label(hdr, text="KONTO", bg=BG, fg=DIM,
                 font=self._fonts["eyebrow"]).pack(anchor="w")
        tk.Label(hdr, text="Konto", bg=BG, fg=TEXT,
                 font=self._fonts["display_m"]).pack(anchor="w", pady=(4, 0))

        tk.Frame(self, bg=LINE, height=1).pack(fill="x", padx=40)

        # ── Body ──────────────────────────────────────────────────────────────
        body = tk.Frame(self, bg=BG)
        body.pack(fill="x", padx=40, pady=20)

        tk.Label(body, text="Nuværende bruger", bg=BG, fg=DIM,
                 font=self._fonts["small"]).pack(anchor="w", pady=(0, 4))

        # Hent brugeroplysninger
        try:
            from setupmanager import SetupManager
            from aula.idp_config import IDP_DISPLAY_NAMES
            mgr = SetupManager()
            username = mgr.get_aula_username() or "—"
            idp_id = mgr.get_aula_idp_id()
            idp_label = IDP_DISPLAY_NAMES.get(idp_id, "UniLogin (STIL)") if idp_id else "UniLogin (STIL)"
        except Exception:
            username = "—"
            idp_label = "—"

        tk.Label(body, text=username, bg=BG, fg=TEXT,
                 font=self._fonts["body_b"]).pack(anchor="w", pady=(0, 4))

        tk.Label(body, text=idp_label, bg=BG, fg=DIM,
                 font=self._fonts["small"]).pack(anchor="w", pady=(0, 16))

        tk.Button(body, text="Konfigurer login",
                  command=self._open_unilogin,
                  bg=ACCENT, fg="white",
                  activebackground="#325039", activeforeground="white",
                  font=self._fonts["body"],
                  relief="flat", borderwidth=0,
                  padx=14, pady=6, cursor="hand2"
                  ).pack(anchor="w")

    def _open_unilogin(self):
        from ui.dialogs.unilogin import UniloginDialog
        UniloginDialog(self.winfo_toplevel(), self._fonts).exec()
