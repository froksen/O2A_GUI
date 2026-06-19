# -*- coding: utf-8 -*-
# ui/opdater_view.py — Opdatering (update) view
import tkinter as tk
import sys
import subprocess
import os
from pathlib import Path
from theme import BG, PANEL, SUBTLE, LINE, TEXT, DIM, FAINT, ACCENT

_CREATE_NO_WINDOW = 0x08000000


class OpdaterView(tk.Frame):
    """Shows technical info and allows the user to update the program."""

    def __init__(self, parent, controller, fonts):
        super().__init__(parent, bg=BG)
        self._controller = controller
        self._fonts = fonts
        self._build()

    def _build(self):
        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=40, pady=(28, 20))

        tk.Label(hdr, text="OPDATERING", bg=BG, fg=DIM,
                 font=self._fonts["eyebrow"]).pack(anchor="w")
        tk.Label(hdr, text="Opdatering", bg=BG, fg=TEXT,
                 font=self._fonts["display_m"]).pack(anchor="w", pady=(4, 0))

        tk.Frame(self, bg=LINE, height=1).pack(fill="x", padx=40)

        # ── Body ──────────────────────────────────────────────────────────────
        body = tk.Frame(self, bg=BG)
        body.pack(fill="x", padx=40, pady=20)

        # Technical info
        tk.Label(body, text="Teknisk information", bg=BG, fg=DIM,
                 font=self._fonts["eyebrow"]).pack(anchor="w", pady=(0, 10))

        for label, value in self._get_info_rows():
            row = tk.Frame(body, bg=BG)
            row.pack(fill="x", anchor="w", pady=(0, 6))
            tk.Label(row, text=label, bg=BG, fg=DIM,
                     font=self._fonts["small"], width=18, anchor="w").pack(side="left")
            tk.Label(row, text=value, bg=BG, fg=TEXT,
                     font=self._fonts["body"]).pack(side="left")

        tk.Frame(body, bg=LINE, height=1).pack(fill="x", pady=(16, 16))

        # Update button
        tk.Button(
            body, text="Opdater program",
            command=self._confirm_update,
            bg=ACCENT, fg="white",
            activebackground="#325039", activeforeground="white",
            font=self._fonts["body"],
            relief="flat", borderwidth=0,
            padx=14, pady=6, cursor="hand2",
        ).pack(anchor="w")

    def _get_info_rows(self):
        py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        try:
            result = subprocess.run(
                ["git", "--version"],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                text=True, timeout=5,
                creationflags=_CREATE_NO_WINDOW,
            )
            git_ver = result.stdout.strip() if result.returncode == 0 else "Ikke fundet"
        except Exception:
            git_ver = "Ikke fundet"

        return [
            ("Python version", py_ver),
            ("Git version",    git_ver),
            ("Programversion", self._get_program_version()),
        ]

    @staticmethod
    def _get_program_version():
        base_dir = Path(__file__).resolve().parent.parent
        try:
            import git
            import datetime as dt
            repo = git.Repo(base_dir, search_parent_directories=True)
            commit_dt = dt.datetime.fromtimestamp(repo.head.commit.committed_date)
            return commit_dt.strftime('%d-%m-%Y %H:%M')
        except Exception:
            version_file = base_dir / "version.txt"
            if version_file.is_file():
                return version_file.read_text(encoding="utf-8").strip() or "Ukendt"
            return "Ukendt"

    def _confirm_update(self):
        parent = self._controller.root
        dlg = tk.Toplevel(parent)
        dlg.title("")
        dlg.configure(bg=PANEL)
        dlg.transient(parent)
        dlg.grab_set()
        dlg.resizable(False, False)

        # Eyebrow pill
        pill = tk.Frame(dlg, bg="#D8EAE0")
        pill.pack(anchor="w", padx=26, pady=(22, 10))
        tk.Label(pill, text="⟳  OPDATER PROGRAM",
                 bg="#D8EAE0", fg="#2A5C3A", font=self._fonts["eyebrow"],
                 padx=10, pady=2).pack()

        tk.Label(dlg, text="Opdater Outlook2Aula?",
                 bg=PANEL, fg=TEXT, font=self._fonts["display_s"],
                 justify="left").pack(anchor="w", padx=26)

        tk.Label(dlg,
                 text=("Programmet lukker ned, henter den nyeste version fra GitHub, "
                       "opdaterer afhængigheder og starter automatisk igen."),
                 bg=PANEL, fg=DIM, font=self._fonts["body"],
                 wraplength=400, justify="left",
                 ).pack(anchor="w", padx=26, pady=(8, 4))

        tk.Label(dlg,
                 text="Sørg for at have internetforbindelse, inden du fortsætter.",
                 bg=PANEL, fg=FAINT, font=self._fonts["small"],
                 wraplength=400, justify="left",
                 ).pack(anchor="w", padx=26, pady=(4, 18))

        tk.Frame(dlg, bg=LINE, height=1).pack(fill="x")

        btn_row = tk.Frame(dlg, bg=SUBTLE)
        btn_row.pack(fill="x")

        tk.Button(btn_row, text="Annullér", command=dlg.destroy,
                  bg=PANEL, fg=TEXT, font=self._fonts["body"],
                  relief="solid", borderwidth=1, padx=14, pady=5,
                  activebackground=SUBTLE,
                  ).pack(side="right", padx=(0, 18), pady=14)

        tk.Button(btn_row, text="Opdater nu",
                  command=lambda: self._do_update(dlg),
                  bg=ACCENT, fg="white", font=self._fonts["body"],
                  relief="flat", borderwidth=0, padx=14, pady=5,
                  activebackground="#325039", activeforeground="white",
                  ).pack(side="right", padx=(0, 8), pady=14)

        # Center on parent
        dlg.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - dlg.winfo_width())  // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - dlg.winfo_height()) // 2
        dlg.geometry(f"+{px}+{py}")

    def _do_update(self, dlg):
        dlg.destroy()
        base_dir = Path(__file__).resolve().parent.parent
        bat_path = base_dir / "updateandrun.bat"
        os.startfile(str(bat_path))
        self._controller.root.after(300, self._controller.root.destroy)
