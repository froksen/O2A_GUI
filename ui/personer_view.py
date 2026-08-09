# -*- coding: utf-8 -*-
# ui/personer_view.py — Personer (people) view
import tkinter as tk
from theme import BG, LINE, TEXT, DIM, FAINT, PANEL, SUBTLE
from ui.widgets import PrimaryButton, SecondaryButton, ScrollableFrame


class PersonerView(tk.Frame):
    """Provides an inline editor for the person ignore list and alias
    mapping, plus the original "open in Excel" buttons as an advanced
    fallback."""

    def __init__(self, parent, controller, fonts):
        super().__init__(parent, bg=BG)
        self._controller = controller
        self._fonts = fonts
        self._ignored_rows = None
        self._alias_rows = None
        self._build()

    def _build(self):
        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=40, pady=(28, 20))

        tk.Label(hdr, text="PERSONER", bg=BG, fg=DIM,
                 font=self._fonts["eyebrow"]).pack(anchor="w")
        tk.Label(hdr, text="Personer", bg=BG, fg=TEXT,
                 font=self._fonts["display_m"]).pack(anchor="w", pady=(4, 0))

        tk.Frame(self, bg=LINE, height=1).pack(fill="x", padx=40)

        # ── Body ──────────────────────────────────────────────────────────────
        body = tk.Frame(self, bg=BG)
        body.pack(fill="x", padx=40, pady=20)

        # ── Udelad bestemte personer ─────────────────────────────────────────
        tk.Label(body, text="Udelad bestemte personer", bg=BG, fg=TEXT,
                 font=self._fonts["body_b"]).pack(anchor="w")
        tk.Label(body,
                 text="Personer på listen bliver aldrig sendt med til Aula.",
                 bg=BG, fg=FAINT, font=self._fonts["small"],
                 wraplength=560, justify="left",
                 ).pack(anchor="w", pady=(2, 8))

        ignored_scroll = ScrollableFrame(body, height=180, bg=PANEL,
                                        highlightthickness=1, highlightbackground=LINE)
        ignored_scroll.pack(fill="x")
        self._ignored_rows = ignored_scroll.inner

        PrimaryButton(body, text="+ Tilføj navn",
                      command=self._on_add_ignored,
                      fonts=self._fonts).pack(anchor="w", pady=(8, 0))

        tk.Frame(body, bg=LINE, height=1).pack(fill="x", pady=(20, 20))

        # ── Personers alias ──────────────────────────────────────────────────
        tk.Label(body, text="Ret et navn, hvis det er forskelligt i Aula", bg=BG, fg=TEXT,
                 font=self._fonts["body_b"]).pack(anchor="w")
        tk.Label(body,
                 text=("Outlook-navnet er som personen hedder i Outlook, "
                       "AULA-navnet er det navn personen skal vises med i Aula."),
                 bg=BG, fg=FAINT, font=self._fonts["small"],
                 wraplength=560, justify="left",
                 ).pack(anchor="w", pady=(2, 8))

        alias_scroll = ScrollableFrame(body, height=180, bg=PANEL,
                                       highlightthickness=1, highlightbackground=LINE)
        alias_scroll.pack(fill="x")
        self._alias_rows = alias_scroll.inner

        PrimaryButton(body, text="+ Tilføj alias",
                      command=self._on_add_alias,
                      fonts=self._fonts).pack(anchor="w", pady=(8, 0))

        tk.Frame(body, bg=LINE, height=1).pack(fill="x", pady=(20, 20))

        # ── Avanceret: redigér direkte i Excel ───────────────────────────────
        tk.Label(body, text="Avanceret: redigér direkte i Excel", bg=BG, fg=DIM,
                 font=self._fonts["eyebrow"]).pack(anchor="w", pady=(0, 8))

        btn_row = tk.Frame(body, bg=BG)
        btn_row.pack(anchor="w")
        SecondaryButton(btn_row, text="Ignorer personer",
                        command=self._controller.on_actionIgnore_people_list_triggered,
                        fonts=self._fonts).pack(side="left", padx=(0, 8))
        SecondaryButton(btn_row, text="Personers alias",
                        command=self._controller.on_actionOutlook_Aulanavne_liste_triggered,
                        fonts=self._fonts).pack(side="left")

        self._refresh_ignored_list()
        self._refresh_alias_list()

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

    def _on_add_ignored(self):
        values = self._prompt_fields("Tilføj person til udeladelse", ["Outlook-navn"])
        if not values or not values[0]:
            return
        from peoplecsvmanager import PeopleCsvManager
        PeopleCsvManager().add_ignored_person(values[0])
        self._refresh_ignored_list()

    def _on_remove_ignored(self, name):
        from peoplecsvmanager import PeopleCsvManager
        PeopleCsvManager().remove_ignored_person(name)
        self._refresh_ignored_list()

    def _on_add_alias(self):
        values = self._prompt_fields("Tilføj alias", ["Outlook-navn", "AULA-navn"])
        if not values or not values[0] or not values[1]:
            return
        from peoplecsvmanager import PeopleCsvManager
        PeopleCsvManager().add_alias(values[0], values[1])
        self._refresh_alias_list()

    def _on_remove_alias(self, outlook_name):
        from peoplecsvmanager import PeopleCsvManager
        PeopleCsvManager().remove_alias(outlook_name)
        self._refresh_alias_list()

    # ── Lille inputdialog ─────────────────────────────────────────────────────

    def _prompt_fields(self, title, labels):
        """Modal dialog med et Entry-felt per label. Returnerer listen af
        indtastede (strippede) værdier, eller None hvis annulleret."""
        parent = self.winfo_toplevel()
        dlg = tk.Toplevel(parent)
        dlg.title(title)
        dlg.configure(bg=PANEL)
        dlg.transient(parent)
        dlg.grab_set()
        dlg.resizable(False, False)

        tk.Label(dlg, text=title, bg=PANEL, fg=TEXT,
                 font=self._fonts["display_s"]).pack(anchor="w", padx=22, pady=(20, 12))

        grid = tk.Frame(dlg, bg=PANEL)
        grid.pack(padx=22)
        entries = []
        for i, label in enumerate(labels):
            tk.Label(grid, text=label, bg=PANEL, fg=TEXT,
                     font=self._fonts["body_b"]).grid(row=i, column=0, sticky="w", pady=4)
            ent = tk.Entry(grid, width=28, relief="solid", borderwidth=1)
            ent.grid(row=i, column=1, padx=(12, 0), pady=4, ipady=3)
            entries.append(ent)
        entries[0].focus_set()

        tk.Frame(dlg, bg=LINE, height=1).pack(fill="x", pady=(16, 0))
        btn_row = tk.Frame(dlg, bg=SUBTLE)
        btn_row.pack(fill="x")

        result = {"values": None}

        def _ok():
            result["values"] = [e.get().strip() for e in entries]
            dlg.destroy()

        SecondaryButton(btn_row, text="Annullér", command=dlg.destroy,
                        fonts=self._fonts, pady=5).pack(side="right", padx=(0, 18), pady=14)
        PrimaryButton(btn_row, text="Gem", command=_ok,
                      fonts=self._fonts, pady=5).pack(side="right", padx=(0, 8), pady=14)
        dlg.bind("<Return>", lambda e: _ok())

        dlg.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - dlg.winfo_width())  // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - dlg.winfo_height()) // 2
        dlg.geometry(f"+{px}+{py}")

        dlg.wait_window()
        return result["values"]
