# -*- coding: utf-8 -*-
# ui/dialogs/wizard.py — First-run setup wizard
import tkinter as tk
from theme import BG, PANEL, SUBTLE, LINE, TEXT, DIM, FAINT, ACCENT, OK, ERR


class FirstRunWizard:
    """4-step first-run wizard: Welcome → Aula login → Outlook categories → Ready."""

    def __init__(self, parent, fonts):
        self._parent = parent
        self._fonts = fonts
        self._step = 0

        self.top = tk.Toplevel(parent)
        self.top.title("Opsætning af Outlook2Aula")
        self.top.configure(bg=PANEL)
        self.top.transient(parent)
        self.top.grab_set()
        self.top.resizable(False, False)
        self.top.minsize(520, 380)

        self._steps = []
        self._build()
        self._show_step(0)

        # Center on parent
        self.top.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - self.top.winfo_width())  // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - self.top.winfo_height()) // 2
        self.top.geometry(f"+{px}+{py}")

    def _build(self):
        # Content area — steps stacked, only one visible at a time
        self._content = tk.Frame(self.top, bg=PANEL)
        self._content.pack(fill="both", expand=True, padx=0, pady=0)

        # Bottom navigation bar
        tk.Frame(self.top, bg=LINE, height=1).pack(fill="x")
        nav = tk.Frame(self.top, bg=SUBTLE)
        nav.pack(fill="x")

        self._back_btn = tk.Button(nav, text="← Tilbage",
                                   command=self._go_back,
                                   bg=PANEL, fg=TEXT, font=self._fonts["body"],
                                   relief="solid", borderwidth=1,
                                   padx=14, pady=5,
                                   activebackground=SUBTLE)
        self._back_btn.pack(side="left", padx=18, pady=14)

        self._next_btn = tk.Button(nav, text="Næste →",
                                   command=self._go_next,
                                   bg=ACCENT, fg="white", font=self._fonts["body"],
                                   relief="flat", borderwidth=0,
                                   padx=14, pady=5,
                                   activebackground="#325039", activeforeground="white")
        self._next_btn.pack(side="right", padx=18, pady=14)

        # Build all step frames
        self._steps = [
            self._build_step_welcome(),
            self._build_step_aula_login(),
            self._build_step_categories(),
            self._build_step_ready(),
        ]

    # ── Step builders ─────────────────────────────────────────────────────────

    def _build_step_welcome(self):
        f = tk.Frame(self._content, bg=PANEL)

        tk.Label(f, text="OPSÆTNING", bg=PANEL, fg=DIM,
                 font=self._fonts["eyebrow"]).pack(anchor="w", padx=26, pady=(22, 2))
        tk.Label(f, text="Velkommen til Outlook2Aula",
                 bg=PANEL, fg=TEXT, font=self._fonts["display_s"]).pack(anchor="w", padx=26)

        tk.Label(f,
                 text=("Dette opsætningsassistent hjælper dig med at konfigurere "
                       "programmet, så det kan synkronisere dine Outlook-aftaler til Aula.\n\n"
                       "Du skal bruge:\n"
                       "  • Dit Uni-login brugernavn og kodeord\n"
                       "  • Outlook installeret og åbent\n\n"
                       "Klik 'Næste' for at komme i gang."),
                 bg=PANEL, fg=DIM, font=self._fonts["body"],
                 wraplength=460, justify="left"
                 ).pack(anchor="w", padx=26, pady=(12, 20))
        return f

    def _build_step_aula_login(self):
        f = tk.Frame(self._content, bg=PANEL)

        tk.Label(f, text="TRIN 1 AF 3", bg=PANEL, fg=DIM,
                 font=self._fonts["eyebrow"]).pack(anchor="w", padx=26, pady=(22, 2))
        tk.Label(f, text="Aula-login",
                 bg=PANEL, fg=TEXT, font=self._fonts["display_s"]).pack(anchor="w", padx=26)

        tk.Label(f,
                 text="Indtast dine Uni-login brugeroplysninger til Aula.",
                 bg=PANEL, fg=DIM, font=self._fonts["body"],
                 justify="left").pack(anchor="w", padx=26, pady=(8, 14))

        grid = tk.Frame(f, bg=PANEL)
        grid.pack(anchor="w", padx=26)

        tk.Label(grid, text="Brugernavn", bg=PANEL, fg=TEXT,
                 font=self._fonts["body_b"]).grid(row=0, column=0, sticky="w", pady=4)
        self._wiz_username = tk.Entry(grid, width=28, relief="solid", borderwidth=1)
        self._wiz_username.grid(row=0, column=1, padx=(12, 0), pady=4, ipady=3)

        tk.Label(grid, text="Kodeord", bg=PANEL, fg=TEXT,
                 font=self._fonts["body_b"]).grid(row=1, column=0, sticky="w", pady=4)
        self._wiz_password = tk.Entry(grid, width=28, show="*", relief="solid", borderwidth=1)
        self._wiz_password.grid(row=1, column=1, padx=(12, 0), pady=4, ipady=3)

        self._login_status = tk.Label(f, text="", bg=PANEL, fg=DIM,
                                      font=self._fonts["small"])
        self._login_status.pack(anchor="w", padx=26, pady=(8, 0))

        # Prefill if already configured
        try:
            from setupmanager import SetupManager
            sm = SetupManager()
            self._wiz_username.insert(0, sm.get_aula_username() or "")
            self._wiz_password.insert(0, sm.get_aula_password() or "")
        except Exception:
            pass

        return f

    def _build_step_categories(self):
        f = tk.Frame(self._content, bg=PANEL)

        tk.Label(f, text="TRIN 2 AF 3", bg=PANEL, fg=DIM,
                 font=self._fonts["eyebrow"]).pack(anchor="w", padx=26, pady=(22, 2))
        tk.Label(f, text="Outlook-kategorier",
                 bg=PANEL, fg=TEXT, font=self._fonts["display_s"]).pack(anchor="w", padx=26)

        tk.Label(f,
                 text=("Outlook2Aula anvender to kategorier i Outlook til at identificere "
                       "hvilke aftaler der skal synkroniseres til Aula:\n\n"
                       "  • AULA\n"
                       "  • AULA Institutionskalender\n\n"
                       "Klik 'Næste' for at oprette disse kategorier automatisk i Outlook."),
                 bg=PANEL, fg=DIM, font=self._fonts["body"],
                 wraplength=460, justify="left"
                 ).pack(anchor="w", padx=26, pady=(8, 14))

        self._cat_status = tk.Label(f, text="", bg=PANEL, fg=DIM,
                                    font=self._fonts["small"])
        self._cat_status.pack(anchor="w", padx=26)

        return f

    def _build_step_ready(self):
        f = tk.Frame(self._content, bg=PANEL)

        tk.Label(f, text="TRIN 3 AF 3", bg=PANEL, fg=DIM,
                 font=self._fonts["eyebrow"]).pack(anchor="w", padx=26, pady=(22, 2))
        tk.Label(f, text="Klar!",
                 bg=PANEL, fg=TEXT, font=self._fonts["display_s"]).pack(anchor="w", padx=26)

        tk.Label(f,
                 text=("Opsætningen er nu gennemført.\n\n"
                       "Outlook2Aula er klar til brug. Du kan nu klikke 'Afslut' for at "
                       "lukke dette vindue og begynde at synkronisere dine aftaler."),
                 bg=PANEL, fg=DIM, font=self._fonts["body"],
                 wraplength=460, justify="left"
                 ).pack(anchor="w", padx=26, pady=(12, 20))

        return f

    # ── Navigation ────────────────────────────────────────────────────────────

    def _show_step(self, idx):
        for f in self._steps:
            f.pack_forget()
        self._steps[idx].pack(fill="both", expand=True)
        self._step = idx

        # Update button labels / states
        self._back_btn.config(state="normal" if idx > 0 else "disabled")
        if idx == len(self._steps) - 1:
            self._next_btn.config(text="Afslut")
        else:
            self._next_btn.config(text="Næste →")

    def _go_back(self):
        if self._step > 0:
            self._show_step(self._step - 1)

    def _go_next(self):
        # On last step — close
        if self._step == len(self._steps) - 1:
            self.top.destroy()
            return

        # Step-specific validation / actions
        if self._step == 1:
            # Aula login step — save credentials
            username = self._wiz_username.get().strip()
            password = self._wiz_password.get()
            if not username:
                self._login_status.config(
                    text="Indtast venligst et brugernavn.", fg=ERR)
                return
            try:
                from setupmanager import SetupManager
                SetupManager().update_unilogin(username, password)
                self._login_status.config(
                    text="✓ Login-oplysninger gemt.", fg=OK)
            except Exception as e:
                self._login_status.config(
                    text=f"Fejl ved gemning: {e}", fg=ERR)
                return

        elif self._step == 2:
            # Categories step — create Outlook categories
            try:
                from setupmanager import SetupManager
                SetupManager().create_outlook_categories()
                self._cat_status.config(
                    text="✓ Kategorier oprettet i Outlook.", fg=OK)
            except Exception as e:
                self._cat_status.config(
                    text=f"Advarsel: {e}\nProgrammet virker alligevel, hvis kategorierne allerede findes.",
                    fg="#C98F1C")
                # Don't block navigation on category failure

        self._show_step(self._step + 1)
