# -*- coding: utf-8 -*-
# udfasning.py — Outlook2Aula er udfaset.
#
# main.pyw viser nu kun denne dialog i stedet for at starte programmet.
# Der logges ikke ind på Aula, og der synkroniseres ikke — mainwindow,
# aula/ og outlookmanager importeres slet ikke.
#
# Brugeren vælger mellem:
#   1) Stop og fjern alt fra computeren (adgangskode, genveje,
#      %APPDATA%\O2A og — når det er sikkert — selve programmappen)
#   2) Udsæt — intet fjernes, og dialogen vises igen ved næste opstart
# Ingen af valgene rører begivenhederne i Aula eller Outlook.
#
# Den fulde version er bevaret i git-tagget arkiv-fuld-version-2026-10-12.
import os
import shutil
import subprocess
import sys
import tempfile
import time
import tkinter as tk
from tkinter import messagebox

from app_paths import APPDATA_DIR, PROGRAM_DIR
from theme import (PANEL, SUBTLE, LINE, TEXT, DIM, FAINT, OK, ERR,
                   ACCENT_TINT, ACCENT, fonts as make_fonts)
from ui.widgets import PrimaryButton, SecondaryButton

SHORTCUT_NAME = "Outlook2Aula.lnk"
DEFAULT_INSTALL_DIR = os.path.join(os.path.expanduser("~"), "Outlook2Aula")

# launcher.pyw tolker det som et crash, hvis main.pyw afslutter inden for
# 3 sekunder — så vi lukker tidligst efter MIN_RUNTIME sekunder.
MIN_RUNTIME = 4.0
_STARTED = time.monotonic()

CREATE_NO_WINDOW = 0x08000000

TITLE = "Outlook2Aula er lukket ned"
INTRO = (
    "Jeg har valgt at lukke Outlook2Aula ned. Det er en forebyggende "
    "beslutning, og du behøver ikke gøre noget med det samme."
)
BODY = (
    "For at undgå eventuelle sikkerhedsbrud. Beslutningen er særligt truffet på baggrund af den "
    "seneste tids sager om læk af CPR-numre. Programmet håndterer dit "
    "UNI-login og har adgang til Aula, og jeg er ret sikker på, at der er "
    "opstået et øget fokus herpå. Samt hvis der skulle ske et læk, om jeg "
    "har et erstatningsansvar."
)
KEPT_TITLE = "✓  Dine begivenheder i Aula og Outlook forsvinder ikke"
KEPT_BODY = (
    "Alle dine begivenheder i både Aula og Outlook bliver liggende præcis "
    "som de er nu — også dem, Outlook2Aula har oprettet i Aula. Der bliver "
    "hverken slettet eller ændret noget i Aula eller Outlook — hverken nu, "
    "eller hvis du vælger at fjerne programmet fra computeren."
)
EVENTS_KEPT = "Dine begivenheder i Aula og Outlook er ikke ændret og bliver liggende."
KEPT_TINT = "#E6F2EC"
CONSEQUENCES = (
    "Der sker ikke længere nogen opdatering. Ændringer i Outlook og nye "
    "aftaler med kategorien \"AULA\" bliver ikke overført til Aula."
)
HISTORY = (
    "Outlook2Aula blev startet den 18. maj 2021, og det har aldrig været "
    "meningen, at projektet skulle eksistere så længe. Tak fordi du har "
    "brugt det."
)
SIGNATURE = "— Ole (OF)"


# ── Oprydning ──────────────────────────────────────────────────────────────

def _same_path(a: str, b: str) -> bool:
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))


def _is_inside_program_dir(path: str) -> bool:
    if not path:
        return False
    prog = os.path.normcase(os.path.abspath(PROGRAM_DIR))
    target = os.path.normcase(os.path.abspath(path))
    return target == prog or target.startswith(prog + os.sep)


def _shortcut_target(lnk_path: str) -> str:
    import win32com.client
    shell = win32com.client.Dispatch("WScript.Shell")
    return shell.CreateShortcut(lnk_path).TargetPath


def _remove_shortcut(lnk_path: str):
    """Sletter en genvej, men kun hvis den peger ind i denne programmappe.
    Returnerer en fejlbeskrivelse, eller None hvis alt gik godt."""
    if not os.path.isfile(lnk_path):
        return None
    try:
        if not _is_inside_program_dir(_shortcut_target(lnk_path)):
            return None   # en anden installations genvej — lad den være
        os.remove(lnk_path)
        return None
    except Exception as e:
        return f"Genvejen {lnk_path} kunne ikke fjernes ({e})"


def _startup_shortcut() -> str:
    import winshell
    return os.path.join(winshell.startup(common=False), SHORTCUT_NAME)


def _desktop_shortcut() -> str:
    import winshell
    return os.path.join(winshell.desktop(common=False), SHORTCUT_NAME)


def remove_password():
    try:
        import keyring
        if keyring.get_password("o2a", "aula_password") is not None:
            keyring.delete_password("o2a", "aula_password")
        return None
    except Exception as e:
        return f"Den gemte adgangskode kunne ikke fjernes ({e})"


def remove_autostart():
    try:
        return _remove_shortcut(_startup_shortcut())
    except Exception as e:
        return f"Autostart-genvejen kunne ikke fjernes ({e})"


def remove_desktop_shortcut():
    try:
        return _remove_shortcut(_desktop_shortcut())
    except Exception as e:
        return f"Genvejen på skrivebordet kunne ikke fjernes ({e})"


def remove_appdata():
    if not os.path.isdir(APPDATA_DIR):
        return None
    shutil.rmtree(APPDATA_DIR, ignore_errors=True)
    if os.path.isdir(APPDATA_DIR):
        return f"Mappen {APPDATA_DIR} kunne ikke slettes helt"
    return None


def _git(*args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=PROGRAM_DIR, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                          creationflags=CREATE_NO_WINDOW)


def program_dir_is_safe_to_delete() -> bool:
    """Programmappen slettes kun, hvis den ligner en almindelig installation
    lavet med install.ps1: standardplaceringen, et git-repo på origin/master
    og ingen lokale ændringer. Alt andet (fx en udviklingsmappe) røres ikke."""
    try:
        if not _same_path(PROGRAM_DIR, DEFAULT_INSTALL_DIR):
            return False
        for name in ("main.pyw", "launcher.pyw", ".git"):
            if not os.path.exists(os.path.join(PROGRAM_DIR, name)):
                return False
        head = _git("rev-parse", "HEAD")
        master = _git("rev-parse", "origin/master")
        if head.returncode or master.returncode:
            return False
        if head.stdout.strip() != master.stdout.strip():
            return False
        status = _git("status", "--porcelain", "--untracked-files=no")
        return status.returncode == 0 and status.stdout.strip() == ""
    except Exception:
        return False


def schedule_program_dir_removal() -> None:
    """Programmappen kan ikke slettes, mens programmet kører fra den. En skjult
    PowerShell-proces venter, til denne proces er lukket, og sletter derefter
    mappen (med genforsøg, hvis launcheren stadig holder fast i den).
    Kommandoen sendes som -EncodedCommand, så stier med æ/ø/å virker."""
    import base64
    def ps(text: str) -> str:
        return "'" + text.replace("'", "''") + "'"
    folder = ps(PROGRAM_DIR)
    ok_msg = ps("Outlook2Aula er nu helt fjernet fra computeren.\n\n" + EVENTS_KEPT)
    fail_msg = ps("Programmappen kunne ikke slettes automatisk. Du kan selv "
                  f"slette mappen:\n{PROGRAM_DIR}\n\n" + EVENTS_KEPT)
    title = ps(TITLE)
    command = (
        f"Wait-Process -Id {os.getpid()} -ErrorAction SilentlyContinue; "
        "for ($i = 0; $i -lt 15; $i++) { "
        f"if (-not (Test-Path -LiteralPath {folder})) {{ break }}; "
        f"Remove-Item -LiteralPath {folder} -Recurse -Force -ErrorAction SilentlyContinue; "
        "Start-Sleep -Seconds 2 }; "
        "$popup = New-Object -ComObject WScript.Shell; "
        f"if (Test-Path -LiteralPath {folder}) {{ $null = $popup.Popup({fail_msg}, 0, {title}, 48) }} "
        f"else {{ $null = $popup.Popup({ok_msg}, 0, {title}, 64) }}"
    )
    encoded = base64.b64encode(command.encode("utf-16-le")).decode("ascii")
    subprocess.Popen(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden",
         "-ExecutionPolicy", "Bypass", "-EncodedCommand", encoded],
        cwd=tempfile.gettempdir(),
        creationflags=CREATE_NO_WINDOW,
        close_fds=True)


# ── Dialog ─────────────────────────────────────────────────────────────────

class UdfasningDialog:

    def __init__(self, root: tk.Tk):
        self.root = root
        self.fonts = make_fonts(root)
        root.title(TITLE)
        root.configure(bg=PANEL)
        root.resizable(False, False)
        root.protocol("WM_DELETE_WINDOW", self._postpone)   # krydset = udsæt
        self._set_icon()
        self._wrapped = []
        self._build()
        self._fit_wraplength()
        self._center()
        root.attributes("-topmost", True)
        root.after(500, lambda: root.attributes("-topmost", False))
        root.focus_force()

    def _set_icon(self):
        try:
            from PIL import Image, ImageTk
            self._icon = ImageTk.PhotoImage(
                Image.open(os.path.join(PROGRAM_DIR, "images", "Exchange.png")))
            self.root.iconphoto(True, self._icon)
        except Exception:
            pass

    def _build(self):
        f = self.fonts
        eyebrow = tk.Frame(self.root, bg=ACCENT_TINT)
        eyebrow.pack(anchor="w", padx=26, pady=(22, 10))
        tk.Label(eyebrow, text="BESKED FRA UDVIKLEREN",
                 bg=ACCENT_TINT, fg=ACCENT, font=f["eyebrow"],
                 padx=10, pady=2).pack()

        tk.Label(self.root, text=TITLE, bg=PANEL, fg=TEXT,
                 font=f["display_s"], justify="left").pack(anchor="w", padx=26)

        intro = tk.Label(self.root, text=INTRO, bg=PANEL, fg=TEXT, font=f["body"],
                         wraplength=460, justify="left")
        intro.pack(anchor="w", padx=26, pady=(8, 0))

        # Det beroligende budskab kommer først — før begrundelsen.
        kept = tk.Frame(self.root, bg=KEPT_TINT,
                        highlightthickness=1, highlightbackground=OK)
        kept.pack(fill="x", padx=26, pady=(14, 0))
        tk.Label(kept, text=KEPT_TITLE, bg=KEPT_TINT, fg=OK, font=f["body_b"],
                 justify="left").pack(anchor="w", padx=14, pady=(10, 2))
        kept_body = tk.Label(kept, text=KEPT_BODY, bg=KEPT_TINT, fg=TEXT,
                             font=f["body"], wraplength=460, justify="left")
        kept_body.pack(anchor="w", padx=14, pady=(0, 10))

        tk.Label(self.root, text="Hvorfor?", bg=PANEL, fg=TEXT,
                 font=f["body_b"], justify="left"
                 ).pack(anchor="w", padx=26, pady=(14, 2))
        body = tk.Label(self.root, text=BODY, bg=PANEL, fg=DIM, font=f["body"],
                        wraplength=460, justify="left")
        body.pack(anchor="w", padx=26)

        tk.Label(self.root, text="Hvad ændrer sig så?", bg=PANEL, fg=TEXT,
                 font=f["body_b"], justify="left"
                 ).pack(anchor="w", padx=26, pady=(14, 2))
        cons = tk.Label(self.root, text=CONSEQUENCES, bg=PANEL, fg=DIM, font=f["body"],
                        wraplength=460, justify="left")
        cons.pack(anchor="w", padx=26)

        history = tk.Label(self.root, text=HISTORY, bg=PANEL, fg=DIM, font=f["body"],
                           wraplength=460, justify="left")
        history.pack(anchor="w", padx=26, pady=(14, 0))

        tk.Label(self.root, text=SIGNATURE, bg=PANEL, fg=DIM, font=f["body"],
                 justify="left").pack(anchor="w", padx=26, pady=(8, 18))

        tk.Frame(self.root, bg=LINE, height=1).pack(fill="x")

        bottom = tk.Frame(self.root, bg=SUBTLE)
        bottom.pack(fill="x")
        self._bottom = bottom
        tk.Label(bottom, text="Vælg hvad der skal ske med programmet på din computer:",
                 bg=SUBTLE, fg=TEXT, font=f["body"], justify="left"
                 ).pack(anchor="w", padx=26, pady=(14, 8))

        PrimaryButton(bottom, text="Stop programmet, og fjern alt omkring programmet på computeren",
                      command=self._remove_all, fonts=f,
                      ).pack(fill="x", padx=26)
        SecondaryButton(bottom, text="Udsæt — spørg mig igen senere",
                        command=self._postpone, fonts=f,
                        ).pack(fill="x", padx=26, pady=(8, 0))

        note = tk.Label(bottom,
                        text="Dine begivenheder i Aula og Outlook bliver liggende, uanset hvad du vælger.",
                        bg=SUBTLE, fg=FAINT, font=f["small"], wraplength=460, justify="left")
        note.pack(anchor="w", padx=26, pady=(10, 16))
        self._wrapped = [intro, body, cons, history, note]
        self._wrapped_inner = [kept_body]

    def _fit_wraplength(self):
        # Vinduets bredde bestemmes af den længste knap; lad teksten fylde
        # samme bredde (uafhængigt af Windows' skaleringsfaktor).
        self.root.update_idletasks()
        width = self.root.winfo_reqwidth() - 2 * 26
        self._wrap_width = width
        for label in self._wrapped:
            label.configure(wraplength=width)
        for label in self._wrapped_inner:      # inde i den grønne boks
            label.configure(wraplength=width - 2 * 14 - 2)

    def _center(self):
        self.root.update_idletasks()
        w, h = self.root.winfo_width(), self.root.winfo_height()
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 3
        self.root.geometry(f"+{x}+{y}")

    # ── Valg ──

    def _remove_all(self):
        if not messagebox.askyesno(
                "Fjern Outlook2Aula?",
                "Programmet, dets indstillinger, logfiler, genveje og din gemte "
                "adgangskode fjernes fra computeren.\n\n"
                "Dine begivenheder i Aula og Outlook bliver liggende — der bliver "
                "hverken slettet eller ændret noget i Aula eller Outlook.\n\n"
                "Vil du fortsætte?",
                icon="question", parent=self.root):
            return
        self._show_progress()

    # ── Fremdrift ──

    def _show_progress(self):
        """Skifter knapperne ud med en tjekliste, der udfyldes trin for trin."""
        f = self.fonts
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)   # ikke midt i det
        for child in self._bottom.winfo_children():
            child.destroy()
        self._progress_header = tk.Label(
            self._bottom, text="Fjerner Outlook2Aula fra computeren…",
            bg=SUBTLE, fg=TEXT, font=f["body_b"], justify="left")
        self._progress_header.pack(anchor="w", padx=26, pady=(14, 8))
        self._checklist = tk.Frame(self._bottom, bg=SUBTLE)
        self._checklist.pack(fill="x", padx=26)

        def shortcuts():
            errors = [e for e in (remove_autostart(), remove_desktop_shortcut()) if e]
            return "; ".join(errors) or None

        steps = [
            ("Gemt adgangskode", remove_password),
            ("Genveje", shortcuts),
            ("Indstillinger og logfiler", remove_appdata),
        ]
        self._run_step(steps, 0)

    def _add_row(self, label, state, detail=None):
        f = self.fonts
        icon, color = {"run": ("…", FAINT), "ok": ("✓", OK),
                       "err": ("✗", ERR), "later": ("→", DIM)}[state]
        row = tk.Frame(self._checklist, bg=SUBTLE)
        row.pack(fill="x", pady=1)
        line = tk.Frame(row, bg=SUBTLE)
        line.pack(fill="x")
        tk.Label(line, text=icon, bg=SUBTLE, fg=color, font=f["body_b"],
                 width=2).pack(side="left", anchor="n")
        tk.Label(line, text=label, bg=SUBTLE, fg=TEXT, font=f["body"],
                 justify="left", wraplength=self._wrap_width - 30
                 ).pack(side="left", anchor="w")
        if detail:
            tk.Label(row, text=detail, bg=SUBTLE, fg=ERR if state == "err" else DIM,
                     font=f["small"], justify="left", wraplength=self._wrap_width - 30
                     ).pack(anchor="w", padx=(28, 0))
        return row

    def _run_step(self, steps, index):
        if index >= len(steps):
            self._program_dir_step()
            return
        label, func = steps[index]
        row = self._add_row(f"{label} fjernes…", "run")
        self.root.update_idletasks()

        def do():
            error = func()
            row.destroy()
            if error:
                self._add_row(f"{label} kunne ikke fjernes", "err", error)
            else:
                self._add_row(f"{label} fjernet", "ok")
            self.root.after(350, lambda: self._run_step(steps, index + 1))
        self.root.after(250, do)

    def _program_dir_step(self):
        if program_dir_is_safe_to_delete():
            try:
                schedule_program_dir_removal()
                self._add_row("Programmappen fjernes, når du lukker vinduet "
                              "(du får en besked, når det er sket)", "later")
            except Exception as e:
                self._add_row("Programmappen kunne ikke fjernes", "err",
                              f"Slet selv mappen, når vinduet er lukket: {PROGRAM_DIR} ({e})")
        else:
            self._add_row("Programmappen skal du selv slette, når vinduet er lukket",
                          "later", PROGRAM_DIR)
        self.root.after(350, self._show_done)

    def _show_done(self):
        f = self.fonts
        self._progress_header.configure(text="Outlook2Aula er fjernet fra computeren")
        done = tk.Frame(self._bottom, bg=KEPT_TINT,
                        highlightthickness=1, highlightbackground=OK)
        done.pack(fill="x", padx=26, pady=(12, 0))
        tk.Label(done, text="✓  Færdig", bg=KEPT_TINT, fg=OK, font=f["body_b"],
                 justify="left").pack(anchor="w", padx=14, pady=(10, 2))
        tk.Label(done, text="Outlook2Aula er stoppet og fjernet. " + EVENTS_KEPT,
                 bg=KEPT_TINT, fg=TEXT, font=f["body"], justify="left",
                 wraplength=self._wrap_width - 30).pack(anchor="w", padx=14, pady=(0, 10))
        PrimaryButton(self._bottom, text="Luk", command=self._close, fonts=f,
                      ).pack(anchor="e", padx=26, pady=(12, 16))
        self.root.protocol("WM_DELETE_WINDOW", self._close)

    def _postpone(self):
        messagebox.showinfo(
            TITLE,
            "Intet er fjernet. Outlook2Aula synkroniserer ikke længere, men "
            "du bliver spurgt igen, næste gang programmet starter.\n\n"
            + EVENTS_KEPT,
            parent=self.root)
        self._close()

    def _close(self):
        self.root.withdraw()
        remaining = MIN_RUNTIME - (time.monotonic() - _STARTED)
        self.root.after(max(0, int(remaining * 1000)), self.root.destroy)


def run():
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('of.o2a.gui')
        import dpi_awareness
        dpi_awareness.enable()
    except Exception:
        pass
    root = tk.Tk()
    UdfasningDialog(root)
    root.mainloop()
    sys.exit(0)
