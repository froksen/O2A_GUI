# -*- coding: utf-8 -*-
# ui/dialogs/preview.py — Forhåndsvisning af ændringer (ingen skrivning til Aula)
import tkinter as tk
from theme import PANEL, SUBTLE, LINE, TEXT, DIM, OK
from ui.widgets import SecondaryButton

_SYMBOLS = {"created": "✓", "updated_candidates": "↻", "deleted": "–"}
_LABELS = {
    "created":            "Oprettes",
    "updated_candidates": "Opdateres (kandidat)",
    "deleted":            "Fjernes",
}
_COLORS = {"created": OK, "updated_candidates": "#5B6CFF", "deleted": "#9B9B9B"}


class PreviewDialog:
    """Viser resultatet af en forhåndsvisning. Intet er gemt eller skrevet
    til Aula — dette er kun en beregnet diff mellem Outlook og Aula."""

    def __init__(self, parent, fonts, data):
        self.top = tk.Toplevel(parent)
        self.top.title("Forhåndsvisning")
        self.top.configure(bg=PANEL)
        self.top.transient(parent)
        self.top.grab_set()
        self.top.resizable(True, True)
        self.top.minsize(480, 360)

        banner = tk.Frame(self.top, bg="#FFF3CD")
        banner.pack(fill="x")
        tk.Label(banner, text="Forhåndsvisning — intet er gemt i Aula",
                 bg="#FFF3CD", fg="#856404", font=fonts["body_b"], pady=8).pack()

        counts = tk.Frame(self.top, bg=PANEL)
        counts.pack(fill="x", padx=20, pady=(16, 8))
        for key in ("created", "updated_candidates", "deleted"):
            col = tk.Frame(counts, bg=PANEL)
            col.pack(side="left", padx=(0, 24))
            tk.Label(col, text=_LABELS[key], bg=PANEL, fg=DIM,
                     font=fonts["eyebrow"]).pack(anchor="w")
            tk.Label(col, text=str(len(data[key])), bg=PANEL, fg=_COLORS[key],
                     font=fonts["display_num"]).pack(anchor="w")

        outer = tk.Frame(self.top, bg=LINE, bd=1, relief="flat")
        outer.pack(fill="both", expand=True, padx=20, pady=(8, 12))
        sb = tk.Scrollbar(outer)
        sb.pack(side="right", fill="y")
        txt = tk.Text(
            outer, bg=PANEL, fg=TEXT, font=fonts["body"],
            bd=0, highlightthickness=0, wrap="word",
            padx=16, pady=12, yscrollcommand=sb.set, cursor="arrow",
        )
        txt.pack(fill="both", expand=True)
        sb.config(command=txt.yview)

        for key, color in _COLORS.items():
            txt.tag_config(key, foreground=color)
        txt.tag_config("meta", foreground=DIM, font=fonts["small"])

        any_rows = False
        for key in ("created", "updated_candidates", "deleted"):
            for title in data[key]:
                any_rows = True
                txt.insert("end", f"{_SYMBOLS[key]} ", key)
                txt.insert("end", f"{_LABELS[key]:<24}  ", key)
                txt.insert("end", f"{title}\n")
        if not any_rows:
            txt.insert("end",
                       "Ingen ændringer fundet — Outlook og Aula er allerede synkroniseret.\n",
                       "meta")
        txt.config(state="disabled")

        tk.Frame(self.top, bg=LINE, height=1).pack(fill="x")
        footer = tk.Frame(self.top, bg=SUBTLE)
        footer.pack(fill="x")
        SecondaryButton(footer, text="Luk", command=self.top.destroy,
                        fonts=fonts, pady=5).pack(side="right", padx=16, pady=10)

        self.top.update_idletasks()
        w, h = 560, 480
        x = parent.winfo_rootx() + (parent.winfo_width()  - w) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
        self.top.geometry(f"{w}x{h}+{x}+{y}")
