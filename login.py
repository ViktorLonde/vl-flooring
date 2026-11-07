import sys
import hashlib
import mysql.connector

from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QLineEdit
from PySide6.QtCore import Qt, QPropertyAnimation
from PySide6.QtGui import QIcon
from login_window import Ui_Login
from PySide6.QtCore import Signal
from config import load_db_config

class LoginWindow(QMainWindow, Ui_Login):
    
    login_successful = Signal(str)

    def __init__(self):
        super().__init__()

        self.setupUi(self)
        
        # Animação de fade-in ao abrir
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(600)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.start()

        # ENTER ativa o login

        self.txt_user.returnPressed.connect(self.btn_login.click)
        self.txt_password.returnPressed.connect(self.btn_login.click)
        # Botões

        self.btn_login.clicked.connect(self.fazer_login)
        self.btn_password_eye.clicked.connect(self.toggle_password)
        
        # placeholder

        self.txt_user.setPlaceholderText("Username")
        self.txt_password.setPlaceholderText("Password")


    #############################################################################
    def toggle_password(self):
        """Mostra/oculta a senha e troca o ícone."""
        if self.txt_password.echoMode() == QLineEdit.Password:
            self.txt_password.setEchoMode(QLineEdit.Normal)
            self.btn_password_eye.setIcon(QIcon(":/icons/icons_/eye_open.png"))
        else:
            self.txt_password.setEchoMode(QLineEdit.Password)
            self.btn_password_eye.setIcon(QIcon(":/icons/icons_/eye_closed.png"))
    #################################################################################

    def fazer_login(self):
        user = self.txt_user.text()
        password = self.txt_password.text()

        if not user or not password:
            QMessageBox.warning(self, "Error", "Please fill in username and password." ) #"Erro", "Preencha usuário e senha."
            return

        password_hash = hashlib.sha256(password.encode()).hexdigest()

        try:
            conn = mysql.connector.connect(**load_db_config())
            cursor = conn.cursor()

            sql = "SELECT id FROM users WHERE username=%s AND password_hash=%s"
            cursor.execute(sql, (user, password_hash))
            resultado = cursor.fetchone()

            #if resultado:
            # QMessageBox.information(self, "Sucesso", "Login realizado!")
            # else:
            #     QMessageBox.warning(self, "Erro", "Usuário ou senha incorretos.")
            if resultado:
                self.login_successful.emit(user) # envia o nome do usuário para a main window
                #self.close()             # fecha a tela de login 
            else:
             QMessageBox.warning(self, "Error", "Incorrect username or password.")


        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao conectar ao banco:\n{e}")

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.btn_login.click()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())
