# -*- coding: utf-8 -*-
"""
Backup do banco MySQL do VL Flooring.

Gera um dump completo (.sql.gz) com o mysqldump, guarda em BACKUP_DIR e copia
para a pasta do OneDrive (cópia fora do notebook). Mantém os últimos
KEEP_DAYS backups em cada pasta. Agendado no Windows pela tarefa
"VL Flooring - Backup MySQL".

Rodar na mão:
    venv\\Scripts\\python.exe backup_db.py

Restaurar um backup (cuidado: sobrescreve o banco): pelo app, em
Settings → "Restore backup…" (faz um backup do estado atual antes), ou
com restore_backup() deste arquivo.
"""

import glob
import gzip
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime

from config import load_db_config

BACKUP_DIR = r"C:\VL_Backups\mysql"
CLOUD_DIR = os.path.join(os.environ.get("OneDrive", ""), "VL_Backups", "mysql") if os.environ.get("OneDrive") else None
KEEP_DAYS = 30
MYSQLDUMP_CANDIDATES = [
    r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe",
    r"C:\Program Files\MySQL\MySQL Workbench 8.0\mysqldump.exe",
    "mysqldump",
]
LOG_PATH = os.path.join(BACKUP_DIR, "backup_log.txt")


def log(msg):
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S}  {msg}"
    print(line)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


MYSQL_CANDIDATES = [p.replace("mysqldump", "mysql") for p in MYSQLDUMP_CANDIDATES]


def find_mysql_client():
    for path in MYSQL_CANDIDATES:
        if os.path.isfile(path) or shutil.which(path):
            return path
    raise FileNotFoundError("mysql.exe não encontrado neste computador. Restaure pelo notebook (servidor).")


def find_mysqldump():
    for path in MYSQLDUMP_CANDIDATES:
        if os.path.isfile(path) or shutil.which(path):
            return path
    raise FileNotFoundError("mysqldump não encontrado. Ajuste MYSQLDUMP_CANDIDATES em backup_db.py.")


def prune(folder):
    """Apaga os backups mais antigos, mantendo os KEEP_DAYS mais recentes."""
    files = sorted(glob.glob(os.path.join(folder, "*.sql.gz")))
    for old in files[:-KEEP_DAYS]:
        os.remove(old)


def run_backup():
    cfg = load_db_config()
    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    sql_path = os.path.join(BACKUP_DIR, f"{cfg['database']}_{stamp}.sql")
    gz_path = sql_path + ".gz"

    # Credenciais num arquivo temporário (não aparecem na linha de comando)
    with tempfile.NamedTemporaryFile("w", suffix=".cnf", delete=False, encoding="utf-8") as cnf:
        cnf.write(f"[client]\nhost={cfg['host']}\nuser={cfg['user']}\npassword=\"{cfg['password']}\"\n")
        cnf_path = cnf.name
    try:
        with open(sql_path, "wb") as out:
            result = subprocess.run(
                [find_mysqldump(), f"--defaults-extra-file={cnf_path}",
                 "--single-transaction", "--routines", "--triggers", "--events",
                 "--default-character-set=utf8mb4", cfg["database"]],
                stdout=out, stderr=subprocess.PIPE,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
    finally:
        os.remove(cnf_path)

    if result.returncode != 0:
        os.remove(sql_path)
        raise RuntimeError(result.stderr.decode(errors="replace").strip())

    with open(sql_path, "rb") as src, gzip.open(gz_path, "wb") as dst:
        shutil.copyfileobj(src, dst)
    os.remove(sql_path)
    prune(BACKUP_DIR)

    size_kb = os.path.getsize(gz_path) / 1024
    log(f"OK  {os.path.basename(gz_path)} ({size_kb:.0f} KB)")

    if CLOUD_DIR:
        try:
            os.makedirs(CLOUD_DIR, exist_ok=True)
            shutil.copy2(gz_path, CLOUD_DIR)
            prune(CLOUD_DIR)
            log(f"OK  copiado para {CLOUD_DIR}")
        except OSError as e:
            log(f"AVISO  não consegui copiar para o OneDrive: {e}")
    return gz_path


def list_backups():
    """Backups disponíveis (mais novo primeiro): lista de (caminho, data, tamanho em KB, pasta).
    Se o mesmo arquivo existe nas duas pastas, mostra só uma vez."""
    seen, result = set(), []
    for folder in [BACKUP_DIR] + ([CLOUD_DIR] if CLOUD_DIR else []):
        for path in glob.glob(os.path.join(folder, "*.sql.gz")):
            name = os.path.basename(path)
            if name in seen:
                continue
            seen.add(name)
            result.append((path, datetime.fromtimestamp(os.path.getmtime(path)),
                           os.path.getsize(path) / 1024, folder))
    result.sort(key=lambda r: r[1], reverse=True)
    return result


def restore_backup(gz_path, database=None):
    """Restaura um .sql.gz no banco (por padrão o do db_config.ini).
    ATENÇÃO: substitui todos os dados atuais desse banco."""
    cfg = load_db_config()
    database = database or cfg["database"]
    with tempfile.NamedTemporaryFile("w", suffix=".cnf", delete=False, encoding="utf-8") as cnf:
        cnf.write(f"[client]\nhost={cfg['host']}\nuser={cfg['user']}\npassword=\"{cfg['password']}\"\n")
        cnf_path = cnf.name
    try:
        with gzip.open(gz_path, "rb") as src:
            data = src.read()
        result = subprocess.run(
            [find_mysql_client(), f"--defaults-extra-file={cnf_path}", "--default-character-set=utf8mb4", database],
            input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    finally:
        os.remove(cnf_path)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode(errors="replace").strip())
    log(f"RESTORE  {os.path.basename(gz_path)} -> {database}")


if __name__ == "__main__":
    try:
        run_backup()
    except Exception as e:
        log(f"ERRO  {e}")
        sys.exit(1)
