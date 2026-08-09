# -*- coding: utf-8 -*-
# ui/status_view.py — Main status / sync view
import tkinter as tk
from tkinter import filedialog, messagebox
import datetime
import time
from theme import (
    BG, PANEL, SUBTLE, LINE, TEXT, DIM, FAINT,
    ACCENT, ACCENT_TINT, OK, ERR, WARN,
)
from ui.widgets import Card, SplitButton, SecondaryButton

# Symboler så begivenheder ikke kun skelnes på farve (læsbart for farveblinde
# og hurtigere at skimme end farvet tekst alene).
ACTION_SYMBOLS = {
    "oprettet":  "✓",
    "opdateret": "↻",
    "fjernet":   "–",
    "error":     "⚠",
}


class StatusView(tk.Frame):
    """Status view: hero + summary tiles + tab-switched event/log content."""

    def __init__(self, parent, controller, fonts):
        super().__init__(parent, bg=BG)
        self._controller = controller
        self._fonts = fonts
        self._build()

    def _build(self):
        # ── Testtilstand-banner ───────────────────────────────────────────────
        if getattr(self._controller, '_dry_run', False):
            banner = tk.Frame(self, bg="#FFF3CD")
            banner.pack(fill="x")
            tk.Label(banner,
                     text="Testtilstand: intet bliver gemt i Aula lige nu.",
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
        self._countdown_after_id = None

        right = tk.Frame(hero, bg=BG)
        right.pack(side="right", anchor="s")

        self._preview_btn = SecondaryButton(
            right, text="Forhåndsvis ændringer",
            command=self._on_preview_clicked, fonts=self._fonts,
        )
        self._preview_btn.pack(side="left", padx=(0, 8))

        self.sync_btn = SplitButton(
            right,
            fonts=self._fonts,
            on_normal=self._controller.on_runO2A_clicked,
            on_force=self._controller.on_forcerunO2A_clicked,
        )
        self.sync_btn.pack(side="left")

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

        # ── Begivenheder ──────────────────────────────────────────────────────
        tk.Frame(self, bg=LINE, height=1).pack(fill="x", padx=40)

        events_frame = tk.Frame(self, bg=BG)
        events_frame.pack(fill="both", expand=True)

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

        # Load history and subscribe to live updates
        from ui.event_store import EventStore
        EventStore.subscribe(lambda _rec: self.after(0, self._render_events))
        self._render_events()

    # ── Forhåndsvisning ───────────────────────────────────────────────────────

    def _on_preview_clicked(self):
        self._preview_btn.config(state="disabled", text="Forhåndsviser …")

        def _done(ok, data):
            self._preview_btn.config(state="normal", text="Forhåndsvis ændringer")
            if ok:
                from ui.dialogs.preview import PreviewDialog
                PreviewDialog(self.winfo_toplevel(), self._fonts, data)
            elif data and data.get("busy"):
                messagebox.showinfo(
                    "Forhåndsvisning",
                    "Der køres allerede en synkronisering eller forhåndsvisning — "
                    "vent til den er færdig, og prøv igen.",
                    parent=self.winfo_toplevel())
            else:
                messagebox.showerror(
                    "Forhåndsvisning mislykkedes",
                    "Det lykkedes ikke at forbinde til Aula. Tjek dine loginoplysninger "
                    "under Konto, og prøv igen.",
                    parent=self.winfo_toplevel())

        self._controller.preview_changes(_done)

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
        else:
            n = len(records)
            self._ev_count_lbl.config(
                text=f"{n} begivenhed{'er' if n != 1 else ''} · seneste uge")

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

                symbol = ACTION_SYMBOLS.get(tag, "●")
                _ins(f"{symbol} ", tag)
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

        details_frame = None
        if rec.get("log_snippet"):
            toggle_row = tk.Frame(dlg, bg=PANEL)
            toggle_row.pack(fill="x", padx=16, pady=(12, 0))

            details_frame = tk.Frame(dlg, bg=PANEL)
            # Ikke pakket endnu — foldet sammen som standard, da indholdet er
            # teknisk (rå logudskrift) og kun relevant hvis man vil undersøge
            # fejlen nærmere eller sende den videre til support.

            toggle_btn = tk.Button(
                toggle_row, text="Vis tekniske detaljer ▾",
                bg=PANEL, fg=DIM, font=self._fonts["small"],
                relief="flat", borderwidth=0, padx=0, pady=2,
                activebackground=PANEL, activeforeground=TEXT,
                cursor="hand2")
            toggle_btn.pack(anchor="w")

            def _toggle_details():
                if details_frame.winfo_ismapped():
                    details_frame.pack_forget()
                    toggle_btn.config(text="Vis tekniske detaljer ▾")
                    dlg.geometry(f"{dlg.winfo_width()}x{280}")
                else:
                    details_frame.pack(fill="both", expand=True, padx=16, pady=(6, 4))
                    toggle_btn.config(text="Skjul tekniske detaljer ▴")
                    dlg.geometry(f"{dlg.winfo_width()}x{420}")

            toggle_btn.config(command=_toggle_details)

            sb = tk.Scrollbar(details_frame)
            sb.pack(side="right", fill="y")
            txt = tk.Text(details_frame, bg=SUBTLE, fg=TEXT, font=self._fonts["mono"],
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
        SecondaryButton(footer, text="Luk", command=dlg.destroy,
                        fonts=self._fonts, pady=5,
                        ).pack(side="right", padx=16, pady=10)
        SecondaryButton(footer, text="Eksporter…", command=lambda: self._export_error_detail(rec, dlg),
                        fonts=self._fonts, pady=5,
                        ).pack(side="right", padx=(16, 0), pady=10)

        dlg.update_idletasks()
        w, h = 560, 280
        x = parent.winfo_rootx() + (parent.winfo_width()  - w) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
        dlg.geometry(f"{w}x{h}+{x}+{y}")

    def _export_error_detail(self, rec, parent_dlg):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = filedialog.asksaveasfilename(
            parent=parent_dlg,
            title="Eksporter fejldetaljer",
            defaultextension=".txt",
            initialfile=f"fejllog_{ts}.txt",
            filetypes=[("Tekstfil", "*.txt"), ("Alle filer", "*.*")],
        )
        if not path:
            return
        lines = [rec.get("title", ""), ""]
        if rec.get("error_detail"):
            lines.append(rec["error_detail"])
            lines.append("")
        if rec.get("log_snippet"):
            lines.append("LOGUDSKRIFT")
            lines.append(rec["log_snippet"])
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
        except OSError as e:
            messagebox.showerror("Eksport mislykkedes", str(e), parent=parent_dlg)
            return
        messagebox.showinfo("Eksporteret", f"Fejldetaljer gemt til:\n{path}", parent=parent_dlg)

    # ── Public API ────────────────────────────────────────────────────────────

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
        self._cancel_countdown()
        self._step_label.config(text=text)
        if not self._progress_strip.winfo_ismapped():
            self._progress_strip.pack(anchor="w")
        if not self._pulsing:
            self._pulsing = True
            self._pulse_tick()

    def set_sync_countdown(self, chunk_next, chunk_total, pause_seconds, total_seconds):
        """Show a friendly, rounded time estimate for the rest of the sync.
        Ticks once per second so the estimate counts down smoothly."""
        self._cancel_countdown()

        total_end = time.monotonic() + total_seconds

        def _tick():
            total_remaining = max(0.0, total_end - time.monotonic())

            self._step_label.config(
                text=f"Synkroniserer… færdig om ca. {self._format_duration(total_remaining)}")

            if total_remaining > 0:
                self._countdown_after_id = self.after(1000, _tick)
            else:
                self._countdown_after_id = None

        if not self._progress_strip.winfo_ismapped():
            self._progress_strip.pack(anchor="w")
        if not self._pulsing:
            self._pulsing = True
            self._pulse_tick()

        _tick()

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Round a duration in seconds to a short, plain-language Danish string."""
        total = int(seconds + 0.5)
        hours, rem = divmod(total, 3600)
        minutes, secs = divmod(rem, 60)
        if hours:
            return f"{hours} t {minutes} min."
        if minutes:
            return f"{minutes} min."
        return f"{secs} sek."

    def _cancel_countdown(self):
        if self._countdown_after_id is not None:
            try:
                self.after_cancel(self._countdown_after_id)
            except Exception:
                pass
            self._countdown_after_id = None

    def clear_sync_step(self):
        """Hide the progress strip and stop pulsing."""
        self._cancel_countdown()
        self._pulsing = False
        self._progress_strip.pack_forget()

    def _pulse_tick(self):
        if not self._pulsing:
            return
        current = self._pulse_canvas.itemcget(self._pulse_oval, "fill")
        next_color = ACCENT_TINT if current == ACCENT else ACCENT
        self._pulse_canvas.itemconfig(self._pulse_oval, fill=next_color)
        self.after(600, self._pulse_tick)
