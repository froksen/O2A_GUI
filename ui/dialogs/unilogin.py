# -*- coding: utf-8 -*-
# ui/dialogs/unilogin.py — Uni-login dialog using the new theme
import tkinter as tk
from theme import BG, PANEL, LINE, TEXT, DIM, ACCENT, SUBTLE


class UniloginDialog:
    """Modal dialog for entering Aula (Uni-login) credentials."""

    def __init__(self, parent: tk.Misc, fonts=None):
        from setupmanager import SetupManager
        self.setupmgr = SetupManager()

        self._dlg = tk.Toplevel(parent)
        self._dlg.title("Uni-login")
        self._dlg.resizable(False, False)
        self._dlg.transient(parent)
        self._dlg.grab_set()
        self._dlg.configure(bg=PANEL)

        self._fonts = fonts
        self._build_ui()
        self._load_credentials()

        # Center over parent
        self._dlg.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - self._dlg.winfo_width())  // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - self._dlg.winfo_height()) // 2
        self._dlg.geometry(f"+{px}+{py}")

    def _build_ui(self):
        d = self._dlg

        # Eyebrow
        tk.Label(d, text="UNI-LOGIN", bg=PANEL, fg=DIM,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=26, pady=(22, 2))

        tk.Label(d, text="Log ind på Aula",
                 bg=PANEL, fg=TEXT,
                 font=("Georgia", 15)).pack(anchor="w", padx=26, pady=(0, 4))

        tk.Label(d,
                 text=("Indtast dine uni-login brugeroplysninger.\n"
                       "Disse bruges til at læse og administrere begivenheder på Aula."),
                 bg=PANEL, fg=DIM,
                 font=("Segoe UI", 9),
                 justify="left").pack(anchor="w", padx=26, pady=(0, 14))

        # Separator
        tk.Frame(d, bg=LINE, height=1).pack(fill="x")

        # Form fields
        grid = tk.Frame(d, bg=PANEL)
        grid.pack(fill="x", padx=26, pady=14)

        tk.Label(grid, text="Brugernavn", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=4)
        self.username = tk.Entry(grid, width=30, relief="solid", borderwidth=1)
        self.username.grid(row=0, column=1, padx=(12, 0), pady=4, ipady=3)

        tk.Label(grid, text="Kodeord", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="w", pady=4)
        self.password = tk.Entry(grid, width=30, show="*", relief="solid", borderwidth=1)
        self.password.grid(row=1, column=1, padx=(12, 0), pady=4, ipady=3)

        # Separator + button row
        tk.Frame(d, bg=LINE, height=1).pack(fill="x")

        btn_row = tk.Frame(d, bg=SUBTLE)
        btn_row.pack(fill="x")

        tk.Button(btn_row, text="Annullér",
                  command=self._dlg.destroy,
                  bg=PANEL, fg=TEXT,
                  relief="solid", borderwidth=1,
                  font=("Segoe UI", 9),
                  padx=14, pady=5,
                  activebackground=SUBTLE
                  ).pack(side="right", padx=(0, 18), pady=14)

        tk.Button(btn_row, text="Gem",
                  command=self._on_ok,
                  bg=ACCENT, fg="white",
                  relief="flat", borderwidth=0,
                  font=("Segoe UI", 9),
                  padx=14, pady=5,
                  activebackground="#325039", activeforeground="white"
                  ).pack(side="right", padx=(0, 8), pady=14)

    def _load_credentials(self):
        try:
            self.username.insert(0, self.setupmgr.get_aula_username() or "")
        except Exception:
            pass
        try:
            self.password.insert(0, self.setupmgr.get_aula_password() or "")
        except Exception:
            pass

    def _on_ok(self):
        self.setupmgr.update_unilogin(
            username=self.username.get(),
            password=self.password.get()
        )
        self._dlg.destroy()

    def exec(self):
        """Block until the dialog is closed (modal)."""
        self._dlg.wait_window()
