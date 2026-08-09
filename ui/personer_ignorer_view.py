# -*- coding: utf-8 -*-
# ui/personer_ignorer_view.py — Udelad personer (ignore list) view
import tkinter as tk
from theme import BG, LINE, TEXT, DIM, FAINT, PANEL, SUBTLE
from ui.widgets import PrimaryButton, SecondaryButton, ScrollableFrame, prompt_fields


class PersonerIgnorerView(tk.Frame):
    """Inline editor for the person ignore list, plus the original
    "open in Excel" button as an advanced fallback."""

    def __init__(self, parent, controller, fonts):
        super().__init__(parent, bg=BG)
        self._controller = controller
        self._fonts = fonts
        self._ignored_rows = None
        self._build()

    def _build(self):
        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=40, pady=(28, 20))

        tk.Label(hdr, text="UDELAD PERSONER", bg=BG, fg=DIM,
                 font=self._fonts["eyebrow"]).pack(anchor="w")
        tk.Label(hdr, text="Udelad personer", bg=BG, fg=TEXT,
                 font=self._fonts["display_m"]).pack(anchor="w", pady=(4, 0))

        tk.Frame(self, bg=LINE, height=1).pack(fill="x", padx=40)

        # ── Body ──────────────────────────────────────────────────────────────
        body = tk.Frame(self, bg=BG)
        body.pack(fill="x", padx=40, pady=20)

        tk.Label(body,
                 text="Personer på listen bliver aldrig sendt med til Aula.",
                 bg=BG, fg=FAINT, font=self._fonts["small"],
                 wraplength=560, justify="left",
                 ).pack(anchor="w", pady=(0, 8))

        ignored_scroll = ScrollableFrame(body, height=280, bg=PANEL,
                                        highlightthickness=1, highlightbackground=LINE)
        ignored_scroll.pack(fill="x")
        self._ignored_rows = ignored_scroll.inner

        PrimaryButton(body, text="+ Tilføj navn",
                      command=self._on_add_ignored,
                      fonts=self._fonts).pack(anchor="w", pady=(8, 0))

        tk.Frame(body, bg=LINE, height=1).pack(fill="x", pady=(20, 20))

        # ── Avanceret: redigér direkte i Excel ───────────────────────────────
        tk.Label(body, text="Avanceret: redigér direkte i Excel", bg=BG, fg=DIM,
                 font=self._fonts["eyebrow"]).pack(anchor="w", pady=(0, 8))
        SecondaryButton(body, text="Ignorer personer",
                        command=self._controller.on_actionIgnore_people_list_triggered,
                        fonts=self._fonts).pack(anchor="w")

        self._refresh_ignored_list()

    # ── Rendering ─────────────────────────────────────────────────────────────

    def _refresh_ignored_list(self):
        for child in self._ignored_rows.winfo_children():
            child.destroy()

        from peoplecsvmanager import PeopleCsvManager
        names = PeopleCsvManager().get_ignored_people()

        if not names:
            tk.Label(self._ignored_rows, text="Ingen personer udeladt endnu.",
                     bg=PANEL, fg=FAINT, font=self._fonts["small"],
                     padx=16, pady=12).pack(anchor="w")
            return

        for i, name in enumerate(names):
            row_bg = PANEL if i % 2 == 0 else SUBTLE
            row = tk.Frame(self._ignored_rows, bg=row_bg)
            row.pack(fill="x")
            tk.Label(row, text=name, bg=row_bg, fg=TEXT,
                     font=self._fonts["body"], anchor="w",
                     padx=16, pady=8).pack(side="left", fill="x", expand=True)
            SecondaryButton(row, text="×", fonts=self._fonts,
                            command=lambda n=name: self._on_remove_ignored(n),
                            padx=8, pady=2).pack(side="right", padx=(0, 12), pady=6)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _on_add_ignored(self):
        values = prompt_fields(self, self._fonts,
                               "Tilføj person til udeladelse", ["Outlook-navn"])
        if not values or not values[0]:
            return
        from peoplecsvmanager import PeopleCsvManager
        PeopleCsvManager().add_ignored_person(values[0])
        self._refresh_ignored_list()

    def _on_remove_ignored(self, name):
        from peoplecsvmanager import PeopleCsvManager
        PeopleCsvManager().remove_ignored_person(name)
        self._refresh_ignored_list()
