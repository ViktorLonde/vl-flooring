# -*- coding: utf-8 -*-
"""
Tela de login do VL Flooring.

Lado esquerdo: foto do escritório com a marca por cima. Lado direito: o
formulário (usuário, senha com botão de mostrar/ocultar e "Sign in"). Os
erros aparecem embaixo do formulário, sem janela.

Emite login_successful(username) quando a senha confere.
"""

import os

import mysql.connector
from PySide6.QtCore import Qt, QPropertyAnimation, QRectF, QSettings, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap, QLinearGradient
from PySide6.QtWidgets import (QApplication, QCheckBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
                               QPushButton, QVBoxLayout, QWidget)

import company_settings
from config import load_db_config
from passwords import hash_password, verify_password, needs_upgrade

HERE = os.path.dirname(os.path.abspath(__file__))
PHOTO = os.path.join(HERE, "icons_", "Tela_Login.jpg")
LOGO = os.path.join(HERE, "icons_", "logo_icon_only_256.png")


class _BrandPanel(QWidget):
    """Foto recortada com uma camada azul-marinho e a marca por cima."""

    def __init__(self):
        super().__init__()
        self._photo = QPixmap(PHOTO)
        self._logo = QPixmap(LOGO)
        self.setMinimumWidth(380)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        r = self.rect()
        if not self._photo.isNull():
            scaled = self._photo.scaled(r.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                        Qt.TransformationMode.SmoothTransformation)
            x = (scaled.width() - r.width()) // 2
            y = (scaled.height() - r.height()) // 2
            p.drawPixmap(0, 0, scaled, x, y, r.width(), r.height())
        grad = QLinearGradient(0, 0, 0, r.height())
        grad.setColorAt(0, QColor(28, 43, 58, 200))
        grad.setColorAt(1, QColor(17, 26, 36, 245))
        p.fillRect(r, grad)

        margin = 44
        if not self._logo.isNull():
            p.drawPixmap(margin, margin, 52, 52, self._logo)
        p.setPen(QColor("#FFFFFF"))
        f = QFont(self.font())
        f.setPointSize(13)
        f.setWeight(QFont.Weight.Bold)
        p.setFont(f)
        p.drawText(QRectF(margin + 66, margin, r.width() - 2 * margin, 52),
                   Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "VL Flooring")

        f.setPointSize(24)
        p.setFont(f)
        p.drawText(QRectF(margin, r.height() - 230, r.width() - 2 * margin, 90),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom | Qt.TextFlag.TextWordWrap,
                   company_settings.COMPANY_NAME)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#FF8A4C"))
        p.drawRoundedRect(QRectF(margin, r.height() - 128, 40, 4), 2, 2)
        f.setPointSize(11)
        f.setWeight(QFont.Weight.Normal)
        p.setFont(f)
        p.setPen(QColor("#C9D3DD"))
        p.drawText(QRectF(margin, r.height() - 110, r.width() - 2 * margin, 60),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
                   "Jobs, invoices and payments — all in one place.")
        p.end()


_FORM_QSS = """
#login_form { background-color: #FFFFFF; }
#login_title { color: #1C2B3A; font-size: 24px; font-weight: 700; }
#login_subtitle { color: #6B7C93; font-size: 13px; }
#login_field_label { color: #6B7C93; font-size: 11px; font-weight: 600; }
QLineEdit {
    background-color: #F5F8FC; color: #1C2B3A; border: 1px solid #CBD5E1; border-radius: 8px;
    padding: 9px 12px; font-size: 14px;
}
QLineEdit:focus { border: 1px solid #1565C0; background-color: #FFFFFF; }
#btn_login {
    background-color: #1565C0; color: #FFFFFF; border: none; border-radius: 8px;
    padding: 11px; font-size: 14px; font-weight: 700;
}
#btn_login:hover { background-color: #1E88E5; }
#btn_login:disabled { background-color: #90B8E0; }
#login_error { color: #C62828; font-size: 12px; }
#login_footer { color: #94A3B8; font-size: 11px; }
"""


class LoginWindow(QMainWindow):
    login_successful = Signal(str)

    def __init__(self):
        super().__init__()
        from paginas.visual import tabler_icon  # ícones do app

        self.setWindowTitle("VL Flooring — Login")
        self.resize(940, 580)
        self.setMinimumSize(780, 520)

        root = QWidget()
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(_BrandPanel(), 5)

        form = QFrame()
        form.setObjectName("login_form")
        form.setStyleSheet(_FORM_QSS)
        outer = QVBoxLayout(form)
        outer.setContentsMargins(56, 40, 56, 28)
        outer.addStretch(1)

        title = QLabel("Welcome back")
        title.setObjectName("login_title")
        subtitle = QLabel("Sign in to continue")
        subtitle.setObjectName("login_subtitle")
        outer.addWidget(title)
        outer.addWidget(subtitle)
        outer.addSpacing(26)

        def field_label(text):
            lbl = QLabel(text)
            lbl.setObjectName("login_field_label")
            return lbl

        outer.addWidget(field_label("USERNAME"))
        outer.addSpacing(4)
        self.txt_user = QLineEdit()
        self.txt_user.setPlaceholderText("Your username")
        self.txt_user.addAction(tabler_icon("user", "#7A8A9A", 18), QLineEdit.ActionPosition.LeadingPosition)
        outer.addWidget(self.txt_user)
        outer.addSpacing(14)

        outer.addWidget(field_label("PASSWORD"))
        outer.addSpacing(4)
        self.txt_password = QLineEdit()
        self.txt_password.setPlaceholderText("Your password")
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_password.addAction(tabler_icon("lock", "#7A8A9A", 18), QLineEdit.ActionPosition.LeadingPosition)
        self._eye_action = self.txt_password.addAction(tabler_icon("eye", "#7A8A9A", 18),
                                                       QLineEdit.ActionPosition.TrailingPosition)
        self._eye_action.setToolTip("Show password")
        self._eye_action.triggered.connect(self.toggle_password)
        self._tabler_icon = tabler_icon
        outer.addWidget(self.txt_password)
        outer.addSpacing(8)

        # "Remember me": guarda só o NOME de usuário neste computador (nunca a senha)
        self.chk_remember = QCheckBox("Remember my username")
        self.chk_remember.setStyleSheet("color:#6B7C93; font-size:12px;")
        outer.addWidget(self.chk_remember)
        outer.addSpacing(4)

        self.lbl_error = QLabel("")
        self.lbl_error.setObjectName("login_error")
        self.lbl_error.setWordWrap(True)
        self.lbl_error.setMinimumHeight(18)
        outer.addWidget(self.lbl_error)
        outer.addSpacing(10)

        self.btn_login = QPushButton("Sign in")
        self.btn_login.setObjectName("btn_login")
        self.btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        outer.addWidget(self.btn_login)
        outer.addStretch(2)

        footer = QLabel(company_settings.COMPANY_NAME)
        footer.setObjectName("login_footer")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(footer)

        layout.addWidget(form, 4)
        self.setCentralWidget(root)

        self.txt_user.returnPressed.connect(self.txt_password.setFocus)
        self.txt_password.returnPressed.connect(self.btn_login.click)
        self.btn_login.clicked.connect(self.fazer_login)
        self.txt_user.textChanged.connect(lambda _t: self.lbl_error.setText(""))
        self.txt_password.textChanged.connect(lambda _t: self.lbl_error.setText(""))

        # Fade-in ao abrir
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(400)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.start()
        settings = QSettings("VL Flooring", "app")
        remembered = settings.value("login/username", "", type=str)
        self.chk_remember.setChecked(bool(remembered) or not settings.contains("login/username"))
        if remembered:
            self.txt_user.setText(remembered)
            self.txt_password.setFocus()
        else:
            self.txt_user.setFocus()

    def toggle_password(self):
        """Mostra/oculta a senha e troca o ícone."""
        hidden = self.txt_password.echoMode() == QLineEdit.EchoMode.Password
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Normal if hidden else QLineEdit.EchoMode.Password)
        self._eye_action.setIcon(self._tabler_icon("eye-off" if hidden else "eye", "#7A8A9A", 18))
        self._eye_action.setToolTip("Hide password" if hidden else "Show password")

    def _show_error(self, text):
        self.lbl_error.setText(text)

    def fazer_login(self):
        user = self.txt_user.text().strip()
        password = self.txt_password.text()

        if not user or not password:
            self._show_error("Enter your username and password.")
            return

        self.btn_login.setEnabled(False)
        self.btn_login.setText("Signing in…")
        QApplication.processEvents()
        try:
            conn = mysql.connector.connect(**load_db_config())
            cursor = conn.cursor()
            cursor.execute("SELECT id, password_hash, status FROM users WHERE username=%s", (user,))
            resultado = cursor.fetchone()

            if not resultado or not verify_password(password, resultado[1]):
                self._show_error("Incorrect username or password.")
                self.txt_password.selectAll()
                self.txt_password.setFocus()
                return

            user_id, stored_hash, status = resultado
            if status and status != "Active":
                self._show_error(f"This user is {status}. Contact an administrator.")
                return

            # Converte hashes antigos (SHA-256 sem salt) pro formato seguro
            # e registra o último login
            if needs_upgrade(stored_hash):
                cursor.execute("UPDATE users SET password_hash=%s, last_login=NOW() WHERE id=%s",
                               (hash_password(password), user_id))
            else:
                cursor.execute("UPDATE users SET last_login=NOW() WHERE id=%s", (user_id,))
            conn.commit()
            cursor.close()
            conn.close()

            QSettings("VL Flooring", "app").setValue(
                "login/username", user if self.chk_remember.isChecked() else "")
            self.login_successful.emit(user)  # envia o nome do usuário para a main window

        except Exception as e:
            self._show_error(f"Could not connect to the database: {e}")
        finally:
            self.btn_login.setEnabled(True)
            self.btn_login.setText("Sign in")
