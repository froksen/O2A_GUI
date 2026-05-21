# -*- coding: utf-8 -*-
import tkinter as tk
import threading
import logging
import datetime as dt
import os
import shutil
from pathlib import Path
from dateutil.relativedelta import relativedelta, SU
import requests
import winshell

from setupmanager import SetupManager
from outlookmanager import OutlookManager
from aula import AulaCalendar, AulaConnection
from calendar_comparer import CalendarComparer
from unilogindialog import UniloginDialog

# ── Colours (matches launcher.pyw palette) ────────────────────────────────────
BG        = "#F2F2F2"
BG_HEADER = "#0078D4"
BG_WHITE  = "#FFFFFF"
ACCENT    = "#0078D4"
HDR_FG    = "#FFFFFF"
TEXT_MAIN = "#1B1B1B"
TEXT_DIM  = "#767676"
TEXT_OK   = "#107C10"
TEXT_ERR  = "#C42B1C"
BORDER    = "#D6D6D6"

LOG_COLORS = {
    logging.DEBUG:    TEXT_MAIN,
    logging.INFO:     ACCENT,
    logging.WARNING:  "#CA5010",
    logging.ERROR:    TEXT_ERR,
    logging.CRITICAL: "#8764B8",
}

INTERNET_ERROR_MESSAGE = (
    "Det var ikke muligt at oprette forbindelse til internettet! "
    "Forsøger igen ved næste kørsel"
)


class MainWindow:
    """Main application window for Outlook2Aula."""

    # Set by main.pyw after construction
    on_tray_text_updated = None   # callable(text: str)
    on_window_closed     = None   # callable()

    def __init__(self, root: tk.Tk, dry_run: bool = False):
        self.root    = root
        self.logger  = logging.getLogger('O2A')
        self._dry_run = dry_run

        self._run_freq_var        = tk.IntVar(value=2)
        self._next_run_var        = tk.StringVar(value="Ukendt")
        self._start_minimized_var = tk.BooleanVar(value=False)
        self._run_at_startup_var  = tk.BooleanVar(value=False)

        self.__next_run                    = dt.datetime.now() + dt.timedelta(hours=2)
        self._countdown_job                = None
        self._frequency_job                = None
        self._internet_error_tray_announced = False

        self._setup_window()
        self._build_ui()
        self.initial_o2a_check()
        self._start_timers()

    # ── Window ────────────────────────────────────────────────────────────────

    def _setup_window(self):
        title = "Outlook2Aula [DRY-RUN — ingen ændringer gemmes]" if self._dry_run else "Outlook2Aula"
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

        tk.Label(wrapper, text=title, bg=BG, fg=ACCENT,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=0, pady=(10, 3))
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
        self._frequency_job = self.root.after(freq * 3_600_000, self._on_frequency_fired)

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
        diff    = self.__next_run - dt.datetime.now()
        total_s = max(0, int(diff.total_seconds()))
        hours   = total_s // 3600
        minutes = (total_s % 3600) // 60
        text = f"Næste kørsel om {hours} timer og {minutes} minutter (kl. {self.__next_run:%H:%M:%S})"
        self._next_run_var.set(text)
        if callable(self.on_tray_text_updated):
            self.on_tray_text_updated(text)

    # ── Sync ──────────────────────────────────────────────────────────────────

    def toggle_gui(self, enabled: bool, force: bool = False):
        if hasattr(self, 'shell') and "status" in self.shell.views:
            self.shell.views["status"].sync_btn.set_busy(not enabled, force=force)

    def on_runO2A_clicked(self):
        if not self.has_internet_connection():
            self._notify_internet_connection_error()
            return
        self.toggle_gui(False)
        threading.Thread(target=self._run_sync, args=(False,), daemon=True).start()

    def on_forcerunO2A_clicked(self):
        if not self.has_internet_connection():
            self._notify_internet_connection_error()
            return
        self.toggle_gui(False, force=True)
        threading.Thread(target=self._run_sync, args=(True,), daemon=True).start()

    def _run_sync(self, force_update: bool):
        import pythoncom
        pythoncom.CoInitialize()
        try:
            result = self.update_calendar(force_update)
            if result:
                self._internet_error_tray_announced = False
        except Exception:
            import traceback
            self.logger.error(traceback.format_exc())
        finally:
            pythoncom.CoUninitialize()
            self.root.after(0, lambda: self.toggle_gui(True))

    def update_calendar(self, force_update):
        today       = dt.datetime.today()
        last_sunday = today + relativedelta(weekday=SU(-1))
        begin_datetime = dt.datetime(last_sunday.year, last_sunday.month, last_sunday.day, 1, 0, 0)
        end_datetime   = dt.datetime(today.year + 1, 7, 1, 0, 0, 0)

        self.logger.info(" ")
        self.logger.info("..:: Sammenligner Outlook og AULA kalenderne :: ...")
        self.logger.info("Mellem datoerne")
        self.logger.info(f" Start: {begin_datetime.strftime('%Y-%m-%d')}")
        self.logger.info(f" End: {end_datetime.strftime('%Y-%m-%d')}")
        self.logger.info(" ")

        setupmgr = SetupManager()
        username = setupmgr.get_aula_username()
        password = setupmgr.get_aula_password()

        aula_connection = AulaConnection()
        aula_connection.login(username, password)

        outlookmgr    = OutlookManager()
        outlook_events = outlookmgr.get_aulaevents_from_outlook(begin_datetime, end_datetime)

        aula_calendar = AulaCalendar(aula_connection=aula_connection)
        aula_events   = aula_calendar.getEvents(startDatetime=begin_datetime, endDatetime=end_datetime)

        calendar_comparer = CalendarComparer(aula_events, outlook_events)
        diff_calendars    = calendar_comparer.find_unique_events()
        identical_events  = calendar_comparer.find_identical_events()

        events_not_deleted = self.__delete_aula_events(aula_calendar, diff_calendars["unique_to_aula"], aula_events=aula_events)
        events_not_created = self.__create_aula_events(aula_calendar, diff_calendars["unique_to_outlook"], outlook_events)
        events_not_updated = self.__update_aula_events(
            aula_calendar=aula_calendar, identical_events_id=identical_events,
            outlook_events=outlook_events, aula_events=aula_events, force_update=force_update)

        combined_error_list = events_not_deleted + events_not_updated + events_not_created
        if combined_error_list:
            OutlookManager().send_a_aula_creation_or_update_error_mail(combined_error_list)

        if hasattr(self, 'shell') and "status" in self.shell.views:
            import datetime as dt
            self.shell.views["status"].update_stats(
                created=len(diff_calendars["unique_to_outlook"]),
                updated=len(identical_events),
                deleted=len(diff_calendars["unique_to_aula"]),
                errors=len(combined_error_list),
                last_run=dt.datetime.now().strftime("%d-%m-%Y %H:%M")
            )

        return True

    def __create_aula_events(self, aula_calendar, event_ids_to_create, outlook_events):
        event_with_errors = []
        index = 1
        outlook_events_count = len(outlook_events)
        for event_id in event_ids_to_create:
            outlook_event = outlook_events[event_id]
            event = aula_calendar.convert_outlook_appointmentitem_to_aula_event(outlook_event)
            self.logger.info(f"OPRETTER BEGIVENHED ({index} af {outlook_events_count}): \"{event.title}\" med start dato {event.start_date_time}")
            if self._dry_run:
                self.logger.info("  STATUS: [DRY-RUN] Oprettelse sprunget over")
            else:
                event = aula_calendar.get_atendees_ids(event)
                event_id, error_text = aula_calendar.createSimpleEvent(event)
                if event_id is not None:
                    self.logger.info("  STATUS: Oprettelse lykkedes")
                else:
                    event.creation_or_update_errors.event_not_update_or_created = True
                    event.creation_or_update_errors.json_dump = error_text
                    self.logger.info("  STATUS: Oprettelse mislykkedes")
                if event.creation_or_update_errors.event_not_update_or_created or event.creation_or_update_errors.attendees_not_found:
                    event_with_errors.append(event)
            index += 1
        return event_with_errors

    def __update_aula_events(self, aula_calendar, identical_events_id, outlook_events, aula_events, force_update=False):
        event_with_errors = []
        index = 1
        for event_id in identical_events_id:
            outlook_event = outlook_events[event_id]
            if outlook_event is None:
                continue
            outlook_ReminderMinutesBeforeStart = outlook_event["appointmentitem"].ReminderMinutesBeforeStart
            outlook_Start                      = outlook_event["appointmentitem"].start
            outlook_LastModificationTime       = outlook_event["appointmentitem"].LastModificationTime
            outlook_diff        = outlook_Start - outlook_LastModificationTime
            outlook_diff_minuts = outlook_diff.total_seconds() / 60

            outlook_event = aula_calendar.convert_outlook_appointmentitem_to_aula_event(outlook_event)
            aula_event    = aula_events[event_id]

            if not force_update and outlook_diff_minuts <= outlook_ReminderMinutesBeforeStart:
                subject = aula_event["appointmentitem"].subject
                self.logger.debug(f"SKIPPER Begivenhed: \"{subject}\" med start dato {outlook_event.start_date_time}")
                continue

            if str(aula_event["outlook_LastModificationTime"]) != str(outlook_event.outlook_last_modification_time) or force_update:
                outlook_event.id = aula_event["appointmentitem"].aula_id
                event_title = aula_event["appointmentitem"].subject
                self.logger.info(f"OPDATERER BEGIVENHED: \"{event_title}\" med start dato {outlook_event.start_date_time}")
                if self._dry_run:
                    self.logger.info("  STATUS: [DRY-RUN] Opdatering sprunget over")
                else:
                    outlook_event = aula_calendar.get_atendees_ids(outlook_event)
                    if aula_calendar.updateEvent(outlook_event):
                        self.logger.info("  STATUS: Opdatering lykkedes")
                    else:
                        self.logger.info("  STATUS: Opdatering mislykkedes")
                        outlook_event.creation_or_update_errors.event_not_update_or_created = True

            if outlook_event.creation_or_update_errors.event_not_update_or_created or outlook_event.creation_or_update_errors.attendees_not_found:
                event_with_errors.append(outlook_event)
            index += 1
        return event_with_errors

    def __delete_aula_events(self, aula_calendar, event_ids_to_delete, aula_events):
        from aula.aula_event import AulaEvent
        events_not_deleted = []
        index = 1
        aula_events_count = len(event_ids_to_delete)
        for event_id in event_ids_to_delete:
            event      = aula_events[event_id]
            event_title = event["appointmentitem"].subject
            aula_id    = event["appointmentitem"].aula_id
            self.logger.info(f"FJERNER BEGIVENHED ({index} af {aula_events_count}): \"{event_title}\"")
            if self._dry_run:
                self.logger.info("  STATUS: [DRY-RUN] Fjernelse sprunget over")
            else:
                if aula_calendar.deleteEvent(aula_id):
                    self.logger.info("  STATUS: Fjernelse lykkedes")
                else:
                    self.logger.info("  STATUS: Fjernelse mislykkedes")
                    err_event = AulaEvent()
                    err_event.title = event_title
                    err_event.all_day = True
                    err_event.start_date = str(event["appointmentitem"].start)
                    err_event.creation_or_update_errors.event_not_deleted = True
                    events_not_deleted.append(err_event)
            index += 1
        return events_not_deleted

    # ── Logging ───────────────────────────────────────────────────────────────

    def update_status(self, text: str, record: logging.LogRecord):
        """Append a formatted log line to the status log widget (thread-safe)."""
        if hasattr(self, 'shell') and "status" in self.shell.views:
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
                f"Hvis kategorierne allerede findes i Outlook, virker programmet alligevel. ({e})")

        self._start_minimized_var.set(setupmgr.hide_on_startup())
        self._run_at_startup_var.set(self.autostart_shortcut_exist())

        # First-run wizard
        try:
            if not SetupManager().get_aula_username():
                from ui.dialogs.wizard import FirstRunWizard
                self.root.after(500, lambda: FirstRunWizard(self.root, self.shell.fonts))
        except Exception:
            pass

    def _csv_exists(self, source, destination):
        if not os.path.isfile(destination):
            try:
                shutil.copyfile(source, destination)
            except Exception:
                self.logger.critical(f"Kunne ikke oprette filen {source}")

    def _get_version_text(self):
        base_dir = Path(__file__).resolve().parent
        try:
            import git
            repo = git.Repo(base_dir, search_parent_directories=True)
            commit_dt = dt.datetime.fromtimestamp(repo.head.commit.committed_date)
            return commit_dt.strftime('%d-%m-%Y %H:%M:%S')
        except Exception:
            version_file = base_dir / "version.txt"
            if version_file.is_file():
                return version_file.read_text(encoding="utf-8").strip() or None
            return None

    # ── Settings ──────────────────────────────────────────────────────────────

    def update_hide_on_startup_clicked(self):
        SetupManager().set_hide_on_startup(str(self._start_minimized_var.get()))

    def on_run_program_at_startup_clicked(self):
        target_path   = os.path.join(os.getcwd(), 'updateandrun.bat')
        shortcut_path = self.get_autostart_shortcut()
        if self._run_at_startup_var.get():
            self._create_shortcut(target_path, shortcut_path)
        else:
            try:
                os.remove(shortcut_path)
            except OSError as e:
                self.logger.warning(f"Kunne ikke fjerne genvej: {e}")

    def get_autostart_shortcut(self) -> str:
        return os.path.join(winshell.startup(common=False), 'Outlook2Aula.lnk')

    def autostart_shortcut_exist(self) -> bool:
        return os.path.isfile(self.get_autostart_shortcut())

    def _create_shortcut(self, target, shortcut_path):
        try:
            winshell.CreateShortcut(
                Path=shortcut_path,
                Target=target,
                Icon=(target, 0),
                Description="Shortcut to main.pyw for automatic startup"
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

    # ── Login dialog ──────────────────────────────────────────────────────────

    def runUniSetup(self):
        UniloginDialog(self.root).exec()
