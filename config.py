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
