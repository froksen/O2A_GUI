# -*- coding: utf-8 -*-
# ui/widgets.py — Reusable widgets for O2A GUI
import tkinter as tk
from theme import (
    ACCENT, ACCENT_HOVER, ACCENT_TINT,
    BG, SIDE, PANEL, SUBTLE, LINE,
    TEXT, DIM, FAINT,
    OK, WARN, WARN_DARK, ERR,
)


def Card(parent, **kw) -> tk.Frame:
    """A white frame with a 1 px border — stand-in for box-shadow."""
    return tk.Frame(parent, bg=PANEL,
                    highlightthickness=1, highlightbackground=LINE,
                    **kw)


class SidebarButton(tk.Frame):
    """Navigation button in the left sidebar."""

    def __init__(self, parent, label, fonts, command):
        super().__init__(parent, bg=SIDE)
        self._command = command
        self._active = False
        self.config(cursor="hand2")

        self._inner = tk.Frame(self, bg=SIDE)
        self._inner.pack(fill="x", padx=0, pady=0)
        self._label = tk.Label(self._inner, text=label, bg=SIDE, fg=DIM,
                               font=fonts["body"], anchor="w", padx=12, pady=7)
        self._label.pack(fill="x")

        for w in (self, self._inner, self._label):
            w.bind("<Button-1>",  lambda e: self._command())
            w.bind("<Enter>",     lambda e: self._on_hover(True))
            w.bind("<Leave>",     lambda e: self._on_hover(False))

    def _on_hover(self, hover):
        if self._active:
            return
        bg = "#E3DFD6" if hover else SIDE
        self._inner.config(bg=bg)
        self._label.config(bg=bg)

    def set_active(self, on):
        self._active = on
        if on:
            self._inner.config(bg=PANEL,
                               highlightthickness=1, highlightbackground=LINE)
            self._label.config(bg=PANEL, fg=TEXT)
        else:
            self._inner.config(bg=SIDE, highlightthickness=0)
            self._label.config(bg=SIDE, fg=DIM)


class SplitButton(tk.Frame):
    """Primary sync button + chevron that opens a menu with 'Force' option."""

    def __init__(self, parent, fonts, on_normal, on_force):
        super().__init__(parent, bg=BG)
        self._fonts = fonts
        self._on_normal = on_normal
        self._on_force  = on_force
        self._busy = False

        self.main = tk.Button(
            self, text="Synkronisér nu", command=self._click_main,
            bg=ACCENT, fg="white", activebackground=ACCENT_HOVER,
            activeforeground="white",
            font=fonts["body"], relief="flat", borderwidth=0,
            padx=14, pady=6, cursor="hand2",
        )
        self.main.pack(side="left")

        self.chev = tk.Button(
            self, text="▾", command=self._open_menu,
            bg=ACCENT, fg="white", activebackground=ACCENT_HOVER,
            activeforeground="white",
            font=fonts["small"], relief="flat", borderwidth=0,
            padx=8, pady=6, cursor="hand2",
        )
        self.chev.pack(side="left", padx=(1, 0))   # 1 px gap = separator

        self.menu = tk.Menu(self, tearoff=0,
                            bg=PANEL, fg=TEXT,
                            activebackground=ACCENT_TINT, activeforeground=TEXT,
                            relief="flat", borderwidth=1,
                            font=fonts["body"])
        self.menu.add_command(label="  Synkronisér nu        Ctrl+R",
                              command=self._click_main)
        self.menu.add_separator()
        self.menu.add_command(label="  Tving fuld synkronisering   Ctrl+Shift+R",
                              command=self._click_force)

    def _click_main(self):
        if self._busy:
            return
        self._on_normal()

    def _click_force(self):
        if self._busy:
            return
        from ui.dialogs.force_confirm import ForceConfirmDialog
        ForceConfirmDialog(self.winfo_toplevel(), self._fonts, self._on_force)

    def _open_menu(self):
        x = self.chev.winfo_rootx()
        y = self.chev.winfo_rooty() + self.chev.winfo_height() + 4
        self.menu.tk_popup(x, y)

    def set_busy(self, busy, force=False):
        self._busy = busy
        text = ("Tvinger fuld kørsel …" if force else "Synkroniserer …") if busy else "Synkronisér nu"
        bg   = "#CFD6D2" if busy else ACCENT
        self.main.config(text=text, bg=bg, state="disabled" if busy else "normal")
        self.chev.config(bg=bg, state="disabled" if busy else "normal")


class UnderlineTabs(tk.Frame):
    """Custom tab bar with underline indicator — avoids ttk.Notebook styling issues."""

    def __init__(self, parent, fonts, tabs, on_change):
        """tabs = [(id, label, count), ...]"""
        super().__init__(parent, bg=BG)
        self._fonts = fonts
        self._buttons = {}
        self._active = tabs[0][0]
        self._on_change = on_change

        row = tk.Frame(self, bg=BG)
        row.pack(fill="x")

        for tab_id, label, count in tabs:
            btn = tk.Frame(row, bg=BG, cursor="hand2")
            btn.pack(side="left", padx=(0, 20))
            lbl = tk.Label(btn, text=label, bg=BG, fg=DIM, font=fonts["body"])
            lbl.pack(side="left", pady=(8, 10))
            cnt = tk.Label(btn, text=str(count), bg="#F0EEE7", fg=FAINT,
                           font=fonts["small"], padx=6, pady=0)
            cnt.pack(side="left", padx=(6, 0), pady=(8, 10))
            underline = tk.Frame(btn, bg=BG, height=2)
            underline.pack(side="bottom", fill="x")
            self._buttons[tab_id] = (btn, lbl, cnt, underline)
            for w in (btn, lbl, cnt):
                w.bind("<Button-1>", lambda e, t=tab_id: self._select(t))

        tk.Frame(self, bg=LINE, height=1).pack(fill="x")
        self._select(self._active)

    def _select(self, tab_id):
        self._active = tab_id
        for tid, (btn, lbl, cnt, ul) in self._buttons.items():
            if tid == tab_id:
                lbl.config(fg=TEXT)
                ul.config(bg=ACCENT)
            else:
                lbl.config(fg=DIM)
                ul.config(bg=BG)
        self._on_change(tab_id)


class ConnChip(tk.Frame):
    """Small connection-status indicator shown at the bottom of the sidebar."""

    def __init__(self, parent, fonts):
        super().__init__(parent, bg=SIDE)

        dot = tk.Canvas(self, width=8, height=8, bg=SIDE, highlightthickness=0)
        dot.create_oval(0, 0, 8, 8, fill=OK, outline="")
        dot.pack(side="left", padx=(0, 6), pady=2)

        tk.Label(self, text="Online", bg=SIDE, fg=DIM,
                 font=fonts["small"]).pack(side="left")
