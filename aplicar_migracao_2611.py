# -*- coding: utf-8 -*-
"""Migração de 26/11/2026 — menu Projects (trabalhos particulares e subcontratos).
Backup antes; pode rodar de novo sem problema.

• job_projects: PROJECT_NAME, CONTRACT_PRICE, PROJECT_STAGE, START_DATE,
  DUE_DATE, PROJECT_NOTES (projetos de preço fechado usam PROJECT_TYPE='PRIVATE').
• project_payment_plan: sinal e parcelas; cada uma vira uma invoice (Client ou
  Company) quando é cobrada.
• subcontractors / project_subs / project_sub_payments: quem você contrata
  para parte do projeto, o combinado e o que já foi pago.
• expenses.CATEGORY ganha 'SUBCONTRACTOR' (pagamento a subcontratado entra no P&L).

Uso: venv\\Scripts\\python.exe aplicar_migracao_2611.py [--no-backup] [--database NOME]"""
import sys

import config
import mysql.connector

COLUMNS = [
    ("job_projects", "PROJECT_NAME", "VARCHAR(120) NULL"),
    ("job_projects", "CONTRACT_PRICE", "DECIMAL(12,2) NULL"),
    ("job_projects", "PROJECT_STAGE", "VARCHAR(20) NULL"),
    ("job_projects", "START_DATE", "DATE NULL"),
    ("job_projects", "DUE_DATE", "DATE NULL"),
    ("job_projects", "PROJECT_NOTES", "TEXT NULL"),
    ("project_sub_payments", "EXPENSE_ID", "INT NULL"),
]
TABLES = {
    "project_payment_plan": """
        CREATE TABLE project_payment_plan (
            ID INT AUTO_INCREMENT PRIMARY KEY,
            JOB_PROJECT_ID INT NOT NULL,
            NAME VARCHAR(80) NOT NULL,
            AMOUNT DECIMAL(12,2) NOT NULL DEFAULT 0,
            DUE_DATE DATE NULL,
            SORT_ORDER INT NOT NULL DEFAULT 0,
            INVOICE_TYPE VARCHAR(20) NULL,
            INVOICE_ID INT NULL,
            KEY ix_plan_invoice (INVOICE_TYPE, INVOICE_ID),
            CONSTRAINT fk_plan_project FOREIGN KEY (JOB_PROJECT_ID) REFERENCES job_projects (ID) ON DELETE CASCADE
        )""",
    "subcontractors": """
        CREATE TABLE subcontractors (
            ID INT AUTO_INCREMENT PRIMARY KEY,
            NAME VARCHAR(120) NOT NULL,
            COMPANY VARCHAR(120) NULL,
            TRADE VARCHAR(60) NULL,
            PHONE VARCHAR(20) NULL,
            EMAIL VARCHAR(150) NULL,
            NOTES VARCHAR(255) NULL,
            CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
    "project_subs": """
        CREATE TABLE project_subs (
            ID INT AUTO_INCREMENT PRIMARY KEY,
            JOB_PROJECT_ID INT NOT NULL,
            SUBCONTRACTOR_ID INT NOT NULL,
            SCOPE VARCHAR(150) NULL,
            AGREED_AMOUNT DECIMAL(12,2) NOT NULL DEFAULT 0,
            NOTES VARCHAR(255) NULL,
            CONSTRAINT fk_psub_project FOREIGN KEY (JOB_PROJECT_ID) REFERENCES job_projects (ID) ON DELETE CASCADE,
            CONSTRAINT fk_psub_sub FOREIGN KEY (SUBCONTRACTOR_ID) REFERENCES subcontractors (ID)
        )""",
    "project_sub_payments": """
        CREATE TABLE project_sub_payments (
            ID INT AUTO_INCREMENT PRIMARY KEY,
            PROJECT_SUB_ID INT NOT NULL,
            PAID_DATE DATE NOT NULL,
            AMOUNT DECIMAL(12,2) NOT NULL,
            METHOD VARCHAR(40) NULL,
            NOTE VARCHAR(255) NULL,
            EXPENSE_ID INT NULL,
            CONSTRAINT fk_psubpay_sub FOREIGN KEY (PROJECT_SUB_ID) REFERENCES project_subs (ID) ON DELETE CASCADE
        )""",
}


def apply(db_config):
    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor()
    done = []
    for name, ddl in TABLES.items():
        cur.execute("SHOW TABLES LIKE %s", (name,))
        if cur.fetchone() is None:
            cur.execute(ddl)
            done.append(name)
    for table, column, ddl in COLUMNS:
        cur.execute(f"SHOW COLUMNS FROM {table} LIKE %s", (column,))
        if cur.fetchone() is None:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")
            done.append(f"{table}.{column}")
    cur.execute("SHOW COLUMNS FROM expenses LIKE 'CATEGORY'")
    ctype = cur.fetchone()[1]
    ctype = ctype.decode() if isinstance(ctype, bytes) else ctype
    if "SUBCONTRACTOR" not in ctype:
        cur.execute("ALTER TABLE expenses MODIFY CATEGORY "
                    "ENUM('MATERIALS','GAS','TOOLS','OTHER','SUBCONTRACTOR') NOT NULL")
        done.append("expenses.CATEGORY += SUBCONTRACTOR")
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
