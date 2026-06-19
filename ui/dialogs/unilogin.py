# -*- coding: utf-8 -*-
# ui/dialogs/unilogin.py — Login-dialog med IDP-vælger
import tkinter as tk
from tkinter import ttk
from theme import BG, PANEL, LINE, TEXT, DIM, ACCENT, SUBTLE
from aula.idp_config import LOCAL_IDPS


# Loginmetode-valg vist i dropdownen
_UNILOGIN_OPTION = ("UniLogin (STIL)", "")          # (visningsnavn, idp_id)
_IDP_OPTIONS = [(_UNILOGIN_OPTION)] + [
    (idp["display_name"], idp["id"]) for idp in LOCAL_IDPS
]
_DISPLAY_NAMES = [opt[0] for opt in _IDP_OPTIONS]


def _idp_id_to_display(idp_id: str) -> str:
    for display, value in _IDP_OPTIONS:
        if value == idp_id:
            return display
    return _UNILOGIN_OPTION[0]


def _display_to_idp_id(display: str) -> str:
    for disp, value in _IDP_OPTIONS:
        if disp == display:
            return value
    return ""


class UniloginDialog:
    """Modal dialog for at konfigurere Aula-loginoplysninger og vælge IDP."""

    def __init__(self, parent: tk.Misc, fonts=None):
        from setupmanager import SetupManager
        self.setupmgr = SetupManager()

        self._dlg = tk.Toplevel(parent)
        self._dlg.title("Login-opsætning")
        self._dlg.resizable(False, False)
        self._dlg.transient(parent)
        self._dlg.grab_set()
        self._dlg.configure(bg=PANEL)

        self._fonts = fonts
        self._build_ui()
        self._load_credentials()

        # Centrer over parent
        self._dlg.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - self._dlg.winfo_width())  // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - self._dlg.winfo_height()) // 2
        self._dlg.geometry(f"+{px}+{py}")

    def _build_ui(self):
        d = self._dlg

        # Overskrift
        tk.Label(d, text="LOGIN-OPSÆTNING", bg=PANEL, fg=DIM,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=26, pady=(22, 2))

        tk.Label(d, text="Log ind på Aula",
                 bg=PANEL, fg=TEXT,
                 font=("Georgia", 15)).pack(anchor="w", padx=26, pady=(0, 4))

        tk.Label(d,
                 text="Vælg loginmetode og indtast brugeroplysninger.\n"
                      "Disse gemmes sikkert og bruges til synkronisering med Aula.",
                 bg=PANEL, fg=DIM,
                 font=("Segoe UI", 9),
                 justify="left").pack(anchor="w", padx=26, pady=(0, 14))

        tk.Frame(d, bg=LINE, height=1).pack(fill="x")

        # Formularfelter
        grid = tk.Frame(d, bg=PANEL)
        grid.pack(fill="x", padx=26, pady=14)

        # Loginmetode (IDP-vælger)
        tk.Label(grid, text="Loginmetode", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=4)

        self._idp_var = tk.StringVar()
        idp_combo = ttk.Combobox(
            grid,
            textvariable=self._idp_var,
            values=_DISPLAY_NAMES,
            state="readonly",
            width=28,
        )
        idp_combo.grid(row=0, column=1, padx=(12, 0), pady=4, ipady=2, sticky="w")

        # Brugernavn
        tk.Label(grid, text="Brugernavn", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="w", pady=4)
        self.username = tk.Entry(grid, width=30, relief="solid", borderwidth=1)
        self.username.grid(row=1, column=1, padx=(12, 0), pady=4, ipady=3)

        # Kodeord
        tk.Label(grid, text="Kodeord", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky="w", pady=4)
        self.password = tk.Entry(grid, width=30, show="*", relief="solid", borderwidth=1)
        self.password.grid(row=2, column=1, padx=(12, 0), pady=4, ipady=3)

        # Separator + knapper
        tk.Frame(d, bg=LINE, height=1).pack(fill="x")

        btn_row = tk.Frame(d, bg=SUBTLE)
        btn_row.pack(fill="x")

        tk.Button(btn_row, text="Annullér",
                  command=self._dlg.destroy,
                  bg=PANEL, fg=TEXT,
                  relief="solid", borderwidth=1,
                  font=("Segoe UI", 9),
                  padx=14, pady=5,
                  activebackground=SUBTLE,
                  ).pack(side="right", padx=(0, 18), pady=14)

        tk.Button(btn_row, text="Gem",
                  command=self._on_ok,
                  bg=ACCENT, fg="white",
                  relief="flat", borderwidth=0,
                  font=("Segoe UI", 9),
                  padx=14, pady=5,
                  activebackground="#325039", activeforeground="white",
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
        try:
            saved_idp = self.setupmgr.get_aula_idp_id()
            self._idp_var.set(_idp_id_to_display(saved_idp))
        except Exception:
            self._idp_var.set(_UNILOGIN_OPTION[0])

    def _on_ok(self):
        idp_id = _display_to_idp_id(self._idp_var.get())
        self.setupmgr.update_unilogin(
            username=self.username.get(),
            password=self.password.get(),
            idp_id=idp_id,
        )
        self._dlg.destroy()

    def exec(self):
        """Blokér til dialogen lukkes (modal)."""
        self._dlg.wait_window()
