# -*- coding: utf-8 -*-
# ui/logfil_view.py — Logfil debug view + LogStore singleton
import os
import tkinter as tk
import logging
from datetime import datetime
from theme import (
    BG, PANEL, SUBTLE, LINE, TEXT, DIM, FAINT,
    STATUS_COLORS,
)

LOG_RETENTION_DAYS = 14
_LOG_DIR  = os.path.expandvars(r"%APPDATA%\O2A")
_LOG_PATH = os.path.join(_LOG_DIR, "o2a.log")


class LogStore:
    """Singleton: holds every LogRecord since startup. Views subscribe for live updates."""
    _records: list = []
    _subscribers: list = []

    @classmethod
    def append(cls, record: logging.LogRecord):
        ts = datetime.fromtimestamp(record.created)
        cls._records.append({
            "date": ts.strftime("%Y-%m-%d"),
            "time": ts.strftime("%H:%M:%S"),
            "lvl":  {10: "debug", 20: "info", 30: "warn",
                     40: "err",   50: "err"}.get(record.levelno, "info"),
            "msg":  record.getMessage(),
        })
        for cb in cls._subscribers:
            try:
                cb(cls._records[-1])
            except Exception:
                pass

    @classmethod
    def subscribe(cls, cb):
        cls._subscribers.append(cb)

    @classmethod
    def all(cls):
        return list(cls._records)


class LogfilView(tk.Frame):
    """Full log viewer with level filter chips, live search, and export tools."""

    def __init__(self, parent, controller, fonts):
        super().__init__(parent, bg=BG)
        self._fonts = fonts
        self._levels = {"info": True, "ok": True, "warn": True, "err": True, "debug": True}
        self._query = ""
        self._follow = tk.BooleanVar(value=True)
        self._build()
        self._render_all()
        LogStore.subscribe(self._on_new_record)

    def _build(self):
        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=40, pady=(28, 16))

        tk.Label(hdr, text=f"LOGFIL · {_LOG_PATH}",
                 bg=BG, fg=DIM, font=self._fonts["eyebrow"]).pack(anchor="w")

        title_row = tk.Frame(hdr, bg=BG)
        title_row.pack(fill="x", pady=(6, 0))

        tk.Label(title_row, text="Alt output fra O2A",
                 bg=BG, fg=TEXT, font=self._fonts["display_m"]).pack(side="left")

        tools = tk.Frame(title_row, bg=BG)
        tools.pack(side="right")

        for label, cmd in [
            ("Kopiér",             self._copy_all),
            ("Åbn i Notesblok ↗",  self._open_in_notepad),
            ("Eksportér .log",      self._export),
        ]:
            tk.Button(tools, text=label, command=cmd, font=self._fonts["small"],
                      bg=PANEL, fg=TEXT, relief="solid", borderwidth=1,
                      activebackground=SUBTLE,
                      padx=10, pady=2).pack(side="left", padx=3)

        tk.Label(self,
                 text=("Komplet rå-output fra alle kørsler. "
                       "Brug filtrene og søgefeltet til at finde en bestemt fejl."),
                 bg=BG, fg=DIM, font=self._fonts["small"],
                 wraplength=640, justify="left"
                 ).pack(anchor="w", padx=40, pady=(8, 4))

        retention_row = tk.Frame(self, bg=BG)
        retention_row.pack(anchor="w", padx=40, pady=(0, 14))
        tk.Label(retention_row, text="Logfilen slettes automatisk efter ",
                 bg=BG, fg=DIM, font=self._fonts["small"]).pack(side="left")
        tk.Label(retention_row, text=str(LOG_RETENTION_DAYS),
                 bg=BG, fg=TEXT, font=self._fonts["body"]).pack(side="left")
        tk.Label(retention_row, text=" dage.",
                 bg=BG, fg=DIM, font=self._fonts["small"]).pack(side="left")

        # ── Toolbar ───────────────────────────────────────────────────────────
        bar = tk.Frame(self, bg=SUBTLE, height=44)
        bar.pack(fill="x")
        tk.Frame(self, bg=LINE, height=1).pack(fill="x")

        self._chips = {}
        chip_row = tk.Frame(bar, bg=SUBTLE)
        chip_row.pack(side="left", padx=40, pady=8)

        for lvl_id, lvl_label in [
            ("info",  "Info"),
            ("ok",    "OK"),
            ("warn",  "Advarsel"),
            ("err",   "Fejl"),
            ("debug", "Debug"),
        ]:
            chip = self._make_chip(chip_row, lvl_id, lvl_label)
            chip.pack(side="left", padx=2)
            self._chips[lvl_id] = chip

        # Search entry
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._on_search())
        ent = tk.Entry(bar, textvariable=self._search_var,
                       font=self._fonts["body"], bg=PANEL, fg=TEXT,
                       relief="solid", borderwidth=1)
        ent.pack(side="left", fill="x", expand=True, padx=8, pady=8, ipady=3)

        tk.Checkbutton(bar, text="Følg nyeste", variable=self._follow,
                       bg=SUBTLE, fg=DIM, activebackground=SUBTLE,
                       selectcolor=PANEL,
                       font=self._fonts["small"]).pack(side="left", padx=12)

        # ── Log text widget ───────────────────────────────────────────────────
        outer = tk.Frame(self, bg=SUBTLE)
        outer.pack(fill="both", expand=True)

        sb = tk.Scrollbar(outer)
        sb.pack(side="right", fill="y")

        self.txt = tk.Text(outer, bg=SUBTLE, fg=TEXT,
                           font=self._fonts["mono"],
                           relief="flat", borderwidth=0,
                           padx=40, pady=8, wrap="none",
                           yscrollcommand=sb.set, state="disabled",
                           cursor="arrow")
        self.txt.pack(side="left", fill="both", expand=True)
        sb.config(command=self.txt.yview)

        # Tags — one per level (color) + one per level (elide on/off)
        for lvl_id in self._levels:
            self.txt.tag_configure(f"lvl_{lvl_id}",
                                    foreground=STATUS_COLORS.get(lvl_id, TEXT))
            self.txt.tag_configure(f"elide_{lvl_id}", elide=False)

        self.txt.tag_configure("ts",      foreground=FAINT)
        self.txt.tag_configure("lvlcol",  foreground=FAINT,
                                font=self._fonts["mono_sm"])
        self.txt.tag_configure("run_hdr", foreground=DIM,
                                font=self._fonts["eyebrow"],
                                spacing1=14, spacing3=6)
        self.txt.tag_configure("err_band", background="#FBEEEA",
                                lmargin1=32, lmargin2=32)
        self.txt.tag_configure("query_hit", background="#FFF2A8")

    def _make_chip(self, parent, lvl_id, label):
        c = tk.Frame(parent, bg=SUBTLE, cursor="hand2")
        dot = tk.Canvas(c, width=8, height=8, bg=SUBTLE, highlightthickness=0)
        dot.create_oval(0, 0, 8, 8, fill=STATUS_COLORS.get(lvl_id, TEXT), outline="")
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

        c._lbl = lbl
        c._dot = dot
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

    # ── Rendering ─────────────────────────────────────────────────────────────

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
        if self._follow.get():
            self.txt.see("end")

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
        if self._follow.get():
            self.txt.see("end")

    def _refilter(self):
        for lvl_id, on in self._levels.items():
            self.txt.tag_configure(f"elide_{lvl_id}", elide=not on)
        # Highlight search hits
        self.txt.tag_remove("query_hit", "1.0", "end")
        q = self._query
        if not q:
            return
        idx = "1.0"
        while True:
            idx = self.txt.search(q, idx, stopindex="end", nocase=True)
            if not idx:
                break
            end = f"{idx}+{len(q)}c"
            self.txt.tag_add("query_hit", idx, end)
            idx = end

    def _on_search(self):
        self._query = self._search_var.get().strip()
        self._refilter()

    # ── Tools ─────────────────────────────────────────────────────────────────

    def _copy_all(self):
        from tkinter import messagebox
        text = "\n".join(
            f"{r['date']} {r['time']}  {r['lvl'].upper():5s}  {r['msg']}"
            for r in LogStore.all()
        )
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("Logfil", "Logfilen er kopieret til udklipsholderen.")

    def _open_in_notepad(self):
        if os.path.exists(_LOG_PATH):
            os.startfile(_LOG_PATH)

    def _export(self):
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Log-fil", "*.log"), ("Tekstfil", "*.txt")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            for r in LogStore.all():
                f.write(f"{r['date']} {r['time']}  {r['lvl'].upper():5s}  {r['msg']}\n")
