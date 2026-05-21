# -*- coding: utf-8 -*-
# ui/status_view.py — Main status / sync view
import tkinter as tk
import logging
from theme import (
    BG, PANEL, SUBTLE, LINE, TEXT, DIM, FAINT,
    ACCENT, OK, ERR, WARN,
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
            ("Oprettet",    "0", OK),
            ("Opdateret",   "0", "#5B6CFF"),
            ("Fjernet",     "0", "#9B9B9B"),
            ("Fejl",        "0", ERR),
            ("Senest kørt", "Aldrig", DIM),
        ]

        self._tile_labels = {}
        for col, (title, value, color) in enumerate(tiles_config):
            tiles_frame.grid_columnconfigure(col, weight=1)
            card = Card(tiles_frame)
            card.grid(row=0, column=col, padx=(0, 8) if col < 4 else 0, sticky="ew")

            inner = tk.Frame(card, bg=PANEL, padx=16, pady=14)
            inner.pack(fill="both")

            tk.Label(inner, text=title, bg=PANEL, fg=DIM,
                     font=self._fonts["eyebrow"]).pack(anchor="w")

            val_lbl = tk.Label(inner, text=value, bg=PANEL, fg=color,
                               font=self._fonts["display_num"])
            val_lbl.pack(anchor="w", pady=(4, 0))
            self._tile_labels[title] = val_lbl

        # ── Tabs ──────────────────────────────────────────────────────────────
        self._tab_content = {}

        tabs_bar = UnderlineTabs(
            self,
            fonts=self._fonts,
            tabs=[("events", "Begivenheder", 0), ("log", "Log", 0)],
            on_change=self._on_tab_change,
        )
        tabs_bar.pack(fill="x", padx=40)

        # Tab content area
        self._content_area = tk.Frame(self, bg=BG)
        self._content_area.pack(fill="both", expand=True)

        # ── "Begivenheder" tab content ────────────────────────────────────────
        events_frame = tk.Frame(self._content_area, bg=BG)
        tk.Label(events_frame,
                 text="Kør en synkronisering for at se ændringer",
                 bg=BG, fg=DIM, font=self._fonts["body"]).pack(
                     anchor="center", pady=40)
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

    def _on_tab_change(self, tab_id):
        for tid, frame in self._tab_content.items():
            if tid == tab_id:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()

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
