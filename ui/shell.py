# -*- coding: utf-8 -*-
# ui/shell.py — Two-column shell: sidebar + content stack
import tkinter as tk
from theme import (
    BG, SIDE, PANEL, LINE, TEXT, DIM, ACCENT,
    SIDEBAR_W, WINDOW_W, WINDOW_H,
    fonts,
)
from ui.widgets import SidebarButton, ConnChip


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

        title = ("Outlook2Aula [DRY-RUN — ingen ændringer gemmes]"
                 if getattr(self.controller, '_dry_run', False)
                 else "Outlook2Aula")
        self.root.title(title)

        # Two-column grid
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        self.sidebar = self._make_sidebar()
        self.sidebar.grid(row=0, column=0, sticky="ns")

        self.content = tk.Frame(self.root, bg=BG)
        self.content.grid(row=0, column=1, sticky="nsew")

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
        for nav_id, label in [
            ("status",   "Status"),
            ("konto",    "Konto"),
            ("personer", "Personer"),
            ("logfil",   "Logfil"),
            ("opsaet",   "Indstillinger"),
        ]:
            btn = SidebarButton(f, label, self.fonts,
                                command=lambda i=nav_id: self._show(i))
            btn.pack(fill="x", padx=8, pady=1)
            self._nav_buttons[nav_id] = btn

        # Spacer
        tk.Frame(f, bg=SIDE).pack(fill="both", expand=True)

        # Connection chip
        ConnChip(f, self.fonts).pack(fill="x", padx=12, pady=12)
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
        from ui.status_view   import StatusView
        from ui.konto_view    import KontoView
        from ui.personer_view import PersonerView
        from ui.logfil_view   import LogfilView
        from ui.settings_view import SettingsView
        return {
            "status":   StatusView(self.content, self.controller, self.fonts),
            "konto":    KontoView(self.content, self.controller, self.fonts),
            "personer": PersonerView(self.content, self.controller, self.fonts),
            "logfil":   LogfilView(self.content, self.controller, self.fonts),
            "opsaet":   SettingsView(self.content, self.controller, self.fonts),
        }[nav_id]
