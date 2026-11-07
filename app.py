# -*- coding: utf-8 -*-
"""
VL FLOORING — Ponto de entrada principal
Conecta o Login → Tela Principal com autenticação MySQL

Para rodar:
    python app.py
"""

import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from config import load_db_config
from login import LoginWindow
from main_ import MainWindow


# ── CONFIGURAÇÃO DO BANCO (usada em todo o sistema) ──────────────────
# As credenciais ficam em db_config.ini (fora do Git) — veja config.py
DB_CONFIG = load_db_config()


def on_login_successful(login_window: LoginWindow, main_window: MainWindow, username: str):
    """Chamado quando o login é bem-sucedido."""
    try:
        main_window.ui.Top_label.setText(f"Dashboard  —  {username}")
    except Exception:
        pass

    login_window.hide()
    main_window.showMaximized()
    login_window.deleteLater()


def main():
    # Faz o Qt escalar corretamente em telas com DPI diferentes
    # (laptop 15" vs monitor 32") — precisa ser ANTES do QApplication(...)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)

    main_window = MainWindow(db_config=DB_CONFIG)
    main_window.hide()

    login = LoginWindow()
    login.login_successful.connect(
        lambda username: on_login_successful(login, main_window, username)
    )
    login.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()


# pyside6-uic main_window_vl_flooring_6.ui -o ui_main_window_vl_flooring.py