# -*- coding: utf-8 -*-
# ui/status_view.py — Main status / sync view
import tkinter as tk
import logging
from theme import (
    BG, PANEL, SUBTLE, LINE, TEXT, DIM, FAINT,
    ACCENT, ACCENT_TINT, OK, ERR, WARN,
)
from ui.widgets import Card, SplitButton, UnderlineTabs

LOG_COLORS = {
    logging.DEBUG:    "#1A1A1A",
    logging.INFO:     "#3A5A44",
    logging.WARNING:  "#C98F1C",
    logging.ERROR:    "#C4452B",
    logging.CRITICAL: "#8764B8",
}


class StatusView(tk.Frame):
    """Status view: hero + summary tiles + tab-switched event/log content."""

    def __init__(self, parent, controller, fonts):
        super().__init__(parent, bg=BG)
        self._controller = controller
        self._fonts = fonts
        self._build()

    def _build(self):
        # ── DRY-RUN banner ────────────────────────────────────────────────────
        if getattr(self._controller, '_dry_run', False):
            banner = tk.Frame(self, bg="#FFF3CD")
            banner.pack(fill="x")
            tk.Label(banner,
                     text="[DRY-RUN AKTIV — ingen ændringer gemmes i Aula]",
                     bg="#FFF3CD", fg="#856404",
                     font=self._fonts["body_b"],
                     pady=6).pack()

        # ── Hero ──────────────────────────────────────────────────────────────
        hero = tk.Frame(self, bg=BG)
        hero.pack(fill="x", padx=40, pady=(28, 16))

        left = tk.Frame(hero, bg=BG)
        left.pack(side="left", fill="x", expand=True)

        tk.Label(left, text="STATUS", bg=BG, fg=DIM,
                 font=self._fonts["eyebrow"]).pack(anchor="w")
        tk.Label(left, text="Synkronisering", bg=BG, fg=TEXT,
                 font=self._fonts["display_m"]).pack(anchor="w", pady=(4, 0))

        # ── Progress strip (shown only during sync) ───────────────────────────
        self._progress_strip = tk.Frame(left, bg=BG)
        # intentionally not packed yet

        strip_inner = tk.Frame(self._progress_strip, bg=BG)
        strip_inner.pack(anchor="w", pady=(6, 2))

        self._pulse_canvas = tk.Canvas(
            strip_inner, width=8, height=8, bg=BG, highlightthickness=0)
        self._pulse_canvas.pack(side="left", padx=(0, 7))
        self._pulse_oval = self._pulse_canvas.create_oval(
            1, 1, 7, 7, fill=ACCENT, outline="")

        self._step_label = tk.Label(
            strip_inner, text="", bg=BG, fg=DIM, font=self._fonts["small"])
        self._step_label.pack(side="left")

        self._pulsing = False

        right = tk.Frame(hero, bg=BG)
        right.pack(side="right", anchor="s")

        self.sync_btn = SplitButton(
            right,
            fonts=self._fonts,
            on_normal=self._controller.on_runO2A_clicked,
            on_force=self._controller.on_forcerunO2A_clicked,
        )
        self.sync_btn.pack()

        # ── Summary tiles ─────────────────────────────────────────────────────
        tiles_frame = tk.Frame(self, bg=BG)
        tiles_frame.pack(fill="x", padx=40, pady=(0, 20))

        tiles_config = [
            ("Oprettet",  "0",      OK),
            ("Opdateret", "0",      "#5B6CFF"),
            ("Fjernet",   "0",      "#9B9B9B"),
            ("Fejl",      "0",      ERR),
        ]

        self._tile_labels = {}
        for col, (title, value, color) in enumerate(tiles_config):
            tiles_frame.grid_columnconfigure(col, weight=1)
            card = Card(tiles_frame)
            card.grid(row=0, column=col, padx=(0, 8), sticky="ew")

            inner = tk.Frame(card, bg=PANEL, padx=16, pady=14)
            inner.pack(fill="both")

            tk.Label(inner, text=title, bg=PANEL, fg=DIM,
                     font=self._fonts["eyebrow"]).pack(anchor="w")

            val_lbl = tk.Label(inner, text=value, bg=PANEL, fg=color,
                               font=self._fonts["display_num"])
            val_lbl.pack(anchor="w", pady=(4, 0))
            self._tile_labels[title] = val_lbl

        # ── Split tile: Senest kørt / Næste kørsel ────────────────────────────
        tiles_frame.grid_columnconfigure(4, weight=1)
        split_card = Card(tiles_frame)
        split_card.grid(row=0, column=4, sticky="ew")

        split_inner = tk.Frame(split_card, bg=PANEL, padx=16, pady=8)
        split_inner.pack(fill="both")

        tk.Label(split_inner, text="Senest kørt", bg=PANEL, fg=DIM,
                 font=self._fonts["eyebrow"]).pack(anchor="w")
        self._tile_labels["Senest kørt"] = tk.Label(
            split_inner, text="Aldrig", bg=PANEL, fg=DIM,
            font=self._fonts["display_s"])
        self._tile_labels["Senest kørt"].pack(anchor="w", pady=(3, 0))

        tk.Frame(split_inner, bg=LINE, height=1).pack(fill="x", pady=4)

        tk.Label(split_inner, text="Næste kørsel", bg=PANEL, fg=DIM,
                 font=self._fonts["eyebrow"]).pack(anchor="w")
        self._tile_labels["Næste kørsel"] = tk.Label(
            split_inner, text="—", bg=PANEL, fg=DIM,
            font=self._fonts["display_s"])
        self._tile_labels["Næste kørsel"].pack(anchor="w", pady=(3, 0))

        # ── Tabs ──────────────────────────────────────────────────────────────
        self._tab_content = {}

        self._tabs_bar = UnderlineTabs(
            self,
            fonts=self._fonts,
            tabs=[("events", "Begivenheder", 0), ("log", "Log", 0)],
            on_change=self._on_tab_change,
        )
        self._tabs_bar.pack(fill="x", padx=40)

        # Tab content area
        self._content_area = tk.Frame(self, bg=BG)
        self._content_area.pack(fill="both", expand=True)

        # ── "Begivenheder" tab content ────────────────────────────────────────
        events_frame = tk.Frame(self._content_area, bg=BG)

        ev_hdr = tk.Frame(events_frame, bg=BG)
        ev_hdr.pack(fill="x", padx=40, pady=(8, 4))
        self._ev_count_lbl = tk.Label(ev_hdr, text="", bg=BG, fg=DIM,
                                      font=self._fonts["small"])
        self._ev_count_lbl.pack(anchor="w")

        ev_outer = tk.Frame(events_frame, bg=LINE, bd=1, relief="flat")
        ev_outer.pack(fill="both", expand=True, padx=40, pady=(0, 12))

        ev_sb = tk.Scrollbar(ev_outer)
        ev_sb.pack(side="right", fill="y")

        self._ev_text = tk.Text(
            ev_outer, bg=PANEL, fg=TEXT,
            font=self._fonts["body"],
            bd=0, highlightthickness=0,
            wrap="word", state="disabled",
            padx=16, pady=12,
            yscrollcommand=ev_sb.set,
            cursor="arrow",
            spacing1=2, spacing3=4,
        )
        self._ev_text.pack(fill="both", expand=True)
        ev_sb.config(command=self._ev_text.yview)

        self._ev_text.tag_config("oprettet",  foreground=OK)
        self._ev_text.tag_config("opdateret", foreground="#5B6CFF")
        self._ev_text.tag_config("fjernet",   foreground="#9B9B9B")
        self._ev_text.tag_config("error",     foreground=ERR)
        self._ev_text.tag_config("title",     font=self._fonts["body_b"])
        self._ev_text.tag_config("meta",      foreground=DIM,
                                              font=self._fonts["small"])
        self._ev_text.tag_config("sep",       foreground=LINE)

        self._tab_content["events"] = events_frame

        # ── "Log" tab content ─────────────────────────────────────────────────
        log_frame = tk.Frame(self._content_area, bg=BG)
        log_outer = tk.Frame(log_frame, bg=LINE, bd=1, relief="flat")
        log_outer.pack(fill="both", expand=True, padx=40, pady=(12, 0))

        scrollbar = tk.Scrollbar(log_outer)
        scrollbar.pack(side="right", fill="y")

        self._log_text = tk.Text(
            log_outer, bg=PANEL, fg=TEXT,
            font=self._fonts["mono"],
            bd=0, highlightthickness=0,
            wrap="word", state="disabled",
            padx=8, pady=8,
            yscrollcommand=scrollbar.set,
        )
        self._log_text.pack(fill="both", expand=True)
        scrollbar.config(command=self._log_text.yview)

        for level, color in LOG_COLORS.items():
            self._log_text.tag_config(str(level), foreground=color)

        self._tab_content["log"] = log_frame

        # Show default tab
        self._on_tab_change("events")

        # Load history and subscribe to live updates
        from ui.event_store import EventStore
        EventStore.subscribe(lambda _rec: self.after(0, self._render_events))
        self._render_events()

    def _on_tab_change(self, tab_id):
        for tid, frame in self._tab_content.items():
            if tid == tab_id:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()

    # ── Event feed ───────────────────────────────────────────────────────────

    def _render_events(self):
        from ui.event_store import EventStore
        from datetime import datetime

        records = EventStore.all()  # newest first

        self._ev_text.config(state="normal")
        self._ev_text.delete("1.0", "end")

        if not records:
            self._ev_text.insert("end", "Ingen begivenheder endnu\n", "meta")
            self._ev_count_lbl.config(text="")
            self._tabs_bar.update_count("events", 0)
        else:
            n = len(records)
            self._ev_count_lbl.config(
                text=f"{n} begivenhed{'er' if n != 1 else ''} · seneste uge")
            self._tabs_bar.update_count("events", n)

            action_labels = {
                "oprettet":  "Oprettet",
                "opdateret": "Opdateret",
                "fjernet":   "Fjernet",
            }

            for i, rec in enumerate(records):
                action       = rec.get("action", "")
                is_error     = rec.get("error", False)
                error_detail = rec.get("error_detail")
                log_snippet  = rec.get("log_snippet")
                clickable    = is_error and (error_detail or log_snippet)
                tag          = "error" if is_error else action
                label        = ("Fejl · " if is_error else "") + action_labels.get(action, action.capitalize())

                try:
                    ts = datetime.fromisoformat(rec["timestamp"]).strftime("%d/%m %H:%M")
                except Exception:
                    ts = str(rec.get("timestamp", ""))[:16]

                start = str(rec.get("start_date", ""))
                try:
                    start = datetime.fromisoformat(start).strftime("%d/%m/%Y %H:%M")
                except Exception:
                    pass

                click_tag = None
                if clickable:
                    click_tag = f"ev_click_{i}"
                    self._ev_text.tag_config(click_tag)
                    self._ev_text.tag_bind(
                        click_tag, "<Button-1>",
                        lambda e, r=rec: self._show_error_detail(r))
                    self._ev_text.tag_bind(
                        click_tag, "<Enter>",
                        lambda e: self._ev_text.config(cursor="hand2"))
                    self._ev_text.tag_bind(
                        click_tag, "<Leave>",
                        lambda e: self._ev_text.config(cursor="arrow"))

                def _ins(text, *base_tags):
                    tags = list(base_tags) + ([click_tag] if click_tag else [])
                    self._ev_text.insert("end", text, tags)

                _ins("● ", tag)
                _ins(f"{label:<12}  ", tag)
                _ins(rec.get("title", "") + "\n", "title")

                if is_error and error_detail:
                    _ins(f"   {error_detail}\n", "error", "meta")
                if clickable:
                    _ins("   → Klik for detaljer\n", "meta")

                _ins(f"   Begivenhed: {start}  ·  Kørt: {ts}\n", "meta")
                self._ev_text.insert("end", "─" * 60 + "\n", "sep")

        self._ev_text.config(state="disabled")

    def _show_error_detail(self, rec):
        parent = self.winfo_toplevel()
        dlg = tk.Toplevel(parent)
        dlg.title("Fejldetaljer")
        dlg.configure(bg=PANEL)
        dlg.transient(parent)
        dlg.grab_set()
        dlg.resizable(True, True)

        hdr = tk.Frame(dlg, bg="#FAEAEA", padx=16, pady=12)
        hdr.pack(fill="x")
        tk.Label(hdr, text=rec.get("title", ""), bg="#FAEAEA", fg=TEXT,
                 font=self._fonts["body_b"]).pack(anchor="w")
        if rec.get("error_detail"):
            tk.Label(hdr, text=rec["error_detail"], bg="#FAEAEA", fg=ERR,
                     font=self._fonts["body"]).pack(anchor="w", pady=(4, 0))

        if rec.get("log_snippet"):
            lf = tk.Frame(dlg, bg=PANEL)
            lf.pack(fill="both", expand=True, padx=16, pady=(12, 4))
            tk.Label(lf, text="LOGUDSKRIFT", bg=PANEL, fg=DIM,
                     font=self._fonts["eyebrow"]).pack(anchor="w", pady=(0, 6))
            sb = tk.Scrollbar(lf)
            sb.pack(side="right", fill="y")
            txt = tk.Text(lf, bg=SUBTLE, fg=TEXT, font=self._fonts["mono"],
                          bd=0, highlightthickness=1, highlightbackground=LINE,
                          wrap="word", padx=8, pady=8,
                          yscrollcommand=sb.set)
            txt.pack(fill="both", expand=True)
            sb.config(command=txt.yview)
            txt.insert("1.0", rec["log_snippet"])
            txt.config(state="disabled")

        tk.Frame(dlg, bg=LINE, height=1).pack(fill="x", pady=(8, 0))
        footer = tk.Frame(dlg, bg=SUBTLE)
        footer.pack(fill="x")
        tk.Button(footer, text="Luk", command=dlg.destroy,
                  bg=PANEL, fg=TEXT, font=self._fonts["body"],
                  relief="solid", borderwidth=1, padx=14, pady=5,
                  activebackground=SUBTLE).pack(side="right", padx=16, pady=10)

        dlg.update_idletasks()
        w, h = 560, 380
        x = parent.winfo_rootx() + (parent.winfo_width()  - w) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
        dlg.geometry(f"{w}x{h}+{x}+{y}")

    # ── Public API ────────────────────────────────────────────────────────────

    def update_log(self, text: str, record: logging.LogRecord):
        """Append a formatted log line to the Log tab (thread-safe via root.after)."""
        tag = str(record.levelno)

        def _write():
            self._log_text.config(state="normal")
            self._log_text.insert("end", text + "\n", tag)
            self._log_text.see("end")
            self._log_text.config(state="disabled")

        self.after(0, _write)

    def update_stats(self, created, updated, deleted, errors, last_run):
        """Update the summary tiles with sync results."""
        self._tile_labels["Oprettet"].config(text=str(created))
        self._tile_labels["Opdateret"].config(text=str(updated))
        self._tile_labels["Fjernet"].config(text=str(deleted))
        self._tile_labels["Fejl"].config(text=str(errors))
        self._tile_labels["Senest kørt"].config(text=last_run)

    def set_last_run_display(self, text: str):
        """Update only the 'Senest kørt' tile (used on startup to restore persisted value)."""
        self._tile_labels["Senest kørt"].config(text=text)

    def update_next_run(self, text: str):
        """Update the 'Næste kørsel' line in the split tile."""
        self._tile_labels["Næste kørsel"].config(text=text)

    def set_sync_step(self, text: str):
        """Show the progress strip with the given step text and start pulsing."""
        self._step_label.config(text=text)
        if not self._progress_strip.winfo_ismapped():
            self._progress_strip.pack(anchor="w")
        if not self._pulsing:
            self._pulsing = True
            self._pulse_tick()

    def clear_sync_step(self):
        """Hide the progress strip and stop pulsing."""
        self._pulsing = False
        self._progress_strip.pack_forget()

    def _pulse_tick(self):
        if not self._pulsing:
            return
        current = self._pulse_canvas.itemcget(self._pulse_oval, "fill")
        next_color = ACCENT_TINT if current == ACCENT else ACCENT
        self._pulse_canvas.itemconfig(self._pulse_oval, fill=next_color)
        self.after(600, self._pulse_tick)
