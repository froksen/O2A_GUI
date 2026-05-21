# O2A — Tkinter Handoff for Claude Code

> **Audience:** Claude Code, implementing Direction A "Stille" on top of the existing `mainwindow.py` (Tkinter).
> **Goal:** Port the HTML mock-up to working Tkinter widgets without rewriting the sync engine.
> **Non-goal:** Pixel-perfect Win11 Mica. Tkinter cannot do acrylic/mica; this doc explains what to substitute.

---

## 0 · Read these first

Before touching anything, read:

1. `mainwindow.py` — the current Tkinter UI. The sync engine (`update_calendar`, `__create_aula_events`, `__update_aula_events`, `__delete_aula_events`) is **already wired** and must be kept. We're rebuilding the *shell* around it.
2. `unilogindialog.py` — current login dialog. We replace it.
3. `O2A - Stille.html` (this project) — the design mock. Open it in a browser to see the target.

The two methods on `MainWindow` you must keep calling exactly as today:

```python
self.on_runO2A_clicked()        # normal sync — already exists
self.on_forcerunO2A_clicked()   # force sync — already exists, just expose it in UI
```

These spin up `threading.Thread(...).start()` against `_run_sync(force_update)`. **Don't change that flow.**

---

## 1 · What Tkinter can and cannot do

| Mock feature | Tkinter answer |
|---|---|
| Soft warm bg (`#F6F5F1`) | ✅ Just set `bg=` everywhere |
| Sidebar with active-row card | ✅ `tk.Frame` per row, change `bg` on hover/active |
| Serif headlines + sans body | ✅ `tkfont.Font(family="Georgia", size=24)` |
| Underline-style tabs | ⚠️ Custom — `ttk.Notebook` is hard to restyle. Build tabs from `tk.Button` + a 2 px frame separator. |
| Summary tiles (5 columns) | ✅ `tk.Frame` in a grid |
| Status feed (event rows) | ✅ Rows of `tk.Frame`. Or `ttk.Treeview` if you accept its native look. |
| Log view with colored levels | ✅ `tk.Text` with tags (already used today) |
| **Logfil debug view** | ✅ `tk.Text` + filter via `tag_config(elide=True)` |
| **Split button** (sync + dropdown) | ✅ Two adjacent `tk.Button`s; second pops a `tk.Menu` |
| **Force-sync confirm** | ✅ `tk.Toplevel` modal with custom layout |
| First-run wizard | ✅ `tk.Toplevel` with a Frame-per-step + Back/Next |
| Tray menu | ✅ Keep your existing `pystray`/`infi.systray` (whichever is in main.pyw); only the **menu items** change |
| Rounded corners | ❌ Tkinter has no native radius. Don't fake them with images — accept square corners as the platform reality. |
| Mica / acrylic | ❌ Impossible in pure Tkinter. Skip. |
| Drop-shadows | ❌ Skip. Use a 1 px border instead (`highlightthickness=1`, `highlightbackground=LINE`). |
| Smooth font rendering on Windows | ⚠️ Use Segoe UI Variable if installed (Win11), else Segoe UI. Tk respects ClearType. |

---

## 2 · Theme module

Create `theme.py`. Single source of truth — every widget reads from here.

```python
# theme.py
"""O2A — design tokens. Mirrors O2A - Stille.html / O2A - Qt Handoff.html."""

# ── Colors ────────────────────────────────────────────────────────────
ACCENT      = "#3A5A44"   # primary CTA, focus, links
ACCENT_HOVER= "#325039"
ACCENT_DOWN = "#2A4530"
ACCENT_TINT = "#E8EEEA"   # rgba(#3a5a44, .08) flattened on white

BG          = "#F6F5F1"   # window background
SIDE        = "#ECEAE3"   # sidebar
PANEL       = "#FFFFFF"   # cards, content
SUBTLE      = "#FBFAF6"   # toolbar bands, table headers, hover
LINE        = "#E3E0D8"   # 1 px borders
HARD        = "#DCD6C7"   # button borders

TEXT        = "#1A1A1A"
DIM         = "#74726B"
FAINT       = "#9C9A92"

OK          = "#1F8A5B"
WARN        = "#C98F1C"
WARN_DARK   = "#A87513"   # warn button bg
ERR         = "#C4452B"

# Status-dot colors (status feed + log)
STATUS_COLORS = {
    "created":   OK,
    "updated":   "#5B6CFF",
    "deleted":   "#9B9B9B",
    "unchanged": "#CFCFCF",
    "error":     ERR,
    "ok":        OK,
    "info":      "#5B6CFF",
    "warn":      WARN,
    "err":       ERR,
    "debug":     "#7A7A7A",
    "dim":       FAINT,
}

# ── Fonts (lazy — created inside Tk after root exists) ────────────────
def fonts(root):
    from tkinter import font as tkfont
    return {
        # display / headlines — serif
        "display_l":  tkfont.Font(root=root, family="Georgia", size=24, weight="normal"),
        "display_m":  tkfont.Font(root=root, family="Georgia", size=20, weight="normal"),
        "display_s":  tkfont.Font(root=root, family="Georgia", size=15, weight="normal"),
        "display_num":tkfont.Font(root=root, family="Georgia", size=22, weight="normal"),
        # body — sans
        "body":       tkfont.Font(root=root, family="Segoe UI", size=10),
        "body_b":     tkfont.Font(root=root, family="Segoe UI", size=10, weight="bold"),
        "small":      tkfont.Font(root=root, family="Segoe UI", size=9),
        "eyebrow":    tkfont.Font(root=root, family="Segoe UI", size=8, weight="bold"),
        "kbd":        tkfont.Font(root=root, family="Segoe UI", size=8),
        # mono
        "mono":       tkfont.Font(root=root, family="Cascadia Code", size=9),
        "mono_sm":    tkfont.Font(root=root, family="Cascadia Code", size=8),
    }

# ── Spacing ───────────────────────────────────────────────────────────
PAD_CONTENT = (28, 40)   # (vertical, horizontal)
SIDEBAR_W   = 200
WINDOW_W    = 1100
WINDOW_H    = 720
```

Note: `Georgia` is the safe serif choice — `Iowan Old Style` from the design doesn't ship with Windows. Iowan looks better; Georgia is *fine* and universally present.

---

## 3 · File layout

Restructure to keep the file count manageable but not silly:

```
mainwindow.py        ← orchestrator + sync logic (mostly preserved)
theme.py             ← tokens + font factory
ui/
  __init__.py
  shell.py           ← MainWindow shell (sidebar + content stack)
  status_view.py     ← Status view
  konto_view.py      ← Konto view
  personer_view.py   ← Personer view
  logfil_view.py     ← Logfil debug view  ★ new
  settings_view.py   ← Indstillinger view
  widgets.py         ← reusable: SidebarButton, SplitButton, Toggle, Card, ToolBtn, …
  dialogs/
    unilogin.py      ← Uni-login dialog
    force_confirm.py ← Force-sync confirm   ★ new
    wizard.py        ← First-run wizard     ★ new
```

Don't create files that aren't needed yet. If a view is 80 lines, fine — inline it in `shell.py` until it grows. The structure above is a target, not a prerequisite.

---

## 4 · Shell structure

The mock has a fixed two-column layout: **sidebar (200 px) | content (rest)**. Use `grid()` (not `pack()`) for the top split — it keeps the sidebar from collapsing.

```python
# ui/shell.py
import tkinter as tk
from theme import *

class Shell:
    def __init__(self, root: tk.Tk, controller):
        self.root = root
        self.controller = controller   # MainWindow with sync methods
        self.fonts = fonts(root)
        self._build()

    def _build(self):
        self.root.configure(bg=BG)
        self.root.geometry(f"{WINDOW_W}x{WINDOW_H}")
        self.root.minsize(900, 600)
        self.root.title("Outlook2Aula")

        # Two-column grid
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        self.sidebar = self._make_sidebar()
        self.sidebar.grid(row=0, column=0, sticky="ns")

        self.content = tk.Frame(self.root, bg=BG)
        self.content.grid(row=0, column=1, sticky="nsew")

        # Views — instantiated lazily but kept around so switching is instant.
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
        tk.Label(wm, text="2",   bg=SIDE, fg=ACCENT,
                 font=self.fonts["display_s"]).pack(side="left")
        tk.Label(wm, text="Aula",bg=SIDE, fg=TEXT,
                 font=self.fonts["display_s"]).pack(side="left")

        # Nav
        self._nav_buttons = {}
        for nav_id, label in [
            ("status",   "Status"),
            ("konto",    "Konto"),
            ("personer", "Personer"),
            ("logfil",   "Logfil"),     # ★ new
            ("opsaet",   "Indstillinger"),
        ]:
            btn = SidebarButton(f, label, self.fonts, command=lambda i=nav_id: self._show(i))
            btn.pack(fill="x", padx=8, pady=1)
            self._nav_buttons[nav_id] = btn

        # Spacer
        tk.Frame(f, bg=SIDE).pack(fill="both", expand=True)

        # Connection chip — see widgets.py
        ConnChip(f, self.fonts).pack(fill="x", padx=12, pady=12)
        return f

    def _show(self, nav_id):
        # active state on sidebar
        for k, b in self._nav_buttons.items():
            b.set_active(k == nav_id)
        # mount the view
        for child in self.content.winfo_children():
            child.pack_forget()
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
```

### Wire `MainWindow` to `Shell`

In `mainwindow.py`, replace `_build_ui()` with:

```python
def _build_ui(self):
    from ui.shell import Shell
    self.shell = Shell(self.root, controller=self)
    # the shell pulls everything it needs off `self.controller`
```

Everything else in `MainWindow` (sync engine, `_run_sync`, `update_calendar`, timers, CSV setup) stays as-is. The shell calls into `self.controller.on_runO2A_clicked()` etc.

`MainWindow.update_status(text, record)` — the log-bridge — needs one tweak: also forward the record to the `LogfilView` model. See §7.

---

## 5 · Reusable widgets

`ui/widgets.py` — three are essential. Build them first.

### 5.1 — SidebarButton

```python
class SidebarButton(tk.Frame):
    def __init__(self, parent, label, fonts, command):
        super().__init__(parent, bg=SIDE)
        self._command = command
        self._active = False
        self.config(cursor="hand2")

        # Inner frame so we can change `bg` for hover/active without losing layout
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
        if self._active: return
        bg = "#E3DFD6" if hover else SIDE
        self._inner.config(bg=bg); self._label.config(bg=bg)

    def set_active(self, on):
        self._active = on
        if on:
            self._inner.config(bg=PANEL,
                               highlightthickness=1, highlightbackground=LINE)
            self._label.config(bg=PANEL, fg=TEXT)
        else:
            self._inner.config(bg=SIDE, highlightthickness=0)
            self._label.config(bg=SIDE, fg=DIM)
```

### 5.2 — SplitButton (sync + force dropdown) ★

The single most important new widget. Two `tk.Button`s flush together; the small one pops a `tk.Menu`.

```python
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
        if self._busy: return
        self._on_normal()

    def _click_force(self):
        if self._busy: return
        self._on_force()

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
```

Wire this into `MainWindow.toggle_gui`:

```python
def toggle_gui(self, enabled: bool, force: bool = False):
    self.shell.views["status"].sync_btn.set_busy(not enabled, force=force)
    # (keep the old runFrequency disable if you still expose it)
```

And `on_forcerunO2A_clicked` already exists in `mainwindow.py` — wire the menu's force item to it via the controller. Don't duplicate the engine logic.

### 5.3 — Card

A frame with a 1 px border that stands in for box-shadow. Tkinter's `highlightthickness` is the trick.

```python
def Card(parent, **kw) -> tk.Frame:
    return tk.Frame(parent, bg=PANEL,
                    highlightthickness=1, highlightbackground=LINE,
                    **kw)
```

---

## 6 · Status view

Layout, top to bottom:

1. **Hero** — eyebrow line + serif title + sub + `SplitButton` (right)
2. **Summary tiles** — 5 `Card`s in a grid, each = eyebrow + serif number
3. **Tabs** — "Begivenheder" / "Log" (custom, see below)
4. **Tab content** — event feed or log

### Custom underline tabs

`ttk.Notebook` is impossible to restyle cleanly. Build your own:

```python
class UnderlineTabs(tk.Frame):
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
                lbl.config(fg=TEXT); ul.config(bg=ACCENT)
            else:
                lbl.config(fg=DIM);  ul.config(bg=BG)
        self._on_change(tab_id)
```

### Event row (no Treeview)

Tkinter's `ttk.Treeview` has limited styling. For the event feed, build rows as `Frame`s — it's only a handful per render.

```python
def make_event_row(parent, fonts, ev, on_open):
    row = tk.Frame(parent, bg=PANEL)
    row.pack(fill="x")

    # status pill
    pill = tk.Frame(row, bg=PANEL, width=110)
    pill.pack(side="left", padx=(0, 16), pady=12)
    pill.pack_propagate(False)
    dot = tk.Canvas(pill, width=8, height=8, bg=PANEL, highlightthickness=0)
    dot.create_oval(0, 0, 8, 8, fill=STATUS_COLORS[ev["status"]], outline="")
    dot.pack(side="left", padx=(0, 6), pady=(4, 0))
    tk.Label(pill, text=ev["status_label"], bg=PANEL,
             fg=STATUS_COLORS[ev["status"]], font=fonts["small"]
             ).pack(side="left")

    # title + meta
    body = tk.Frame(row, bg=PANEL)
    body.pack(side="left", fill="x", expand=True, pady=10)
    tk.Label(body, text=ev["title"], bg=PANEL, fg=TEXT,
             font=fonts["body_b"], anchor="w").pack(fill="x")
    tk.Label(body, text=ev["when"], bg=PANEL, fg=DIM,
             font=fonts["small"], anchor="w").pack(fill="x")

    # action
    tk.Button(row, text="Åbn i Aula", command=lambda: on_open(ev),
              bg=PANEL, fg=DIM, font=fonts["small"],
              relief="solid", borderwidth=1,
              activebackground=SUBTLE).pack(side="right", padx=8, pady=12)

    tk.Frame(parent, bg=LINE, height=1).pack(fill="x")
    return row
```

---

## 7 · Logfil view ★ (the important new piece)

This is the debugging tool. Treat it as the third deliverable after Status and SplitButton.

### Two-level model

A **`LogStore`** singleton holds every `LogRecord` since startup. The view re-renders from it whenever filters change. The current `MainWindow.update_status()` only writes formatted strings to the in-status Text widget — we need to **also** push records to the store.

```python
# ui/logfil_view.py
import tkinter as tk
import logging
from datetime import datetime
from theme import *

class LogStore:
    """Singleton: every record since startup. Filtered re-renders read from here."""
    _records: list[dict] = []
    _subscribers: list = []

    @classmethod
    def append(cls, record: logging.LogRecord):
        ts = datetime.fromtimestamp(record.created)
        cls._records.append({
            "date": ts.strftime("%Y-%m-%d"),
            "time": ts.strftime("%H:%M:%S"),
            "lvl":  {10:"debug", 20:"info", 30:"warn",
                     40:"err",   50:"err"}.get(record.levelno, "info"),
            "msg":  record.getMessage(),
        })
        for cb in cls._subscribers:
            try: cb(cls._records[-1])
            except Exception: pass

    @classmethod
    def subscribe(cls, cb):  cls._subscribers.append(cb)

    @classmethod
    def all(cls):            return list(cls._records)
```

In `mainwindow.py`'s log handler setup (wherever `logger.addHandler(...)` is called), add a second handler:

```python
class _StoreHandler(logging.Handler):
    def emit(self, record): LogStore.append(record)

logger.addHandler(_StoreHandler())
```

### The view

A single `tk.Text` widget is the right tool here — it's *built* for tagged, scrollable text. Use `tag_config(elide=True)` to filter without rebuilding.

```python
class LogfilView(tk.Frame):
    def __init__(self, parent, controller, fonts):
        super().__init__(parent, bg=BG)
        self._fonts = fonts
        self._levels = {"info":True, "ok":True, "warn":True, "err":True, "debug":True}
        self._query = ""
        self._follow = tk.BooleanVar(value=True)
        self._build()
        self._render_all()
        LogStore.subscribe(self._on_new_record)

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=40, pady=(28, 16))
        tk.Label(hdr, text="LOGFIL · %APPDATA%\\O2A\\o2a.log",
                 bg=BG, fg=DIM, font=self._fonts["eyebrow"]).pack(anchor="w")
        title_row = tk.Frame(hdr, bg=BG); title_row.pack(fill="x", pady=(6, 0))
        tk.Label(title_row, text="Alt output fra O2A",
                 bg=BG, fg=TEXT, font=self._fonts["display_m"]).pack(side="left")

        tools = tk.Frame(title_row, bg=BG); tools.pack(side="right")
        for label, cmd in [
            ("Kopiér",      self._copy_all),
            ("Åbn i Notesblok ↗", self._open_in_notepad),
            ("Eksportér .log",    self._export),
        ]:
            tk.Button(tools, text=label, command=cmd, font=self._fonts["small"],
                      bg=PANEL, fg=TEXT, relief="solid", borderwidth=1,
                      activebackground=SUBTLE,
                      padx=10, pady=2).pack(side="left", padx=3)

        tk.Label(self, text="Komplet rå-output fra alle kørsler. Brug filtrene og søgefeltet til at finde en bestemt fejl. Logfilen rouleres automatisk efter 14 dage.",
                 bg=BG, fg=DIM, font=self._fonts["small"], wraplength=640,
                 justify="left").pack(anchor="w", padx=40, pady=(8, 14))

        # Toolbar
        bar = tk.Frame(self, bg=SUBTLE, height=44)
        bar.pack(fill="x")
        tk.Frame(self, bg=LINE, height=1).pack(fill="x")  # bottom rule

        self._chips = {}
        chip_row = tk.Frame(bar, bg=SUBTLE)
        chip_row.pack(side="left", padx=40, pady=8)
        for lvl_id, lvl_label in [("info","Info"),("ok","OK"),
                                  ("warn","Advarsel"),("err","Fejl"),
                                  ("debug","Debug")]:
            chip = self._make_chip(chip_row, lvl_id, lvl_label)
            chip.pack(side="left", padx=2)
            self._chips[lvl_id] = chip

        # Search
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._on_search())
        ent = tk.Entry(bar, textvariable=self._search_var,
                       font=self._fonts["body"], bg=PANEL, fg=TEXT,
                       relief="solid", borderwidth=1)
        ent.pack(side="left", fill="x", expand=True, padx=8, pady=8, ipady=3)

        tk.Checkbutton(bar, text="Følg nyeste", variable=self._follow,
                       bg=SUBTLE, fg=DIM, activebackground=SUBTLE,
                       font=self._fonts["small"]).pack(side="left", padx=12)

        # Log text widget
        outer = tk.Frame(self, bg=SUBTLE)
        outer.pack(fill="both", expand=True)
        sb = tk.Scrollbar(outer); sb.pack(side="right", fill="y")
        self.txt = tk.Text(outer, bg=SUBTLE, fg=TEXT,
                          font=self._fonts["mono"],
                          relief="flat", borderwidth=0,
                          padx=40, pady=8, wrap="none",
                          yscrollcommand=sb.set, state="disabled",
                          cursor="arrow")
        self.txt.pack(side="left", fill="both", expand=True)
        sb.config(command=self.txt.yview)

        # Tags — one per level (color) + per level (elide on/off)
        for lvl_id in self._levels:
            self.txt.tag_configure(f"lvl_{lvl_id}",
                                    foreground=STATUS_COLORS[lvl_id])
            self.txt.tag_configure(f"elide_{lvl_id}", elide=False)
        self.txt.tag_configure("ts",       foreground=FAINT)
        self.txt.tag_configure("lvlcol",   foreground=FAINT,
                                font=self._fonts["mono_sm"])
        self.txt.tag_configure("run_hdr",  foreground=DIM,
                                font=self._fonts["eyebrow"],
                                spacing1=14, spacing3=6)
        self.txt.tag_configure("err_band", background="#FBEEEA",
                                lmargin1=32, lmargin2=32)
        self.txt.tag_configure("query_hit", background="#FFF2A8")

    def _make_chip(self, parent, lvl_id, label):
        c = tk.Frame(parent, bg=SUBTLE, cursor="hand2")
        dot = tk.Canvas(c, width=8, height=8, bg=SUBTLE, highlightthickness=0)
        dot.create_oval(0, 0, 8, 8, fill=STATUS_COLORS[lvl_id], outline="")
        dot.pack(side="left", padx=(8, 6), pady=4)
        lbl = tk.Label(c, text=label, bg=SUBTLE, fg=TEXT,
                       font=self._fonts["small"])
        lbl.pack(side="left", padx=(0, 8), pady=4)

        def toggle(_e=None):
            self._levels[lvl_id] = not self._levels[lvl_id]
            self._update_chip_appearance(c, lvl_id)
            self._refilter()
        for w in (c, dot, lbl):
            w.bind("<Button-1>", toggle)
        c._lbl, c._dot = lbl, dot
        self._update_chip_appearance(c, lvl_id)
        return c

    def _update_chip_appearance(self, chip, lvl_id):
        on = self._levels[lvl_id]
        bg = PANEL if on else SUBTLE
        fg = TEXT  if on else FAINT
        chip.config(bg=bg, highlightthickness=1,
                    highlightbackground=LINE if on else SUBTLE)
        chip._lbl.config(bg=bg, fg=fg)
        chip._dot.config(bg=bg)

    # ── Rendering ──────────────────────────────────────────────────────
    def _render_all(self):
        self.txt.config(state="normal")
        self.txt.delete("1.0", "end")
        last_hour_key = None
        for rec in LogStore.all():
            key = f"{rec['date']}@{rec['time'][:2]}"
            if key != last_hour_key:
                self.txt.insert("end",
                                f"\nKørsel · {rec['date']} kl. {rec['time'][:2]}:00\n",
                                "run_hdr")
                last_hour_key = key
            self._insert_line(rec)
        self.txt.config(state="disabled")
        self._refilter()
        if self._follow.get(): self.txt.see("end")

    def _insert_line(self, rec):
        start = self.txt.index("end-1c")
        self.txt.insert("end", f"{rec['time']}  ", ("ts",))
        self.txt.insert("end", f"{rec['lvl'].upper():5s}  ", ("lvlcol",))
        self.txt.insert("end", rec["msg"] + "\n",
                        (f"lvl_{rec['lvl']}", f"elide_{rec['lvl']}"))
        if rec["lvl"] == "err":
            self.txt.tag_add("err_band", start, "end-1c")

    def _on_new_record(self, rec):
        self.txt.config(state="normal")
        self._insert_line(rec)
        self.txt.config(state="disabled")
        if self._follow.get(): self.txt.see("end")

    def _refilter(self):
        # Hide/show whole levels via per-level elide tag
        for lvl_id, on in self._levels.items():
            self.txt.tag_configure(f"elide_{lvl_id}", elide=not on)
        # Highlight search hits (cheap — just remove + re-add)
        self.txt.tag_remove("query_hit", "1.0", "end")
        q = self._query
        if not q: return
        idx = "1.0"
        while True:
            idx = self.txt.search(q, idx, stopindex="end", nocase=True)
            if not idx: break
            end = f"{idx}+{len(q)}c"
            self.txt.tag_add("query_hit", idx, end)
            idx = end

    def _on_search(self):
        self._query = self._search_var.get().strip()
        self._refilter()

    # ── Tools ──────────────────────────────────────────────────────────
    def _copy_all(self):
        from tkinter import messagebox
        text = "\n".join(
            f"{r['date']} {r['time']}  {r['lvl'].upper():5s}  {r['msg']}"
            for r in LogStore.all()
        )
        self.clipboard_clear(); self.clipboard_append(text)
        messagebox.showinfo("Logfil", "Logfilen er kopieret til udklipsholderen.")

    def _open_in_notepad(self):
        import os
        path = os.path.expandvars(r"%APPDATA%\O2A\o2a.log")
        if os.path.exists(path):
            os.startfile(path)

    def _export(self):
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Log-fil", "*.log"), ("Tekstfil", "*.txt")])
        if not path: return
        with open(path, "w", encoding="utf-8") as f:
            for r in LogStore.all():
                f.write(f"{r['date']} {r['time']}  {r['lvl'].upper():5s}  {r['msg']}\n")
```

### Important: the existing log path

The current `mainwindow.py` already configures `logger = logging.getLogger('O2A')` and routes records through `update_status()`. You need **two** handlers from now on:

1. The existing one writing to the small `Status` log Text (keep it — it's a quick glance)
2. A new `_StoreHandler` feeding `LogStore` (the debug view)

Both handlers attach to the same `logger`. Don't move the existing log Text — it's the at-a-glance summary on the Status page. Logfil is the deep view.

### Persisting to disk

Add `logging.FileHandler` writing to `%APPDATA%\O2A\o2a.log` so the "Åbn i Notesblok" button finds something real. Use `RotatingFileHandler` with 14-day rotation.

```python
import logging, os
from logging.handlers import TimedRotatingFileHandler

log_dir = os.path.expandvars(r"%APPDATA%\O2A")
os.makedirs(log_dir, exist_ok=True)
fh = TimedRotatingFileHandler(
    os.path.join(log_dir, "o2a.log"),
    when="midnight", backupCount=14, encoding="utf-8")
fh.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-5s  %(message)s"))
logger.addHandler(fh)
```

---

## 8 · Force-sync confirm dialog

Custom `Toplevel`, not `messagebox` — we want the warm warn-color and explanation text.

```python
# ui/dialogs/force_confirm.py
import tkinter as tk
from theme import *

class ForceConfirmDialog:
    def __init__(self, parent, fonts, on_confirm):
        self.top = tk.Toplevel(parent)
        self.top.title("")
        self.top.configure(bg=PANEL)
        self.top.transient(parent)
        self.top.grab_set()
        self.top.resizable(False, False)

        # Eyebrow pill
        eyebrow = tk.Frame(self.top, bg="#F4E9D2")
        eyebrow.pack(anchor="w", padx=26, pady=(22, 10))
        tk.Label(eyebrow, text="⚠  BEKRÆFT HANDLING",
                 bg="#F4E9D2", fg=WARN_DARK, font=fonts["eyebrow"],
                 padx=10, pady=2).pack()

        tk.Label(self.top, text="Tving en fuld synkronisering?",
                 bg=PANEL, fg=TEXT, font=fonts["display_s"],
                 justify="left").pack(anchor="w", padx=26)

        tk.Label(self.top,
                 text=("Alle AULA-mærkede Outlook-aftaler bliver gen-overført til "
                       "Aula — også dem, der er uændrede siden sidst."),
                 bg=PANEL, fg=DIM, font=fonts["body"],
                 wraplength=400, justify="left"
                 ).pack(anchor="w", padx=26, pady=(8, 4))

        tk.Label(self.top,
                 text=("Brug det, hvis Aula-siden ser forkert ud, eller hvis du har "
                       "slettet noget i Aula som bør gendannes. Det tager typisk "
                       "lidt længere tid end en almindelig kørsel."),
                 bg=PANEL, fg=FAINT, font=fonts["small"],
                 wraplength=400, justify="left"
                 ).pack(anchor="w", padx=26, pady=(8, 18))

        tk.Frame(self.top, bg=LINE, height=1).pack(fill="x")

        btn_row = tk.Frame(self.top, bg=SUBTLE)
        btn_row.pack(fill="x", padx=0, pady=0)

        tk.Button(btn_row, text="Annullér", command=self.top.destroy,
                  bg=PANEL, fg=TEXT, font=fonts["body"],
                  relief="solid", borderwidth=1, padx=14, pady=5,
                  activebackground=SUBTLE
                  ).pack(side="right", padx=(0, 18), pady=14)

        def _confirm():
            self.top.destroy()
            on_confirm()
        tk.Button(btn_row, text="Tving kørsel", command=_confirm,
                  bg=WARN_DARK, fg="white", font=fonts["body"],
                  relief="flat", borderwidth=0, padx=14, pady=5,
                  activebackground="#8c5e0e", activeforeground="white"
                  ).pack(side="right", padx=(0, 8), pady=14)

        # center on parent
        self.top.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - self.top.winfo_width())  // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - self.top.winfo_height()) // 2
        self.top.geometry(f"+{px}+{py}")
```

Wire from `SplitButton._click_force` → `ForceConfirmDialog(...)`.

---

## 9 · First-run wizard

A `Toplevel` covering the whole window. Steps stored as Frame instances; show/hide via `pack_forget()`.

Skip detailed code — the pattern mirrors `ForceConfirmDialog` (Toplevel + grab_set + transient + center). Four steps:

1. **Velkommen** — display headline, intro paragraph
2. **Aula-login** — username/password entries (call existing `SetupManager.update_unilogin`)
3. **Outlook-kategorier** — call existing `SetupManager.create_outlook_categories`, show success per kategori
4. **Klar** — trigger first sync, close

Trigger condition: `if not SetupManager().get_aula_username(): show_wizard()` on first launch.

---

## 10 · Tray menu

`mainwindow.py` doesn't own the tray — that's likely in `main.pyw`/`launcher.pyw`. Whichever library is used (`pystray`, `infi.systray`, or a Qt fallback), update the menu items to match Direction A's structure:

```
─ Outlook2Aula
─ I sync · næste kørsel kl. 17:49
─────────────────────────────────
  Synkronisér nu                   Ctrl+R
  Tving fuld synkronisering        Ctrl+Shift+R   ★ new
  Sæt automatisk kørsel på pause
─────────────────────────────────
  Åbn vindue
  Indstillinger
  Afslut O2A
```

Bind keyboard shortcuts at the main window level:

```python
self.root.bind("<Control-r>",       lambda e: self.on_runO2A_clicked())
self.root.bind("<Control-Shift-R>", lambda e: self.shell.views["status"].force_sync())
```

---

## 11 · Migration steps (do in this order)

Each step ships a working app — don't batch.

1. **Theme + Shell** — `theme.py`, `ui/shell.py`. Replace `_build_ui()` with `Shell(self.root, self)`. App opens to a blank Status view; sidebar nav works (placeholder views).
2. **Status view** — port the existing functionality (sync button, log Text, summary tiles populated from a stub). Keep all sync wiring identical.
3. **SplitButton + Force-confirm** — replace the single sync button. Wire force path to existing `on_forcerunO2A_clicked`.
4. **Logfil view** — add `LogStore` + `_StoreHandler` + file handler. Build the view. Add to sidebar.
5. **Konto + Personer + Indstillinger** — straightforward Forms-style layouts. Personer keeps the existing "open CSV in Excel" path for now; don't try to build an inline editor unless asked.
6. **Wizard** — only triggered when `not SetupManager().get_aula_username()`.
7. **Tray menu rewrite** — match the new structure, especially the force-sync item.
8. **Polish pass** — keyboard shortcuts, mnemonics on dialog buttons, sidebar collapse behavior on small windows (optional).

---

## 12 · Things to explicitly **not** do

- Don't rewrite `update_calendar`, `__create_aula_events`, `__update_aula_events`, `__delete_aula_events`, or `_run_sync`. They work. Touch only the surface.
- Don't migrate to PySide6 in this pass. (There's a separate Qt handoff if you want to do that later — `O2A - Qt Handoff.html`.)
- Don't try to add Mica/acryl. Tkinter cannot. The design has been adjusted to look intentional with flat panels.
- Don't add icons just to fill space. The mock uses sparse iconography on purpose. Sidebar nav rows have **no icons** in this Tkinter port — labels alone are cleaner and easier in Tk.
- Don't `from tkinter import *`. Use `import tkinter as tk`.
- Don't shrink the window below 900×600 — the two-column layout breaks below that.

---

## 13 · Testing checklist

Before shipping each migration step:

- [ ] App opens, no exceptions in console
- [ ] Sidebar nav switches views; active state visible
- [ ] "Synkronisér nu" still works (compare against pre-change behavior)
- [ ] "Tving fuld synkronisering" appears in menu, confirm dialog opens, force path calls `on_forcerunO2A_clicked`
- [ ] Logfil view shows entries appearing live during a sync
- [ ] Filter chips toggle visibility instantly (no jank)
- [ ] Search highlights matches; clearing the field removes highlights
- [ ] "Følg nyeste" auto-scrolls during a live sync; unchecking stops it
- [ ] Window resize doesn't break sidebar width
- [ ] Tray menu's "Tving fuld synkronisering" works without opening the main window first

---

*This handoff was generated from the design in `O2A - Stille.html` (Direction A). Refer back to that file when in doubt about a specific detail — open it in a browser side-by-side while implementing.*
