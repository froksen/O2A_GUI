# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainwindow.ui'
##
## Created by: Qt User Interface Compiler version 6.6.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QHBoxLayout, QLabel,
    QMainWindow, QMenu, QMenuBar, QPlainTextEdit,
    QPushButton, QSizePolicy, QSpacerItem, QSpinBox,
    QStatusBar, QToolBar, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(781, 371)
        icon = QIcon()
        icon.addFile(u"images/exchange.png", QSize(), QIcon.Normal, QIcon.Off)
        icon.addFile(u"images/exchange.png", QSize(), QIcon.Normal, QIcon.On)
        MainWindow.setWindowIcon(icon)
        self.actionUnilogin = QAction(MainWindow)
        self.actionUnilogin.setObjectName(u"actionUnilogin")
        icon1 = QIcon()
        icon1.addFile(u"images/Aula-logo.jpg", QSize(), QIcon.Normal, QIcon.Off)
        self.actionUnilogin.setIcon(icon1)
        self.actionOutlook = QAction(MainWindow)
        self.actionOutlook.setObjectName(u"actionOutlook")
        self.actionOm_Qt = QAction(MainWindow)
        self.actionOm_Qt.setObjectName(u"actionOm_Qt")
        self.actionIgnore_people_list = QAction(MainWindow)
        self.actionIgnore_people_list.setObjectName(u"actionIgnore_people_list")
        icon2 = QIcon()
        icon2.addFile(u"images/ignore.png", QSize(), QIcon.Normal, QIcon.Off)
        self.actionIgnore_people_list.setIcon(icon2)
        self.actionIgnore_people_list.setMenuRole(QAction.NoRole)
        self.actionOutlook_Aulanavne_liste = QAction(MainWindow)
        self.actionOutlook_Aulanavne_liste.setObjectName(u"actionOutlook_Aulanavne_liste")
        icon3 = QIcon()
        icon3.addFile(u"images/switch.png", QSize(), QIcon.Normal, QIcon.Off)
        self.actionOutlook_Aulanavne_liste.setIcon(icon3)
        self.actionOutlook_Aulanavne_liste.setMenuRole(QAction.NoRole)
        self.actionOutlook_Aulanavne_liste.setIconVisibleInMenu(True)
        self.actionOutlook_Aulanavne_liste.setShortcutVisibleInContextMenu(True)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_2 = QLabel(self.centralwidget)
        self.label_2.setObjectName(u"label_2")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.label_2.setFont(font)
        self.label_2.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label_2)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_3 = QLabel(self.centralwidget)
        self.label_3.setObjectName(u"label_3")
        font1 = QFont()
        font1.setBold(True)
        self.label_3.setFont(font1)

        self.horizontalLayout_3.addWidget(self.label_3)

        self.runFrequency = QSpinBox(self.centralwidget)
        self.runFrequency.setObjectName(u"runFrequency")
        self.runFrequency.setMinimum(1)
        self.runFrequency.setMaximum(4)
        self.runFrequency.setValue(2)

        self.horizontalLayout_3.addWidget(self.runFrequency)

        self.runFrequencyNextRun = QLabel(self.centralwidget)
        self.runFrequencyNextRun.setObjectName(u"runFrequencyNextRun")

        self.horizontalLayout_3.addWidget(self.runFrequencyNextRun)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_2)


        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.start_window_minimized = QCheckBox(self.centralwidget)
        self.start_window_minimized.setObjectName(u"start_window_minimized")
        self.start_window_minimized.setEnabled(True)

        self.horizontalLayout_4.addWidget(self.start_window_minimized)

        self.run_program_at_startup = QCheckBox(self.centralwidget)
        self.run_program_at_startup.setObjectName(u"run_program_at_startup")

        self.horizontalLayout_4.addWidget(self.run_program_at_startup)


        self.verticalLayout.addLayout(self.horizontalLayout_4)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.runO2A = QPushButton(self.centralwidget)
        self.runO2A.setObjectName(u"runO2A")

        self.horizontalLayout.addWidget(self.runO2A)

        self.forcerunO2A = QPushButton(self.centralwidget)
        self.forcerunO2A.setObjectName(u"forcerunO2A")

        self.horizontalLayout.addWidget(self.forcerunO2A)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.actionDetails = QPlainTextEdit(self.centralwidget)
        self.actionDetails.setObjectName(u"actionDetails")

        self.verticalLayout.addWidget(self.actionDetails)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 781, 22))
        self.menuIndstillinger = QMenu(self.menubar)
        self.menuIndstillinger.setObjectName(u"menuIndstillinger")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.toolBar = QToolBar(MainWindow)
        self.toolBar.setObjectName(u"toolBar")
        self.toolBar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        MainWindow.addToolBar(Qt.TopToolBarArea, self.toolBar)

        self.menubar.addAction(self.menuIndstillinger.menuAction())
        self.menuIndstillinger.addAction(self.actionOm_Qt)
        self.toolBar.addAction(self.actionUnilogin)
        self.toolBar.addAction(self.actionIgnore_people_list)
        self.toolBar.addAction(self.actionOutlook_Aulanavne_liste)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Outlook2Aula (O2A)", None))
        self.actionUnilogin.setText(QCoreApplication.translate("MainWindow", u"Opdater UNI-Login", None))
        self.actionOutlook.setText(QCoreApplication.translate("MainWindow", u"Ops\u00e6t Outlook", None))
        self.actionOm_Qt.setText(QCoreApplication.translate("MainWindow", u"Om Qt", None))
        self.actionIgnore_people_list.setText(QCoreApplication.translate("MainWindow", u"Ignorer personer (Liste)", None))
        self.actionOutlook_Aulanavne_liste.setText(QCoreApplication.translate("MainWindow", u"Outlook=>Aulanavne (liste)", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Outlook2Aula", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"K\u00f8rselsinterval (Timer)", None))
        self.runFrequencyNextRun.setText(QCoreApplication.translate("MainWindow", u"Ukendt", None))
        self.start_window_minimized.setText(QCoreApplication.translate("MainWindow", u"\u00c5ben programmet i baggrunden", None))
        self.run_program_at_startup.setText(QCoreApplication.translate("MainWindow", u"Start Outlook2Aula automatisk", None))
        self.runO2A.setText(QCoreApplication.translate("MainWindow", u"K\u00f8r opdatering", None))
        self.forcerunO2A.setText(QCoreApplication.translate("MainWindow", u"Gennemtving opdatering", None))
        self.menuIndstillinger.setTitle(QCoreApplication.translate("MainWindow", u"Om", None))
        self.toolBar.setWindowTitle(QCoreApplication.translate("MainWindow", u"toolBar", None))
    # retranslateUi

