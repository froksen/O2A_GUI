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
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QMainWindow, QMenuBar,
    QPushButton, QSizePolicy, QSpacerItem, QSpinBox,
    QStatusBar, QTextEdit, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(720, 572)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout_3 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.label_2 = QLabel(self.centralwidget)
        self.label_2.setObjectName(u"label_2")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.label_2.setFont(font)
        self.label_2.setAlignment(Qt.AlignCenter)

        self.verticalLayout_3.addWidget(self.label_2)

        self.groupBox = QGroupBox(self.centralwidget)
        self.groupBox.setObjectName(u"groupBox")
        self.horizontalLayout = QHBoxLayout(self.groupBox)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.settings_button_aula = QPushButton(self.groupBox)
        self.settings_button_aula.setObjectName(u"settings_button_aula")

        self.gridLayout.addWidget(self.settings_button_aula, 0, 3, 1, 1)

        self.settings_aula_status = QLabel(self.groupBox)
        self.settings_aula_status.setObjectName(u"settings_aula_status")

        self.gridLayout.addWidget(self.settings_aula_status, 0, 1, 1, 1)

        self.settings_label_aula = QLabel(self.groupBox)
        self.settings_label_aula.setObjectName(u"settings_label_aula")

        self.gridLayout.addWidget(self.settings_label_aula, 0, 0, 1, 1)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 0, 2, 1, 1)


        self.horizontalLayout.addLayout(self.gridLayout)


        self.verticalLayout_3.addWidget(self.groupBox)

        self.groupBox_3 = QGroupBox(self.centralwidget)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.verticalLayout_2 = QVBoxLayout(self.groupBox_3)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.customize_ignore_people_button = QPushButton(self.groupBox_3)
        self.customize_ignore_people_button.setObjectName(u"customize_ignore_people_button")

        self.gridLayout_2.addWidget(self.customize_ignore_people_button, 0, 0, 1, 1)

        self.customize_alias_button = QPushButton(self.groupBox_3)
        self.customize_alias_button.setObjectName(u"customize_alias_button")

        self.gridLayout_2.addWidget(self.customize_alias_button, 0, 1, 1, 1)


        self.verticalLayout_2.addLayout(self.gridLayout_2)

        self.gridLayout_3 = QGridLayout()
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.start_window_minimized = QCheckBox(self.groupBox_3)
        self.start_window_minimized.setObjectName(u"start_window_minimized")
        self.start_window_minimized.setEnabled(True)

        self.gridLayout_3.addWidget(self.start_window_minimized, 0, 0, 1, 1)

        self.run_program_at_startup = QCheckBox(self.groupBox_3)
        self.run_program_at_startup.setObjectName(u"run_program_at_startup")

        self.gridLayout_3.addWidget(self.run_program_at_startup, 0, 1, 1, 1)


        self.verticalLayout_2.addLayout(self.gridLayout_3)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_3 = QLabel(self.groupBox_3)
        self.label_3.setObjectName(u"label_3")
        font1 = QFont()
        font1.setBold(True)
        self.label_3.setFont(font1)

        self.horizontalLayout_3.addWidget(self.label_3)

        self.runFrequency = QSpinBox(self.groupBox_3)
        self.runFrequency.setObjectName(u"runFrequency")
        self.runFrequency.setMinimum(1)
        self.runFrequency.setMaximum(4)
        self.runFrequency.setValue(2)

        self.horizontalLayout_3.addWidget(self.runFrequency)

        self.runFrequencyNextRun = QLabel(self.groupBox_3)
        self.runFrequencyNextRun.setObjectName(u"runFrequencyNextRun")

        self.horizontalLayout_3.addWidget(self.runFrequencyNextRun)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_2)


        self.verticalLayout_2.addLayout(self.horizontalLayout_3)


        self.verticalLayout_3.addWidget(self.groupBox_3)

        self.groupBox_2 = QGroupBox(self.centralwidget)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.verticalLayout = QVBoxLayout(self.groupBox_2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.gridLayout_4 = QGridLayout()
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.runO2A = QPushButton(self.groupBox_2)
        self.runO2A.setObjectName(u"runO2A")

        self.gridLayout_4.addWidget(self.runO2A, 0, 0, 1, 1)

        self.forcerunO2A = QPushButton(self.groupBox_2)
        self.forcerunO2A.setObjectName(u"forcerunO2A")

        self.gridLayout_4.addWidget(self.forcerunO2A, 0, 1, 1, 1)


        self.verticalLayout.addLayout(self.gridLayout_4)

        self.label = QLabel(self.groupBox_2)
        self.label.setObjectName(u"label")

        self.verticalLayout.addWidget(self.label)

        self.actionDetails = QTextEdit(self.groupBox_2)
        self.actionDetails.setObjectName(u"actionDetails")

        self.verticalLayout.addWidget(self.actionDetails)


        self.verticalLayout_3.addWidget(self.groupBox_2)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 720, 22))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Outlook2Aula", None))
        self.groupBox.setTitle(QCoreApplication.translate("MainWindow", u"Aula", None))
        self.settings_button_aula.setText(QCoreApplication.translate("MainWindow", u"Konfigurer", None))
        self.settings_aula_status.setText(QCoreApplication.translate("MainWindow", u"Forbundet", None))
        self.settings_label_aula.setText(QCoreApplication.translate("MainWindow", u"Status:", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("MainWindow", u"Tilpasning", None))
        self.customize_ignore_people_button.setText(QCoreApplication.translate("MainWindow", u"Ignorer personer", None))
        self.customize_alias_button.setText(QCoreApplication.translate("MainWindow", u"Personers alias", None))
        self.start_window_minimized.setText(QCoreApplication.translate("MainWindow", u"\u00c5ben programmet i baggrunden", None))
        self.run_program_at_startup.setText(QCoreApplication.translate("MainWindow", u"Start Outlook2Aula automatisk", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"K\u00f8rselsinterval (Timer)", None))
        self.runFrequencyNextRun.setText(QCoreApplication.translate("MainWindow", u"Ukendt", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("MainWindow", u"Status", None))
        self.runO2A.setText(QCoreApplication.translate("MainWindow", u"K\u00f8r opdatering", None))
        self.forcerunO2A.setText(QCoreApplication.translate("MainWindow", u"Gennemtving opdatering", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Nuv\u00e6rrende", None))
    # retranslateUi

