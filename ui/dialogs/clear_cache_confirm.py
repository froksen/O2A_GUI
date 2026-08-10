# -*- coding: utf-8 -*-
# ui/dialogs/clear_cache_confirm.py — Confirm clearing the local Aula-event cache
import tkinter as tk
from theme import PANEL, SUBTLE, LINE, TEXT, DIM, FAINT, WARN, WARN_DARK, WARN_HOVER
from ui.widgets import PrimaryButton, SecondaryButton


class ClearCacheConfirmDialog:
    """Custom modal asking the user to confirm clearing the local Aula-
    event cache. Ikke destruktivt for data i Aula — kun en advarsel om at
    næste synkronisering bliver langsommere, fordi alt skal genhentes."""

    def __init__(self, parent, fonts, on_confirm):
        self.top = tk.Toplevel(parent)
        self.top.title("")
        self.top.configure(bg=PANEL)
        self.top.transient(parent)
        self.top.grab_set()
        self.top.resizable(False, False)

        eyebrow = tk.Frame(self.top, bg="#F4E9D2")
        eyebrow.pack(anchor="w", padx=26, pady=(22, 10))
        tk.Label(eyebrow, text="⚠  BEKRÆFT HANDLING",
                 bg="#F4E9D2", fg=WARN_DARK, font=fonts["eyebrow"],
                 padx=10, pady=2).pack()

        tk.Label(self.top, text="Nulstil begivenheds-cachen?",
                 bg=PANEL, fg=TEXT, font=fonts["display_s"],
                 justify="left").pack(anchor="w", padx=26)

        tk.Label(self.top,
                 text=("Cachen indeholder ingen data der ændrer noget i Aula — den "
                       "bruges kun til at undgå at hente de samme begivenheders "
                       "detaljer igen og igen. Efter nulstilling skal alt hentes "
                       "friskt igen, så den næste synkronisering bliver markant "
                       "langsommere."),
                 bg=PANEL, fg=DIM, font=fonts["body"],
                 wraplength=400, justify="left"
                 ).pack(anchor="w", padx=26, pady=(8, 4))

        tk.Label(self.top,
                 text="Brug det, hvis du har mistanke om at cachen viser forkert data.",
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

        PrimaryButton(btn_row, text="Nulstil cache", command=_confirm,
                      fonts=fonts, bg=WARN_DARK, hover=WARN_HOVER, pady=5,
                      ).pack(side="right", padx=(0, 8), pady=14)

        # Center on parent
        self.top.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - self.top.winfo_width())  // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - self.top.winfo_height()) // 2
        self.top.geometry(f"+{px}+{py}")
