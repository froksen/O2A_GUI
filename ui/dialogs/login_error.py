# -*- coding: utf-8 -*-
# ui/dialogs/login_error.py — Login-fejl dialog
import tkinter as tk
from theme import PANEL, SUBTLE, LINE, TEXT, DIM, FAINT, ERR


class LoginErrorDialog:
    """Modal dialog shown when Aula login fails."""

    def __init__(self, parent, fonts, on_fix_credentials=None):
        self.top = tk.Toplevel(parent)
        self.top.title("")
        self.top.configure(bg=PANEL)
        self.top.transient(parent)
        self.top.grab_set()
        self.top.resizable(False, False)

        # Eyebrow pill
        eyebrow = tk.Frame(self.top, bg="#FDECEA")
        eyebrow.pack(anchor="w", padx=26, pady=(22, 10))
        tk.Label(eyebrow, text="✕  LOGIN MISLYKKEDES",
                 bg="#FDECEA", fg=ERR, font=fonts["eyebrow"],
                 padx=10, pady=2).pack()

        tk.Label(self.top, text="Kunne ikke logge ind på Aula",
                 bg=PANEL, fg=TEXT, font=fonts["display_s"],
                 justify="left").pack(anchor="w", padx=26)

        tk.Label(self.top,
                 text=("Synkroniseringen blev afbrudt, da det ikke lykkedes\n"
                       "at logge ind på Aula med de gemte oplysninger."),
                 bg=PANEL, fg=DIM, font=fonts["body"],
                 wraplength=400, justify="left",
                 ).pack(anchor="w", padx=26, pady=(8, 4))

        tk.Label(self.top, text="Mulige årsager:",
                 bg=PANEL, fg=TEXT, font=fonts["body_b"],
                 ).pack(anchor="w", padx=26, pady=(10, 2))

        for cause in [
            "Forkert brugernavn eller kodeord",
            "Ingen internetforbindelse",
            "Aulas login-tjeneste er midlertidigt nede",
        ]:
            row = tk.Frame(self.top, bg=PANEL)
            row.pack(anchor="w", padx=26, fill="x")
            tk.Label(row, text="•", bg=PANEL, fg=DIM, font=fonts["body"]).pack(side="left", padx=(4, 8))
            tk.Label(row, text=cause, bg=PANEL, fg=DIM, font=fonts["body"]).pack(side="left")

        tk.Label(self.top,
                 text="Ret dine Aula-loginoplysninger under Konto og prøv igen.",
                 bg=PANEL, fg=FAINT, font=fonts["small"],
                 wraplength=400, justify="left",
                 ).pack(anchor="w", padx=26, pady=(12, 18))

        tk.Frame(self.top, bg=LINE, height=1).pack(fill="x")

        btn_row = tk.Frame(self.top, bg=SUBTLE)
        btn_row.pack(fill="x")

        tk.Button(btn_row, text="OK", command=self.top.destroy,
                  bg=PANEL, fg=TEXT, font=fonts["body"],
                  relief="solid", borderwidth=1, padx=14, pady=5,
                  activebackground=SUBTLE,
                  ).pack(side="right", padx=(0, 18), pady=14)

        if on_fix_credentials:
            def _fix():
                self.top.destroy()
                on_fix_credentials()

            tk.Button(btn_row, text="Ret login-oplysninger", command=_fix,
                      bg=ERR, fg="white", font=fonts["body"],
                      relief="flat", borderwidth=0, padx=14, pady=5,
                      activebackground="#a33220", activeforeground="white",
                      ).pack(side="right", padx=(0, 8), pady=14)

        # Center on parent
        self.top.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - self.top.winfo_width())  // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - self.top.winfo_height()) // 2
        self.top.geometry(f"+{px}+{py}")
