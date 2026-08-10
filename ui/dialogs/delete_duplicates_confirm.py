# -*- coding: utf-8 -*-
# ui/dialogs/delete_duplicates_confirm.py — Confirm permanent deletion of duplicate Aula events
import tkinter as tk
from theme import PANEL, SUBTLE, LINE, TEXT, DIM, FAINT, ERR, ERR_HOVER
from ui.widgets import PrimaryButton, SecondaryButton


class DeleteDuplicatesConfirmDialog:
    """Custom modal asking the user to confirm permanent deletion of the
    duplicate Aula events found by the Avanceret-side dublet-scanning."""

    def __init__(self, parent, fonts, count, on_confirm):
        self.top = tk.Toplevel(parent)
        self.top.title("")
        self.top.configure(bg=PANEL)
        self.top.transient(parent)
        self.top.grab_set()
        self.top.resizable(False, False)

        # Eyebrow pill
        eyebrow = tk.Frame(self.top, bg="#FAEAEA")
        eyebrow.pack(anchor="w", padx=26, pady=(22, 10))
        tk.Label(eyebrow, text="⚠  BEKRÆFT SLETNING",
                 bg="#FAEAEA", fg=ERR, font=fonts["eyebrow"],
                 padx=10, pady=2).pack()

        tk.Label(self.top, text=f"Slet {count} dublet-begivenheder fra Aula?",
                 bg=PANEL, fg=TEXT, font=fonts["display_s"],
                 justify="left").pack(anchor="w", padx=26)

        tk.Label(self.top,
                 text=("Dette sletter permanent alle undtagen den oprindelige kopi i hver "
                       "dublet-gruppe. Handlingen kan ikke fortrydes."),
                 bg=PANEL, fg=DIM, font=fonts["body"],
                 wraplength=400, justify="left"
                 ).pack(anchor="w", padx=26, pady=(8, 4))

        tk.Label(self.top,
                 text=("Den bevarede kopi opdateres automatisk til at matche Outlook ved "
                       "næste almindelige synkronisering, hvis indholdet er ændret siden."),
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

        PrimaryButton(btn_row, text="Slet dubletter", command=_confirm,
                      fonts=fonts, bg=ERR, hover=ERR_HOVER, pady=5,
                      ).pack(side="right", padx=(0, 8), pady=14)

        # Center on parent
        self.top.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - self.top.winfo_width())  // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - self.top.winfo_height()) // 2
        self.top.geometry(f"+{px}+{py}")
