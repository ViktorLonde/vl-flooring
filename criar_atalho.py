# -*- coding: utf-8 -*-
"""
Cria o atalho "VL Flooring" na Área de Trabalho deste computador.

Rode uma vez em cada computador (notebook e desktop):
    venv\\Scripts\\python.exe criar_atalho.py

O atalho abre o app com pythonw (sem a janela preta do console). Erros vão
para logs\\vl_flooring.log.
"""

import os
import subprocess

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHONW = os.path.join(PROJECT_DIR, "venv", "Scripts", "pythonw.exe")
ICON = os.path.join(PROJECT_DIR, "assets", "vl_flooring.ico")


def ps_quote(text):
    return "'" + text.replace("'", "''") + "'"


def main():
    script = f"""
$desktop = [Environment]::GetFolderPath('Desktop')
$lnk = Join-Path $desktop 'VL Flooring.lnk'
$s = (New-Object -ComObject WScript.Shell).CreateShortcut($lnk)
$s.TargetPath = {ps_quote(PYTHONW)}
$s.Arguments = '"' + {ps_quote(os.path.join(PROJECT_DIR, "app.py"))} + '"'
$s.WorkingDirectory = {ps_quote(PROJECT_DIR)}
$s.IconLocation = {ps_quote(ICON)}
$s.Description = 'Vertex Londe Flooring LLC'
$s.Save()
Write-Output $lnk
"""
    out = subprocess.run(["powershell", "-NoProfile", "-Command", script],
                         capture_output=True, text=True, check=True).stdout.strip()
    print("Atalho criado:", out)


if __name__ == "__main__":
    main()
