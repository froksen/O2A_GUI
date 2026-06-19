# -*- coding: utf-8 -*-
# ui/notifikationer_view.py — Notification preference table
import tkinter as tk
from theme import BG, PANEL, SUBTLE, LINE, TEXT, DIM, FAINT
from notification_settings import NotificationSettings, EVENTS


class NotifikationerView(tk.Frame):
    """Table with checkboxes for E-mail, Toast and Ingen per error event.

    E-mail and Toast are independent — both can be active simultaneously.
    Checking Ingen clears the other two; checking either clears Ingen.
    """

    def __init__(self, parent, controller, fonts):
        super().__init__(parent, bg=BG)
        self._fonts = fonts
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
                       "under synkronisering. E-mail og Toast kan begge være aktive "
                       "samtidigt. Standard er E-mail. "
                       "Kritisk programfejl dækker uventede fejl der stopper synkroniseringen helt."),
                 bg=BG, fg=DIM, font=self._fonts["small"],
                 wraplength=640, justify="left",
                 ).pack(anchor="w", pady=(0, 16))

        # ── Table card ────────────────────────────────────────────────────────
        card = tk.Frame(body, bg=PANEL,
                        highlightthickness=1, highlightbackground=LINE)
        card.pack(fill="x")
        card.grid_columnconfigure(0, weight=1)
        for c in (1, 2, 3):
            card.grid_columnconfigure(c, minsize=100)

        # Table header
        for c, label in enumerate(["Hændelse", "E-mail", "Toast", "Ingen"]):
            tk.Label(card, text=label,
                     bg=SUBTLE, fg=DIM, font=self._fonts["eyebrow"],
                     padx=16 if c == 0 else 0, pady=10,
                     anchor="w" if c == 0 else "center",
                     ).grid(row=0, column=c, sticky="ew")

        tk.Frame(card, bg=LINE, height=1).grid(
            row=1, column=0, columnspan=4, sticky="ew")

        ns = NotificationSettings()
        for i, (key, event_label) in enumerate(EVENTS):
            data_row = i * 2 + 2
            row_bg   = PANEL if i % 2 == 0 else SUBTLE
            methods  = ns.get(key)   # set, e.g. {'email'} or {'email','toast'}

            email_var = tk.BooleanVar(value="email" in methods)
            toast_var = tk.BooleanVar(value="toast" in methods)
            none_var  = tk.BooleanVar(value=not methods)

            def _on_email(ev=email_var, tv=toast_var, nv=none_var, k=key):
                if ev.get():
                    nv.set(False)
                elif not tv.get():
                    nv.set(True)
                self._save(k, ev, tv)

            def _on_toast(ev=email_var, tv=toast_var, nv=none_var, k=key):
                if tv.get():
                    nv.set(False)
                elif not ev.get():
                    nv.set(True)
                self._save(k, ev, tv)

            def _on_none(ev=email_var, tv=toast_var, nv=none_var, k=key):
                if nv.get():
                    ev.set(False)
                    tv.set(False)
                else:
                    # Cannot uncheck Ingen without selecting something else
                    nv.set(True)
                self._save(k, ev, tv)

            tk.Label(card, text=event_label, bg=row_bg, fg=TEXT,
                     font=self._fonts["body"],
                     padx=16, pady=11, anchor="w",
                     ).grid(row=data_row, column=0, sticky="ew")

            tk.Checkbutton(card, variable=email_var, bg=row_bg,
                           activebackground=row_bg, selectcolor=PANEL,
                           command=_on_email,
                           ).grid(row=data_row, column=1)

            tk.Checkbutton(card, variable=toast_var, bg=row_bg,
                           activebackground=row_bg, selectcolor=PANEL,
                           command=_on_toast,
                           ).grid(row=data_row, column=2)

            tk.Checkbutton(card, variable=none_var, bg=row_bg,
                           activebackground=row_bg, selectcolor=PANEL,
                           command=_on_none,
                           ).grid(row=data_row, column=3)

            if i < len(EVENTS) - 1:
                tk.Frame(card, bg=LINE, height=1).grid(
                    row=data_row + 1, column=0, columnspan=4, sticky="ew")

    @staticmethod
    def _save(key: str, email_var: tk.BooleanVar, toast_var: tk.BooleanVar):
        methods = set()
        if email_var.get():
            methods.add("email")
        if toast_var.get():
            methods.add("toast")
        NotificationSettings().set(key, methods)
