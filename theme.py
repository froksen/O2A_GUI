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
