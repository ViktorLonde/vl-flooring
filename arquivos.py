# -*- coding: utf-8 -*-
"""
Pasta de arquivos do app (invoices, fotos, recibos, estimates, relatórios…).

• Onde fica: na pasta escolhida em Settings → System (guardada em
  files_location.json, ao lado do app). Sem escolha: <usuário>\\Documents\\
  VL Flooring Files — pasta local, fora do OneDrive (no PC do Viktor o
  "Documentos" do Explorer fica dentro do OneDrive). O Viktor adiciona essa
  pasta ao backup do Google Drive para computador ("Pastas do meu computador").
• Toda vez que o app abre, ensure_structure() cria as subpastas que faltarem.
• Caminhos guardados no banco: arquivos dentro da pasta viram "files:<relativo>"
  (funcionam mesmo se o Google Drive tiver outra letra em outro computador);
  resolve() transforma de volta em caminho completo.
Sem dependência de Qt — também é usado pelo backup_db.py.
"""
import json
import os
import shutil
import string

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(PROJECT_DIR, "files_location.json")
LOCAL_FALLBACK = os.path.join(PROJECT_DIR, "Files")  # pasta usada só em 25/11/2026 (é movida)
DEFAULT_PARENT = os.path.join(os.path.expanduser("~"), "Documents")
ROOT_NAME = "VL Flooring Files"
PREFIX = "files:"

SUBFOLDERS = {
    "invoices": "Invoices",
    "estimates": "Estimates",
    "statements": "Statements",
    "photos": "Job Photos",
    "receipts": "Receipts",
    "completion": "Completion",
    "reports": "Reports",
    "accountant": "Accountant",
    "backups": "Backups",
}

# pastas antigas (dentro do app) → subpasta nova
LEGACY_DIRS = {
    os.path.join(PROJECT_DIR, "job_photos"): "photos",
    os.path.join(PROJECT_DIR, "receipts_received"): "receipts",
}


def find_google_drive():
    """Pasta raiz do 'My Drive' do Google Drive para computador, ou None."""
    candidates = []
    for letter in string.ascii_uppercase:
        root = f"{letter}:\\"
        candidates += [root + "My Drive", root + "Meu Drive"]
    home = os.path.expanduser("~")
    candidates += [os.path.join(home, n) for n in ("My Drive", "Meu Drive", "Google Drive",
                                                     os.path.join("Google Drive", "My Drive"))]
    for c in candidates:
        try:
            if os.path.isdir(c):
                return c
        except OSError:
            continue
    return None


def _read_config():
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def configured_root():
    return (_read_config().get("root") or "").strip() or None


def set_root(path):
    data = _read_config()
    data["root"] = os.path.abspath(path) if path else ""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def default_root():
    return os.path.join(DEFAULT_PARENT, ROOT_NAME)


def files_root():
    """Pasta principal em uso agora."""
    chosen = configured_root()
    if chosen and os.path.isdir(os.path.dirname(chosen.rstrip("\\/")) or chosen):
        return chosen
    return default_root()


def using_google_drive(root=None):
    root = os.path.normcase(root or files_root())
    return any(n in root for n in (os.path.normcase("My Drive"), os.path.normcase("Meu Drive"),
                                   os.path.normcase("Google Drive")))


def ensure_structure(root=None):
    root = root or files_root()
    for sub in SUBFOLDERS.values():
        os.makedirs(os.path.join(root, sub), exist_ok=True)
    return root


def folder(kind, *parts):
    """Subpasta (criada se faltar). Ex.: folder('photos', 'JB-0041')."""
    path = os.path.join(files_root(), SUBFOLDERS[kind], *[p for p in parts if p])
    os.makedirs(path, exist_ok=True)
    return path


def to_stored(path):
    """Caminho para gravar no banco."""
    if not path:
        return path
    full = os.path.abspath(path)
    root = os.path.abspath(files_root())
    if os.path.normcase(full).startswith(os.path.normcase(root) + os.sep):
        return PREFIX + os.path.relpath(full, root).replace("\\", "/")
    if os.path.normcase(full).startswith(os.path.normcase(PROJECT_DIR) + os.sep):
        return os.path.relpath(full, PROJECT_DIR)
    return full


def resolve(stored):
    """Caminho do banco → caminho completo no computador."""
    if not stored:
        return stored
    if stored.startswith(PREFIX):
        return os.path.join(files_root(), *stored[len(PREFIX):].split("/"))
    return stored if os.path.isabs(stored) else os.path.join(PROJECT_DIR, stored)


def is_inside(path, root=None):
    root = os.path.normcase(os.path.abspath(root or files_root()))
    return os.path.normcase(os.path.abspath(path)).startswith(root + os.sep)


# ───────────────────────── mover arquivos ─────────────────────────

# (tabela, coluna) com caminhos de arquivo
PATH_COLUMNS = [
    ("documents", "FILE_PATH"),
    ("contractor_invoices", "PDF_PATH"),
    ("company_invoices", "PDF_PATH"),
    ("client_invoices", "PDF_PATH"),
    ("expenses", "RECEIPT_PATH"),
    ("purchases", "RECEIPT_PATH"),
]


def _move_tree(src, dst):
    """Move o conteúdo de src para dst (sem sobrescrever). Devolve {antigo: novo}."""
    moved = {}
    for base, _dirs, files in os.walk(src):
        rel = os.path.relpath(base, src)
        target_dir = os.path.normpath(os.path.join(dst, rel))
        os.makedirs(target_dir, exist_ok=True)
        for name in files:
            old = os.path.join(base, name)
            new = os.path.join(target_dir, name)
            if os.path.exists(new):
                stem, ext = os.path.splitext(name)
                i = 2
                while os.path.exists(os.path.join(target_dir, f"{stem}_{i}{ext}")):
                    i += 1
                new = os.path.join(target_dir, f"{stem}_{i}{ext}")
            shutil.move(old, new)
            moved[os.path.normcase(os.path.abspath(old))] = new
    # apaga pastas que ficaram vazias
    for base, _dirs, _files in sorted(os.walk(src), key=lambda t: -len(t[0])):
        try:
            os.rmdir(base)
        except OSError:
            pass
    return moved


def _move_tree_file(old, target_dir):
    os.makedirs(target_dir, exist_ok=True)
    stem, ext = os.path.splitext(os.path.basename(old))
    new, i = os.path.join(target_dir, stem + ext), 2
    while os.path.exists(new):
        new, i = os.path.join(target_dir, f"{stem}_{i}{ext}"), i + 1
    shutil.move(old, new)
    return {os.path.normcase(os.path.abspath(old)): new}


def _update_db_paths(conn, moved, new_root):
    """Atualiza os caminhos do banco dos arquivos que foram movidos."""
    cur = conn.cursor()
    changed = 0
    try:
        for table, col in PATH_COLUMNS:
            try:
                cur.execute(f"SELECT ID, {col} FROM {table} WHERE {col} IS NOT NULL AND {col} <> ''")
            except Exception:
                continue  # tabela/coluna que não existe neste banco
            for rid, stored in cur.fetchall():
                if stored.startswith(PREFIX):
                    continue  # relativo à pasta: continua certo depois de mover a pasta toda
                full = stored if os.path.isabs(stored) else os.path.join(PROJECT_DIR, stored)
                new = moved.get(os.path.normcase(os.path.abspath(full)))
                if not new:
                    continue
                rel = os.path.relpath(new, new_root).replace("\\", "/")
                value = PREFIX + rel if table == "documents" else new
                cur.execute(f"UPDATE {table} SET {col}=%s WHERE ID=%s", (value, rid))
                changed += 1
        conn.commit()
    finally:
        cur.close()
    return changed


def pending_moves(new_root=None):
    """Quantos arquivos ainda estão fora da pasta nova (pastas antigas / outra raiz)."""
    new_root = os.path.abspath(new_root or files_root())
    n = 0
    sources = list(LEGACY_DIRS) + [LOCAL_FALLBACK]
    old_docs = os.path.join(os.path.expanduser("~"), "Documents", "VL Flooring")
    sources.append(old_docs)
    for src in sources:
        if os.path.isdir(src) and os.path.normcase(os.path.abspath(src)) != os.path.normcase(new_root):
            n += sum(len(f) for _b, _d, f in os.walk(src))
    return n


def move_everything(conn, new_root=None, old_root=None):
    """Leva para new_root: as pastas antigas do app, a pasta local Files,
    Documentos\\VL Flooring e (se informado) a raiz anterior. Atualiza o banco.
    Devolve (arquivos movidos, linhas do banco atualizadas)."""
    new_root = os.path.abspath(new_root or files_root())
    ensure_structure(new_root)
    moved = {}
    for src, kind in LEGACY_DIRS.items():
        if os.path.isdir(src):
            moved.update(_move_tree(src, os.path.join(new_root, SUBFOLDERS[kind])))
    for src in {old_root, LOCAL_FALLBACK}:
        if src and os.path.isdir(src) and os.path.normcase(os.path.abspath(src)) != os.path.normcase(new_root):
            moved.update(_move_tree(src, new_root))
    # Documentos\VL Flooring (pasta antiga das exportações): subpastas conhecidas
    # vão para a subpasta igual; o resto vai para Reports
    old_docs = os.path.join(os.path.expanduser("~"), "Documents", "VL Flooring")
    if os.path.isdir(old_docs) and os.path.normcase(os.path.abspath(old_docs)) != os.path.normcase(new_root):
        known = {v.lower(): v for v in SUBFOLDERS.values()}
        for name in os.listdir(old_docs):
            src = os.path.join(old_docs, name)
            if os.path.isdir(src):
                dst = os.path.join(new_root, known.get(name.lower(), os.path.join(SUBFOLDERS["reports"], name)))
                moved.update(_move_tree(src, dst))
            else:
                moved.update(_move_tree_file(src, os.path.join(new_root, SUBFOLDERS["reports"])))
        try:
            os.rmdir(old_docs)
        except OSError:
            pass
    changed = _update_db_paths(conn, moved, new_root) if conn is not None else 0
    return len(moved), changed
