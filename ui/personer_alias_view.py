# -*- coding: utf-8 -*-
# ui/personer_alias_view.py — Personers alias (name mapping) view
import tkinter as tk
from tkinter import filedialog
from theme import BG, LINE, TEXT, DIM, FAINT, PANEL, SUBTLE
from ui.widgets import PrimaryButton, SecondaryButton, ScrollableFrame, prompt_fields
from ui.dialogs.export_warning import ExportWarningDialog


class PersonerAliasView(tk.Frame):
    """Inline editor for the Outlook-name → Aula-name alias mapping, plus
    export/import to a plaintext CSV as an advanced fallback for bulk
    editing (listen selv er krypteret på disk — se peoplecsvmanager.py)."""

    def __init__(self, parent, controller, fonts):
        super().__init__(parent, bg=BG)
        self._controller = controller
        self._fonts = fonts
        self._alias_rows = None
        self._build()

    def _build(self):
        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=40, pady=(28, 20))

        tk.Label(hdr, text="PERSONERS ALIAS", bg=BG, fg=DIM,
                 font=self._fonts["eyebrow"]).pack(anchor="w")
        tk.Label(hdr, text="Personers alias", bg=BG, fg=TEXT,
                 font=self._fonts["display_m"]).pack(anchor="w", pady=(4, 0))

        tk.Frame(self, bg=LINE, height=1).pack(fill="x", padx=40)

        # ── Body ──────────────────────────────────────────────────────────────
        body = tk.Frame(self, bg=BG)
        body.pack(fill="x", padx=40, pady=20)

        tk.Label(body,
                 text=("Outlook-navnet er som personen hedder i Outlook, "
                       "AULA-navnet er det navn personen skal vises med i Aula."),
                 bg=BG, fg=FAINT, font=self._fonts["small"],
                 wraplength=560, justify="left",
                 ).pack(anchor="w", pady=(0, 8))

        alias_scroll = ScrollableFrame(body, height=280, bg=PANEL,
                                       highlightthickness=1, highlightbackground=LINE)
        alias_scroll.pack(fill="x")
        self._alias_rows = alias_scroll.inner

        PrimaryButton(body, text="+ Tilføj alias",
                      command=self._on_add_alias,
                      fonts=self._fonts).pack(anchor="w", pady=(8, 0))

        tk.Frame(body, bg=LINE, height=1).pack(fill="x", pady=(20, 20))

        # ── Avanceret: eksportér/importér CSV ────────────────────────────────
        tk.Label(body, text="Avanceret: eksportér/importér CSV", bg=BG, fg=DIM,
                 font=self._fonts["eyebrow"]).pack(anchor="w", pady=(0, 8))
        adv_row = tk.Frame(body, bg=BG)
        adv_row.pack(anchor="w")
        SecondaryButton(adv_row, text="Eksportér til CSV…",
                        command=self._on_export,
                        fonts=self._fonts).pack(side="left")
        SecondaryButton(adv_row, text="Importér fra CSV…",
                        command=self._on_import,
                        fonts=self._fonts).pack(side="left", padx=(8, 0))

        self._refresh_alias_list()

    # ── Rendering ─────────────────────────────────────────────────────────────

    def _refresh_alias_list(self):
        for child in self._alias_rows.winfo_children():
            child.destroy()

        from peoplecsvmanager import PeopleCsvManager
        aliases = PeopleCsvManager().get_aliases()

        if not aliases:
            tk.Label(self._alias_rows, text="Ingen alias-oversættelser endnu.",
                     bg=PANEL, fg=FAINT, font=self._fonts["small"],
                     padx=16, pady=12).pack(anchor="w")
            return

        for i, (outlook_name, aula_name) in enumerate(aliases):
            row_bg = PANEL if i % 2 == 0 else SUBTLE
            row = tk.Frame(self._alias_rows, bg=row_bg)
            row.pack(fill="x")
            tk.Label(row, text=f"{outlook_name}  →  {aula_name}", bg=row_bg, fg=TEXT,
                     font=self._fonts["body"], anchor="w",
                     padx=16, pady=8).pack(side="left", fill="x", expand=True)
            SecondaryButton(row, text="×", fonts=self._fonts,
                            command=lambda n=outlook_name: self._on_remove_alias(n),
                            padx=8, pady=2).pack(side="right", padx=(0, 12), pady=6)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _on_add_alias(self):
        values = prompt_fields(self, self._fonts,
                               "Tilføj alias", ["Outlook-navn", "AULA-navn"])
        if not values or not values[0] or not values[1]:
            return
        from peoplecsvmanager import PeopleCsvManager
        PeopleCsvManager().add_alias(values[0], values[1])
        self._refresh_alias_list()

    def _on_remove_alias(self, outlook_name):
        from peoplecsvmanager import PeopleCsvManager
        PeopleCsvManager().remove_alias(outlook_name)
        self._refresh_alias_list()

    def _on_export(self):
        ExportWarningDialog(self, self._fonts, on_confirm=self._do_export)

    def _do_export(self):
        path = filedialog.asksaveasfilename(
            parent=self, title="Eksportér personers alias",
            defaultextension=".csv",
            filetypes=[("CSV-filer", "*.csv")],
            initialfile="personer.csv")
        if not path:
            return
        from peoplecsvmanager import PeopleCsvManager
        PeopleCsvManager().export_aliases_to(path)

    def _on_import(self):
        path = filedialog.askopenfilename(
            parent=self, title="Importér personers alias",
            filetypes=[("CSV-filer", "*.csv")])
        if not path:
            return
        from peoplecsvmanager import PeopleCsvManager
        PeopleCsvManager().import_aliases_from(path)
        self._refresh_alias_list()
