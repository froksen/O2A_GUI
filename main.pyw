# This Python file uses the following encoding: utf-8
from __future__ import unicode_literals

import sys
import os
import winshell
from win32com.client import Dispatch
import os.path
import shutil
import time
import traceback
import requests
import ctypes
from dateutil.relativedelta import relativedelta, SU
import datetime as dt
import logging

#Qt Imports
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QApplication, QMainWindow, QDialog, QSystemTrayIcon, QMenu,QStyle
from PySide6.QtCore import QRunnable, Signal, QObject, QThreadPool, Slot,QTimer

#Dialogs
from mainwindow import Ui_MainWindow
from unilogindialog import Ui_UniloginDialog

#Other classes
from eventmanager import EventManager
from setupmanager import SetupManager
from outlookmanager import OutlookManager
import git






#https://www.pythonguis.com/tutorials/pyside6-first-steps-qt-designer/
#https://www.pythonguis.com/tutorials/pyside6-creating-your-first-window/

class MainWindowSignals(QObject):
    trayicon_text_updated = Signal(object)
    window_closed = Signal()


class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        tuple (exctype, value, traceback.format_exc() )

    result
        object data returned from processing, anything

    progress
        int indicating % progress

    '''
    finished = Signal()
    error = Signal(tuple)
    result = Signal(object)
    status = Signal(object)
    progress = Signal(int)


class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        self.kwargs['progress_callback'] = self.signals.progress

    @Slot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing

        finally:
            self.signals.finished.emit()  # Done

class MainWindow(QMainWindow, Ui_MainWindow):
    COLORS = {
            logging.DEBUG: 'black',
            logging.INFO: 'blue',
            logging.WARNING: 'orange',
            logging.ERROR: 'red',
            logging.CRITICAL: 'purple',
        }

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.signals = MainWindowSignals()
        self.setup_gui()

        self.internal_errors_count = 0
        self.__next_run = dt.datetime.now() + dt.timedelta(hours=self.runFrequency.value())

        self.threadpool = QThreadPool()
        #print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        self.initialize_run_frequency_timer() #Timer der bruges til, hvor langtid der går mellem der køres sammenligning
        self.initialize_countdown_timer() #Timer der opdaterer intervallget i GUI´en.

        self.initial_o2a_check()#Basal opsætning af programmet

    def setup_gui(self):
        self.runO2A.clicked.connect(self.on_runO2A_clicked)
        self.forcerunO2A.clicked.connect(self.on_forcerunO2A_clicked)
        self.settings_button_aula.clicked.connect(self.runUniSetup)
        self.customize_ignore_people_button.clicked.connect(self.on_actionIgnore_people_list_triggered)
        self.customize_alias_button.clicked.connect(self.on_actionOutlook_Aulanavne_liste_triggered)
        self.start_window_minimized.clicked.connect(self.update_hide_on_startup_clicked)
        self.run_program_at_startup.clicked.connect(self.on_run_program_at_startup_clicked)


        repo = git.Repo(search_parent_directories=True)
        sha = repo.head.object.hexsha
        latest_commit = repo.head.commit
        commit_date = latest_commit.committed_date
        commit_datetime = dt.datetime.fromtimestamp(commit_date)
        date_formatted = commit_datetime.strftime('%d-%m-%Y %H:%M:%S')

        self.program_version_label.setText(date_formatted)

    def initialize_countdown_timer(self):
        self.countdown_timer = QTimer()
        self.countdown_timer.setInterval(60*1000)
        self.countdown_timer.timeout.connect(self.on_countdown_timer_timeout)
        self.countdown_timer.start()

    def initialize_run_frequency_timer(self):
        self.runFrequencyTimer = QTimer()
        self.runFrequencyTimer.timeout.connect(self.on_runFrequencyTimer_timeout)
        self.runFrequencyTimer.timeout.connect(self.on_runO2A_clicked)

        self.runFrequency.valueChanged.connect(self.on_runFrequency_valueChanged)
        self.runFrequency.valueChanged.connect(self.on_runFrequencyTimer_timeout)
        self.on_runFrequency_valueChanged(self.runFrequency.value())


    def closeEvent(self, event):
        self.signals.window_closed.emit()

    def on_countdown_timer_timeout(self):
        time_to_next_run = self.__next_run - dt.datetime.now()
        next_run = self.__next_run

        # Extract the total seconds from the difference
        total_seconds = int(time_to_next_run.total_seconds())

        # Calculate hours, minutes, and seconds
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        # Print the result
        #time_to_next_run_text = f"{hours}:{minutes}:{seconds}"
        time_to_next_run_text = f"{hours} timer og {minutes} minutter"

        next_run_text = 'Næste kørsel om {} (kl. {:%H:%M:%S})'.format(time_to_next_run_text,next_run)
        self.runFrequencyNextRun.setText(next_run_text)
        self.signals.trayicon_text_updated.emit(next_run_text)

    def csv_exists(self,source,destination):
        if not os.path.isfile(destination):
            try:
                shutil.copyfile(source, destination)
            except:
                self.logger.critical(f"Kunne ikke oprette filen {source}")

    def initial_o2a_check(self):
        #Undersøger om personer.csv findes.
        self.csv_exists("./personer_skabelon.csv","personer.csv")

        #Undersøger om personer_ignorer.csv findes
        self.csv_exists("./personer_ignorer_skabelon.csv","personer_ignorer.csv")

        #Opsætter Outlook. Hvis kategorier mangler, da oprettes de
        setupmgr = SetupManager()
        setupmgr.create_outlook_categories()

        self.start_window_minimized.setChecked(setupmgr.hide_on_startup())
        self.run_program_at_startup.setChecked(self.autostart_shortcut_exist())

    def update_hide_on_startup_clicked(self,value: bool):
        setupmgr = SetupManager()
        print("HER")
        if value == True:
            setupmgr.set_hide_on_startup("True")
            return
        setupmgr.set_hide_on_startup("False")


    def on_runFrequencyTimer_timeout(self):
        value = self.runFrequency.value()
        self.__next_run = dt.datetime.now() + dt.timedelta(hours=value)

        self.on_countdown_timer_timeout()
        #next_run_text = 'Næste kørsel kl. {:%H:%M:%S}'.format(self.__next_run)
        #self.runFrequencyNextRun.setText(next_run_text)
        #self.signals.trayicon_text_updated.emit(next_run_text)

    def restart_timer(self):
        print("Timer restarted")
        self.runFrequencyTimer.stop()
        self.runFrequencyTimer.start()


    def on_runFrequency_valueChanged(self,value):
        hours = value*60*60*1000
        #self.actionDetails.appendHtml(f"Interval ændret til {value} timer")
        self.runFrequencyTimer.setInterval(hours)

        self.restart_timer()
        #self.on_runFrequencyTimer_timeout()

    def on_showHideDetails_clicked(self):
        if not self.actionDetails.isVisible():
            self.actionDetails.setVisible(True)
            return

        self.actionDetails.setVisible(False)

    def on_actionIgnore_people_list_triggered(self):
        self.action_openExcel("personer_ignorer.csv")

    def on_actionOutlook_Aulanavne_liste_triggered(self):
        self.action_openExcel("personer.csv")

    def action_openExcel(self,file_to_open):
        #cwd = os.getcwd()
        #file_to_open = "{cwd}/{file_to_open}"
        #dir_path = os.path.dirname(os.path.realpath(__file__))

        cmd_to_run = f'excel.exe "{file_to_open}"'
        os.system(f'start {cmd_to_run}')

    def on_status_unilogin_update(self,status_text):
        self.status_unilogin.setText(status_text)

    def on_status_aula_update(self,status_text):
        self.status_aula.setText(status_text)

    def on_status_outlook_update(self,status_text):
        self.status_outlook.setText(status_text)

    def on_status_updated_update(self,status_text):
        self.status_updated.setText(status_text)

    def get_autostart_shortcut(self) -> str:
        # Path to the common startup folder
        common_startup_folder = winshell.startup(common=False)

        # Name of the shortcut file
        shortcut_name = 'Outlook2Aula'

        # Full path to the shortcut file
        shortcut_path = os.path.join(common_startup_folder, f'{shortcut_name}.lnk')
        return shortcut_path


    def autostart_shortcut_exist(self) -> bool:
        if os.path.isfile(self.get_autostart_shortcut()):
            return True

        return False

    def on_run_program_at_startup_clicked(self,value: bool):

        # Path to the main.pyw file
        target_path = os.path.join(os.getcwd(), 'updateandrun.bat')

        # Full path to the shortcut file
        shortcut_path = self.get_autostart_shortcut()


        if value == True:
            # Create the shortcut
            self.create_shortcut(target_path, shortcut_path)
            print(f'Shortcut created at: {shortcut_path}')
            return

        try:
            os.remove(shortcut_path)
            print(f"File '{shortcut_path}' removed successfully.")
        except OSError as e:
            print(f"Error: {shortcut_path} : {e.strerror}")




    def create_shortcut(self, target, shortcut_path):
        try:
            winshell.CreateShortcut(
                Path=shortcut_path,
                Target=target,
                Icon=(target, 0),
                Description="Shortcut to main.pyw for automatic startup"
            )
            print(f"Shortcut created at: {shortcut_path}")
        except Exception as e:
            print(f"An error occurred: {e}")


    def do_update_force(self,progress_callback):


        today = dt.datetime.today()
        last_sunday = today + relativedelta(weekday=SU(-1))
        #self.progressStatus.setText("Starter op")
        eman = EventManager()

        #self.progressStatus.setText("Sammenligner kalendre")
        #comp = eman.compare_calendars(today,today+relativedelta(days=+4)) #Start dato er nu altid dags dato :)
        eman.login_to_aula()
        comp = eman.compare_calendars(dt.datetime(last_sunday.year,last_sunday.month,last_sunday.day,1,00,00,00),dt.datetime(today.year+1,7,1,00,00,00,00),True)
        #self.progressStatus.setText("Opdater AULA Kalender")
        eman.update_aula_calendar(comp)

    def do_update(self,progress_callback):
        today = dt.datetime.today()
        last_sunday = today + relativedelta(weekday=SU(-1))

        try:
            #self.progressStatus.setText("Starter op")
            eman = EventManager()
            #self.progressStatus.setText("Sammenligner kalendre")
            #comp = eman.compare_calendars(today,today+relativedelta(days=+4)) #Start dato er nu altid dags dato :)
            eman.login_to_aula()
            #comp = eman.compare_calendars(dt.datetime(today.year,today.month,today.day,1,00,00,00),dt.datetime(today.year,today.month,today.day+15,1,00,00,00),False)
            comp = eman.compare_calendars(dt.datetime(last_sunday.year,last_sunday.month,last_sunday.day,1,00,00,00),dt.datetime(today.year+1,7,1,00,00,00,00),False)
            #self.progressStatus.setText("Opdater AULA Kalender")
            eman.update_aula_calendar(comp)
        except Exception as err:
          logger.critical(traceback.format_exc())

          self.internal_errors_count = self.internal_errors_count +1 
          print("ERRORS COUNT")
          print(self.internal_errors_count)

          if self.internal_errors_count >2: 
            outlookmanager = OutlookManager()
            outlookmanager.send_a_mail_program(traceback.format_exc())
            self.internal_errors_count = 0

        finally:
          pass

    @Slot(str, logging.LogRecord)
    def update_status(self, status, record):
        color = self.COLORS.get(record.levelno, 'black')
        s = '<pre><font color="%s">%s</font></pre>' % (color, status)
        self.actionDetails.appendHtml(s)

    def print_output(self, s):
        print(s)

    def thread_complete(self):
        print("THREAD COMPLETE!")
        self.toggle_gui()

    def toggle_gui(self):
        if self.runO2A.isEnabled():
            print("DEAKTIVERER")
            self.runO2A.setEnabled(False)
            self.forcerunO2A.setEnabled(False)
            self.runFrequency.setEnabled(False)
            return

        print("AKTIVIERER")
        self.runO2A.setEnabled(True)
        self.forcerunO2A.setEnabled(True)
        self.runFrequency.setEnabled(True)

    def has_internet_connection(self):

        try:
            requests.get("https://www.google.dk/",timeout=5)
            return True
        except requests.ConnectionError:
            return False

    def on_runO2A_clicked(self):
        if not self.has_internet_connection():
            logger.critical("Det var ikke muligt at oprette forbindelse til internettet! Forsøger igen ved næste kørsel")
            return

        self.toggle_gui()

        # Pass the function to execute
        worker = Worker(self.do_update) # Any other args, kwargs are passed to the run function
        worker.signals.result.connect(self.print_output)
        worker.signals.finished.connect(self.thread_complete)
        #worker.signals.progress.connect(self.progress_fn)

        # Execute
        self.threadpool.start(worker)

    def on_forcerunO2A_clicked(self):
        if not self.has_internet_connection():
            logger.critical("Det var ikke muligt at oprette forbindelse til internettet! Forsøger igen ved næste kørsel")
            return

        self.toggle_gui()

        # Pass the function to execute
        worker = Worker(self.do_update_force) # Any other args, kwargs are passed to the run function
        worker.signals.result.connect(self.print_output)
        worker.signals.finished.connect(self.thread_complete)
        #worker.signals.progress.connect(self.progress_fn)

        # Execute
        self.threadpool.start(worker)

    def runUniSetup(self):

        mdialog = UniloginDialog()
        mdialog.exec()

class Signaller(QObject):
    signal = Signal(str, logging.LogRecord)

class QtHandler(logging.Handler):
    def __init__(self, slotfunc, *args, **kwargs):
        super(QtHandler, self).__init__(*args, **kwargs)
        self.signaller = Signaller()
        self.signaller.signal.connect(slotfunc)

    def emit(self, record):
        s = self.format(record)
        self.signaller.signal.emit(s, record)

class UniloginDialog(Ui_UniloginDialog, QDialog):
    """Employee dialog."""
    def __init__(self, parent=None):
        super().__init__(parent)
        # Run the .setupUi() method to show the GUI
        self.setupUi(self)
        self.buttonBox.accepted.connect(self.on_update_pressed)

        self.setupmgr = SetupManager()
        username = self.setupmgr.get_aula_username()
        password = self.setupmgr.get_aula_password()

        self.username.setText(username)
        self.password.setText(password)

    def on_update_pressed(self):
        self.setupmgr.update_unilogin(username=str(self.username.text()),password=str(self.password.text()))


def update_systemtray_tooltip(text):
    tray.setToolTip(f"O2A: {text}")
    #tray.showMessage("O2A", text)

def on_mainwindow_closed():
    tray.showMessage("O2A", "Programmet fortsætter i baggrunden.")


if __name__ == "__main__":

    myappid = u'of.o2a.gui' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    #SETUPMANAGER
    setupmgr = SetupManager()


    #MAINWINDOW
    window = MainWindow()

    if not setupmgr.hide_on_startup() == True:
        window.show()

    #TRAYICON
    # Create the icon
    #https://www.iconfinder.com/icons/298875/sync_icon
    icon = QIcon("images/Exchange.png")

    # Create the tray
    tray = QSystemTrayIcon()
    tray.setIcon(icon)
    tray.setVisible(True)

    window.signals.trayicon_text_updated.connect(update_systemtray_tooltip)
    window.signals.window_closed.connect(on_mainwindow_closed)

    window.on_runFrequencyTimer_timeout() #Tvinger opdatering af Hover-text

    # Create the menu
    menu = QMenu()
    show_mainwindow_action = QAction("Vis")
    show_mainwindow_action.triggered.connect(window.show)
    menu.addAction(show_mainwindow_action)

    # Add a Quit option to the menu.
    quit = QAction("Afslut O2A")
    quit.triggered.connect(app.quit)
    menu.addAction(quit)

    # Add the menu to the tray
    tray.setContextMenu(menu)


    #LOGGING SETUP
    logger = logging.getLogger('O2A')
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler('o2a.log')
    fh.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    h = QtHandler(window.update_status)
    h.setLevel(logging.INFO)

    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fs = '%(asctime)s - %(levelname)s - %(message)s'
    gui_formatter = logging.Formatter(fs)
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    h.setFormatter(gui_formatter)

    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)
    logger.addHandler(h)

    logger.info('O2A startet')


    sys.exit(app.exec())
