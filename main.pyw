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
    logger = logging.getLogger('O2A')
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler('o2a.log')
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

    # ── System tray ────────────────────────────────────────────────────────────
    tray = None
    try:
        import pystray
        from PIL import Image as PILImage

        icon_img = PILImage.open("images/Exchange.png")

        def _show_window():
            root.after(0, window.show)

        def _quit_app():
            root.after(0, root.quit)

        tray_menu = pystray.Menu(
            pystray.MenuItem("Vis",        _show_window),
            pystray.MenuItem("Afslut O2A", _quit_app),
        )
        tray = pystray.Icon("O2A", icon_img, "O2A", tray_menu)

        window.on_tray_text_updated = lambda text: setattr(tray, 'title', f"O2A: {text}")
        window.on_window_closed     = lambda: tray.notify("O2A", "Programmet fortsætter i baggrunden.")

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
