# -*- coding: utf-8 -*-
"""
Lê as credenciais do banco de db_config.ini (fica fora do Git).
Para configurar numa máquina nova: copie db_config.example.ini para
db_config.ini e preencha os dados do MySQL.
"""

import configparser
import os

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db_config.ini")


def load_db_config() -> dict:
    """Retorna {"host", "user", "password", "database"} lidos do db_config.ini."""
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(
            f"Arquivo de configuração não encontrado: {CONFIG_PATH}\n"
            "Copie db_config.example.ini para db_config.ini e preencha os dados do banco."
        )
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(CONFIG_PATH, encoding="utf-8")
    section = parser["mysql"]
    return {
        "host": section.get("host"),
        "user": section.get("user"),
        "password": section.get("password", ""),
        "database": section.get("database"),
    }


def check_db_connection(cfg: dict, timeout: int = 5) -> str | None:
    """Tenta conectar rapidamente. Retorna None se deu certo ou a mensagem de erro.

    Sem esse teste, com o notebook (servidor MySQL) desligado, cada tentativa
    de conexão demora ~21s e o app parece travado ao abrir.
    """
    import mysql.connector
    try:
        conn = mysql.connector.connect(**cfg, connection_timeout=timeout)
        conn.close()
        return None
    except mysql.connector.Error as e:
        return str(e)
