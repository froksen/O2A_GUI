# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'unilogindialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QGridLayout, QLabel, QLineEdit, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_UniloginDialog(object):
    def setupUi(self, UniloginDialog):
        if not UniloginDialog.objectName():
            UniloginDialog.setObjectName(u"UniloginDialog")
        UniloginDialog.resize(371, 171)
        self.verticalLayout = QVBoxLayout(UniloginDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_3 = QLabel(UniloginDialog)
        self.label_3.setObjectName(u"label_3")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.label_3.setFont(font)

        self.verticalLayout.addWidget(self.label_3)

        self.label_4 = QLabel(UniloginDialog)
        self.label_4.setObjectName(u"label_4")

        self.verticalLayout.addWidget(self.label_4)

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.label = QLabel(UniloginDialog)
        self.label.setObjectName(u"label")
        font1 = QFont()
        font1.setBold(True)
        self.label.setFont(font1)

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.username = QLineEdit(UniloginDialog)
        self.username.setObjectName(u"username")
        self.username.setEchoMode(QLineEdit.Normal)

        self.gridLayout.addWidget(self.username, 0, 1, 1, 1)

        self.label_2 = QLabel(UniloginDialog)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setFont(font1)

        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)

        self.password = QLineEdit(UniloginDialog)
        self.password.setObjectName(u"password")
        self.password.setEchoMode(QLineEdit.Password)

        self.gridLayout.addWidget(self.password, 1, 1, 1, 1)


        self.verticalLayout.addLayout(self.gridLayout)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.buttonBox = QDialogButtonBox(UniloginDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(UniloginDialog)
        self.buttonBox.accepted.connect(UniloginDialog.accept)
        self.buttonBox.rejected.connect(UniloginDialog.reject)

        QMetaObject.connectSlotsByName(UniloginDialog)
    # setupUi

    def retranslateUi(self, UniloginDialog):
        UniloginDialog.setWindowTitle(QCoreApplication.translate("UniloginDialog", u"Uni-login", None))
        self.label_3.setText(QCoreApplication.translate("UniloginDialog", u"UNI-LOGIN", None))
        self.label_4.setText(QCoreApplication.translate("UniloginDialog", u"Indtast dine uni-login brugeroplysninger. \n"
" Disse bruges til at f\u00e5 l\u00e6se og administerer begivenheder p\u00e5 AULA.", None))
        self.label.setText(QCoreApplication.translate("UniloginDialog", u"Brugernavn", None))
        self.label_2.setText(QCoreApplication.translate("UniloginDialog", u"Kodeord", None))
    # retranslateUi

