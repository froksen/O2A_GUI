# main.pyw — Entry point for Outlook2Aula
# Builds the tkinter root, wires up logging, system tray, and starts the app.

import tkinter as tk
import sys
import ctypes
import logging

from mainwindow import MainWindow
from setupmanager import SetupManager

INTERNET_ERROR_TITLE   = "O2A"
INTERNET_ERROR_MESSAGE = (
    "Det var ikke muligt at oprette forbindelse til internettet! "
    "Forsøger igen ved næste kørsel"
)


class TkLogHandler(logging.Handler):
    """Logging handler that writes to the MainWindow text widget (thread-safe)."""

    def __init__(self, window: MainWindow):
        super().__init__()
        self._window = window

    def emit(self, record):
        s = self.format(record)
        self._window.update_status(s, record)


if __name__ == "__main__":
    myappid = 'of.o2a.gui'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    dry_run = "--dry-run" in sys.argv

    root   = tk.Tk()
    window = MainWindow(root, dry_run=dry_run)

    # ── Logging ────────────────────────────────────────────────────────────────
    LOG_RETENTION_DAYS = 14

    logger = logging.getLogger('O2A')
    logger.setLevel(logging.DEBUG)

    import os
    import glob as _glob
    import time as _time
    from logging.handlers import TimedRotatingFileHandler
    log_dir = os.path.expandvars(r"%APPDATA%\O2A")
    os.makedirs(log_dir, exist_ok=True)

    # Slet backup-logfiler der er ældre end LOG_RETENTION_DAYS dage
    _cutoff = _time.time() - LOG_RETENTION_DAYS * 86400
    for _f in _glob.glob(os.path.join(log_dir, "o2a.log.*")):
        try:
            if os.path.getmtime(_f) < _cutoff:
                os.remove(_f)
        except Exception:
            pass

    # Slet gammel logfil i programmappen hvis den findes
    _local_log = os.path.join(os.path.dirname(os.path.abspath(__file__)), "o2a.log")
    if os.path.exists(_local_log):
        try:
            os.remove(_local_log)
        except Exception:
            pass

    fh = TimedRotatingFileHandler(
        os.path.join(log_dir, "o2a.log"),
        when="midnight", backupCount=LOG_RETENTION_DAYS, encoding="utf-8")
    fh.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    h = TkLogHandler(window)
    h.setLevel(logging.INFO)

    base_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    gui_fmt  = '%(asctime)s - %(levelname)s - %(message)s'
    fh.setFormatter(logging.Formatter(base_fmt))
    ch.setFormatter(logging.Formatter(base_fmt))
    h.setFormatter(logging.Formatter(gui_fmt))

    logger.addHandler(fh)
    logger.addHandler(ch)
    logger.addHandler(h)

    from ui.logfil_view import LogStore

    class _StoreHandler(logging.Handler):
        def emit(self, record):
            LogStore.append(record)

    store_h = _StoreHandler()
    store_h.setLevel(logging.DEBUG)
    logger.addHandler(store_h)

    # ── System tray ────────────────────────────────────────────────────────────
    tray = None
    try:
        import pystray
        from PIL import Image as PILImage

        icon_img = PILImage.open("images/Exchange.png")

        def _show_window(icon=None, item=None):
            root.after(0, window.show)

        def _show_settings(icon=None, item=None):
            def _do():
                window.show()
                if hasattr(window, 'shell'):
                    window.shell._show("opsaet")
            root.after(0, _do)

        def _sync_now(icon=None, item=None):
            root.after(0, window.on_runO2A_clicked)

        def _force_sync(icon=None, item=None):
            root.after(0, window.on_forcerunO2A_clicked)

        def _toggle_pause(icon=None, item=None):
            window.toggle_auto_pause()
            if tray is not None:
                tray.update_menu()

        def _quit_app(icon=None, item=None):
            root.after(0, root.quit)

        def _pause_label(item):
            return "Genoptag automatisk kørsel" if window._auto_sync_paused else "Sæt automatisk kørsel på pause"

        def _status_label(item):
            return window.get_tray_status()

        tray_menu = pystray.Menu(
            pystray.MenuItem("Outlook2Aula", None, enabled=False),
            pystray.MenuItem(_status_label,  None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Synkronisér nu",              _sync_now),
            pystray.MenuItem("Tving fuld synkronisering",   _force_sync),
            pystray.MenuItem(_pause_label,                  _toggle_pause),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Åbn vindue",      _show_window),
            pystray.MenuItem("Indstillinger",   _show_settings),
            pystray.MenuItem("Afslut O2A",      _quit_app),
        )
        tray = pystray.Icon("O2A", icon_img, "Outlook2Aula", tray_menu)

        window.on_tray_text_updated = lambda text: tray.update_menu() if tray is not None else None
        window.on_window_closed     = lambda: tray.notify("Outlook2Aula", "Programmet fortsætter i baggrunden.")
        window.show_toast           = lambda title, msg: tray.notify(title, msg)

        tray.run_detached()

    except Exception as e:
        logger.warning(f"System tray ikke tilgængeligt: {e}")

    # ── Start ──────────────────────────────────────────────────────────────────
    if SetupManager().hide_on_startup():
        root.withdraw()

    logger.info('O2A startet')
    root.mainloop()

    if tray is not None:
        try:
            tray.stop()
        except Exception:
            pass
