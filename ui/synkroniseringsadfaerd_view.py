# -*- coding: utf-8 -*-
# ui/synkroniseringsadfaerd_view.py — Synkroniseringsinterval + -adfærd view
import tkinter as tk
from theme import BG, LINE, TEXT, DIM, PANEL
from setupmanager import SYNC_BEHAVIOR_OPTIONS


class SynkroniseringsadfaerdView(tk.Frame):
    """Sync frequency (interval) and sync behaviour (what gets transferred)."""

    def __init__(self, parent, controller, fonts):
        super().__init__(parent, bg=BG)
        self._controller = controller
        self._fonts = fonts
        self._behavior_radios = []
        self._build()

    def _build(self):
        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=40, pady=(28, 20))

        tk.Label(hdr, text="SYNKRONISERINGSADFÆRD", bg=BG, fg=DIM,
                 font=self._fonts["eyebrow"]).pack(anchor="w")
        tk.Label(hdr, text="Synkroniseringsadfærd", bg=BG, fg=TEXT,
                 font=self._fonts["display_m"]).pack(anchor="w", pady=(4, 0))

        tk.Frame(self, bg=LINE, height=1).pack(fill="x", padx=40)

        # ── Body ──────────────────────────────────────────────────────────────
        body = tk.Frame(self, bg=BG)
        body.pack(fill="x", padx=40, pady=20)

        # Sync frequency
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

        # Sync behaviour
        tk.Frame(body, bg=LINE, height=1).pack(fill="x", pady=(16, 16))

        tk.Label(body, text="Hvad skal overføres til Aula", bg=BG, fg=DIM,
                 font=self._fonts["eyebrow"]).pack(anchor="w", pady=(0, 8))

        self._behavior_radios = []
        for key, label in SYNC_BEHAVIOR_OPTIONS:
            radio = tk.Radiobutton(
                body,
                text=label,
                variable=self._controller._sync_behavior_var,
                value=key,
                command=self._controller.on_sync_behavior_changed,
                bg=BG, fg=TEXT,
                activebackground=BG,
                selectcolor=PANEL,
                font=self._fonts["body"],
                wraplength=640,
                justify="left",
                anchor="w",
            )
            radio.pack(anchor="w", fill="x", pady=(0, 8))
            self._behavior_radios.append(radio)

        # Låst mens en synkronisering kører, så adfærden ikke skifter midt i en kørsel.
        self.set_sync_behavior_locked(getattr(self._controller, '_sync_in_progress', False))

    def set_sync_behavior_locked(self, locked: bool):
        state = "disabled" if locked else "normal"
        for radio in self._behavior_radios:
            radio.config(state=state)
