# -*- coding: utf-8 -*-
# ui/dialogs/export_warning.py — Advarsel før eksport af personoplysninger til klartekst-CSV
import tkinter as tk
from theme import PANEL, SUBTLE, LINE, TEXT, DIM, FAINT, WARN_DARK, WARN_HOVER
from ui.widgets import PrimaryButton, SecondaryButton


class ExportWarningDialog:
    """Advarer om at eksportfilen er ukrypteret klartekst, før filvalgsdialogen åbnes."""

    def __init__(self, parent, fonts, on_confirm):
        self.top = tk.Toplevel(parent)
        self.top.title("")
        self.top.configure(bg=PANEL)
        self.top.transient(parent)
        self.top.grab_set()
        self.top.resizable(False, False)

        eyebrow = tk.Frame(self.top, bg="#F4E9D2")
        eyebrow.pack(anchor="w", padx=26, pady=(22, 10))
        tk.Label(eyebrow, text="⚠  SIKKERHEDSADVARSEL",
                 bg="#F4E9D2", fg=WARN_DARK, font=fonts["eyebrow"],
                 padx=10, pady=2).pack()

        tk.Label(self.top, text="Eksportér til CSV?",
                 bg=PANEL, fg=TEXT, font=fonts["display_s"],
                 justify="left").pack(anchor="w", padx=26)

        tk.Label(self.top,
                 text=("Filen gemmes i klartekst og er, i modsætning til listen "
                       "inde i programmet, ikke krypteret. Alle der kan åbne "
                       "filen kan læse navnene i den."),
                 bg=PANEL, fg=DIM, font=fonts["body"],
                 wraplength=400, justify="left"
                 ).pack(anchor="w", padx=26, pady=(8, 4))

        tk.Label(self.top,
                 text=("Opbevar filen et sikkert sted, og slet den igen når du "
                       "ikke længere har brug for den."),
                 bg=PANEL, fg=FAINT, font=fonts["small"],
                 wraplength=400, justify="left"
                 ).pack(anchor="w", padx=26, pady=(8, 18))

        tk.Frame(self.top, bg=LINE, height=1).pack(fill="x")

        btn_row = tk.Frame(self.top, bg=SUBTLE)
        btn_row.pack(fill="x")

        SecondaryButton(btn_row, text="Annullér", command=self.top.destroy,
                        fonts=fonts, pady=5,
                        ).pack(side="right", padx=(0, 18), pady=14)

        def _confirm():
            self.top.destroy()
            on_confirm()

        PrimaryButton(btn_row, text="Eksportér", command=_confirm,
                      fonts=fonts, bg=WARN_DARK, hover=WARN_HOVER, pady=5,
                      ).pack(side="right", padx=(0, 8), pady=14)

        # Center on parent
        self.top.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - self.top.winfo_width())  // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - self.top.winfo_height()) // 2
        self.top.geometry(f"+{px}+{py}")
