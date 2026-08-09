# -*- coding: utf-8 -*-
# ui/opstartsadfaerd_view.py — Opstartsadfærd (startup behaviour) view
import tkinter as tk
from theme import BG, LINE, TEXT, DIM, PANEL


class OpstartsadfaerdView(tk.Frame):
    """Startup behaviour: run at Windows startup, open minimized."""

    def __init__(self, parent, controller, fonts):
        super().__init__(parent, bg=BG)
        self._controller = controller
        self._fonts = fonts
        self._build()

    def _build(self):
        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=40, pady=(28, 20))

        tk.Label(hdr, text="OPSTARTSADFÆRD", bg=BG, fg=DIM,
                 font=self._fonts["eyebrow"]).pack(anchor="w")
        tk.Label(hdr, text="Opstartsadfærd", bg=BG, fg=TEXT,
                 font=self._fonts["display_m"]).pack(anchor="w", pady=(4, 0))

        tk.Frame(self, bg=LINE, height=1).pack(fill="x", padx=40)

        # ── Body ──────────────────────────────────────────────────────────────
        body = tk.Frame(self, bg=BG)
        body.pack(fill="x", padx=40, pady=20)

        tk.Checkbutton(
            body,
            text="Åben programmet i baggrunden",
            variable=self._controller._start_minimized_var,
            command=self._controller.update_hide_on_startup_clicked,
            bg=BG, fg=TEXT,
            activebackground=BG,
            selectcolor=PANEL,
            font=self._fonts["body"],
        ).pack(anchor="w", pady=(0, 4))

        tk.Checkbutton(
            body,
            text="Start Outlook2Aula automatisk",
            variable=self._controller._run_at_startup_var,
            command=self._controller.on_run_program_at_startup_clicked,
            bg=BG, fg=TEXT,
            activebackground=BG,
            selectcolor=PANEL,
            font=self._fonts["body"],
        ).pack(anchor="w")
