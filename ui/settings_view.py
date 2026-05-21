# -*- coding: utf-8 -*-
# ui/settings_view.py — Indstillinger (settings) view
import tkinter as tk
from theme import BG, LINE, TEXT, DIM, PANEL, SUBTLE, ACCENT


class SettingsView(tk.Frame):
    """Application settings: startup behaviour and sync frequency."""

    def __init__(self, parent, controller, fonts):
        super().__init__(parent, bg=BG)
        self._controller = controller
        self._fonts = fonts
        self._build()

    def _build(self):
        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=40, pady=(28, 20))

        tk.Label(hdr, text="INDSTILLINGER", bg=BG, fg=DIM,
                 font=self._fonts["eyebrow"]).pack(anchor="w")
        tk.Label(hdr, text="Indstillinger", bg=BG, fg=TEXT,
                 font=self._fonts["display_m"]).pack(anchor="w", pady=(4, 0))

        tk.Frame(self, bg=LINE, height=1).pack(fill="x", padx=40)

        # ── Body ──────────────────────────────────────────────────────────────
        body = tk.Frame(self, bg=BG)
        body.pack(fill="x", padx=40, pady=20)

        # Startup behaviour
        tk.Label(body, text="Opstartsadfærd", bg=BG, fg=DIM,
                 font=self._fonts["eyebrow"]).pack(anchor="w", pady=(0, 8))

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
        ).pack(anchor="w", pady=(0, 16))

        # Sync frequency
        tk.Frame(body, bg=LINE, height=1).pack(fill="x", pady=(0, 16))

        tk.Label(body, text="Synkroniseringsinterval", bg=BG, fg=DIM,
                 font=self._fonts["eyebrow"]).pack(anchor="w", pady=(0, 8))

        freq_row = tk.Frame(body, bg=BG)
        freq_row.pack(anchor="w")

        tk.Label(freq_row, text="Kørselsinterval (Timer)", bg=BG, fg=TEXT,
                 font=self._fonts["body"]).pack(side="left")

        tk.Spinbox(
            freq_row, from_=1, to=4, width=4,
            textvariable=self._controller._run_freq_var,
            command=self._controller._on_freq_changed,
            font=self._fonts["body"],
        ).pack(side="left", padx=8)

        next_run_row = tk.Frame(body, bg=BG)
        next_run_row.pack(anchor="w", pady=(8, 0))

        tk.Label(next_run_row, text="Næste kørsel: ", bg=BG, fg=DIM,
                 font=self._fonts["small"]).pack(side="left")
        tk.Label(next_run_row, textvariable=self._controller._next_run_var,
                 bg=BG, fg=DIM, font=self._fonts["small"]).pack(side="left")
