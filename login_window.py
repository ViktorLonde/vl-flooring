# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'login.ui'
##
## Created by: Qt User Interface Compiler version 6.11.0
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
from PySide6.QtWidgets import (QApplication, QFrame, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QWidget)
import icons_rc

class Ui_Login(object):
    def setupUi(self, Login):
        if not Login.objectName():
            Login.setObjectName(u"Login")
        Login.resize(970, 630)
        Login.setMinimumSize(QSize(970, 630))
        Login.setMaximumSize(QSize(970, 630))
        font = QFont()
        font.setPointSize(12)
        Login.setFont(font)
        Login.setStyleSheet(u"QFrame#frame_login {\n"
"    box-shadow: 0px 4px 20px rgba(0,0,0,0.35);\n"
"}\n"
"")
        self.frame = QFrame(Login)
        self.frame.setObjectName(u"frame")
        self.frame.setGeometry(QRect(350, 100, 271, 461))
        self.frame.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.frame.setStyleSheet(u"background-color: rgba(193, 193, 193,0.6);\n"
"Border-radius:10px\n"
"\n"
"")
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.txt_user = QLineEdit(self.frame)
        self.txt_user.setObjectName(u"txt_user")
        self.txt_user.setGeometry(QRect(40, 190, 190, 35))
        font1 = QFont()
        font1.setFamilies([u"Segoe UI"])
        font1.setPointSize(12)
        font1.setBold(True)
        self.txt_user.setFont(font1)
        self.txt_user.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.txt_user.setStyleSheet(u"QLineEdit {\n"
"    background: rgba(127, 127, 127, 220);\n"
"    border: 1px solid rgba(255, 255, 255, 90);\n"
"    border-radius: 8px;\n"
"    padding: 6px 8px;\n"
"    color: white;              /* texto vis\u00edvel */\n"
"}\n"
"\n"
"QLineEdit:focus {\n"
"    border: 1px solid #0078ff;\n"
"    background: rgba(38, 50, 64, 200);\n"
"}\n"
"")
        self.txt_user.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btn_login = QPushButton(self.frame)
        self.btn_login.setObjectName(u"btn_login")
        self.btn_login.setGeometry(QRect(70, 340, 131, 61))
        font2 = QFont()
        font2.setBold(True)
        self.btn_login.setFont(font2)
        self.btn_login.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_login.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.btn_login.setStyleSheet(u"\n"
"QPushButton {\n"
"    background-color: #0078D4;\n"
"    color: white;\n"
"    border: none;\n"
"    border-radius: 12px;\n"
"    padding: 10px 24px;\n"
"    font-size: 20px;\n"
"    font-weight: bold;\n"
"}\n"
"QPushButton:hover {\n"
"    background-color: #1493FF;\n"
"}\n"
"QPushButton:pressed {\n"
"    background-color: #005A9E;\n"
"}\n"
"")
        self.img_login = QLabel(self.frame)
        self.img_login.setObjectName(u"img_login")
        self.img_login.setGeometry(QRect(90, 80, 101, 91))
        self.img_login.setStyleSheet(u"background-color: rgba(193, 193, 193,0.6);")
        self.img_login.setPixmap(QPixmap(u":/icons/icons_/icon_sem_fundo.png"))
        self.img_login.setScaledContents(True)
        self.txt_password = QLineEdit(self.frame)
        self.txt_password.setObjectName(u"txt_password")
        self.txt_password.setGeometry(QRect(40, 260, 190, 35))
        self.txt_password.setFont(font1)
        self.txt_password.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.txt_password.setStyleSheet(u"QLineEdit {\n"
"    background: rgba(127, 127, 127, 220);\n"
"    border: 1px solid rgba(255, 255, 255, 90);\n"
"    border-radius: 8px;\n"
"    padding: 6px 8px;\n"
"    color: white;              /* texto vis\u00edvel */\n"
"}\n"
"\n"
"QLineEdit:focus {\n"
"    border: 1px solid #0078ff;\n"
"    background: rgba(38, 50, 64, 200);\n"
"}\n"
"\n"
"")
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_password.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btn_password_eye = QPushButton(self.frame)
        self.btn_password_eye.setObjectName(u"btn_password_eye")
        self.btn_password_eye.setGeometry(QRect(190, 260, 41, 35))
        self.btn_password_eye.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_password_eye.setAutoFillBackground(False)
        self.btn_password_eye.setStyleSheet(u"QPushButton {\n"
"    background-color: transparent;\n"
"    border: none;\n"
"}\n"
"QPushButton:hover {\n"
"    background-color: rgba(0,0,0,20); /* opcional */\n"
"}\n"
"\n"
"/* QPushButton {\n"
"    background-color: transparent;\n"
"    border: none;\n"
"}*/\n"
"")
        icon = QIcon()
        icon.addFile(u"icons_/eye_closed.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_password_eye.setIcon(icon)
        self.btn_password_eye.setIconSize(QSize(50, 50))
        self.btn_password_eye.setFlat(True)
        self.img_back_login = QLabel(Login)
        self.img_back_login.setObjectName(u"img_back_login")
        self.img_back_login.setGeometry(QRect(0, 0, 971, 631))
        self.img_back_login.setPixmap(QPixmap(u":/icons/icons_/Tela_Login.jpg"))
        self.img_back_login.setScaledContents(True)
        self.img_back_login.raise_()
        self.frame.raise_()
        QWidget.setTabOrder(self.txt_user, self.txt_password)
        QWidget.setTabOrder(self.txt_password, self.btn_login)

        self.retranslateUi(Login)

        self.btn_login.setDefault(True)


        QMetaObject.connectSlotsByName(Login)
    # setupUi

    def retranslateUi(self, Login):
        Login.setWindowTitle(QCoreApplication.translate("Login", u"Form", None))
        self.txt_user.setPlaceholderText(QCoreApplication.translate("Login", u"User", None))
        self.btn_login.setText(QCoreApplication.translate("Login", u"Login", None))
        self.img_login.setText("")
        self.txt_password.setPlaceholderText(QCoreApplication.translate("Login", u"Password", None))
        self.btn_password_eye.setText("")
        self.img_back_login.setText("")
    # retranslateUi

