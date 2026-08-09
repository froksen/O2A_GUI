# -*- coding: utf-8 -*-
# ui/personer_view.py — Personer (people) view
import tkinter as tk
from theme import BG, LINE, TEXT, DIM, FAINT, PANEL
from ui.widgets import SecondaryButton


class PersonerView(tk.Frame):
    """Provides access to the person ignore list and alias mapping."""

    def __init__(self, parent, controller, fonts):
        super().__init__(parent, bg=BG)
        self._controller = controller
        self._fonts = fonts
        self._build()

    def _build(self):
        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=40, pady=(28, 20))

        tk.Label(hdr, text="PERSONER", bg=BG, fg=DIM,
                 font=self._fonts["eyebrow"]).pack(anchor="w")
        tk.Label(hdr, text="Personer", bg=BG, fg=TEXT,
                 font=self._fonts["display_m"]).pack(anchor="w", pady=(4, 0))

        tk.Frame(self, bg=LINE, height=1).pack(fill="x", padx=40)

        # ── Body ──────────────────────────────────────────────────────────────
        body = tk.Frame(self, bg=BG)
        body.pack(fill="x", padx=40, pady=20)

        tk.Label(body,
                 text="Begge knapper åbner en liste i Excel, som du kan rette i og gemme.",
                 bg=BG, fg=DIM,
                 font=self._fonts["body"],
                 justify="left").pack(anchor="w", pady=(0, 20))

        # ── Ignorer personer ─────────────────────────────────────────────────
        tk.Label(body, text="Udelad bestemte personer", bg=BG, fg=TEXT,
                 font=self._fonts["body_b"]).pack(anchor="w")
        tk.Label(body,
                 text=("Skriv ét navn per linje, præcis som det står i Outlook. Personer på "
                       "listen bliver aldrig sendt med til Aula."),
                 bg=BG, fg=FAINT, font=self._fonts["small"],
                 wraplength=560, justify="left",
                 ).pack(anchor="w", pady=(2, 8))
        SecondaryButton(body, text="Ignorer personer",
                        command=self._controller.on_actionIgnore_people_list_triggered,
                        fonts=self._fonts).pack(anchor="w")

        tk.Frame(body, bg=LINE, height=1).pack(fill="x", pady=(20, 20))

        # ── Personers alias ──────────────────────────────────────────────────
        tk.Label(body, text="Ret et navn, hvis det er forskelligt i Aula", bg=BG, fg=TEXT,
                 font=self._fonts["body_b"]).pack(anchor="w")
        tk.Label(body,
                 text=("To kolonner: 'Outlook navn' (som personen hedder i Outlook) og "
                       "'AULA navn' (det navn, personen skal vises med i Aula)."),
                 bg=BG, fg=FAINT, font=self._fonts["small"],
                 wraplength=560, justify="left",
                 ).pack(anchor="w", pady=(2, 8))
        SecondaryButton(body, text="Personers alias",
                        command=self._controller.on_actionOutlook_Aulanavne_liste_triggered,
                        fonts=self._fonts).pack(anchor="w")
