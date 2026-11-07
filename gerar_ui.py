# -*- coding: utf-8 -*-
"""
Gera os arquivos .py das telas a partir dos .ui do Qt Designer.

Substitui o pyside6-uic.exe (que o Windows bloqueia e que guarda o caminho
antigo do venv). Rodar na pasta do projeto:
    venv\\Scripts\\python.exe gerar_ui.py

Para abrir o Qt Designer:
    venv\\Scripts\\python.exe gerar_ui.py designer
"""

import os
import sys

from PySide6.scripts import pyside_tool

HERE = os.path.dirname(os.path.abspath(__file__))
UI_FILES = {
    "main_window_vl_flooring_6.ui": "ui_main_window_vl_flooring.py",
    "login.ui": "login_window.py",
}


def run_tool(tool, args):
    """Roda uma ferramenta do PySide6 (ela chama sys.exit no fim, por isso o except)."""
    sys.argv = [tool] + args
    try:
        getattr(pyside_tool, tool)()
    except SystemExit as e:
        if e.code:
            raise


if __name__ == "__main__":
    os.chdir(HERE)
    if sys.argv[1:] == ["designer"]:
        run_tool("designer", [f for f in UI_FILES])
    else:
        for ui, py in UI_FILES.items():
            run_tool("uic", [ui, "-o", py])
            print(f"{ui} -> {py}")
