# -*- coding: utf-8 -*-
# ui/advanceret_view.py — Advanced/maintenance tools page
import tkinter as tk
from theme import BG, PANEL, SUBTLE, LINE, TEXT, DIM, OK, ERR, ERR_HOVER, WARN
from ui.widgets import Card, PrimaryButton, SecondaryButton
from aula.aula_event_cache import AulaEventCache


class AdvanceretView(tk.Frame):
    """Avanceret-siden: tekniske vedligeholdelses-/fejlfindingsværktøjer, som
    almindelige brugere normalt ikke har brug for. Tænkt til at vokse med
    flere værktøjs-kort over tid — indeholder pt. dublet-oprydningen fra
    cleanup_duplicate_events.py."""

    def __init__(self, parent, controller, fonts):
        super().__init__(parent, bg=BG)
        self._controller = controller
        self._fonts = fonts
        self._report = None
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=40, pady=(28, 20))
        tk.Label(hdr, text="AVANCERET", bg=BG, fg=DIM,
                 font=self._fonts["eyebrow"]).pack(anchor="w")
        tk.Label(hdr, text="Avanceret", bg=BG, fg=TEXT,
                 font=self._fonts["display_m"]).pack(anchor="w", pady=(4, 0))

        tk.Frame(self, bg=LINE, height=1).pack(fill="x", padx=40)

        # Kortene herunder kan blive højere end vinduet (flere værktøjer,
        # smalt/lavt vindue) — Shell pakker hele siden i en ScrollableFrame
        # (se ui/shell.py), så vi behøver ikke en lokal wrapper her.
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=40, pady=20)

        tk.Label(body,
                 text=("Tekniske værktøjer til fejlfinding og oprydning. De fleste "
                       "brugere har ikke brug for denne side — brug værktøjerne med "
                       "omtanke, da nogle handlinger ikke kan fortrydes."),
                 bg=BG, fg=DIM, font=self._fonts["small"],
                 wraplength=640, justify="left",
                 ).pack(anchor="w", pady=(0, 16))

        self._build_duplicate_tool(body)
        self._build_cache_tool(body)
        self._build_wizard_tool(body)

    # ── Værktøj: dublet-oprydning ─────────────────────────────────────────────

    def _build_duplicate_tool(self, parent):
        card = Card(parent)
        card.pack(fill="x", pady=(0, 16))
        inner = tk.Frame(card, bg=PANEL, padx=20, pady=18)
        inner.pack(fill="both", expand=True)

        tk.Label(inner, text="Ryd dubletter i Aula", bg=PANEL, fg=TEXT,
                 font=self._fonts["body_b"]).pack(anchor="w")
        tk.Label(inner,
                 text=("Finder Aula-begivenheder som O2A har oprettet flere gange af "
                       "samme Outlook-aftale (fx pga. en tidligere fejl med rate-limits "
                       "mod Aula), og sletter alle undtagen den oprindelige kopi. "
                       "Scanner altid først uden at ændre noget — sletning kræver et "
                       "separat, bekræftet klik."),
                 bg=PANEL, fg=DIM, font=self._fonts["small"],
                 wraplength=640, justify="left",
                 ).pack(anchor="w", pady=(4, 12))

        btn_row = tk.Frame(inner, bg=PANEL)
        btn_row.pack(anchor="w")

        self._scan_btn = PrimaryButton(
            btn_row, text="Find dubletter",
            command=self._on_scan_clicked, fonts=self._fonts)
        self._scan_btn.pack(side="left")

        self._delete_btn = PrimaryButton(
            btn_row, text="Slet fundne dubletter",
            command=self._on_delete_clicked, fonts=self._fonts,
            bg=ERR, hover=ERR_HOVER, state="disabled")
        self._delete_btn.pack(side="left", padx=(8, 0))

        self._status_lbl = tk.Label(inner, text="", bg=PANEL, fg=DIM,
                                    font=self._fonts["small"], wraplength=640,
                                    justify="left", anchor="w")
        self._status_lbl.pack(anchor="w", fill="x", pady=(10, 0))

        # Resultat-liste — pakkes først når der er noget at vise
        self._results_outer = tk.Frame(inner, bg=LINE, highlightthickness=1,
                                       highlightbackground=LINE)
        results_sb = tk.Scrollbar(self._results_outer)
        results_sb.pack(side="right", fill="y")
        self._results_text = tk.Text(
            self._results_outer, bg=SUBTLE, fg=TEXT, font=self._fonts["mono_sm"],
            bd=0, highlightthickness=0, wrap="word", state="disabled",
            padx=12, pady=10, height=12,
            yscrollcommand=results_sb.set, cursor="arrow")
        self._results_text.pack(fill="both", expand=True)
        results_sb.config(command=self._results_text.yview)

    # ── Handlinger ────────────────────────────────────────────────────────────

    def _on_scan_clicked(self):
        self._report = None
        self._delete_btn.config(state="disabled")
        self._scan_btn.config(state="disabled", text="Scanner …")
        self._status_lbl.config(text="Starter scanning — kan tage et par minutter…", fg=DIM)
        self._hide_results()

        def _progress(text):
            self._status_lbl.config(text=text, fg=DIM)

        def _done(ok, data):
            self._scan_btn.config(state="normal", text="Find dubletter")
            if not ok:
                if data and data.get("busy"):
                    self._status_lbl.config(
                        text=("Der køres allerede en synkronisering eller forhåndsvisning "
                              "— vent til den er færdig, og prøv igen."), fg=DIM)
                else:
                    msg = (data or {}).get("error", "Ukendt fejl")
                    self._status_lbl.config(text=f"Scanning mislykkedes: {msg}", fg=ERR)
                return

            report = data["report"]
            self._report = report
            if not report:
                self._status_lbl.config(text="Ingen dubletter fundet. ✓", fg=OK)
                return

            total = sum(len(row["losers"]) for row in report)
            self._status_lbl.config(
                text=(f"Fandt {len(report)} grupper med i alt {total} dublet-begivenheder "
                      f"der kan slettes."),
                fg=WARN)
            self._show_results(report)
            self._delete_btn.config(state="normal")

        self._controller.find_aula_duplicate_events(_done, progress_callback=_progress)

    def _on_delete_clicked(self):
        if not self._report:
            return
        total = sum(len(row["losers"]) for row in self._report)
        from ui.dialogs.delete_duplicates_confirm import DeleteDuplicatesConfirmDialog
        DeleteDuplicatesConfirmDialog(self.winfo_toplevel(), self._fonts, total, self._do_delete)

    def _do_delete(self):
        self._delete_btn.config(state="disabled", text="Sletter …")
        self._scan_btn.config(state="disabled")

        def _progress(text):
            self._status_lbl.config(text=text, fg=DIM)

        def _done(ok, data):
            self._scan_btn.config(state="normal")
            self._delete_btn.config(text="Slet fundne dubletter")
            if not ok:
                msg = (data or {}).get("error", "Ukendt fejl")
                self._status_lbl.config(text=f"Sletning mislykkedes: {msg}", fg=ERR)
                return

            deleted = data["deleted"]
            failed = data["failed"]
            text = f"Færdig — {deleted} dubletter slettet"
            if failed:
                text += f", {failed} fejlede (se logfilen for detaljer)"
            self._status_lbl.config(text=text, fg=OK if not failed else WARN)
            self._report = None
            self._hide_results()

        self._controller.delete_aula_duplicate_events(self._report, _done, progress_callback=_progress)

    # ── Resultat-visning ──────────────────────────────────────────────────────

    def _show_results(self, report):
        self._results_text.config(state="normal")
        self._results_text.delete("1.0", "end")
        for row in report:
            copies = len(row["losers"]) + 1
            self._results_text.insert("end", f"{row['title']}  ({row['start']}) — {copies} kopier\n")
            self._results_text.insert("end", f"  Beholder: id {row['keeper']['id']}\n")
            for loser in row["losers"]:
                self._results_text.insert("end", f"  Sletter:  id {loser['id']}\n")
            self._results_text.insert("end", "\n")
        self._results_text.config(state="disabled")
        if not self._results_outer.winfo_ismapped():
            self._results_outer.pack(fill="both", expand=True, pady=(12, 0))

    def _hide_results(self):
        self._results_outer.pack_forget()

    # ── Værktøj: nulstil begivenheds-cache ────────────────────────────────────

    def _build_cache_tool(self, parent):
        card = Card(parent)
        card.pack(fill="x", pady=(0, 16))
        inner = tk.Frame(card, bg=PANEL, padx=20, pady=18)
        inner.pack(fill="both", expand=True)

        tk.Label(inner, text="Nulstil begivenheds-cache", bg=PANEL, fg=TEXT,
                 font=self._fonts["body_b"]).pack(anchor="w")
        tk.Label(inner,
                 text=("O2A husker Aula-begivenheders detaljer lokalt mellem "
                       "kørsler, så en synkronisering ikke behøver hente alt forfra "
                       "hver gang. Nulstil cachen hvis du har mistanke om at den "
                       "viser forkert data — næste synkronisering bliver til gengæld "
                       "markant langsommere, da alt så skal hentes friskt igen."),
                 bg=PANEL, fg=DIM, font=self._fonts["small"],
                 wraplength=640, justify="left",
                 ).pack(anchor="w", pady=(4, 12))

        btn_row = tk.Frame(inner, bg=PANEL)
        btn_row.pack(anchor="w")

        self._cache_btn = SecondaryButton(
            btn_row, text="Ryd cache", command=self._on_clear_cache_clicked, fonts=self._fonts)
        self._cache_btn.pack(side="left")

        self._cache_status_lbl = tk.Label(inner, text="", bg=PANEL, fg=DIM,
                                          font=self._fonts["small"], wraplength=640,
                                          justify="left", anchor="w")
        self._cache_status_lbl.pack(anchor="w", fill="x", pady=(10, 0))
        self._refresh_cache_status()

    def _refresh_cache_status(self):
        try:
            count = AulaEventCache.count()
        except Exception:
            count = None
        if count is None:
            self._cache_status_lbl.config(text="")
        elif count == 0:
            self._cache_status_lbl.config(text="Cachen er tom.", fg=DIM)
        else:
            self._cache_status_lbl.config(
                text=f"Cachen indeholder p.t. {count} begivenhed{'er' if count != 1 else ''}.",
                fg=DIM)

    def _on_clear_cache_clicked(self):
        from ui.dialogs.clear_cache_confirm import ClearCacheConfirmDialog
        ClearCacheConfirmDialog(self.winfo_toplevel(), self._fonts, self._do_clear_cache)

    def _do_clear_cache(self):
        AulaEventCache.clear()
        self._refresh_cache_status()
        self._cache_status_lbl.config(text="Cachen er ryddet. ✓", fg=OK)

    # ── Værktøj: kør opsætningsguide igen ─────────────────────────────────────

    def _build_wizard_tool(self, parent):
        card = Card(parent)
        card.pack(fill="x")
        inner = tk.Frame(card, bg=PANEL, padx=20, pady=18)
        inner.pack(fill="both", expand=True)

        tk.Label(inner, text="Kør opsætningsguide igen", bg=PANEL, fg=TEXT,
                 font=self._fonts["body_b"]).pack(anchor="w")
        tk.Label(inner,
                 text=("Gennemgå den samme guide som ved allerførste opstart — Aula-"
                       "login, Outlook-kategorier, synkroniseringsadfærd og "
                       "notifikationer. Dine nuværende valg er forudfyldt og "
                       "ændres kun der, hvor du selv aktivt vælger noget nyt."),
                 bg=PANEL, fg=DIM, font=self._fonts["small"],
                 wraplength=640, justify="left",
                 ).pack(anchor="w", pady=(4, 12))

        PrimaryButton(
            inner, text="Kør opsætningsguide", command=self._on_run_wizard_clicked,
            fonts=self._fonts).pack(anchor="w")

    def _on_run_wizard_clicked(self):
        from ui.dialogs.wizard import FirstRunWizard
        FirstRunWizard(self.winfo_toplevel(), self._fonts)
