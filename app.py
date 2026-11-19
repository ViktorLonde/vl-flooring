# -*- coding: utf-8 -*-
"""
VL FLOORING — Ponto de entrada principal
Conecta o Login → Tela Principal com autenticação MySQL

Para rodar:
    python app.py
"""

import os
import sys

# Os ícones da tela (Icons_/..., logo) são carregados com caminho relativo à
# pasta atual. Sem isso, abrir o app a partir de outra pasta (ex.: VS Code
# aberto em D:\) deixava a sidebar sem ícones.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Erros vão para logs/vl_flooring.log (ver registro.py)
import registro
registro.setup_logging()

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from config import load_db_config, check_db_connection
from login import LoginWindow
from main_ import MainWindow


# ── CONFIGURAÇÃO DO BANCO (usada em todo o sistema) ──────────────────
# As credenciais ficam em db_config.ini (fora do Git) — veja config.py
DB_CONFIG = load_db_config()


# Janelas abertas (guardadas aqui pro Python não apagar no meio do caminho)
_session = {}


def start_session():
    """Monta a janela principal (escondida) e mostra o login. Usado ao abrir
    o app e em "Switch user" (cada login ganha uma janela nova, já com as
    permissões do perfil certo)."""
    main_window = MainWindow(db_config=DB_CONFIG)
    main_window.hide()
    login = LoginWindow()
    _session["main"], _session["login"] = main_window, login

    def on_login_successful(username: str):
        main_window.set_current_user(username)
        maximized = main_window.restore_ui_state()
        login.hide()
        if maximized:
            main_window.showMaximized()
        else:
            main_window.show()
        login.deleteLater()
        main_window.show_attention_summary()
        QTimer.singleShot(4000, main_window._auto_send_weekly_summary)

    def on_signed_out():
        old = main_window
        start_session()               # mostra o login novo antes de fechar a janela antiga
        old._closing_for_sign_out = True
        old.close()
        old.deleteLater()

    login.login_successful.connect(on_login_successful)
    main_window.signed_out.connect(on_signed_out)
    login.show()


def wait_for_database() -> bool:
    """Confere se o banco responde antes de abrir as telas. Se não responder,
    explica o motivo provável e deixa tentar de novo. Retorna False se o
    usuário preferir fechar o app."""
    while True:
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        error = check_db_connection(DB_CONFIG)
        QApplication.restoreOverrideCursor()
        if error is None:
            return True

        box = QMessageBox(QMessageBox.Icon.Warning, "VL Flooring — sem conexão",
                          f"Não foi possível conectar ao banco de dados em {DB_CONFIG['host']}.\n\n"
                          "Verifique se:\n"
                          "  • o notebook (servidor MySQL) está ligado;\n"
                          "  • este computador está na mesma rede Wi-Fi;\n"
                          "  • o IP do notebook não mudou (db_config.ini).")
        box.setDetailedText(error)
        retry = box.addButton("Tentar de novo", QMessageBox.ButtonRole.AcceptRole)
        box.addButton("Fechar", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        if box.clickedButton() is not retry:
            return False


def main():
    # Faz o Qt escalar corretamente em telas com DPI diferentes
    # (laptop 15" vs monitor 32") — precisa ser ANTES do QApplication(...)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    registro.install_message_box_logging()
    registro.install_default_save_folder()
    from paginas.visual import install_icon_theme
    install_icon_theme(app)
    from paginas.moderno import install_modern_ui
    install_modern_ui(app)
    from paginas.digitacao import install_select_all_on_focus
    install_select_all_on_focus(app)

    if not wait_for_database():
        sys.exit(1)

    start_session()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


# pyside6-uic main_window_vl_flooring_6.ui -o ui_main_window_vl_flooring.py