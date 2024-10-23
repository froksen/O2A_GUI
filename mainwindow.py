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
    QPlainTextEdit, QPushButton, QSizePolicy, QSpacerItem,
    QSpinBox, QStatusBar, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(720, 572)
        icon = QIcon()
        icon.addFile(u"images/exchange.png", QSize(), QIcon.Normal, QIcon.Off)
        MainWindow.setWindowIcon(icon)
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
        self.groupBox.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.groupBox.setFlat(True)
        self.horizontalLayout = QHBoxLayout(self.groupBox)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.settings_button_aula = QPushButton(self.groupBox)
        self.settings_button_aula.setObjectName(u"settings_button_aula")
        icon1 = QIcon()
        icon1.addFile(u"images/Aula-logo.jpg", QSize(), QIcon.Normal, QIcon.Off)
        self.settings_button_aula.setIcon(icon1)

        self.gridLayout.addWidget(self.settings_button_aula, 1, 0, 1, 1)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 1, 1, 1, 1)

        self.label_4 = QLabel(self.groupBox)
        self.label_4.setObjectName(u"label_4")
        font1 = QFont()
        font1.setItalic(True)
        self.label_4.setFont(font1)

        self.gridLayout.addWidget(self.label_4, 0, 0, 1, 2)


        self.horizontalLayout.addLayout(self.gridLayout)


        self.verticalLayout_3.addWidget(self.groupBox)

        self.groupBox_3 = QGroupBox(self.centralwidget)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.groupBox_3.setFlat(True)
        self.groupBox_3.setCheckable(False)
        self.verticalLayout_2 = QVBoxLayout(self.groupBox_3)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label_5 = QLabel(self.groupBox_3)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setFont(font1)

        self.verticalLayout_2.addWidget(self.label_5)

        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.customize_alias_button = QPushButton(self.groupBox_3)
        self.customize_alias_button.setObjectName(u"customize_alias_button")
        icon2 = QIcon()
        icon2.addFile(u"images/switch.png", QSize(), QIcon.Normal, QIcon.Off)
        self.customize_alias_button.setIcon(icon2)

        self.gridLayout_2.addWidget(self.customize_alias_button, 0, 1, 1, 1)

        self.start_window_minimized = QCheckBox(self.groupBox_3)
        self.start_window_minimized.setObjectName(u"start_window_minimized")
        self.start_window_minimized.setEnabled(True)

        self.gridLayout_2.addWidget(self.start_window_minimized, 0, 2, 1, 1)

        self.customize_ignore_people_button = QPushButton(self.groupBox_3)
        self.customize_ignore_people_button.setObjectName(u"customize_ignore_people_button")
        icon3 = QIcon()
        icon3.addFile(u"images/ignore.png", QSize(), QIcon.Normal, QIcon.Off)
        self.customize_ignore_people_button.setIcon(icon3)

        self.gridLayout_2.addWidget(self.customize_ignore_people_button, 0, 0, 1, 1)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout_2.addItem(self.horizontalSpacer_3, 0, 4, 1, 1)

        self.run_program_at_startup = QCheckBox(self.groupBox_3)
        self.run_program_at_startup.setObjectName(u"run_program_at_startup")

        self.gridLayout_2.addWidget(self.run_program_at_startup, 0, 3, 1, 1)


        self.verticalLayout_2.addLayout(self.gridLayout_2)

        self.gridLayout_3 = QGridLayout()
        self.gridLayout_3.setObjectName(u"gridLayout_3")

        self.verticalLayout_2.addLayout(self.gridLayout_3)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_3 = QLabel(self.groupBox_3)
        self.label_3.setObjectName(u"label_3")
        font2 = QFont()
        font2.setBold(False)
        self.label_3.setFont(font2)

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
        self.groupBox_2.setFlat(True)
        self.verticalLayout = QVBoxLayout(self.groupBox_2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.gridLayout_4 = QGridLayout()
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.forcerunO2A = QPushButton(self.groupBox_2)
        self.forcerunO2A.setObjectName(u"forcerunO2A")
        self.forcerunO2A.setMinimumSize(QSize(200, 0))
        icon4 = QIcon()
        icon4.addFile(u"images/icon.png", QSize(), QIcon.Normal, QIcon.Off)
        self.forcerunO2A.setIcon(icon4)

        self.gridLayout_4.addWidget(self.forcerunO2A, 0, 1, 1, 1)

        self.runO2A = QPushButton(self.groupBox_2)
        self.runO2A.setObjectName(u"runO2A")
        self.runO2A.setMinimumSize(QSize(250, 0))
        self.runO2A.setIcon(icon4)

        self.gridLayout_4.addWidget(self.runO2A, 0, 0, 1, 1)

        self.gridLayout_4.setColumnStretch(0, 1)
        self.gridLayout_4.setColumnMinimumWidth(0, 1)

        self.verticalLayout.addLayout(self.gridLayout_4)

        self.label = QLabel(self.groupBox_2)
        self.label.setObjectName(u"label")

        self.verticalLayout.addWidget(self.label)

        self.actionDetails = QPlainTextEdit(self.groupBox_2)
        self.actionDetails.setObjectName(u"actionDetails")

        self.verticalLayout.addWidget(self.actionDetails)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_6 = QLabel(self.groupBox_2)
        self.label_6.setObjectName(u"label_6")

        self.horizontalLayout_2.addWidget(self.label_6)

        self.program_version_label = QLabel(self.groupBox_2)
        self.program_version_label.setObjectName(u"program_version_label")

        self.horizontalLayout_2.addWidget(self.program_version_label)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_4)


        self.verticalLayout.addLayout(self.horizontalLayout_2)


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
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Outlook2Aula", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Outlook2Aula", None))
        self.groupBox.setTitle(QCoreApplication.translate("MainWindow", u"Aula", None))
#if QT_CONFIG(tooltip)
        self.settings_button_aula.setToolTip(QCoreApplication.translate("MainWindow", u"\u00c5bner en dialog, hvor du kan indtaste dine AULA login-oplysninger", None))
#endif // QT_CONFIG(tooltip)
        self.settings_button_aula.setText(QCoreApplication.translate("MainWindow", u"Konfigurer", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"Indtast dine login-informationer til AULA via knappen \"Konfigurer\". Disse bruges til at  kommunikere med AULA.", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("MainWindow", u"Tilpasning", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"Brug mulighederne herunder til at tilpasse hvordan programmet afvikles.", None))
#if QT_CONFIG(tooltip)
        self.customize_alias_button.setToolTip(QCoreApplication.translate("MainWindow", u"Nogle kontakter har forskelligt navn i Outlook end de har i AULA f.eks. et mellemnavn der er det ene sted, men ikke det andet. Med denne funktion kan du h\u00e5ndtere disse.", None))
#endif // QT_CONFIG(tooltip)
        self.customize_alias_button.setText(QCoreApplication.translate("MainWindow", u"Personers alias", None))
#if QT_CONFIG(tooltip)
        self.start_window_minimized.setToolTip(QCoreApplication.translate("MainWindow", u"N\u00e5r programmet \u00e5bens, da \u00e5bner det direkte i proceslinjen. S\u00e6rlig relevant, hvis programmet \u00e5bner automatisk ved start af computeren.", None))
#endif // QT_CONFIG(tooltip)
        self.start_window_minimized.setText(QCoreApplication.translate("MainWindow", u"\u00c5ben programmet i baggrunden", None))
#if QT_CONFIG(tooltip)
        self.customize_ignore_people_button.setToolTip(QCoreApplication.translate("MainWindow", u"I nogle Outlook begivenheder er der deltagere, som ikke findes i AULA f.eks. eksterne kontakter. Normalt vil programmet give en fejl om, at disse personer ikke blev fundet p\u00e5 Aula. Brug denne funktion til at f\u00e5 programmet til at se bort fra disse, og alts\u00e5 ikke fors\u00f8ge at tilf\u00f8je dem til AULA begivenheden.", None))
#endif // QT_CONFIG(tooltip)
        self.customize_ignore_people_button.setText(QCoreApplication.translate("MainWindow", u"Ignorer personer", None))
#if QT_CONFIG(tooltip)
        self.run_program_at_startup.setToolTip(QCoreApplication.translate("MainWindow", u"F\u00e5r programmet til at starte op med computeren.", None))
#endif // QT_CONFIG(tooltip)
        self.run_program_at_startup.setText(QCoreApplication.translate("MainWindow", u"Start Outlook2Aula automatisk", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"K\u00f8rselsinterval (Timer)", None))
        self.runFrequencyNextRun.setText(QCoreApplication.translate("MainWindow", u"Ukendt", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("MainWindow", u"Status", None))
#if QT_CONFIG(tooltip)
        self.forcerunO2A.setToolTip(QCoreApplication.translate("MainWindow", u"Opretter alle nye og opdaterer alle eksisterende selvom de ikke er \u00e6ndret. Bruges til at gennemtvinge en opdatering.", None))
#endif // QT_CONFIG(tooltip)
        self.forcerunO2A.setText(QCoreApplication.translate("MainWindow", u"Opdater alle begivenheder", None))
#if QT_CONFIG(tooltip)
        self.runO2A.setToolTip(QCoreApplication.translate("MainWindow", u"Tilf\u00f8jer nye og opdaterer \u00e6ndrede begivenheder.", None))
#endif // QT_CONFIG(tooltip)
        self.runO2A.setText(QCoreApplication.translate("MainWindow", u"Opdater med seneste \u00e6ndringer", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Nuv\u00e6rrende", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"Programmets version: ", None))
        self.program_version_label.setText(QCoreApplication.translate("MainWindow", u"<Ukendt>", None))
    # retranslateUi

