# -*- coding: utf-8 -*-
# ui/shell.py — Two-column shell: sidebar + content stack
import tkinter as tk
from theme import (
    BG, SIDE, PANEL, LINE, TEXT, DIM, ACCENT,
    SIDEBAR_W, WINDOW_W, WINDOW_H,
    fonts,
)
from ui.widgets import SidebarButton, VersionLabel, ScrollableFrame
import gitinfo


class Shell:
    def __init__(self, root: tk.Tk, controller):
        self.root = root
        self.controller = controller
        self.fonts = fonts(root)
        self._build()

    def _build(self):
        self.root.configure(bg=BG)
        self.root.geometry(f"{WINDOW_W}x{WINDOW_H}")
        self.root.minsize(900, 600)

        branch = gitinfo.get_branch_name()
        is_dev = gitinfo.is_non_master_branch()

        title = "Outlook2Aula"
        if is_dev:
            title += f" — DEV ({branch})"
        if getattr(self.controller, '_dry_run', False):
            title += " (testtilstand — intet bliver gemt)"
        self.root.title(title)

        # Two-column grid — banneret (hvis relevant) i row 0 på tværs af
        # begge kolonner, sidebar+indhold i row 1. Sidder på Shell (ikke i
        # den enkelte side), så det er synligt uanset hvilken side vises.
        self.root.grid_columnconfigure(1, weight=1)

        content_row = 0
        if is_dev:
            dev_banner = tk.Frame(self.root, bg="#E8DEF8")
            dev_banner.grid(row=0, column=0, columnspan=2, sticky="ew")
            tk.Label(dev_banner,
                     text=f"⎇ Udviklerversion — kører fra branch \"{branch}\" (ikke master).",
                     bg="#E8DEF8", fg="#4A148C",
                     font=self.fonts["body_b"],
                     pady=6).pack()
            content_row = 1

        self.root.grid_rowconfigure(content_row, weight=1)

        self.sidebar = self._make_sidebar()
        self.sidebar.grid(row=content_row, column=0, sticky="ns")

        # Content-området pakkes i en ScrollableFrame, så enhver side der
        # fylder mere end vinduets højde bliver scrollbar i stedet for at
        # blive klippet af (se ui/widgets.py). self.content peger på selve
        # den scrollbare indre frame, så _build_view()/_show() er uændrede.
        self._content_scroll = ScrollableFrame(self.root, bg=BG)
        self._content_scroll.grid(row=content_row, column=1, sticky="nsew")
        self.content = self._content_scroll.inner

        # Views — instantiated lazily; kept alive so switching is instant
        self.views = {}
        self._show("status")

    def _make_sidebar(self):
        f = tk.Frame(self.root, bg=SIDE, width=SIDEBAR_W)
        f.grid_propagate(False)
        f.pack_propagate(False)

        # Wordmark
        wm = tk.Frame(f, bg=SIDE)
        wm.pack(fill="x", padx=12, pady=(18, 18))
        tk.Label(wm, text="Outlook", bg=SIDE, fg=TEXT,
                 font=self.fonts["display_s"]).pack(side="left")
        tk.Label(wm, text="2", bg=SIDE, fg=ACCENT,
                 font=self.fonts["display_s"]).pack(side="left")
        tk.Label(wm, text="Aula", bg=SIDE, fg=TEXT,
                 font=self.fonts["display_s"]).pack(side="left")

        # Nav
        self._nav_buttons = {}
        for nav_id, label, icon in [
            ("status",                   "Status",                   "▣"),
            ("konto",                    "Konto",                    "⚿"),
            ("opstartsadfaerd",          "Opstartsadfærd",           "⚙"),
            ("synkroniseringsadfaerd",   "Synkroniseringsadfærd",    "⇄"),
            ("notifikationer",           "Notifikationer",           "❢"),
            ("personer_ignorer",         "Udelad personer",          "⊘"),
            ("personer_alias",           "Personers alias",          "☺"),
            ("logfil",                   "Logfil",                   "▤"),
            ("advanceret",               "Avanceret",                "⚒"),
            ("opdater",                  "Opdatering",                "↻"),
        ]:
            btn = SidebarButton(f, label, self.fonts,
                                command=lambda i=nav_id: self._show(i),
                                icon=icon)
            btn.pack(fill="x", padx=8, pady=1)
            self._nav_buttons[nav_id] = btn

        # Spacer
        tk.Frame(f, bg=SIDE).pack(fill="both", expand=True)

        # Version info
        VersionLabel(f, self.fonts).pack(fill="x", padx=12, pady=12)
        return f

    def _show(self, nav_id):
        # Update active state on sidebar buttons
        for k, b in self._nav_buttons.items():
            b.set_active(k == nav_id)

        # Unmount all current children
        for child in self.content.winfo_children():
            child.pack_forget()

        # Build view on first visit
        if nav_id not in self.views:
            self.views[nav_id] = self._build_view(nav_id)

        self.views[nav_id].pack(fill="both", expand=True)

    def _build_view(self, nav_id):
        # NB: importer og bygger KUN den efterspurgte view — views cachet i
        # self.views (se _show) skal ikke genopbygges, og views der aldrig
        # besøges skal aldrig bygges. Et tidligere dict-literal her byggede
        # alle ti views ved hvert førstebesøg (kun for at kassere ni af dem),
        # hvilket bl.a. udløste unødvendige keyring-opslag via KontoView.
        if nav_id == "status":
            from ui.status_view import StatusView
            return StatusView(self.content, self.controller, self.fonts)
        if nav_id == "konto":
            from ui.konto_view import KontoView
            return KontoView(self.content, self.controller, self.fonts)
        if nav_id == "opstartsadfaerd":
            from ui.opstartsadfaerd_view import OpstartsadfaerdView
            return OpstartsadfaerdView(self.content, self.controller, self.fonts)
        if nav_id == "synkroniseringsadfaerd":
            from ui.synkroniseringsadfaerd_view import SynkroniseringsadfaerdView
            return SynkroniseringsadfaerdView(self.content, self.controller, self.fonts)
        if nav_id == "notifikationer":
            from ui.notifikationer_view import NotifikationerView
            return NotifikationerView(self.content, self.controller, self.fonts)
        if nav_id == "personer_ignorer":
            from ui.personer_ignorer_view import PersonerIgnorerView
            return PersonerIgnorerView(self.content, self.controller, self.fonts)
        if nav_id == "personer_alias":
            from ui.personer_alias_view import PersonerAliasView
            return PersonerAliasView(self.content, self.controller, self.fonts)
        if nav_id == "logfil":
            from ui.logfil_view import LogfilView
            return LogfilView(self.content, self.controller, self.fonts)
        if nav_id == "advanceret":
            from ui.advanceret_view import AdvanceretView
            return AdvanceretView(self.content, self.controller, self.fonts)
        if nav_id == "opdater":
            from ui.opdater_view import OpdaterView
            return OpdaterView(self.content, self.controller, self.fonts)
        raise KeyError(f"Ukendt nav_id: {nav_id!r}")
