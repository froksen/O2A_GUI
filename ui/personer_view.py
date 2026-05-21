# -*- coding: utf-8 -*-
# ui/personer_view.py — Personer (people) view
import tkinter as tk
from theme import BG, LINE, TEXT, DIM, ACCENT, PANEL, SUBTLE


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
                 text="Administrer hvilke personer der ignoreres og tilpas navne-aliaser.",
                 bg=BG, fg=DIM,
                 font=self._fonts["body"],
                 justify="left").pack(anchor="w", pady=(0, 16))

        btn_frame = tk.Frame(body, bg=BG)
        btn_frame.pack(anchor="w")

        tk.Button(btn_frame, text="Ignorer personer",
                  command=self._controller.on_actionIgnore_people_list_triggered,
                  bg=PANEL, fg=TEXT,
                  activebackground=SUBTLE,
                  font=self._fonts["body"],
                  relief="solid", borderwidth=1,
                  padx=14, pady=6, cursor="hand2"
                  ).pack(side="left", padx=(0, 8))

        tk.Button(btn_frame, text="Personers alias",
                  command=self._controller.on_actionOutlook_Aulanavne_liste_triggered,
                  bg=PANEL, fg=TEXT,
                  activebackground=SUBTLE,
                  font=self._fonts["body"],
                  relief="solid", borderwidth=1,
                  padx=14, pady=6, cursor="hand2"
                  ).pack(side="left")
