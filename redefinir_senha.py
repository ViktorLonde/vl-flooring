# -*- coding: utf-8 -*-
"""
Redefine a senha de um usuário do VL Flooring (para quando a senha foi
esquecida). Rode no notebook ou no desktop:

    venv\\Scripts\\python.exe redefinir_senha.py

A senha é digitada sem aparecer na tela e é gravada protegida (PBKDF2),
igual às outras. A alteração fica registrada no histórico (audit_log).
"""

import getpass
import sys

import mysql.connector

from config import load_db_config
from passwords import hash_password


def main():
    conn = mysql.connector.connect(**load_db_config())
    cur = conn.cursor()
    cur.execute("SELECT username, full_name, role, status FROM users ORDER BY username")
    users = cur.fetchall()
    print("\nUsuários cadastrados:")
    for username, full_name, role, status in users:
        print(f"  - {username:15} {full_name or '':25} {role or '':8} {status or ''}")

    username = input("\nUsuário para trocar a senha: ").strip()
    match = next((u for u in users if u[0].lower() == username.lower()), None)
    if not match:
        print("Usuário não encontrado. Nada foi alterado.")
        return 1
    username = match[0]

    while True:
        pw1 = getpass.getpass("Nova senha (não aparece enquanto digita): ")
        if len(pw1) < 6:
            print("Use pelo menos 6 caracteres.")
            continue
        pw2 = getpass.getpass("Repita a nova senha: ")
        if pw1 != pw2:
            print("As senhas não são iguais. Tente de novo.")
            continue
        break

    cur.execute("UPDATE users SET password_hash=%s, status='Active' WHERE username=%s",
                (hash_password(pw1), username))
    try:
        cur.execute("INSERT INTO audit_log (username, action, table_name, details) "
                    "VALUES (%s, 'UPDATE', 'users', %s)",
                    ("(redefinir_senha.py)", f"Password reset for {username}"))
    except mysql.connector.Error:
        pass  # histórico é opcional
    conn.commit()
    cur.close()
    conn.close()
    print(f"\nPronto! A senha de '{username}' foi trocada. Já pode entrar no app.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nCancelado. Nada foi alterado.")
        sys.exit(1)
