# -*- coding: utf-8 -*-
"""
Histórico de alterações (tabela audit_log).

Em vez de colocar uma linha de "registrar histórico" em cada tela, a conexão
devolvida por _get_connection() é embrulhada aqui: todo INSERT/UPDATE/DELETE
executado por ela é anotado e, quando a tela faz commit(), as anotações são
gravadas no audit_log junto, com o usuário logado e a hora.

Se gravar o histórico falhar por qualquer motivo, a alteração do usuário
continua valendo — o histórico nunca pode impedir um salvamento.
"""

import logging
import re

log = logging.getLogger("vl_flooring.historico")

AUDIT_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS audit_log (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    username VARCHAR(100) NULL,
    action VARCHAR(10) NOT NULL,
    table_name VARCHAR(64) NULL,
    record_id VARCHAR(64) NULL,
    details TEXT NULL,
    INDEX idx_audit_created (created_at),
    INDEX idx_audit_table (table_name, record_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""

_WRITE_RE = re.compile(
    r"^\s*(INSERT|REPLACE|UPDATE|DELETE)\b(?:\s+IGNORE)?(?:\s+INTO|\s+FROM)?\s+`?(\w+)`?",
    re.IGNORECASE,
)
_ID_RE = re.compile(r"\bWHERE\s+`?(?:\w+\.)?(ID|id)`?\s*=\s*%s", re.IGNORECASE)
_MAX_DETAILS = 2000


def ensure_audit_table(conn):
    cur = conn.cursor()
    cur.execute(AUDIT_TABLE_SQL)
    conn.commit()
    cur.close()


def _describe(sql, params):
    """Texto curto e legível do que foi alterado."""
    sql_one_line = " ".join(str(sql).split())
    if params is None:
        text = sql_one_line
    else:
        shown = []
        for p in (params.values() if isinstance(params, dict) else params):
            if isinstance(p, (bytes, bytearray)):
                shown.append(f"<{len(p)} bytes>")
            else:
                s = str(p)
                shown.append(s if len(s) <= 120 else s[:117] + "...")
        text = f"{sql_one_line}  ←  {shown}"
    return text if len(text) <= _MAX_DETAILS else text[: _MAX_DETAILS - 3] + "..."


def _record_id(sql, params, cursor, action):
    if action in ("INSERT", "REPLACE"):
        try:
            return str(cursor.lastrowid) if cursor.lastrowid else None
        except Exception:
            return None
    m = _ID_RE.search(" ".join(str(sql).split()))
    if m and params is not None and not isinstance(params, dict):
        # O id é o parâmetro que corresponde ao %s depois de "WHERE ID ="
        before = " ".join(str(sql).split())[: m.end()]
        index = before.count("%s") - 1
        try:
            return str(list(params)[index])
        except (IndexError, TypeError):
            return None
    return None


class AuditCursor:
    def __init__(self, cursor, owner):
        self._cursor = cursor
        self._owner = owner

    def execute(self, operation, params=None, *args, **kwargs):
        result = self._cursor.execute(operation, params, *args, **kwargs)
        self._owner._note(operation, params, self._cursor)
        return result

    def executemany(self, operation, seq_params, *args, **kwargs):
        seq_params = list(seq_params)
        result = self._cursor.executemany(operation, seq_params, *args, **kwargs)
        for params in seq_params:
            self._owner._note(operation, params, self._cursor)
        return result

    def __iter__(self):
        return iter(self._cursor)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self._cursor.close()
        return False

    def __getattr__(self, name):
        return getattr(self._cursor, name)


class AuditConnection:
    """Conexão MySQL que anota as alterações para o histórico."""

    def __init__(self, conn, username):
        object.__setattr__(self, "_conn", conn)
        object.__setattr__(self, "_username", username)
        object.__setattr__(self, "_pending", [])

    # ── anotações ───────────────────────────────────────────────────
    def _note(self, sql, params, cursor):
        m = _WRITE_RE.match(str(sql))
        if not m:
            return
        action, table = m.group(1).upper(), m.group(2)
        if table.lower() == "audit_log":
            return
        try:
            entry = (self._username, action, table, _record_id(sql, params, cursor, action), _describe(sql, params))
        except Exception:
            log.exception("could not describe change for history")
            return
        if getattr(self._conn, "autocommit", False):
            self._write([entry])
        else:
            self._pending.append(entry)

    def _write(self, entries):
        if not entries:
            return
        try:
            cur = self._conn.cursor()
            cur.executemany(
                "INSERT INTO audit_log (username, action, table_name, record_id, details) "
                "VALUES (%s, %s, %s, %s, %s)", entries)
            cur.close()
        except Exception:
            log.exception("could not write %d history entr(ies)", len(entries))

    # ── API da conexão ──────────────────────────────────────────────
    def cursor(self, *args, **kwargs):
        return AuditCursor(self._conn.cursor(*args, **kwargs), self)

    def commit(self):
        pending, self._pending[:] = list(self._pending), []
        self._write(pending)
        return self._conn.commit()

    def rollback(self):
        self._pending.clear()
        return self._conn.rollback()

    def close(self):
        self._pending.clear()  # sem commit = alteração desfeita, nada pra registrar
        return self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False

    def __getattr__(self, name):
        return getattr(self._conn, name)

    def __setattr__(self, name, value):
        setattr(self._conn, name, value)
