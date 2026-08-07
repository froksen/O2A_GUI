# ui/personer_view.py — Personer (people) view
import csv
import shutil
from pathlib import Path

import tkinter as tk
from tkinter import messagebox

from theme import BG, LINE, TEXT, DIM, PANEL, SUBTLE, OK, WARN, ERR
from ui.widgets import UnderlineTabs

_ALIAS_CSV = "personer.csv"
_ALIAS_TEMPLATE = "personer_skabelon.csv"
_ALIAS_HEADER = ["Outlook navn", "AULA navn"]

_IGNORE_CSV = "personer_ignorer.csv"
_IGNORE_TEMPLATE = "personer_ignorer_skabelon.csv"
_IGNORE_HEADER = ["Outlook navn"]


def _read_csv_rows(csv_file: str, template_file: str, header: list) -> list:
    """Reads a ';'-delimited CSV (creating it from a template on first run) and
    returns each row as a tuple of column values in header order."""
    path = Path(csv_file)
    if not path.is_file():
        shutil.copy2(template_file, csv_file)

    rows = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            rows.append(tuple((row.get(col) or "").strip() for col in header))
    return rows


def _write_csv_rows(csv_file: str, header: list, rows: list):
    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(header)
        writer.writerows(rows)


def _load_alias_rows():
    return _read_csv_rows(_ALIAS_CSV, _ALIAS_TEMPLATE, _ALIAS_HEADER)


def _save_alias_rows(rows):
    _write_csv_rows(_ALIAS_CSV, _ALIAS_HEADER, rows)


def _load_ignore_rows():
    return _read_csv_rows(_IGNORE_CSV, _IGNORE_TEMPLATE, _IGNORE_HEADER)


def _save_ignore_rows(rows):
    _write_csv_rows(_IGNORE_CSV, _IGNORE_HEADER, rows)


class _TableEditor(tk.Frame):
    """A minimal in-app CSV table editor: add/remove/edit rows, load & save.

    columns: list of (key, label, width_chars) in the order they appear in
    the underlying CSV. The first column is treated as the required key —
    rows blank in that column are dropped on save, and duplicates (case-
    insensitive) are flagged before saving.
    """

    def __init__(self, parent, fonts, columns, load_fn, save_fn, excel_command):
        super().__init__(parent, bg=BG)
        self._fonts = fonts
        self._columns = columns
        self._load_fn = load_fn
        self._save_fn = save_fn
        self._rows = []
        self._dirty = False
        self._build(excel_command)
        self._load()

    def _build(self, excel_command):
        toolbar = tk.Frame(self, bg=BG)
        toolbar.pack(fill="x", pady=(0, 8))

        def _btn(parent, text, command, **kw):
            return tk.Button(
                parent,
                text=text,
                command=command,
                bg=PANEL,
                fg=TEXT,
                activebackground=SUBTLE,
                font=self._fonts["small"],
                relief="solid",
                borderwidth=1,
                padx=10,
                pady=4,
                cursor="hand2",
                **kw,
            )

        _btn(toolbar, "+ Tilføj række", self._add_blank_row).pack(side="left")
        self._save_btn = _btn(toolbar, "Gem ændringer", self._save, state="disabled")
        self._save_btn.pack(side="left", padx=(8, 0))
        _btn(toolbar, "Genindlæs", self._reload).pack(side="left", padx=(8, 0))
        _btn(toolbar, "Åbn i Excel", excel_command).pack(side="left", padx=(8, 0))

        self._status_lbl = tk.Label(
            toolbar, text="", bg=BG, fg=DIM, font=self._fonts["small"]
        )
        self._status_lbl.pack(side="right")

        outer = tk.Frame(self, bg=LINE, bd=1, relief="flat")
        outer.pack(fill="both", expand=True)

        header = tk.Frame(outer, bg=SUBTLE)
        header.pack(fill="x")
        for _key, label, width in self._columns:
            tk.Label(
                header,
                text=label,
                bg=SUBTLE,
                fg=DIM,
                font=self._fonts["eyebrow"],
                width=width,
                anchor="w",
            ).pack(side="left", padx=(8, 4), pady=6)
        tk.Frame(header, bg=SUBTLE, width=28).pack(side="left")

        canvas = tk.Canvas(outer, bg=PANEL, highlightthickness=0)
        vsb = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        self._rows_frame = tk.Frame(canvas, bg=PANEL)
        self._rows_frame.bind(
            "<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        window_id = canvas.create_window((0, 0), window=self._rows_frame, anchor="nw")
        canvas.bind(
            "<Configure>", lambda e: canvas.itemconfig(window_id, width=e.width)
        )
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        def _wheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        self._wheel_handler = _wheel
        canvas.bind("<MouseWheel>", _wheel)
        self._rows_frame.bind("<MouseWheel>", _wheel)

    # ── Row management ───────────────────────────────────────────────────────

    def _add_row(self, values=None):
        values = values or ["" for _ in self._columns]
        row_frame = tk.Frame(self._rows_frame, bg=PANEL)
        row_frame.pack(fill="x")

        row_entry = {"frame": row_frame, "vars": {}}

        for i, ((key, _label, width), val) in enumerate(zip(self._columns, values)):
            var = tk.StringVar(value=val)
            var.trace_add("write", lambda *_a: self._mark_dirty())
            entry = tk.Entry(
                row_frame,
                textvariable=var,
                font=self._fonts["body"],
                relief="solid",
                borderwidth=1,
                width=width,
            )
            entry.pack(side="left", padx=(8, 4) if i == 0 else (0, 4), pady=4)
            entry.bind("<MouseWheel>", self._wheel_handler)
            row_entry["vars"][key] = var

        tk.Button(
            row_frame,
            text="✕",
            command=lambda: self._remove_row(row_entry),
            bg=PANEL,
            fg=DIM,
            relief="flat",
            borderwidth=0,
            font=self._fonts["small"],
            cursor="hand2",
            activebackground=SUBTLE,
            padx=6,
        ).pack(side="left", padx=(4, 8))

        self._rows.append(row_entry)
        return row_entry

    def _remove_row(self, row_entry):
        row_entry["frame"].destroy()
        self._rows.remove(row_entry)
        self._mark_dirty()

    def _add_blank_row(self):
        self._add_row()
        self._mark_dirty()

    def _mark_dirty(self):
        self._dirty = True
        self._save_btn.config(state="normal")
        self._status_lbl.config(text="Ikke-gemte ændringer", fg=WARN)

    # ── Load / save ──────────────────────────────────────────────────────────

    def _load(self):
        for row in list(self._rows):
            row["frame"].destroy()
        self._rows = []

        try:
            data = self._load_fn()
        except OSError as e:
            self._status_lbl.config(text=f"Kunne ikke indlæse: {e}", fg=ERR)
            data = []
        else:
            self._status_lbl.config(
                text=f"{len(data)} række{'r' if len(data) != 1 else ''}"
                if data
                else "Ingen rækker endnu",
                fg=DIM,
            )

        for values in data:
            self._add_row(list(values))

        self._dirty = False
        self._save_btn.config(state="disabled")

    def _reload(self):
        if self._dirty and not messagebox.askyesno(
            "Genindlæs fra fil",
            "Ikke-gemte ændringer i tabellen vil gå tabt. Vil du fortsætte?",
            parent=self.winfo_toplevel(),
        ):
            return
        self._load()

    def _save(self):
        values = []
        seen = set()
        duplicates = []
        for row in self._rows:
            vals = tuple(v.get().strip() for v in row["vars"].values())
            if not vals[0]:
                continue
            key = vals[0].lower()
            if key in seen:
                duplicates.append(vals[0])
            seen.add(key)
            values.append(vals)

        if duplicates:
            messagebox.showwarning(
                "Dubletter fundet",
                "Følgende Outlook-navne optræder flere gange og gemmes som dubletter:\n\n"
                + "\n".join(sorted(set(duplicates))),
                parent=self.winfo_toplevel(),
            )

        try:
            self._save_fn(values)
        except OSError as e:
            messagebox.showerror(
                "Kunne ikke gemme", str(e), parent=self.winfo_toplevel()
            )
            self._status_lbl.config(text=f"Fejl ved gem: {e}", fg=ERR)
            return

        self._dirty = False
        self._save_btn.config(state="disabled")
        n = len(values)
        self._status_lbl.config(
            text=f"Gemt · {n} række{'r' if n != 1 else ''}", fg=OK
        )


class PersonerView(tk.Frame):
    """Editor for the person ignore list and the Outlook↔Aula alias mapping."""

    def __init__(self, parent, controller, fonts):
        super().__init__(parent, bg=BG)
        self._controller = controller
        self._fonts = fonts
        self._build()

    def _build(self):
        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=40, pady=(28, 20))

        tk.Label(hdr, text="PERSONER", bg=BG, fg=DIM, font=self._fonts["eyebrow"]).pack(
            anchor="w"
        )
        tk.Label(
            hdr, text="Personer", bg=BG, fg=TEXT, font=self._fonts["display_m"]
        ).pack(anchor="w", pady=(4, 0))

        tk.Frame(self, bg=LINE, height=1).pack(fill="x", padx=40)

        # ── Tabs ──────────────────────────────────────────────────────────────
        self._tab_content = {}
        self._tabs_bar = UnderlineTabs(
            self,
            fonts=self._fonts,
            tabs=[("alias", "Personers alias", 0), ("ignorer", "Ignorer personer", 0)],
            on_change=self._on_tab_change,
        )
        self._tabs_bar.pack(fill="x", padx=40, pady=(16, 0))

        content_area = tk.Frame(self, bg=BG)
        content_area.pack(fill="both", expand=True, padx=40, pady=(12, 20))

        # ── "Alias" tab ───────────────────────────────────────────────────────
        alias_frame = tk.Frame(content_area, bg=BG)
        tk.Label(
            alias_frame,
            text="Personer hvis navn i Outlook afviger fra deres navn i Aula. "
            "Begivenheder med disse Outlook-navne overføres under det tilsvarende "
            "Aula-navn.",
            bg=BG,
            fg=DIM,
            font=self._fonts["body"],
            wraplength=760,
            justify="left",
        ).pack(anchor="w", pady=(0, 12))
        _TableEditor(
            alias_frame,
            fonts=self._fonts,
            columns=[("outlook", "Outlook navn", 28), ("aula", "AULA navn", 28)],
            load_fn=_load_alias_rows,
            save_fn=_save_alias_rows,
            excel_command=self._controller.on_actionOutlook_Aulanavne_liste_triggered,
        ).pack(fill="both", expand=True)
        self._tab_content["alias"] = alias_frame

        # ── "Ignorer" tab ─────────────────────────────────────────────────────
        ignorer_frame = tk.Frame(content_area, bg=BG)
        tk.Label(
            ignorer_frame,
            text="Personer hvis Outlook-navn aldrig skal overføres til Aula. "
            "Begivenheder med disse navne springes helt over ved synkronisering.",
            bg=BG,
            fg=DIM,
            font=self._fonts["body"],
            wraplength=760,
            justify="left",
        ).pack(anchor="w", pady=(0, 12))
        _TableEditor(
            ignorer_frame,
            fonts=self._fonts,
            columns=[("outlook", "Outlook navn", 40)],
            load_fn=_load_ignore_rows,
            save_fn=_save_ignore_rows,
            excel_command=self._controller.on_actionIgnore_people_list_triggered,
        ).pack(fill="both", expand=True)
        self._tab_content["ignorer"] = ignorer_frame

        self._on_tab_change("alias")

    def _on_tab_change(self, tab_id):
        for tid, frame in self._tab_content.items():
            if tid == tab_id:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()
