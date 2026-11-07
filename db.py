import mysql.connector
from mysql.connector import Error
from config import load_db_config

def conectar():
    try:
        conexao = mysql.connector.connect(**load_db_config())

        if conexao.is_connected():
            print("Conectado ao MySQL com sucesso")
            return conexao

    except Error as e:
        print("Erro ao conectar ao MySQL:", e)
        return None

