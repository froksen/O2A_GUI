# launcher.pyw — Splash screen launcher for Outlook2Aula
# Runs with system Python (no venv needed). Handles git update, venv, deps, then starts main.pyw.

import tkinter as tk
from tkinter import font as tkfont
import subprocess
import threading
import sys
import os
import configparser
import socket
from pathlib import Path

# ── Configuration ────────────────────────────────────────────────────────────
DEBUG = False   # Set True to skip git pull
BASE_DIR = Path(__file__).parent
VENV_PYTHON = BASE_DIR / "venv" / "Scripts" / "python.exe"
REQUIREMENTS = BASE_DIR / "Requirements.txt"

# ── Update source (read from configuration.ini) ───────────────────────────────
_cfg = configparser.ConfigParser()
_cfg.read(BASE_DIR / "configuration.ini", encoding="utf-8")
GIT_REPO   = _cfg.get("UPDATE", "repo",   fallback="https://github.com/froksen/O2A_GUI")
GIT_BRANCH = _cfg.get("UPDATE", "branch", fallback="master")

# ── Colours (Sønderborg Kommune — light / Windows blue) ───────────────────────
BG          = "#F2F2F2"    # window / body background
BG_HEADER   = "#0078D4"    # top blue header bar
BG_TOOLBAR  = "#FFFFFF"    # bottom toolbar strip
BG_LOG      = "#FFFFFF"    # log text area
ACCENT      = "#0078D4"    # primary blue accent
ACCENT_DARK = "#005A9E"    # darker blue (sub-progress bar)
HDR_FG      = "#FFFFFF"    # text/icons on blue header
HDR_DIM     = "#B3D9F7"    # dimmed elements on blue header
TEXT_MAIN   = "#1B1B1B"    # primary body text
TEXT_DIM    = "#767676"    # muted body text
TEXT_OK     = "#107C10"    # success green
TEXT_ERR    = "#C42B1C"    # error red
BAR_BG      = "#DEECF9"    # progress bar track (light blue)
BORDER      = "#D6D6D6"    # separators / borders

# Aliases so the rest of the file keeps working unchanged
TEAL        = ACCENT
TEAL_DARK   = ACCENT_DARK

COMPACT_H   = 310
EXPANDED_H  = 560
WIDTH       = 480

# ── Steps (label, weight) ────────────────────────────────────────────────────
STEPS = [
    ("Tjekker internetforbindelse",  1),
    ("Henter nyeste version",        1),
    ("Forbereder Python-miljø",      1),
    ("Installerer afhængigheder",    4),
    ("Starter Outlook2Aula",         1),
]

class SplashApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.expanded = False
        self._log_lines: list[str] = []
        self._step_index = 0
        self._progress = 0.0
        self._total_weight = sum(w for _, w in STEPS)
        self._aborted = False
        self._current_proc: subprocess.Popen | None = None

        self._build_ui()
        self._center()

        # Kick off background work after window is drawn
        self.root.after(120, self._start_worker)

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        root = self.root
        root.overrideredirect(True)
        root.configure(bg=BG)
        root.geometry(f"{WIDTH}x{COMPACT_H}")
        root.resizable(False, False)
        root.attributes("-topmost", True)

        # Thin teal border effect via outer frame
        border = tk.Frame(root, bg=TEAL, bd=0)
        border.place(x=0, y=0, width=WIDTH, height=COMPACT_H + 300)

        inner = tk.Frame(border, bg=BG, bd=0)
        inner.place(x=1, y=1, width=WIDTH - 2, height=COMPACT_H + 298)
        self._inner = inner

        # ── Header strip ─────────────────────────────────────────────────────
        header = tk.Frame(inner, bg=BG_HEADER, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)

        # Icon (load PNG if available, else fallback unicode symbol)
        icon_path = BASE_DIR / "images" / "icon.png"
        self._icon_img = None
        try:
            from PIL import Image, ImageTk
            img = Image.open(icon_path).resize((36, 36))
            # Recolour white icon to teal
            r, g, b, a = img.split() if img.mode == "RGBA" else (*img.split(), None)
            self._icon_img = ImageTk.PhotoImage(img)
        except Exception:
            pass

        if self._icon_img:
            tk.Label(header, image=self._icon_img, bg=BG_HEADER).pack(side="left", padx=(16, 8), pady=14)
        else:
            tk.Label(header, text="⟳", fg=HDR_FG, bg=BG_HEADER,
                     font=("Segoe UI", 22)).pack(side="left", padx=(16, 8), pady=10)

        title_frame = tk.Frame(header, bg=BG_HEADER)
        title_frame.pack(side="left", pady=10)
        tk.Label(title_frame, text="Outlook2Aula", fg=HDR_FG, bg=BG_HEADER,
                 font=("Segoe UI Semibold", 15, "bold")).pack(anchor="w")
        tk.Label(title_frame, text="Starter op…" if not DEBUG else "DEBUG-TILSTAND",
                 fg=HDR_DIM, bg=BG_HEADER,
                 font=("Segoe UI", 9)).pack(anchor="w")

        # Close (X) button top-right
        close_btn = tk.Label(header, text="✕", fg=HDR_DIM, bg=BG_HEADER,
                             font=("Segoe UI", 12), cursor="hand2", padx=14)
        close_btn.pack(side="right")
        close_btn.bind("<Enter>",  lambda _e: close_btn.config(fg=HDR_FG))
        close_btn.bind("<Leave>",  lambda _e: close_btn.config(fg=HDR_DIM))
        close_btn.bind("<Button-1>", lambda _e: self._abort())

        # Minimize button
        min_btn = tk.Label(header, text="─", fg=HDR_DIM, bg=BG_HEADER,
                           font=("Segoe UI", 12), cursor="hand2", padx=10)
        min_btn.pack(side="right")
        min_btn.bind("<Enter>",  lambda _e: min_btn.config(fg=HDR_FG))
        min_btn.bind("<Leave>",  lambda _e: min_btn.config(fg=HDR_DIM))
        min_btn.bind("<Button-1>", lambda _e: self._minimize())

        # Version / tag top-right
        tk.Label(header, text="v2", fg=HDR_DIM, bg=BG_HEADER,
                 font=("Segoe UI", 9)).pack(side="right", padx=4)

        # ── Drag support (header is the drag handle) ──────────────────────────
        self._drag_x = 0
        self._drag_y = 0
        for widget in (header,):
            widget.bind("<ButtonPress-1>",   self._drag_start)
            widget.bind("<B1-Motion>",       self._drag_move)

        # ── Step indicators ───────────────────────────────────────────────────
        steps_frame = tk.Frame(inner, bg=BG)
        steps_frame.pack(fill="x", padx=20, pady=(14, 0))

        self._step_labels: list[tk.Label] = []
        self._step_dots: list[tk.Label]  = []

        for i, (name, _) in enumerate(STEPS):
            row = tk.Frame(steps_frame, bg=BG)
            row.pack(fill="x", pady=2)
            dot = tk.Label(row, text="○", fg=TEXT_DIM, bg=BG,
                           font=("Segoe UI", 9), width=2)
            dot.pack(side="left")
            lbl = tk.Label(row, text=name, fg=TEXT_DIM, bg=BG,
                           font=("Segoe UI", 9), anchor="w")
            lbl.pack(side="left")
            self._step_dots.append(dot)
            self._step_labels.append(lbl)

        # ── Status line ───────────────────────────────────────────────────────
        self._status_var = tk.StringVar(value="Forbereder…")
        tk.Label(inner, textvariable=self._status_var, fg=TEXT_MAIN, bg=BG,
                 font=("Segoe UI", 10), anchor="w").pack(fill="x", padx=20, pady=(12, 2))

        # ── Step progress bar (current step) ──────────────────────────────────
        step_bar_outer = tk.Frame(inner, bg=BAR_BG, height=3)
        step_bar_outer.pack(fill="x", padx=20, pady=(0, 5))
        step_bar_outer.pack_propagate(False)

        self._step_bar_fill = tk.Frame(step_bar_outer, bg=TEAL_DARK, height=3, width=0)
        self._step_bar_fill.place(x=0, y=0, height=3)
        self._step_bar_outer = step_bar_outer

        # ── Total progress bar ────────────────────────────────────────────────
        bar_outer = tk.Frame(inner, bg=BAR_BG, height=6)
        bar_outer.pack(fill="x", padx=20, pady=(0, 0))
        bar_outer.pack_propagate(False)

        self._bar_fill = tk.Frame(bar_outer, bg=TEAL, height=6, width=0)
        self._bar_fill.place(x=0, y=0, height=6)
        self._bar_outer = bar_outer

        # ── Separator ─────────────────────────────────────────────────────────
        tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", padx=0, pady=(14, 0))

        # ── Bottom toolbar ────────────────────────────────────────────────────
        toolbar = tk.Frame(inner, bg=BG_TOOLBAR, height=32)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)

        self._toggle_btn = tk.Label(
            toolbar, text="▼  Vis detaljer", fg=ACCENT, bg=BG_TOOLBAR,
            font=("Segoe UI", 8), cursor="hand2")
        self._toggle_btn.pack(side="left", padx=12, pady=7)
        self._toggle_btn.bind("<Button-1>", lambda e: self._toggle_details())

        self._err_label = tk.Label(toolbar, text="", fg=TEXT_ERR, bg=BG_TOOLBAR,
                                   font=("Segoe UI", 8))
        self._err_label.pack(side="right", padx=12)

        # ── Detail log (hidden by default) ────────────────────────────────────
        self._log_frame = tk.Frame(inner, bg=BG_LOG)
        # Not packed yet — toggled in

        log_inner = tk.Frame(self._log_frame, bg=BG_LOG)
        log_inner.pack(fill="both", expand=True, padx=1, pady=1)

        scrollbar = tk.Scrollbar(log_inner, bg=BORDER, troughcolor=BG_LOG,
                                 activebackground=ACCENT, width=10, bd=0,
                                 highlightthickness=0)
        scrollbar.pack(side="right", fill="y")

        self._log_text = tk.Text(
            log_inner, bg=BG_LOG, fg="#444444", font=("Consolas", 8),
            bd=0, highlightthickness=0, wrap="word",
            yscrollcommand=scrollbar.set, state="disabled")
        self._log_text.pack(fill="both", expand=True, padx=6, pady=4)
        scrollbar.config(command=self._log_text.yview)

        self._log_text.tag_config("ok",  foreground=TEXT_OK)
        self._log_text.tag_config("err", foreground=TEXT_ERR)
        self._log_text.tag_config("hd",  foreground=TEAL)

    def _minimize(self):
        self.root.overrideredirect(False)
        self.root.iconify()
        self.root.bind("<Map>", self._on_restore)

    def _on_restore(self, _e):
        self.root.overrideredirect(True)
        self.root.unbind("<Map>")

    def _drag_start(self, event):
        self._drag_x = event.x_root - self.root.winfo_x()
        self._drag_y = event.y_root - self.root.winfo_y()

    def _drag_move(self, event):
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    def _abort(self):
        self._aborted = True
        if self._current_proc:
            self._current_proc.kill()
        self.root.destroy()

    def _bottom_right_pos(self, height: int) -> tuple[int, int]:
        self.root.update_idletasks()
        try:
            import ctypes
            # SPI_GETWORKAREA (0x30) returns the screen rect excluding taskbar
            class RECT(ctypes.Structure):
                _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                             ("right", ctypes.c_long), ("bottom", ctypes.c_long)]
            rect = RECT()
            ctypes.windll.user32.SystemParametersInfoW(0x30, 0, ctypes.byref(rect), 0)
            work_right  = rect.right
            work_bottom = rect.bottom
        except Exception:
            work_right  = self.root.winfo_screenwidth()
            work_bottom = self.root.winfo_screenheight()
        margin = 12  # pixels from right edge / above taskbar
        x = work_right  - WIDTH  - margin
        y = work_bottom - height - margin
        return x, y

    def _center(self):
        x, y = self._bottom_right_pos(COMPACT_H)
        self.root.geometry(f"{WIDTH}x{COMPACT_H}+{x}+{y}")

    # ── Toggle detail panel ───────────────────────────────────────────────────

    def _toggle_details(self):
        self.expanded = not self.expanded
        h = EXPANDED_H if self.expanded else COMPACT_H
        x, y = self._bottom_right_pos(h)
        self.root.geometry(f"{WIDTH}x{h}+{x}+{y}")

        if self.expanded:
            self._log_frame.pack(fill="both", expand=True, padx=1, pady=(0, 1))
            self._toggle_btn.config(text="▲  Skjul detaljer")
        else:
            self._log_frame.pack_forget()
            self._toggle_btn.config(text="▼  Vis detaljer")

    # ── Progress helpers ──────────────────────────────────────────────────────

    def _set_step(self, index: int):
        self._step_index = index
        self.root.after(0, self._refresh_steps)

    def _refresh_steps(self):
        for i, (dot, lbl) in enumerate(zip(self._step_dots, self._step_labels)):
            if i < self._step_index:
                dot.config(text="✓", fg=TEXT_OK)
                lbl.config(fg=TEXT_DIM)
            elif i == self._step_index:
                dot.config(text="▶", fg=TEAL)
                lbl.config(fg=TEXT_MAIN)
            else:
                dot.config(text="○", fg=TEXT_DIM)
                lbl.config(fg=TEXT_DIM)

    def _set_progress(self, fraction: float):
        self._progress = max(0.0, min(1.0, fraction))
        self.root.after(0, self._redraw_bar)

    def _redraw_bar(self):
        self._bar_outer.update_idletasks()
        w = self._bar_outer.winfo_width()
        fill_w = max(4, int(w * self._progress))
        self._bar_fill.place(x=0, y=0, width=fill_w, height=6)

    def _set_step_progress(self, fraction: float):
        self.root.after(0, lambda: self._redraw_step_bar(fraction))

    def _redraw_step_bar(self, fraction: float):
        self._step_bar_outer.update_idletasks()
        w = self._step_bar_outer.winfo_width()
        fill_w = int(w * max(0.0, min(1.0, fraction)))
        self._step_bar_fill.place(x=0, y=0, width=fill_w, height=3)

    def _set_status(self, text: str):
        self.root.after(0, lambda: self._status_var.set(text))

    def _set_error(self, text: str):
        self.root.after(0, lambda: self._err_label.config(text=text))

    def _show_error_dialog(self, title: str, message: str):
        dlg = tk.Toplevel(self.root)
        dlg.title(title)
        dlg.configure(bg=BG)
        dlg.resizable(False, False)
        dlg.attributes("-topmost", True)
        dlg.grab_set()

        # Border
        border = tk.Frame(dlg, bg=TEXT_ERR, bd=0)
        border.pack(fill="both", expand=True, padx=0, pady=0)
        inner = tk.Frame(border, bg=BG, bd=0)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        # Header
        hdr = tk.Frame(inner, bg=BG_TOOLBAR)
        hdr.pack(fill="x")
        tk.Label(hdr, text="✕  " + title, fg=TEXT_ERR, bg=BG_TOOLBAR,
                 font=("Segoe UI", 10, "bold"), anchor="w",
                 padx=14, pady=10).pack(fill="x")

        # Error text (scrollable)
        txt = tk.Text(inner, bg=BG_LOG, fg=TEXT_MAIN,
                      font=("Consolas", 8), bd=0, highlightthickness=0,
                      wrap="word", height=10, padx=10, pady=8)
        txt.insert("1.0", message)
        txt.config(state="disabled")
        txt.pack(fill="both", expand=True, padx=12, pady=10)

        # Close button
        btn = tk.Label(inner, text="Luk", fg=TEXT_MAIN, bg=TEXT_ERR,
                       font=("Segoe UI", 9, "bold"), cursor="hand2",
                       padx=20, pady=6)
        btn.pack(pady=(0, 14))
        btn.bind("<Button-1>", lambda _e: dlg.destroy())

        # Center over splash
        dlg.update_idletasks()
        w, h = 420, 280
        x = self.root.winfo_x() + (WIDTH - w) // 2
        y = self.root.winfo_y() + (COMPACT_H - h) // 2
        dlg.geometry(f"{w}x{h}+{x}+{y}")

    def _log(self, text: str, tag: str = ""):
        def _write():
            self._log_text.config(state="normal")
            self._log_text.insert("end", text + "\n", tag)
            self._log_text.see("end")
            self._log_text.config(state="disabled")
        self.root.after(0, _write)

    # ── Background worker ─────────────────────────────────────────────────────

    def _start_worker(self):
        t = threading.Thread(target=self._run_steps, daemon=True)
        t.start()

    def _run_steps(self):
        completed_weight = 0.0

        def advance(step_idx: int, sub: str = ""):
            self._set_step(step_idx)
            if sub:
                self._set_status(sub)
                self._log(f"── {sub}", "hd")
            p = completed_weight / self._total_weight
            self._set_progress(p)

        def finish_step(weight: int):
            nonlocal completed_weight
            completed_weight += weight
            self._set_progress(completed_weight / self._total_weight)

        CREATE_NO_WINDOW = 0x08000000

        def run(cmd: list, **kwargs) -> subprocess.CompletedProcess:
            if self._aborted:
                return subprocess.CompletedProcess(cmd, 1)
            self._log("$ " + " ".join(str(c) for c in cmd))
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, cwd=str(BASE_DIR),
                creationflags=CREATE_NO_WINDOW, **kwargs)
            self._current_proc = proc
            stdout, stderr = proc.communicate()
            self._current_proc = None
            if self._aborted:
                return subprocess.CompletedProcess(cmd, 1)
            if stdout.strip():
                for line in stdout.strip().splitlines():
                    self._log(line)
            if stderr.strip():
                for line in stderr.strip().splitlines():
                    self._log(line, "err" if proc.returncode != 0 else "")
            return subprocess.CompletedProcess(cmd, proc.returncode)

        # ── Trin 0: Internetcheck ─────────────────────────────────────────────
        advance(0, "Tjekker internetforbindelse…")
        self._log("Forsøger forbindelse til 8.8.8.8:53…")

        def _has_internet() -> bool:
            for host, port in [("github.com", 443), ("8.8.8.8", 53), ("1.1.1.1", 53)]:
                try:
                    socket.create_connection((host, port), timeout=3)
                    return True
                except OSError:
                    continue
            return False

        online = _has_internet()

        if online:
            self._log("Internetforbindelse OK.", "ok")
            finish_step(STEPS[0][1])
        else:
            self._log("Ingen internetforbindelse — starter med eksisterende version.", "err")

            # 1. Tjek venv
            if not VENV_PYTHON.exists():
                self._set_error("Intet venv fundet — kan ikke starte offline")
                self._log("FEJL: Virtuelt miljø (venv) er ikke oprettet.", "err")
                self.root.after(0, lambda: self._show_error_dialog(
                    "Kan ikke starte offline",
                    "Ingen internetforbindelse og det virtuelle Python-miljø (venv) er ikke oprettet.\n\n"
                    "Tilslut internettet og start programmet igen."))
                return

            self._log("Eksisterende venv fundet.", "ok")

            # 2. Tjek afhængigheder
            list_result = subprocess.run(
                [str(VENV_PYTHON), "-m", "pip", "list", "--format=freeze"],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                text=True, creationflags=CREATE_NO_WINDOW)
            installed_pkgs = {
                line.split("==")[0].lower()
                for line in list_result.stdout.splitlines() if "==" in line
            }
            reqs_offline = [
                ln.strip() for ln in REQUIREMENTS.read_text(encoding="utf-8-sig").splitlines()
                if ln.strip() and not ln.strip().startswith("#")
            ]
            missing_offline = [
                pkg for pkg in reqs_offline
                if pkg.split(">=")[0].split("==")[0].split("!=")[0].split("~=")[0].strip().lower()
                   not in installed_pkgs
            ]
            if missing_offline:
                names = ", ".join(
                    p.split(">=")[0].split("==")[0].split("!=")[0].split("~=")[0].strip()
                    for p in missing_offline)
                self._set_error("Manglende pakker — kan ikke starte offline")
                self._log(f"FEJL: Følgende pakker mangler: {names}", "err")
                self.root.after(0, lambda: self._show_error_dialog(
                    "Kan ikke starte offline",
                    f"Ingen internetforbindelse og følgende pakker er ikke installeret:\n\n{names}\n\n"
                    "Tilslut internettet og start programmet igen."))
                return

            self._log("Alle afhængigheder installeret.", "ok")

            # Markér trin 0-3 som klaret og gå direkte til start
            finish_step(STEPS[0][1])
            finish_step(STEPS[1][1])
            finish_step(STEPS[2][1])
            finish_step(STEPS[3][1])
            advance(4, "Starter Outlook2Aula (offline)…")
            self._log("Starter main.pyw med eksisterende version…", "ok")
            try:
                proc = subprocess.Popen(
                    [str(VENV_PYTHON), str(BASE_DIR / "main.pyw")],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, cwd=str(BASE_DIR),
                    creationflags=CREATE_NO_WINDOW)
                try:
                    stdout, stderr = proc.communicate(timeout=3)
                    error_text = stderr.strip() or stdout.strip() or "(ingen fejlbesked)"
                    for line in error_text.splitlines():
                        self._log(line, "err")
                    self._set_error("Programmet crashede ved opstart")
                    self.root.after(0, lambda: self._show_error_dialog(
                        "Outlook2Aula kunne ikke starte",
                        f"Programmet stoppede uventet.\n\n{error_text}"))
                    return
                except subprocess.TimeoutExpired:
                    pass
            except Exception as e:
                self._set_error("Kunne ikke starte programmet")
                self._log(f"FEJL: {e}", "err")
                self.root.after(0, lambda: self._show_error_dialog(
                    "Kunne ikke starte Outlook2Aula",
                    f"Fejl ved opstart:\n\n{e}"))
                return

            finish_step(STEPS[4][1])
            self._set_step(len(STEPS))
            self._set_status("Klar! (offline-tilstand)")
            self._log("Outlook2Aula er startet (offline).", "ok")
            self.root.after(900, self.root.destroy)
            return

        # ── Trin 1: Git update ────────────────────────────────────────────────
        advance(1, "Henter nyeste version fra git…")
        if DEBUG:
            self._log("DEBUG: git-opdatering sprunget over", "ok")
        else:
            self._log(f"Kilde: {GIT_REPO} ({GIT_BRANCH})")
            r = run(["git", "remote", "set-url", "origin", GIT_REPO])
            if r.returncode != 0:
                self._set_error("Kunne ikke sætte git remote")
                self._log("FEJL: git remote set-url fejlede", "err")
                return
            r = run(["git", "fetch", "origin"])
            if r.returncode != 0:
                self._set_error("Git fetch fejlede")
                self._log("FEJL: git fetch origin fejlede", "err")
                return
            r = run(["git", "reset", "--hard", f"origin/{GIT_BRANCH}"])
            if r.returncode != 0:
                self._set_error("Git reset fejlede")
                self._log(f"FEJL: git reset --hard origin/{GIT_BRANCH} fejlede", "err")
                return
        finish_step(STEPS[1][1])

        # ── Trin 2: venv ──────────────────────────────────────────────────────
        advance(2, "Forbereder Python-miljø…")
        if not VENV_PYTHON.exists():
            self._log("Opretter nyt venv…")
            r = run([sys.executable, "-m", "venv", str(BASE_DIR / "venv")])
            if r.returncode != 0:
                self._set_error("Kunne ikke oprette venv")
                return
        else:
            self._log("Eksisterende venv fundet.", "ok")
        finish_step(STEPS[2][1])

        # ── Trin 3: Dependencies ──────────────────────────────────────────────
        advance(3, "Installerer afhængigheder…")

        # Upgrade pip quietly first
        run([str(VENV_PYTHON), "-m", "pip", "install", "--upgrade", "--quiet", "pip"])

        reqs = [
            ln.strip() for ln in REQUIREMENTS.read_text(encoding="utf-8-sig").splitlines()
            if ln.strip() and not ln.strip().startswith("#")
        ]
        step_weight = STEPS[3][1]

        # Batch-check all installed packages in one pip call (replaces N pip show calls)
        self._set_status("Tjekker installerede pakker…")
        list_result = subprocess.run(
            [str(VENV_PYTHON), "-m", "pip", "list", "--format=freeze"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, creationflags=0x08000000)
        installed_pkgs = {
            line.split("==")[0].lower()
            for line in list_result.stdout.splitlines() if "==" in line
        }

        missing = []
        for pkg in reqs:
            pkg_name = pkg.split(">=")[0].split("==")[0].split("!=")[0].split("~=")[0].strip()
            if pkg_name.lower() in installed_pkgs:
                self._log(f"Allerede installeret: {pkg_name}", "ok")
            else:
                missing.append(pkg)

        # Install missing packages in parallel
        if missing:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            total_missing = len(missing)
            done_count = [0]
            install_lock = threading.Lock()
            install_failed = [False]

            def install_pkg(pkg):
                if self._aborted or install_failed[0]:
                    return pkg, 1, ""
                pkg_name = pkg.split(">=")[0].split("==")[0].split("!=")[0].split("~=")[0].strip()
                self._log(f"$ pip install {pkg_name}")
                result = subprocess.run(
                    [str(VENV_PYTHON), "-m", "pip", "install", "--quiet", pkg],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, creationflags=0x08000000, cwd=str(BASE_DIR))
                if result.returncode != 0:
                    self._log(f"Forsøger igen: {pkg_name}")
                    result = subprocess.run(
                        [str(VENV_PYTHON), "-m", "pip", "install", "--quiet", pkg],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        text=True, creationflags=0x08000000, cwd=str(BASE_DIR))
                with install_lock:
                    done_count[0] += 1
                    n = done_count[0]
                    self._set_status(f"Installerer afhængigheder… ({n}/{total_missing})")
                    self._set_step_progress(n / total_missing)
                    frac = (completed_weight + step_weight * n / total_missing) / self._total_weight
                    self._set_progress(frac)
                if result.returncode == 0:
                    self._log(f"Installeret: {pkg_name}", "ok")
                else:
                    self._log(result.stderr.strip() or result.stdout.strip(), "err")
                return pkg, result.returncode, pkg_name

            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {executor.submit(install_pkg, pkg): pkg for pkg in missing}
                for future in as_completed(futures):
                    pkg, rc, pkg_name = future.result()
                    if rc != 0:
                        install_failed[0] = True
                        self._set_error(f"Fejl: {pkg_name}")
                        self._log(f"FEJL ved installation af {pkg}", "err")
            if install_failed[0]:
                return
        else:
            self._log("Alle afhængigheder allerede installeret.", "ok")

        self._set_step_progress(0.0)
        finish_step(STEPS[3][1])

        # ── Trin 4: Launch ────────────────────────────────────────────────────
        advance(4, "Starter Outlook2Aula…")
        self._log("Starter main.pyw…", "ok")

        try:
            # Use python.exe (not pythonw) so we can capture stderr on crash
            venv_python = VENV_PYTHON
            proc = subprocess.Popen(
                [str(venv_python), str(BASE_DIR / "main.pyw")],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, cwd=str(BASE_DIR),
                creationflags=CREATE_NO_WINDOW)

            # Wait briefly — if it crashes immediately we'll know within 3 s
            try:
                stdout, stderr = proc.communicate(timeout=3)
                # Process already exited → it crashed
                error_text = stderr.strip() or stdout.strip() or "(ingen fejlbesked)"
                for line in error_text.splitlines():
                    self._log(line, "err")
                self._set_error("Programmet crashede ved opstart")
                self.root.after(0, lambda: self._show_error_dialog(
                    "Outlook2Aula kunne ikke starte",
                    f"Programmet stoppede uventet.\n\n{error_text}"))
                return
            except subprocess.TimeoutExpired:
                # Still running after 3 s → success
                pass

        except Exception as e:
            self._set_error("Kunne ikke starte programmet")
            self._log(f"FEJL: {e}", "err")
            self.root.after(0, lambda: self._show_error_dialog(
                "Kunne ikke starte Outlook2Aula",
                f"Fejl ved opstart:\n\n{e}"))
            return

        finish_step(STEPS[4][1])
        self._set_step(len(STEPS))  # all done
        self._set_status("Klar!")
        self._log("Outlook2Aula er startet.", "ok")

        # Close splash after a short delay
        self.root.after(900, self.root.destroy)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    try:
        from PIL import Image, ImageTk
        _icon = ImageTk.PhotoImage(Image.open(BASE_DIR / "images" / "exchange.png"))
        root.iconphoto(True, _icon)
    except Exception:
        pass
    app = SplashApp(root)
    root.mainloop()
