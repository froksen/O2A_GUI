# -*- coding: utf-8 -*-
# ui/dialogs/force_confirm.py — Force-sync confirmation dialog
import tkinter as tk
from theme import PANEL, SUBTLE, LINE, TEXT, DIM, FAINT, WARN, WARN_DARK


class ForceConfirmDialog:
    """Custom modal asking the user to confirm a full force-sync."""

    def __init__(self, parent, fonts, on_confirm):
        self.top = tk.Toplevel(parent)
        self.top.title("")
        self.top.configure(bg=PANEL)
        self.top.transient(parent)
        self.top.grab_set()
        self.top.resizable(False, False)

        # Eyebrow pill
        eyebrow = tk.Frame(self.top, bg="#F4E9D2")
        eyebrow.pack(anchor="w", padx=26, pady=(22, 10))
        tk.Label(eyebrow, text="⚠  BEKRÆFT HANDLING",
                 bg="#F4E9D2", fg=WARN_DARK, font=fonts["eyebrow"],
                 padx=10, pady=2).pack()

        tk.Label(self.top, text="Tving en fuld synkronisering?",
                 bg=PANEL, fg=TEXT, font=fonts["display_s"],
                 justify="left").pack(anchor="w", padx=26)

        tk.Label(self.top,
                 text=("Alle AULA-mærkede Outlook-aftaler bliver gen-overført til "
                       "Aula — også dem, der er uændrede siden sidst."),
                 bg=PANEL, fg=DIM, font=fonts["body"],
                 wraplength=400, justify="left"
                 ).pack(anchor="w", padx=26, pady=(8, 4))

        tk.Label(self.top,
                 text=("Brug det, hvis Aula-siden ser forkert ud, eller hvis du har "
                       "slettet noget i Aula som bør gendannes. Det tager typisk "
                       "lidt længere tid end en almindelig kørsel."),
                 bg=PANEL, fg=FAINT, font=fonts["small"],
                 wraplength=400, justify="left"
                 ).pack(anchor="w", padx=26, pady=(8, 18))

        tk.Frame(self.top, bg=LINE, height=1).pack(fill="x")

        btn_row = tk.Frame(self.top, bg=SUBTLE)
        btn_row.pack(fill="x")

        tk.Button(btn_row, text="Annullér", command=self.top.destroy,
                  bg=PANEL, fg=TEXT, font=fonts["body"],
                  relief="solid", borderwidth=1, padx=14, pady=5,
                  activebackground=SUBTLE
                  ).pack(side="right", padx=(0, 18), pady=14)

        def _confirm():
            self.top.destroy()
            on_confirm()

        tk.Button(btn_row, text="Tving kørsel", command=_confirm,
                  bg=WARN_DARK, fg="white", font=fonts["body"],
                  relief="flat", borderwidth=0, padx=14, pady=5,
                  activebackground="#8c5e0e", activeforeground="white"
                  ).pack(side="right", padx=(0, 8), pady=14)

        # Center on parent
        self.top.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - self.top.winfo_width())  // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - self.top.winfo_height()) // 2
        self.top.geometry(f"+{px}+{py}")
