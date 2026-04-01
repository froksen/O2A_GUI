# -*- coding: utf-8 -*-
import tkinter as tk
from setupmanager import SetupManager

# ── Colours (matches launcher.pyw palette) ────────────────────────────────────
BG        = "#F2F2F2"
BG_WHITE  = "#FFFFFF"
TEXT_MAIN = "#1B1B1B"
BORDER    = "#D6D6D6"


class UniloginDialog:
    """Modal dialog for entering AULA (Uni-login) credentials."""

    def __init__(self, parent: tk.Misc):
        self.setupmgr = SetupManager()

        self._dlg = tk.Toplevel(parent)
        self._dlg.title("Uni-login")
        self._dlg.resizable(False, False)
        self._dlg.grab_set()
        self._dlg.configure(bg=BG)

        self._build_ui()
        self._load_credentials()

        # Center over parent
        self._dlg.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - self._dlg.winfo_width())  // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - self._dlg.winfo_height()) // 2
        self._dlg.geometry(f"+{px}+{py}")

    def _build_ui(self):
        d = self._dlg

        tk.Label(d, text="UNI-LOGIN", bg=BG, fg=TEXT_MAIN,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=14, pady=(12, 2))

        tk.Label(d,
                 text="Indtast dine uni-login brugeroplysninger.\n"
                      "Disse bruges til at få læse og administerer begivenheder på AULA.",
                 bg=BG, fg=TEXT_MAIN, font=("Segoe UI", 9),
                 justify="left").pack(anchor="w", padx=14, pady=(0, 8))

        grid = tk.Frame(d, bg=BG)
        grid.pack(fill="x", padx=14)

        tk.Label(grid, text="Brugernavn", bg=BG, fg=TEXT_MAIN,
                 font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=3)
        self.username = tk.Entry(grid, width=30)
        self.username.grid(row=0, column=1, padx=(10, 0), pady=3)

        tk.Label(grid, text="Kodeord", bg=BG, fg=TEXT_MAIN,
                 font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="w", pady=3)
        self.password = tk.Entry(grid, width=30, show="*")
        self.password.grid(row=1, column=1, padx=(10, 0), pady=3)

        tk.Frame(d, bg=BORDER, height=1).pack(fill="x", pady=(12, 0))

        btn_row = tk.Frame(d, bg=BG_WHITE)
        btn_row.pack(fill="x", padx=10, pady=8)
        tk.Button(btn_row, text="OK", width=8,
                  command=self._on_ok).pack(side="right", padx=(4, 0))
        tk.Button(btn_row, text="Annuller", width=8,
                  command=self._dlg.destroy).pack(side="right")

    def _load_credentials(self):
        self.username.insert(0, self.setupmgr.get_aula_username() or "")
        self.password.insert(0, self.setupmgr.get_aula_password() or "")

    def _on_ok(self):
        self.setupmgr.update_unilogin(
            username=self.username.get(),
            password=self.password.get()
        )
        self._dlg.destroy()

    def exec(self):
        """Block until the dialog is closed (modal)."""
        self._dlg.wait_window()
