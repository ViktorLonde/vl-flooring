# -*- coding: utf-8 -*-
"""Migração de 25/11/2026 — com backup antes, pode rodar de novo sem problema.

• invoice_expenses: quais despesas já entraram em qual invoice (igual ao
  invoice_work_days dos dias). Preenche as antigas: despesa do mesmo
  contractor, dentro do período de uma invoice que tem EXPENSES_TOTAL, quando
  a soma bate com o total de despesas da invoice.
• app_settings.DAILY_SUMMARY (liga/desliga o resumo diário por e-mail) e
  app_settings.DAILY_LAST_SENT (o outro computador não manda de novo).

Uso: venv\\Scripts\\python.exe aplicar_migracao_2511.py [--no-backup] [--database NOME]"""
import sys

import config
import mysql.connector

COLUMNS = [
    ("app_settings", "DAILY_SUMMARY", "TINYINT(1) NOT NULL DEFAULT 1"),
    ("app_settings", "DAILY_LAST_SENT", "DATE NULL"),
]
INVOICE_EXPENSES = """
CREATE TABLE IF NOT EXISTS invoice_expenses (
    INVOICE_TYPE VARCHAR(20) NOT NULL,
    INVOICE_ID INT NOT NULL,
    EXPENSE_ID INT NOT NULL,
    PRIMARY KEY (EXPENSE_ID),
    KEY ix_invoice_expenses_invoice (INVOICE_TYPE, INVOICE_ID),
    CONSTRAINT fk_invoice_expenses_expense FOREIGN KEY (EXPENSE_ID) REFERENCES expenses (ID) ON DELETE CASCADE
)"""


def backfill(cur):
    """Liga as despesas antigas às invoices de Contractor que já as cobraram."""
    linked = 0
    cur.execute("SELECT ID, CONTRACTOR_ID, PERIOD_FROM, PERIOD_TO, EXPENSES_TOTAL FROM contractor_invoices "
                "WHERE COALESCE(EXPENSES_TOTAL, 0) > 0")
    for iid, cid, d_from, d_to, exp_total in cur.fetchall():
        cur.execute("SELECT e.ID, e.AMOUNT FROM expenses e WHERE e.CONTRACTOR_ID=%s AND e.EXPENSE_DATE BETWEEN %s AND %s "
                    "AND NOT EXISTS (SELECT 1 FROM invoice_expenses x WHERE x.EXPENSE_ID = e.ID)",
                    (cid, d_from, d_to))
        rows = cur.fetchall()
        target = round(float(exp_total), 2)
        chosen = None
        if round(sum(float(a) for _i, a in rows), 2) == target:
            chosen = [i for i, _a in rows]
        else:  # uma despesa só com o valor exato
            single = [i for i, a in rows if round(float(a), 2) == target]
            if len(single) == 1:
                chosen = single
        for eid in chosen or []:
            cur.execute("INSERT IGNORE INTO invoice_expenses (INVOICE_TYPE, INVOICE_ID, EXPENSE_ID) "
                        "VALUES ('Contractor', %s, %s)", (iid, eid))
            linked += cur.rowcount
    return linked


def apply(db_config):
    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor()
    done = []
    for table, column, ddl in COLUMNS:
        cur.execute(f"SHOW COLUMNS FROM {table} LIKE %s", (column,))
        if cur.fetchone() is None:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")
            done.append(f"{table}.{column}")
    cur.execute("SHOW TABLES LIKE 'invoice_expenses'")
    if cur.fetchone() is None:
        cur.execute(INVOICE_EXPENSES)
        done.append("invoice_expenses")
    n = backfill(cur)
    if n:
        done.append(f"{n} old expense(s) linked to their invoice")
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
