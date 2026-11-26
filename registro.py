# -*- coding: utf-8 -*-
"""
Registro de erros e pasta padrão das exportações.

• Todo erro (inclusive os que antes passavam em silêncio) vai para
  logs/vl_flooring.log, com data e hora. O arquivo gira sozinho em 1 MB
  (guarda os 5 últimos).
• As janelas de erro (QMessageBox.critical/warning) também são registradas.
• "Salvar como…" sem pasta (ex.: "customers.pdf") passa a sugerir
  Documentos\\VL Flooring em vez da pasta do código.
"""

import logging
import os
import sys
import threading
import traceback
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
LOG_FILE = os.path.join(LOG_DIR, "vl_flooring.log")
import arquivos  # noqa: E402

# pasta principal de arquivos (Google Drive quando instalado) — ver arquivos.py
EXPORTS_DIR = arquivos.files_root()

log = logging.getLogger("vl_flooring")


def setup_logging():
    os.makedirs(LOG_DIR, exist_ok=True)
    handler = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=5, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-7s  %(name)s  %(message)s",
                                           "%Y-%m-%d %H:%M:%S"))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    if sys.stderr is not None:  # com pythonw não existe console
        root.addHandler(logging.StreamHandler())

    sys.excepthook = _excepthook
    threading.excepthook = lambda args: log.error(
        "unhandled error in thread %s", args.thread.name if args.thread else "?",
        exc_info=(args.exc_type, args.exc_value, args.exc_traceback))
    log.info("---- app started (%s) ----", os.environ.get("COMPUTERNAME", "?"))


def _excepthook(exc_type, exc_value, exc_tb):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return
    log.error("unhandled error", exc_info=(exc_type, exc_value, exc_tb))
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox
        if QApplication.instance() is not None:
            box = QMessageBox(QMessageBox.Icon.Critical, "VL Flooring — unexpected error",
                              f"Something went wrong:\n{exc_value}\n\n"
                              f"The details were saved in:\n{LOG_FILE}")
            box.setDetailedText("".join(traceback.format_exception(exc_type, exc_value, exc_tb)))
            box.exec()
    except Exception:
        pass


def install_message_box_logging():
    """Registra no log o texto de toda janela de erro/aviso mostrada."""
    from PySide6.QtWidgets import QMessageBox

    def wrap(original, level):
        def wrapper(*args, **kwargs):
            try:
                title = args[1] if len(args) > 1 else kwargs.get("title", "")
                text = args[2] if len(args) > 2 else kwargs.get("text", "")
                log.log(level, "[dialog] %s: %s", title, " ".join(str(text).split()))
            except Exception:
                pass
            return original(*args, **kwargs)
        return staticmethod(wrapper)

    QMessageBox.critical = wrap(QMessageBox.critical, logging.ERROR)
    QMessageBox.warning = wrap(QMessageBox.warning, logging.WARNING)


def install_default_save_folder():
    """Nomes sugeridos sem pasta vão para Documentos\\VL Flooring."""
    from PySide6.QtWidgets import QFileDialog
    original = QFileDialog.getSaveFileName

    def get_save_file_name(parent=None, caption="", directory="", *args, **kwargs):
        if "dir" in kwargs:
            directory = kwargs.pop("dir")
        if directory and not os.path.isabs(directory) and not os.path.dirname(directory):
            try:
                directory = os.path.join(arquivos.folder("reports"), directory)
            except OSError:
                pass
        return original(parent, caption, directory, *args, **kwargs)

    QFileDialog.getSaveFileName = staticmethod(get_save_file_name)
