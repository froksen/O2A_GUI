# -*- coding: utf-8 -*-
# ui/konto_view.py — Konto (account) view
import tkinter as tk
from theme import BG, PANEL, LINE, TEXT, DIM, FAINT, SUBTLE, HARD, OK, ERR
from ui.widgets import PrimaryButton, SecondaryButton


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
            username = mgr.get_aula_username() if mgr.is_aula_configured() else "—"
            idp_id = mgr.get_aula_idp_id()
            idp_label = IDP_DISPLAY_NAMES.get(idp_id, "UniLogin (STIL)") if idp_id else "UniLogin (STIL)"
        except Exception:
            username = "—"
            idp_label = "—"

        tk.Label(body, text=username, bg=BG, fg=TEXT,
                 font=self._fonts["body_b"]).pack(anchor="w", pady=(0, 4))

        tk.Label(body, text=idp_label, bg=BG, fg=DIM,
                 font=self._fonts["small"]).pack(anchor="w", pady=(0, 16))

        btn_row = tk.Frame(body, bg=BG)
        btn_row.pack(anchor="w")

        PrimaryButton(btn_row, text="Konfigurer login",
                      command=self._open_unilogin,
                      fonts=self._fonts).pack(side="left")

        self._test_btn = SecondaryButton(btn_row, text="Test forbindelse",
                                         command=self._on_test_connection,
                                         fonts=self._fonts)
        self._test_btn.pack(side="left", padx=(8, 0))

        self._test_result_lbl = tk.Label(body, text="", bg=BG,
                                         font=self._fonts["small"])
        self._test_result_lbl.pack(anchor="w", pady=(10, 0))

    def _open_unilogin(self):
        from ui.dialogs.unilogin import UniloginDialog
        UniloginDialog(self.winfo_toplevel(), self._fonts).exec()

    def _on_test_connection(self):
        from setupmanager import SetupManager
        if not SetupManager().is_aula_configured():
            self._test_result_lbl.config(text="Konfigurer login, før du tester forbindelsen.", fg=DIM)
            return

        self._test_btn.config(state="disabled")
        self._test_result_lbl.config(text="Tester forbindelse …", fg=DIM)

        def _on_result(ok, login_status):
            self._test_btn.config(state="normal")
            if ok:
                self._test_result_lbl.config(text="Login virker ✓", fg=OK)
            else:
                self._test_result_lbl.config(text="Login mislykkedes — se detaljer", fg=ERR)
                from ui.dialogs.login_error import LoginErrorDialog
                LoginErrorDialog(
                    self.winfo_toplevel(), self._fonts,
                    on_fix_credentials=self._open_unilogin,
                    description="Det lykkedes ikke at logge ind på Aula med de gemte oplysninger.",
                )

        self._controller.test_connection(_on_result)
