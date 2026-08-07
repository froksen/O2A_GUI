import tkinter as tk
from tkinter import messagebox
import threading
import logging
import datetime as dt
import os
import random
import shutil
import time
from typing import ClassVar
from dateutil.relativedelta import relativedelta, SU
import requests
import winshell

from setupmanager import SetupManager, SYNC_BEHAVIOR_OPTIONS
from outlookmanager import OutlookManager
from aula import AulaCalendar, AulaConnection
from calendar_comparer import CalendarComparer
from ui.dialogs.login_error import LoginErrorDialog

# ── Colours (matches launcher.pyw palette) ────────────────────────────────────
BG = "#F2F2F2"
BG_HEADER = "#0078D4"
BG_WHITE = "#FFFFFF"
ACCENT = "#0078D4"
HDR_FG = "#FFFFFF"
TEXT_MAIN = "#1B1B1B"
TEXT_DIM = "#767676"
TEXT_OK = "#107C10"
TEXT_ERR = "#C42B1C"
BORDER = "#D6D6D6"

LOG_COLORS = {
    logging.DEBUG: TEXT_MAIN,
    logging.INFO: ACCENT,
    logging.WARNING: "#CA5010",
    logging.ERROR: TEXT_ERR,
    logging.CRITICAL: "#8764B8",
}

INTERNET_ERROR_MESSAGE = (
    "Det var ikke muligt at oprette forbindelse til internettet! "
    "Forsøger igen ved næste kørsel"
)


class _LogCapture(logging.Handler):
    """Temporary log handler that captures formatted lines during a single event operation."""

    def __init__(self):
        super().__init__(level=logging.DEBUG)
        self._fmt = logging.Formatter("%(levelname)s: %(message)s")
        self.lines: list = []

    def emit(self, record):
        self.lines.append(self._fmt.format(record))

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


class MainWindow:
    """Main application window for Outlook2Aula."""

    # Set by main.pyw after construction
    on_tray_text_updated = None  # callable(text: str)
    on_window_closed = None  # callable()
    show_toast = None  # callable(title: str, msg: str)

    # Rate-limiting af skriveoperationer mod AULA: over denne mængde
    # begivenheder deles arbejdet op i bunker, med en tilfældig pause
    # mellem hver bunke, så AULA ikke stopper processen pga. mange
    # oprettelser/opdateringer/sletninger på kort tid.
    _SYNC_BATCH_THRESHOLD = 100
    _SYNC_BATCH_SIZE = 100
    _SYNC_BATCH_PAUSE_MIN_S = 1 * 60
    _SYNC_BATCH_PAUSE_MAX_S = 5 * 60

    def __init__(self, root: tk.Tk, dry_run: bool = False):
        self.root = root
        self.logger = logging.getLogger("O2A")
        self._dry_run = dry_run

        self._run_freq_var = tk.IntVar(value=2)
        self._next_run_var = tk.StringVar(value="Ukendt")
        self._start_minimized_var = tk.BooleanVar(value=False)
        self._run_at_startup_var = tk.BooleanVar(value=False)
        self._sync_behavior_var = tk.StringVar(value=SYNC_BEHAVIOR_OPTIONS[0][0])

        self.__next_run = dt.datetime.now() + dt.timedelta(hours=2)
        self._countdown_job = None
        self._frequency_job = None
        self._internet_error_tray_announced = False
        self._auto_sync_paused = False
        self._sync_in_progress = False

        self._setup_window()
        self._build_ui()
        self.initial_o2a_check()
        self._start_timers()

    # ── Window ────────────────────────────────────────────────────────────────

    def _setup_window(self):
        title = (
            "Outlook2Aula [DRY-RUN — ingen ændringer gemmes]"
            if self._dry_run
            else "Outlook2Aula"
        )
        self.root.title(title)
        self.root.geometry("720x572")
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        try:
            from PIL import Image, ImageTk

            _img = Image.open("images/exchange.png")
            self._icon_img = ImageTk.PhotoImage(_img)
            self.root.iconphoto(True, self._icon_img)
        except Exception:
            pass

    def _on_close(self):
        self.root.withdraw()
        if callable(self.on_window_closed):
            self.on_window_closed()

    def show(self):
        self.root.deiconify()
        self.root.lift()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _section(self, parent, title, expand=False):
        """Blue bold title + 1px accent separator + white content area (Software Center style)."""
        wrapper = tk.Frame(parent, bg=BG)
        wrapper.pack(fill="both" if expand else "x", expand=expand, pady=(0, 2))

        tk.Label(
            wrapper, text=title, bg=BG, fg=ACCENT, font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", padx=0, pady=(10, 3))
        tk.Frame(wrapper, bg=ACCENT, height=1).pack(fill="x")

        content = tk.Frame(wrapper, bg=BG_WHITE, padx=12, pady=10)
        content.pack(fill="both", expand=expand)
        return content

    def _build_ui(self):
        from ui.shell import Shell

        self.shell = Shell(self.root, controller=self)

    # ── Timers ────────────────────────────────────────────────────────────────

    def _start_timers(self):
        self._schedule_countdown()
        self._schedule_frequency()

    def _schedule_countdown(self):
        self.on_countdown_timer_timeout()
        self._countdown_job = self.root.after(60_000, self._schedule_countdown)

    def _schedule_frequency(self):
        freq = self._get_freq()
        self.__next_run = dt.datetime.now() + dt.timedelta(hours=freq)
        self.on_countdown_timer_timeout()
        self._frequency_job = self.root.after(
            freq * 3_600_000, self._on_frequency_fired
        )

    def _on_frequency_fired(self):
        self.on_runO2A_clicked()
        self._schedule_frequency()

    def _get_freq(self) -> int:
        try:
            return max(1, min(4, self._run_freq_var.get()))
        except tk.TclError:
            return 2

    def _on_freq_changed(self):
        try:
            self._run_freq_var.get()
        except tk.TclError:
            return
        if self._frequency_job:
            self.root.after_cancel(self._frequency_job)
        self._schedule_frequency()

    def on_countdown_timer_timeout(self):
        diff = self.__next_run - dt.datetime.now()
        total_s = max(0, int(diff.total_seconds()))
        hours = total_s // 3600
        minutes = (total_s % 3600) // 60
        text = f"Næste kørsel om {hours} timer og {minutes} minutter (kl. {self.__next_run:%H:%M:%S})"
        self._next_run_var.set(text)
        if callable(self.on_tray_text_updated):
            self.on_tray_text_updated(text)
        if hasattr(self, "shell") and "status" in self.shell.views:
            tile_text = f"kl. {self.__next_run:%H:%M}"
            self.shell.views["status"].update_next_run(tile_text)

    # ── Sync ──────────────────────────────────────────────────────────────────

    def toggle_gui(self, enabled: bool, force: bool = False):
        self._sync_in_progress = not enabled
        if hasattr(self, "shell") and "status" in self.shell.views:
            self.shell.views["status"].sync_btn.set_busy(not enabled, force=force)
        if hasattr(self, "shell") and "opsaet" in self.shell.views:
            self.shell.views["opsaet"].set_sync_behavior_locked(self._sync_in_progress)

    def toggle_auto_pause(self):
        """Toggle automatic sync on/off. Returns True if now paused."""
        self._auto_sync_paused = not self._auto_sync_paused
        if self._auto_sync_paused:
            if self._frequency_job:
                self.root.after_cancel(self._frequency_job)
                self._frequency_job = None
        else:
            self._schedule_frequency()
        return self._auto_sync_paused

    def update_sync_step(self, text: str):
        """Update the sync progress strip on the Status view (thread-safe)."""

        def _do():
            if hasattr(self, "shell") and "status" in self.shell.views:
                self.shell.views["status"].set_sync_step(text)

        self.root.after(0, _do)

    def update_sync_countdown(
        self, chunk_next, chunk_total, pause_seconds, total_seconds
    ):
        """Show a live mm:ss countdown to the next batch plus an hh:mm:ss estimate
        for the remaining sync process (thread-safe)."""

        def _do():
            if hasattr(self, "shell") and "status" in self.shell.views:
                self.shell.views["status"].set_sync_countdown(
                    chunk_next, chunk_total, pause_seconds, total_seconds
                )

        self.root.after(0, _do)

    def _clear_sync_step(self):
        if hasattr(self, "shell") and "status" in self.shell.views:
            self.shell.views["status"].clear_sync_step()

    def get_tray_status(self) -> str:
        """Short status string for tray menu (one line)."""
        if self._auto_sync_paused:
            return "Automatisk kørsel sat på pause"
        return f"næste kørsel kl. {self.__next_run:%H:%M}"

    def on_runO2A_clicked(self):
        if self._dry_run:
            self.toggle_gui(False)
            threading.Thread(target=self._run_demo_sync, daemon=True).start()
            return
        if not self.has_internet_connection():
            self._notify_internet_connection_error()
            return
        self.toggle_gui(False)
        threading.Thread(target=self._run_sync, args=(False,), daemon=True).start()

    def on_forcerunO2A_clicked(self):
        if self._dry_run:
            self.toggle_gui(False, force=True)
            threading.Thread(target=self._run_demo_sync, daemon=True).start()
            return
        if not self.has_internet_connection():
            self._notify_internet_connection_error()
            return
        self.toggle_gui(False, force=True)
        threading.Thread(target=self._run_sync, args=(True,), daemon=True).start()

    _DEMO_EVENTS: ClassVar[list] = [
        ("oprettet", "Forældremøde 2.A", "2026-06-03 08:00:00"),
        ("oprettet", "Skolefest", "2026-06-10 13:00:00"),
        ("oprettet", "Studiedag — ingen elever", "2026-06-17 08:00:00"),
        ("opdateret", "Skole-hjem samtale", "2026-05-28 14:00:00"),
        ("opdateret", "Møde med klasseteam", "2026-06-05 09:30:00"),
        ("fjernet", "Julefrokost (aflyst)", "2026-06-13 12:00:00"),
    ]

    def _run_demo_sync(self):
        import time
        from ui.event_store import EventStore

        steps = [
            ("Logger ind i Aula…", 0.9),
            ("Henter Outlook-begivenheder…", 0.7),
            ("Henter Aula-begivenheder…", 0.8),
            ("Sammenligner kalendere…", 0.5),
            ("Sletter begivenheder…", 0.6),
            ("Opretter begivenheder…", 0.8),
            ("Opdaterer begivenheder…", 0.6),
        ]
        try:
            self.logger.info("[DEMO] Starter simuleret synkronisering med fiktive data")
            for step_text, delay in steps:
                self.update_sync_step(step_text)
                self.logger.info(f"[DEMO] {step_text}")
                time.sleep(delay)

            for action, title, start in self._DEMO_EVENTS:
                tag = {
                    "oprettet": "OPRETTER",
                    "opdateret": "OPDATERER",
                    "fjernet": "FJERNER",
                }[action]
                self.logger.info(f'[DEMO] {tag} BEGIVENHED: "{title}" ({start})')
                EventStore.append(action, title, start, error=False, volatile=True)
                time.sleep(0.15)

            created = sum(1 for a, *_ in self._DEMO_EVENTS if a == "oprettet")
            updated = sum(1 for a, *_ in self._DEMO_EVENTS if a == "opdateret")
            deleted = sum(1 for a, *_ in self._DEMO_EVENTS if a == "fjernet")
            self.logger.info(
                f"[DEMO] Færdig — {created} oprettet · {updated} opdateret · {deleted} fjernet · 0 fejl"
            )

            def _update_stats():
                if hasattr(self, "shell") and "status" in self.shell.views:
                    self.shell.views["status"].update_stats(
                        created=created,
                        updated=updated,
                        deleted=deleted,
                        errors=0,
                        last_run=dt.datetime.now().strftime("%d-%m-%Y %H:%M"),
                    )

            self.root.after(0, _update_stats)
        finally:
            self.root.after(0, lambda: self.toggle_gui(True))
            self.root.after(0, self._clear_sync_step)

    def _run_sync(self, force_update: bool):
        import pythoncom

        pythoncom.CoInitialize()
        try:
            result = self.update_calendar(force_update)
            if result:
                self._internet_error_tray_announced = False
        except Exception:
            import traceback

            tb = traceback.format_exc()
            self.logger.error(tb)
            self._dispatch_critical_error_notification(tb)
        finally:
            pythoncom.CoUninitialize()
            self.root.after(0, lambda: self.toggle_gui(True))
            self.root.after(0, self._clear_sync_step)

    def _dispatch_critical_error_notification(self, traceback_str: str):
        from notification_settings import NotificationSettings

        methods = NotificationSettings().get("on_critical_error")
        if "email" in methods:
            try:
                OutlookManager().send_critical_error_mail(traceback_str)
            except Exception:
                import traceback as tb_mod

                self.logger.error(
                    "Kunne ikke sende kritisk fejlmail: " + tb_mod.format_exc()
                )
        if "toast" in methods and callable(self.show_toast):
            self.show_toast(
                "Outlook2Aula – Kritisk fejl",
                "Synkroniseringen stoppede pga. en uventet fejl.",
            )

    def update_calendar(self, force_update):
        today = dt.datetime.today()
        last_sunday = today + relativedelta(weekday=SU(-1))
        begin_datetime = dt.datetime(
            last_sunday.year, last_sunday.month, last_sunday.day, 1, 0, 0
        )
        end_datetime = dt.datetime(today.year + 1, 7, 1, 0, 0, 0)

        self.logger.info(" ")
        self.logger.info("..:: Sammenligner Outlook og AULA kalenderne :: ...")
        self.logger.info("Mellem datoerne")
        self.logger.info(f" Start: {begin_datetime.strftime('%Y-%m-%d')}")
        self.logger.info(f" End: {end_datetime.strftime('%Y-%m-%d')}")
        self.logger.info(" ")

        setupmgr = SetupManager()
        username = setupmgr.get_aula_username()
        password = setupmgr.get_aula_password()
        idp_id = setupmgr.get_aula_idp_id()
        sync_behavior = setupmgr.get_sync_behavior()

        self.update_sync_step("Logger ind i Aula…")
        aula_connection = AulaConnection()
        login_status = aula_connection.login(username, password, idp_id=idp_id or None)
        setupmgr.set_last_login_status(
            login_status.status,
            dt.datetime.now().isoformat(timespec="seconds"),
            "; ".join(login_status.error_messages),
        )
        if not login_status.status:
            self.root.after(
                0,
                lambda: LoginErrorDialog(
                    self.root,
                    self.shell.fonts,
                    on_fix_credentials=lambda: self.shell._show("konto"),
                ),
            )
            return False

        self.update_sync_step("Henter Outlook-begivenheder…")
        outlookmgr = OutlookManager()

        def _outlook_progress(count):
            self.update_sync_step(f"Henter Outlook-begivenheder… ({count} gennemgået)")

        outlook_events = outlookmgr.get_aulaevents_from_outlook(
            begin_datetime,
            end_datetime,
            progress_callback=_outlook_progress,
            sync_behavior=sync_behavior,
        )

        self.update_sync_step("Henter Aula-begivenheder…")
        aula_calendar = AulaCalendar(aula_connection=aula_connection)

        def _aula_progress(current, total):
            self.update_sync_step(f"Henter Aula-begivenheder… ({current} af {total})")

        aula_events = aula_calendar.getEvents(
            startDatetime=begin_datetime,
            endDatetime=end_datetime,
            progress_callback=_aula_progress,
        )

        self.update_sync_step("Sammenligner kalendere…")
        calendar_comparer = CalendarComparer(aula_events, outlook_events)
        diff_calendars = calendar_comparer.find_unique_events()
        identical_events = calendar_comparer.find_identical_events()

        events_not_deleted, events_not_created, events_not_updated = (
            self.__run_write_operations(
                aula_calendar=aula_calendar,
                delete_ids=diff_calendars["unique_to_aula"],
                aula_events=aula_events,
                create_ids=diff_calendars["unique_to_outlook"],
                outlook_events=outlook_events,
                update_ids=identical_events,
                force_update=force_update,
            )
        )

        combined_error_list = (
            events_not_deleted + events_not_updated + events_not_created
        )
        if combined_error_list:
            self._dispatch_error_notifications(
                events_not_deleted, events_not_created, events_not_updated
            )

        now_str = dt.datetime.now().strftime("%d-%m-%Y %H:%M")
        setupmgr.set_last_run(now_str)

        if hasattr(self, "shell") and "status" in self.shell.views:
            self.shell.views["status"].update_stats(
                created=len(diff_calendars["unique_to_outlook"]),
                updated=len(identical_events),
                deleted=len(diff_calendars["unique_to_aula"]),
                errors=len(combined_error_list),
                last_run=now_str,
            )

        return True

    def __run_write_operations(
        self,
        aula_calendar,
        delete_ids,
        aula_events,
        create_ids,
        outlook_events,
        update_ids,
        force_update,
    ):
        """Bygger alle slette-/opret-/opdaterings-kald som en samlet arbejdsliste og
        kører dem via __run_batched, så bunkning/rate-limiting gælder på tværs af
        alle tre typer skriveoperationer samlet."""
        delete_ids = list(delete_ids)
        create_ids = list(create_ids)
        update_ids = list(update_ids)

        delete_total = len(delete_ids)
        create_total = len(create_ids)
        update_total = len(update_ids)

        work_items = []
        for i, event_id in enumerate(delete_ids, start=1):
            work_items.append(
                (
                    "delete",
                    lambda ev=event_id, idx=i: self.__delete_single_event(
                        aula_calendar, ev, aula_events, idx, delete_total
                    ),
                )
            )
        for i, event_id in enumerate(create_ids, start=1):
            work_items.append(
                (
                    "create",
                    lambda ev=event_id, idx=i: self.__create_single_event(
                        aula_calendar, ev, outlook_events, idx, create_total
                    ),
                )
            )
        for i, event_id in enumerate(update_ids, start=1):
            work_items.append(
                (
                    "update",
                    lambda ev=event_id, idx=i: self.__update_single_event(
                        aula_calendar,
                        ev,
                        outlook_events,
                        aula_events,
                        force_update,
                        idx,
                        update_total,
                    ),
                )
            )

        results = self.__run_batched(work_items)
        return results["delete"], results["create"], results["update"]

    def __run_batched(self, work_items):
        """Kører (kind, callable)-arbejdsposter. Hvis der er mere end
        _SYNC_BATCH_THRESHOLD poster i alt, deles arbejdet op i bunker af
        _SYNC_BATCH_SIZE med en tilfældig pause (1-5 min) mellem hver bunke,
        så AULA ikke stopper processen pga. mange oprettelser/opdateringer/
        sletninger på kort tid. Springes over i dry-run, da der ikke sker
        nogen reelle AULA-kald der kan overbelaste noget."""
        results = {"delete": [], "create": [], "update": []}

        def _run(items):
            for kind, action in items:
                result = action()
                if result is not None:
                    results[kind].append(result)

        total = len(work_items)
        if self._dry_run or total <= self._SYNC_BATCH_THRESHOLD:
            _run(work_items)
            return results

        chunks = [
            work_items[i : i + self._SYNC_BATCH_SIZE]
            for i in range(0, total, self._SYNC_BATCH_SIZE)
        ]
        self.logger.info(
            f"{total} begivenheder skal oprettes/opdateres/slettes i AULA — deler op i "
            f"{len(chunks)} bunker af op til {self._SYNC_BATCH_SIZE} for at undgå at "
            f"AULA stopper processen."
        )
        avg_pause_s = (self._SYNC_BATCH_PAUSE_MIN_S + self._SYNC_BATCH_PAUSE_MAX_S) / 2
        chunk_durations = []
        for chunk_idx, chunk in enumerate(chunks, start=1):
            self.update_sync_step(f"Behandler bunke {chunk_idx} af {len(chunks)}…")
            chunk_start = time.monotonic()
            _run(chunk)
            chunk_durations.append(time.monotonic() - chunk_start)
            if chunk_idx < len(chunks):
                pause_seconds = random.uniform(
                    self._SYNC_BATCH_PAUSE_MIN_S, self._SYNC_BATCH_PAUSE_MAX_S
                )
                pause_minutes = pause_seconds / 60
                self.logger.info(
                    f"Bunke {chunk_idx} af {len(chunks)} færdig. Venter {pause_minutes:.1f} "
                    f"minutter før næste bunke."
                )
                remaining_chunks = len(chunks) - chunk_idx
                remaining_pauses = remaining_chunks - 1
                avg_chunk_s = sum(chunk_durations) / len(chunk_durations)
                total_remaining_s = (
                    pause_seconds
                    + remaining_chunks * avg_chunk_s
                    + remaining_pauses * avg_pause_s
                )
                self.update_sync_countdown(
                    chunk_idx + 1, len(chunks), pause_seconds, total_remaining_s
                )
                time.sleep(pause_seconds)
        return results

    def __create_single_event(
        self, aula_calendar, event_id, outlook_events, index, total
    ):
        from aula.aula_event import AulaEvent

        outlook_event = outlook_events[event_id]
        try:
            event = aula_calendar.convert_outlook_appointmentitem_to_aula_event(
                outlook_event
            )
        except Exception as e:
            try:
                fallback_title = outlook_event["appointmentitem"].subject
            except Exception:
                fallback_title = "(ukendt begivenhed)"
            self.logger.error(
                f'  STATUS: Kunne ikke læse Outlook-begivenhed "{fallback_title}" '
                f"({index} af {total}) — sprunget over: {e}"
            )
            from ui.event_store import EventStore

            EventStore.append(
                "oprettet",
                fallback_title,
                "",
                error=True,
                error_detail="Outlook-begivenheden kunne ikke læses (muligvis slettet/ændret undervejs)",
                log_snippet=str(e),
            )
            err_event = AulaEvent()
            err_event.title = fallback_title
            err_event.all_day = True
            err_event.creation_or_update_errors.event_not_update_or_created = True
            return err_event
        self.logger.info(
            f'OPRETTER BEGIVENHED ({index} af {total}): "{event.title}" med start dato {event.start_date_time}'
        )
        self.update_sync_step(f"Opretter begivenheder… ({index} af {total})")
        if self._dry_run:
            self.logger.info("  STATUS: [DRY-RUN] Oprettelse sprunget over")
            return None

        _cap = _LogCapture()
        self.logger.addHandler(_cap)
        try:
            event = aula_calendar.get_atendees_ids(event)
            created_event_id, error_text = aula_calendar.createSimpleEvent(event)
            if created_event_id is not None:
                self.logger.info("  STATUS: Oprettelse lykkedes")
            else:
                event.creation_or_update_errors.event_not_update_or_created = True
                event.creation_or_update_errors.json_dump = error_text
                self.logger.info("  STATUS: Oprettelse mislykkedes")
        except Exception as e:
            self.logger.error(f"  STATUS: Uventet fejl ved oprettelse: {e}")
            event.creation_or_update_errors.event_not_update_or_created = True
        finally:
            self.logger.removeHandler(_cap)
        _has_err = (
            event.creation_or_update_errors.event_not_update_or_created
            or event.creation_or_update_errors.attendees_not_found
        )
        _error_detail = None
        if _has_err:
            if event.creation_or_update_errors.attendees_not_found:
                _names = ", ".join(
                    str(p) for p in event.creation_or_update_errors.attendees_not_found
                )
                _error_detail = f"Person ikke fundet: {_names}"
            else:
                _error_detail = "Oprettelse mislykkedes"
        from ui.event_store import EventStore

        EventStore.append(
            "oprettet",
            event.title,
            str(event.start_date_time),
            error=_has_err,
            error_detail=_error_detail,
            log_snippet=_cap.text if _has_err else None,
        )
        return event if _has_err else None

    def __update_single_event(
        self,
        aula_calendar,
        event_id,
        outlook_events,
        aula_events,
        force_update,
        index,
        total,
    ):
        from aula.aula_event import AulaEvent

        self.update_sync_step(f"Opdaterer begivenheder… ({index} af {total})")
        outlook_event = outlook_events[event_id]
        if outlook_event is None:
            return None
        aula_event = aula_events[event_id]

        try:
            outlook_ReminderMinutesBeforeStart = outlook_event[
                "appointmentitem"
            ].ReminderMinutesBeforeStart
            outlook_Start = outlook_event["appointmentitem"].start
            outlook_LastModificationTime = outlook_event[
                "appointmentitem"
            ].LastModificationTime
            outlook_diff = outlook_Start - outlook_LastModificationTime
            outlook_diff_minuts = outlook_diff.total_seconds() / 60

            outlook_event = aula_calendar.convert_outlook_appointmentitem_to_aula_event(
                outlook_event
            )
        except Exception as e:
            fallback_title = aula_event["appointmentitem"].subject
            self.logger.error(
                f'  STATUS: Kunne ikke læse Outlook-begivenhed "{fallback_title}" '
                f"({index} af {total}) — sprunget over: {e}"
            )
            from ui.event_store import EventStore

            EventStore.append(
                "opdateret",
                fallback_title,
                "",
                error=True,
                error_detail="Outlook-begivenheden kunne ikke læses (muligvis slettet/ændret undervejs)",
                log_snippet=str(e),
            )
            err_event = AulaEvent()
            err_event.title = fallback_title
            err_event.all_day = True
            err_event.creation_or_update_errors.event_not_update_or_created = True
            return err_event

        if (
            not force_update
            and outlook_diff_minuts <= outlook_ReminderMinutesBeforeStart
        ):
            subject = aula_event["appointmentitem"].subject
            self.logger.debug(
                f'SKIPPER Begivenhed: "{subject}" med start dato {outlook_event.start_date_time}'
            )
            return None

        if (
            str(aula_event["outlook_LastModificationTime"])
            != str(outlook_event.outlook_last_modification_time)
            or force_update
        ):
            outlook_event.id = aula_event["appointmentitem"].aula_id
            event_title = aula_event["appointmentitem"].subject
            self.logger.info(
                f'OPDATERER BEGIVENHED: "{event_title}" med start dato {outlook_event.start_date_time}'
            )
            if self._dry_run:
                self.logger.info("  STATUS: [DRY-RUN] Opdatering sprunget over")
            else:
                _cap = _LogCapture()
                self.logger.addHandler(_cap)
                try:
                    outlook_event = aula_calendar.get_atendees_ids(outlook_event)
                    if aula_calendar.updateEvent(outlook_event):
                        self.logger.info("  STATUS: Opdatering lykkedes")
                    else:
                        self.logger.info("  STATUS: Opdatering mislykkedes")
                        outlook_event.creation_or_update_errors.event_not_update_or_created = True
                except Exception as e:
                    self.logger.error(f"  STATUS: Uventet fejl ved opdatering: {e}")
                    outlook_event.creation_or_update_errors.event_not_update_or_created = True
                finally:
                    self.logger.removeHandler(_cap)
                _upd_err = (
                    outlook_event.creation_or_update_errors.event_not_update_or_created
                )
                _upd_attendee_err = bool(
                    outlook_event.creation_or_update_errors.attendees_not_found
                )
                _upd_error_detail = None
                if _upd_err or _upd_attendee_err:
                    if _upd_attendee_err:
                        _names = ", ".join(
                            str(p)
                            for p in outlook_event.creation_or_update_errors.attendees_not_found
                        )
                        _upd_error_detail = f"Person ikke fundet: {_names}"
                    else:
                        _upd_error_detail = "Opdatering mislykkedes"
                from ui.event_store import EventStore

                EventStore.append(
                    "opdateret",
                    event_title,
                    str(outlook_event.start_date_time),
                    error=(_upd_err or _upd_attendee_err),
                    error_detail=_upd_error_detail,
                    log_snippet=_cap.text if (_upd_err or _upd_attendee_err) else None,
                )

        if (
            outlook_event.creation_or_update_errors.event_not_update_or_created
            or outlook_event.creation_or_update_errors.attendees_not_found
        ):
            return outlook_event
        return None

    def __delete_single_event(self, aula_calendar, event_id, aula_events, index, total):
        from aula.aula_event import AulaEvent

        event = aula_events[event_id]
        event_title = event["appointmentitem"].subject
        aula_id = event["appointmentitem"].aula_id
        self.logger.info(f'FJERNER BEGIVENHED ({index} af {total}): "{event_title}"')
        self.update_sync_step(f"Sletter begivenheder… ({index} af {total})")
        if self._dry_run:
            self.logger.info("  STATUS: [DRY-RUN] Fjernelse sprunget over")
            return None

        _cap = _LogCapture()
        self.logger.addHandler(_cap)
        try:
            _deleted_ok = aula_calendar.deleteEvent(aula_id)
        except Exception as e:
            self.logger.error(f"  STATUS: Uventet fejl ved sletning: {e}")
            _deleted_ok = False
        finally:
            self.logger.removeHandler(_cap)
        from ui.event_store import EventStore

        EventStore.append(
            "fjernet",
            event_title,
            str(event["appointmentitem"].start),
            error=not _deleted_ok,
            error_detail="Sletning mislykkedes" if not _deleted_ok else None,
            log_snippet=_cap.text if not _deleted_ok else None,
        )
        if _deleted_ok:
            self.logger.info("  STATUS: Fjernelse lykkedes")
            return None

        self.logger.info("  STATUS: Fjernelse mislykkedes")
        err_event = AulaEvent()
        err_event.title = event_title
        err_event.all_day = True
        err_event.start_date = str(event["appointmentitem"].start)
        err_event.creation_or_update_errors.event_not_deleted = True
        return err_event

    # ── Notifications ─────────────────────────────────────────────────────────

    def _dispatch_error_notifications(
        self, events_not_deleted, events_not_created, events_not_updated
    ):
        from notification_settings import NotificationSettings, EVENTS as _EV

        ns = NotificationSettings()

        delete_errors = events_not_deleted
        create_errors = [
            e
            for e in events_not_created
            if e.creation_or_update_errors.event_not_update_or_created
        ]
        update_errors = [
            e
            for e in events_not_updated
            if e.creation_or_update_errors.event_not_update_or_created
        ]
        person_errors = [
            e
            for e in events_not_created + events_not_updated
            if e.creation_or_update_errors.attendees_not_found
        ]

        buckets = [
            ("on_delete_error", delete_errors),
            ("on_create_error", create_errors),
            ("on_update_error", update_errors),
            ("on_person_not_found", person_errors),
        ]

        email_set = {}  # id(e) → event, no duplicates
        toast_parts = []

        for key, events in buckets:
            if not events:
                continue
            methods = ns.get(key)  # set, e.g. {'email'} or {'email','toast'}
            if "email" in methods:
                for e in events:
                    email_set[id(e)] = e
            if "toast" in methods:
                label = next((lbl for k, lbl in _EV if k == key), key)
                toast_parts.append(f"{len(events)} × {label.lower()}")

        if email_set:
            OutlookManager().send_a_aula_creation_or_update_error_mail(
                list(email_set.values())
            )

        if toast_parts and callable(self.show_toast):
            self.show_toast(
                "Outlook2Aula – Fejl",
                "Fejl under synkronisering:\n" + "\n".join(toast_parts),
            )

    # ── Logging ───────────────────────────────────────────────────────────────

    def update_status(self, text: str, record: logging.LogRecord):
        """Append a formatted log line to the status log widget (thread-safe)."""
        if hasattr(self, "shell") and "status" in self.shell.views:
            self.shell.views["status"].update_log(text, record)

    # ── Internet ──────────────────────────────────────────────────────────────

    def has_internet_connection(self) -> bool:
        try:
            requests.get("https://www.google.dk/", timeout=5)
            return True
        except requests.ConnectionError:
            return False

    def _notify_internet_connection_error(self):
        self.logger.critical(INTERNET_ERROR_MESSAGE)
        if not self._internet_error_tray_announced:
            self._internet_error_tray_announced = True

    # ── Initial setup ─────────────────────────────────────────────────────────

    def initial_o2a_check(self):
        self._csv_exists("./personer_skabelon.csv", "personer.csv")
        self._csv_exists("./personer_ignorer_skabelon.csv", "personer_ignorer.csv")

        setupmgr = SetupManager()
        try:
            setupmgr.create_outlook_categories()
        except AttributeError as e:
            self.logger.warning(
                "Det var ikke muligt at undersøge/oprette kategorier i Outlook. "
                f"Hvis kategorierne allerede findes i Outlook, virker programmet alligevel. ({e})"
            )

        self._start_minimized_var.set(setupmgr.hide_on_startup())
        self._run_at_startup_var.set(self.autostart_shortcut_exist())
        self._sync_behavior_var.set(setupmgr.get_sync_behavior())

        last_run = setupmgr.get_last_run()
        if last_run and hasattr(self, "shell") and "status" in self.shell.views:
            self.shell.views["status"].set_last_run_display(last_run)

        # First-run wizard
        try:
            if not SetupManager().get_aula_username():
                from ui.dialogs.wizard import FirstRunWizard

                self.root.after(
                    500, lambda: FirstRunWizard(self.root, self.shell.fonts)
                )
        except Exception:
            pass

    def _csv_exists(self, source, destination):
        if not os.path.isfile(destination):
            try:
                shutil.copyfile(source, destination)
            except Exception:
                self.logger.critical(f"Kunne ikke oprette filen {source}")

    # ── Settings ──────────────────────────────────────────────────────────────

    def update_hide_on_startup_clicked(self):
        SetupManager().set_hide_on_startup(str(self._start_minimized_var.get()))

    _SYNC_BEHAVIORS_WITH_MANY_EVENTS = ("all_direct", "aula_busy_fallback")

    def on_sync_behavior_changed(self, *_args):
        behavior = self._sync_behavior_var.get()
        SetupManager().set_sync_behavior(behavior)
        if behavior in self._SYNC_BEHAVIORS_WITH_MANY_EVENTS:
            messagebox.showwarning(
                "Flere begivenheder overføres",
                "Denne indstilling overfører langt flere begivenheder end før.\n\n"
                "Den første synkronisering kan derfor tage lang tid, da begivenhederne "
                "bliver delt op i mindre dele for ikke at overbelaste AULA. "
                "Efterfølgende kørsler vil være hurtigere.",
                parent=self.root,
            )

    def on_run_program_at_startup_clicked(self):
        target_path = os.path.join(os.getcwd(), "updateandrun.bat")
        shortcut_path = self.get_autostart_shortcut()
        if self._run_at_startup_var.get():
            self._create_shortcut(target_path, shortcut_path)
        else:
            try:
                os.remove(shortcut_path)
            except OSError as e:
                self.logger.warning(f"Kunne ikke fjerne genvej: {e}")

    def get_autostart_shortcut(self) -> str:
        return os.path.join(winshell.startup(common=False), "Outlook2Aula.lnk")

    def autostart_shortcut_exist(self) -> bool:
        return os.path.isfile(self.get_autostart_shortcut())

    def _create_shortcut(self, target, shortcut_path):
        try:
            winshell.CreateShortcut(
                Path=shortcut_path,
                Target=target,
                Icon=(target, 0),
                Description="Shortcut to main.pyw for automatic startup",
            )
        except Exception as e:
            self.logger.warning(f"Kunne ikke oprette genvej: {e}")

    # ── CSV editors ───────────────────────────────────────────────────────────

    def on_actionIgnore_people_list_triggered(self):
        self._open_excel("personer_ignorer.csv")

    def on_actionOutlook_Aulanavne_liste_triggered(self):
        self._open_excel("personer.csv")

    def _open_excel(self, filename):
        os.system(f'start excel.exe "{filename}"')
