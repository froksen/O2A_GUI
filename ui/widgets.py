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


class PrimaryButton(tk.Button):
    """Solid, colour-filled call-to-action button. Defaults to the accent
    green; pass bg/hover (e.g. ERR/ERR_HOVER or WARN_DARK/WARN_HOVER from
    theme.py) for a danger or warning variant."""

    def __init__(self, parent, text, command, fonts, bg=ACCENT, hover=ACCENT_HOVER, **kw):
        opts = dict(
            bg=bg, fg="white", activebackground=hover, activeforeground="white",
            font=fonts["body"], relief="flat", borderwidth=0,
            padx=14, pady=6, cursor="hand2",
        )
        opts.update(kw)
        super().__init__(parent, text=text, command=command, **opts)


class SecondaryButton(tk.Button):
    """White, thin-bordered button for neutral/secondary actions
    (Annullér, Luk, Eksportér…)."""

    def __init__(self, parent, text, command, fonts, **kw):
        opts = dict(
            bg=PANEL, fg=TEXT, activebackground=SUBTLE,
            font=fonts["body"], relief="solid", borderwidth=1,
            padx=14, pady=6, cursor="hand2",
        )
        opts.update(kw)
        super().__init__(parent, text=text, command=command, **opts)


class SidebarButton(tk.Frame):
    """Navigation button in the left sidebar."""

    def __init__(self, parent, label, fonts, command, icon=""):
        super().__init__(parent, bg=SIDE)
        self._command = command
        self._active = False
        self.config(cursor="hand2")

        self._inner = tk.Frame(self, bg=SIDE)
        self._inner.pack(fill="x", padx=0, pady=0)
        text = f"{icon}  {label}" if icon else label
        self._label = tk.Label(self._inner, text=text, bg=SIDE, fg=DIM,
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

    def update_count(self, tab_id: str, count: int):
        """Update the badge count shown next to a tab label."""
        if tab_id in self._buttons:
            self._buttons[tab_id][2].config(text=str(count))


class VersionLabel(tk.Frame):
    """Version info shown at the bottom of the sidebar."""

    def __init__(self, parent, fonts):
        super().__init__(parent, bg=SIDE)
        version_text = self._get_version()
        if version_text:
            tk.Label(self, text=f"v {version_text}", bg=SIDE, fg=DIM,
                     font=fonts["small"]).pack(side="left")

    @staticmethod
    def _get_version():
        from pathlib import Path
        import datetime as dt
        base_dir = Path(__file__).resolve().parent.parent
        try:
            import git
            repo = git.Repo(base_dir, search_parent_directories=True)
            commit_dt = dt.datetime.fromtimestamp(repo.head.commit.committed_date)
            return commit_dt.strftime('%d-%m-%Y %H:%M')
        except Exception:
            version_file = base_dir / "version.txt"
            if version_file.is_file():
                return version_file.read_text(encoding="utf-8").strip() or None
            return None


class ScrollableFrame(tk.Frame):
    """A fixed-height, vertically scrollable container. Add rows as children
    of `.inner` — the scrollbar and mouse-wheel support are handled
    automatically as content grows past `height`."""

    def __init__(self, parent, height=200, bg=PANEL, **kw):
        super().__init__(parent, bg=bg, **kw)

        self._canvas = tk.Canvas(self, bg=bg, highlightthickness=0, height=height)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scrollbar.set)

        self._canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.inner = tk.Frame(self._canvas, bg=bg)
        self._window = self._canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.inner.bind("<Configure>", self._on_inner_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind("<Enter>", self._bind_mousewheel)
        self._canvas.bind("<Leave>", self._unbind_mousewheel)

    def _on_inner_configure(self, _event):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._canvas.itemconfig(self._window, width=event.width)

    def _bind_mousewheel(self, _event=None):
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, _event=None):
        self._canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


def prompt_fields(parent_widget, fonts, title, labels):
    """Modal dialog with one Entry per label, anchored above the toplevel
    that owns `parent_widget`. Returns the list of entered (stripped)
    values, or None if cancelled."""
    parent = parent_widget.winfo_toplevel()
    dlg = tk.Toplevel(parent)
    dlg.title(title)
    dlg.configure(bg=PANEL)
    dlg.transient(parent)
    dlg.grab_set()
    dlg.resizable(False, False)

    tk.Label(dlg, text=title, bg=PANEL, fg=TEXT,
             font=fonts["display_s"]).pack(anchor="w", padx=22, pady=(20, 12))

    grid = tk.Frame(dlg, bg=PANEL)
    grid.pack(padx=22)
    entries = []
    for i, label in enumerate(labels):
        tk.Label(grid, text=label, bg=PANEL, fg=TEXT,
                 font=fonts["body_b"]).grid(row=i, column=0, sticky="w", pady=4)
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
                    fonts=fonts, pady=5).pack(side="right", padx=(0, 18), pady=14)
    PrimaryButton(btn_row, text="Gem", command=_ok,
                  fonts=fonts, pady=5).pack(side="right", padx=(0, 8), pady=14)
    dlg.bind("<Return>", lambda e: _ok())

    dlg.update_idletasks()
    px = parent.winfo_rootx() + (parent.winfo_width()  - dlg.winfo_width())  // 2
    py = parent.winfo_rooty() + (parent.winfo_height() - dlg.winfo_height()) // 2
    dlg.geometry(f"+{px}+{py}")

    dlg.wait_window()
    return result["values"]
