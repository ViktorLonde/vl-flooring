# -*- coding: utf-8 -*-
"""Aplica migration-emails-pos-job.sql com segurança: backup antes, e cada
coluna só é criada se ainda não existir. Pode rodar de novo sem problema.
Uso: venv\\Scripts\\python.exe aplicar_migracao_2111.py [--no-backup] [--database NOME]"""
import sys

import config
import mysql.connector

COLUMNS = [
    ("estimates", "SENT_AT", "DATETIME NULL"),
    ("compliance_items", "REMINDED_30_FOR", "DATE NULL"),
    ("compliance_items", "REMINDED_7_FOR", "DATE NULL"),
    ("products", "MIN_STOCK", "DECIMAL(10,2) NOT NULL DEFAULT 0"),
]
FOLLOWUPS = """
CREATE TABLE IF NOT EXISTS job_followups (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    JOB_PROJECT_ID INT NOT NULL,
    KIND VARCHAR(20) NOT NULL,
    RESULT VARCHAR(20) NOT NULL,
    NOTE VARCHAR(255) NULL,
    DONE_AT DATETIME NOT NULL,
    UNIQUE KEY uq_followup (JOB_PROJECT_ID, KIND),
    CONSTRAINT fk_followup_project FOREIGN KEY (JOB_PROJECT_ID) REFERENCES job_projects (ID) ON DELETE CASCADE
)"""


def apply(db_config):
    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor()
    done = []
    for table, column, ddl in COLUMNS:
        cur.execute(f"SHOW COLUMNS FROM {table} LIKE %s", (column,))
        if cur.fetchone() is None:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")
            done.append(f"{table}.{column}")
    cur.execute("SHOW TABLES LIKE 'job_followups'")
    if cur.fetchone() is None:
        cur.execute(FOLLOWUPS)
        done.append("job_followups")
    conn.commit()
    cur.close()
    conn.close()
    return done


if __name__ == "__main__":
    cfg = config.load_db_config()
    if "--database" in sys.argv:
        cfg = {**cfg, "database": sys.argv[sys.argv.index("--database") + 1]}
    if "--no-backup" not in sys.argv:
        import backup_db
        print("backup:", backup_db.run_backup())
    print("applied:", apply(cfg) or "nothing (already up to date)")
