# -*- coding: utf-8 -*-
# ui/notifikationer_view.py — Notification preference table
import tkinter as tk
from theme import BG, PANEL, SUBTLE, LINE, TEXT, DIM
from notification_settings import NotificationSettings, EVENTS, METHODS


class NotifikationerView(tk.Frame):
    """Table where the user picks E-mail / Toast / Ingen per error event."""

    def __init__(self, parent, controller, fonts):
        super().__init__(parent, bg=BG)
        self._fonts = fonts
        self._vars  = {}
        self._build()

    def _build(self):
        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=40, pady=(28, 20))

        tk.Label(hdr, text="NOTIFIKATIONER", bg=BG, fg=DIM,
                 font=self._fonts["eyebrow"]).pack(anchor="w")
        tk.Label(hdr, text="Notifikationer", bg=BG, fg=TEXT,
                 font=self._fonts["display_m"]).pack(anchor="w", pady=(4, 0))

        tk.Frame(self, bg=LINE, height=1).pack(fill="x", padx=40)

        # ── Body ──────────────────────────────────────────────────────────────
        body = tk.Frame(self, bg=BG)
        body.pack(fill="x", padx=40, pady=20)

        tk.Label(body,
                 text=("Vælg, hvordan du ønsker at blive adviseret om hændelser "
                       "under synkronisering. Standard er E-mail."),
                 bg=BG, fg=DIM, font=self._fonts["small"],
                 ).pack(anchor="w", pady=(0, 16))

        # ── Table card ────────────────────────────────────────────────────────
        card = tk.Frame(body, bg=PANEL,
                        highlightthickness=1, highlightbackground=LINE)
        card.pack(fill="x")
        card.grid_columnconfigure(0, weight=1)
        for c in range(1, len(METHODS) + 1):
            card.grid_columnconfigure(c, minsize=100)

        # Header row
        for c, (_, col_label) in enumerate(
                [("", "Hændelse")] + METHODS):
            tk.Label(card, text=col_label,
                     bg=SUBTLE, fg=DIM, font=self._fonts["eyebrow"],
                     padx=16 if c == 0 else 0, pady=10,
                     anchor="w" if c == 0 else "center",
                     ).grid(row=0, column=c, sticky="ew")

        tk.Frame(card, bg=LINE, height=1).grid(
            row=1, column=0, columnspan=len(METHODS) + 1, sticky="ew")

        ns = NotificationSettings()
        for i, (key, event_label) in enumerate(EVENTS):
            data_row = i * 2 + 2
            row_bg   = PANEL if i % 2 == 0 else SUBTLE

            var = tk.StringVar(value=ns.get(key))
            self._vars[key] = var

            tk.Label(card, text=event_label, bg=row_bg, fg=TEXT,
                     font=self._fonts["body"],
                     padx=16, pady=11, anchor="w",
                     ).grid(row=data_row, column=0, sticky="ew")

            for c, (method, _) in enumerate(METHODS):
                tk.Radiobutton(
                    card, variable=var, value=method,
                    bg=row_bg, activebackground=row_bg,
                    command=lambda k=key, v=var: self._save(k, v),
                ).grid(row=data_row, column=c + 1)

            if i < len(EVENTS) - 1:
                tk.Frame(card, bg=LINE, height=1).grid(
                    row=data_row + 1, column=0,
                    columnspan=len(METHODS) + 1, sticky="ew")

    def _save(self, key: str, var: tk.StringVar):
        NotificationSettings().set(key, var.get())
