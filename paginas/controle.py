# -*- coding: utf-8 -*-
"""
Controle do dinheiro e dos dados — 25/11/2026 (pedido do Viktor: "pode fazer tudo"):

• Invoice da semana: na Home ("Needs your attention"), para cada pagador com
  dias da semana passada (domingo a sábado) fora de invoice → um clique abre
  o Generate Invoices com a semana e os dias certos marcados.
• Despesas a reembolsar ainda não cobradas (invoice_expenses).
• Pagamento repetido: ao lançar o mesmo valor na mesma invoice com até 7
  dias de diferença (ou lançado há menos de 10 minutos), pergunta antes.
• Data check: abas novas na janela de limpeza — quem paga?, datas muito no
  futuro, dias cancelados com valor, Job Codes sem dados, pagamentos que
  parecem repetidos.
• Resumo diário por e-mail (17h, uma vez por dia nos dois computadores):
  jobs de amanhã com equipe, dinheiro recebido hoje, atrasados, o que falta
  cobrar e o que deve entrar na semana. Liga/desliga em Settings → System.

Métodos da MainWindow (mixin) — veja main_.py.
"""
import html
import threading
from datetime import date, datetime, timedelta

from PySide6.QtWidgets import QCheckBox, QTextBrowser

from app_common import *  # noqa: F401,F403
from paginas import correio
from paginas.moderno import show_toast
from paginas.recebiveis_plus import ENTITY_SQL, money
from paginas.visual import tabler_icon

DAILY_HOUR = 17
# invoices já revisadas (pagamento a mais guardado como extra) não aparecem em "Repeated payments"
_REVIEWED = "AND NOT EXISTS (SELECT 1 FROM contractor_invoices ci WHERE p2.INVOICE_TYPE = 'Contractor' AND ci.ID = p2.INVOICE_ID AND ci.ADJUSTMENT_NOTE LIKE '%%Extra/tip received%%') AND NOT EXISTS (SELECT 1 FROM company_invoices co WHERE p2.INVOICE_TYPE = 'Company' AND co.ID = p2.INVOICE_ID AND co.ADJUSTMENT_NOTE LIKE '%%Extra/tip received%%') AND NOT EXISTS (SELECT 1 FROM client_invoices cl WHERE p2.INVOICE_TYPE = 'Client' AND cl.ID = p2.INVOICE_ID AND cl.ADJUSTMENT_NOTE LIKE '%%Extra/tip received%%')"


class ControlMixin:
    # ═════════════════════════ despesas não cobradas ═════════════════════════
    def _unbilled_expenses_total(self):
        """(total, quantidade) das despesas de contractor que ainda não entraram em invoice."""
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SHOW TABLES LIKE 'invoice_expenses'")
            if cur.fetchone() is None:
                return 0.0, 0
            cur.execute("SELECT COALESCE(SUM(e.AMOUNT), 0), COUNT(*) FROM expenses e "
                        "WHERE e.CONTRACTOR_ID IS NOT NULL AND e.EXPENSE_DATE <= CURDATE() "
                        "AND NOT EXISTS (SELECT 1 FROM invoice_expenses x WHERE x.EXPENSE_ID = e.ID)")
            total, n = cur.fetchone()
            return float(total or 0), int(n or 0)
        finally:
            cur.close()
            conn.close()

    # ═════════════════════════ invoice da semana ═════════════════════════
    @staticmethod
    def _last_full_week(today=None):
        """Última semana de cobrança completa: domingo a sábado (pedido do Viktor)."""
        today = today or date.today()
        this_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
        sunday = this_sunday - timedelta(days=7)
        return sunday, sunday + timedelta(days=6)

    def _weekly_invoice_suggestions(self, today=None):
        monday, sunday = self._last_full_week(today)
        groups = self._not_invoiced_groups(today=sunday, date_from=monday)
        return [g for g in groups if g["entity_id"] is not None], monday, sunday

    def _weekly_invoice_attention_items(self):
        if not self._role_rule("finance"):
            return []
        try:
            groups, monday, sunday = self._weekly_invoice_suggestions()
        except (MySQLError, RuntimeError):
            return []
        items = []
        for g in groups[:2]:
            text = (f"Invoice last week ({monday:%m/%d}–{sunday:%m/%d}) for {g['name']}: "
                    f"{len(g['days'])} day(s), {money(g['total'])}")
            items.append(("file-type-pdf", "#E65100", text,
                          lambda *_clicked, g=g, a=monday, b=sunday: self.open_generate_invoices_dialog(
                              prefill_bill_to=g["kind"], prefill_entity_id=g["entity_id"],
                              prefill_from=a, prefill_to=b, prefill_day_ids=set(g["days"]))))
        return items

    def _data_check_attention_item(self):
        try:
            n = sum(self._data_check_counts().values())
        except (MySQLError, RuntimeError):
            return None
        if not n:
            return None
        return ("clipboard-list", "#B26A00", f"{n} thing{'s' if n != 1 else ''} to check in your data",
                self.open_data_cleanup_dialog)

    # ═════════════════════════ pagamento repetido ═════════════════════════
    def _check_duplicate_payment(self, parent, entity_type, invoice_id, amount, paid_date_str):
        """True = pode gravar. Pergunta se já existe pagamento igual parecido."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT PAID_DATE, PAYMENT_METHOD FROM payments
                WHERE INVOICE_TYPE=%s AND INVOICE_ID=%s AND ABS(AMOUNT - %s) < 0.005
                  AND (ABS(DATEDIFF(PAID_DATE, %s)) <= 7 OR CREATED_AT >= NOW() - INTERVAL 10 MINUTE)
                ORDER BY PAID_DATE DESC LIMIT 1""", (entity_type, invoice_id, amount, paid_date_str))
            row = cur.fetchone()
            cur.close()
            conn.close()
        except (MySQLError, RuntimeError):
            return True
        if not row:
            return True
        when = row[0].strftime("%m/%d/%Y") if hasattr(row[0], "strftime") else str(row[0])
        answer = QMessageBox.question(
            parent, "Same payment again?",
            f"A payment of {money(amount)} ({row[1] or 'no method'}) on {when} is already recorded for this "
            f"invoice.\n\nRecord another {money(amount)} anyway?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        return answer == QMessageBox.StandardButton.Yes

    @staticmethod
    def _recalc_invoice_paid(cur, entity_type, invoice_id):
        table = ENTITY_SQL[entity_type][0]
        cur.execute("SELECT COALESCE(SUM(AMOUNT), 0) FROM payments WHERE INVOICE_TYPE=%s AND INVOICE_ID=%s",
                    (entity_type, invoice_id))
        paid = float(cur.fetchone()[0] or 0)
        cur.execute(f"SELECT TOTAL_AMOUNT FROM {table} WHERE ID=%s", (invoice_id,))
        row = cur.fetchone()
        total = float(row[0] or 0) if row else 0.0
        status = "RECEIVED" if paid >= total - 0.005 and paid > 0 else ("PARTIAL" if paid > 0 else "PENDING")
        cur.execute(f"UPDATE {table} SET AMOUNT_PAID=%s, STATUS=%s, "
                    f"RECEIVED_AT = CASE WHEN %s='RECEIVED' THEN COALESCE(RECEIVED_AT, NOW()) ELSE NULL END "
                    f"WHERE ID=%s", (paid, status, status, invoice_id))

    # ═════════════════════════ data check ═════════════════════════
    _OWN_COMPANY_SQL = None

    def _who_pays_rows(self):
        """Dias a cobrar sem pagador (sem contractor/company/client, ou só a própria empresa)."""
        groups = self._not_invoiced_groups()
        ids = [d for g in groups if g["entity_id"] is None for d in g["days"]]
        return ids

    def _data_check_queries(self):
        """{chave: (sql_linhas, sql_contagem)} das abas novas."""
        return {
            "future": ("""
                SELECT wd.ID, wd.ID, DATE_FORMAT(wd.WORK_DATE, '%m/%d/%Y'), COALESCE(jp.CODE, ''),
                       COALESCE(wd.JOB_ADDRESS, ''), CONCAT('$', FORMAT(COALESCE(wd.VALUE, 0), 2))
                FROM work_days wd LEFT JOIN job_projects jp ON jp.ID = wd.JOB_PROJECT_ID
                WHERE wd.WORK_DATE > CURDATE() + INTERVAL 120 DAY ORDER BY wd.WORK_DATE""",
                "SELECT COUNT(*) FROM work_days WHERE WORK_DATE > CURDATE() + INTERVAL 120 DAY"),
            "cancelled": ("""
                SELECT wd.ID, wd.ID, DATE_FORMAT(wd.WORK_DATE, '%m/%d/%Y'), COALESCE(jp.CODE, ''),
                       COALESCE(wd.JOB_ADDRESS, ''), CONCAT('$', FORMAT(COALESCE(wd.VALUE, 0), 2))
                FROM work_days wd LEFT JOIN job_projects jp ON jp.ID = wd.JOB_PROJECT_ID
                WHERE wd.STATUS = 'CANCELLED' AND COALESCE(wd.VALUE, 0) > 0
                  AND NOT EXISTS (SELECT 1 FROM invoice_work_days i WHERE i.WORK_DAY_ID = wd.ID)
                ORDER BY wd.WORK_DATE DESC""",
                "SELECT COUNT(*) FROM work_days wd WHERE wd.STATUS = 'CANCELLED' AND COALESCE(wd.VALUE, 0) > 0 "
                "AND NOT EXISTS (SELECT 1 FROM invoice_work_days i WHERE i.WORK_DAY_ID = wd.ID)"),
            "jobcodes": ("""
                SELECT jp.ID, jp.CODE,
                       (SELECT COUNT(*) FROM work_days w WHERE w.JOB_PROJECT_ID = jp.ID),
                       CONCAT_WS(', ',
                         IF(jp.CLIENT_ID IS NULL AND jp.COMPANY_ID IS NULL AND jp.CONTRACTOR_ID IS NULL,
                            'who it is for', NULL),
                         IF(COALESCE(jp.JOB_ADDRESS, '') = '', 'address', NULL))
                FROM job_projects jp
                WHERE (jp.CLIENT_ID IS NULL AND jp.COMPANY_ID IS NULL AND jp.CONTRACTOR_ID IS NULL)
                   OR COALESCE(jp.JOB_ADDRESS, '') = ''
                ORDER BY jp.CODE""",
                "SELECT COUNT(*) FROM job_projects jp WHERE (jp.CLIENT_ID IS NULL AND jp.COMPANY_ID IS NULL "
                "AND jp.CONTRACTOR_ID IS NULL) OR COALESCE(jp.JOB_ADDRESS, '') = ''"),
            "duplicates": ("""
                SELECT p2.ID, CONCAT(p2.INVOICE_TYPE, ' #', p2.INVOICE_ID),
                       DATE_FORMAT(p1.PAID_DATE, '%m/%d/%Y'), DATE_FORMAT(p2.PAID_DATE, '%m/%d/%Y'),
                       CONCAT('$', FORMAT(p2.AMOUNT, 2)), COALESCE(p2.PAYMENT_METHOD, '')
                FROM payments p1 JOIN payments p2
                  ON p2.INVOICE_TYPE = p1.INVOICE_TYPE AND p2.INVOICE_ID = p1.INVOICE_ID AND p2.ID > p1.ID
                 AND ABS(p2.AMOUNT - p1.AMOUNT) < 0.005 AND ABS(DATEDIFF(p2.PAID_DATE, p1.PAID_DATE)) <= 7
                WHERE 1=1 """ + _REVIEWED + """
                ORDER BY p2.PAID_DATE DESC""",
                "SELECT COUNT(*) FROM payments p1 JOIN payments p2 ON p2.INVOICE_TYPE = p1.INVOICE_TYPE "
                "AND p2.INVOICE_ID = p1.INVOICE_ID AND p2.ID > p1.ID AND ABS(p2.AMOUNT - p1.AMOUNT) < 0.005 "
                "AND ABS(DATEDIFF(p2.PAID_DATE, p1.PAID_DATE)) <= 7 " + _REVIEWED),
        }

    def _data_check_counts(self):
        out = {"whopays": len(self._who_pays_rows())}
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            for key, (_rows_sql, count_sql) in self._data_check_queries().items():
                cur.execute(count_sql)
                out[key] = int(cur.fetchone()[0] or 0)
        finally:
            cur.close()
            conn.close()
        return out

    def _extra_cleanup_pages(self, dialog, make_table, fill, selected_ids, run):
        """Abas novas da janela Data check. Cada uma: (chave, página, título, loader(cur) -> n)."""
        pages = []
        read_only = self._role_rule("read_only")

        def open_day_from(t):
            ids = selected_ids(t)
            if ids:
                dialog.accept()
                self._open_job_by_id(ids[0], None)

        # ── quem paga? ──
        wp = QWidget()
        wl = QVBoxLayout(wp)
        info = QLabel("Work days to bill that have nobody to bill: no contractor, company or client — or only your "
                      "own company as contractor. Double-click to open the day and choose who pays.")
        info.setWordWrap(True)
        wl.addWidget(info)
        wp_t = make_table(["Job #", "Date", "Job Code", "Address", "Value"], stretch=3)
        wp_t.setObjectName("table_check_whopays")
        wl.addWidget(wp_t, 1)
        wp_t.cellDoubleClicked.connect(lambda *_: open_day_from(wp_t))

        def load_whopays(cur):
            ids = self._who_pays_rows()
            rows = []
            if ids:
                cur.execute(f"""
                    SELECT wd.ID, wd.ID, DATE_FORMAT(wd.WORK_DATE, '%m/%d/%Y'), COALESCE(jp.CODE, ''),
                           COALESCE(wd.JOB_ADDRESS, ''), CONCAT('$', FORMAT(COALESCE(wd.VALUE, 0), 2))
                    FROM work_days wd LEFT JOIN job_projects jp ON jp.ID = wd.JOB_PROJECT_ID
                    WHERE wd.ID IN ({','.join(['%s'] * len(ids))}) ORDER BY wd.WORK_DATE""", ids)
                rows = cur.fetchall()
            fill(wp_t, rows)
            return len(rows)
        pages.append(("whopays", wp, "Who pays?", load_whopays))

        q = self._data_check_queries()

        # ── datas muito no futuro ──
        fp = QWidget()
        fl = QVBoxLayout(fp)
        fl.addWidget(QLabel("Days more than 4 months ahead — usually a typo in the year. Double-click to fix the date:"))
        fp_t = make_table(["Job #", "Date", "Job Code", "Address", "Value"], stretch=3)
        fp_t.setObjectName("table_check_future")
        fl.addWidget(fp_t, 1)
        fp_t.cellDoubleClicked.connect(lambda *_: open_day_from(fp_t))

        def load_future(cur):
            cur.execute(q["future"][0])
            rows = cur.fetchall()
            fill(fp_t, rows)
            return len(rows)
        pages.append(("future", fp, "Dates far ahead", load_future))

        # ── cancelados com valor ──
        cp = QWidget()
        cl = QVBoxLayout(cp)
        cinfo = QLabel("Cancelled days that still have a value. The value is not billed or counted, but it shows up in "
                       "some totals — set it to $0, or double-click to open the day.")
        cinfo.setWordWrap(True)
        cl.addWidget(cinfo)
        cp_t = make_table(["Job #", "Date", "Job Code", "Address", "Value"], stretch=3)
        cp_t.setObjectName("table_check_cancelled")
        cl.addWidget(cp_t, 1)
        cb = QHBoxLayout()
        b_zero = QPushButton("  Set value to $0")
        b_zero.setObjectName("btn_check_zero_cancelled")
        b_zero.setIcon(tabler_icon("eraser", "#37474F", 16))
        b_all = QPushButton("Select all")
        cb.addWidget(b_all)
        cb.addWidget(b_zero)
        cb.addStretch(1)
        cl.addLayout(cb)
        cp_t.cellDoubleClicked.connect(lambda *_: open_day_from(cp_t))
        b_all.clicked.connect(cp_t.selectAll)

        def zero_cancelled():
            ids = selected_ids(cp_t)
            if not ids:
                QMessageBox.information(dialog, "Nothing selected", "Select the days first.")
                return
            marks = ",".join(["%s"] * len(ids))
            run([(f"UPDATE work_days SET VALUE=0 WHERE STATUS='CANCELLED' AND ID IN ({marks})", tuple(ids))],
                f"{len(ids)} cancelled day(s) set to $0.")
        b_zero.clicked.connect(zero_cancelled)

        def load_cancelled(cur):
            cur.execute(q["cancelled"][0])
            rows = cur.fetchall()
            fill(cp_t, rows)
            return len(rows)
        pages.append(("cancelled", cp, "Cancelled with value", load_cancelled))

        # ── Job Codes sem dados ──
        jp = QWidget()
        jl = QVBoxLayout(jp)
        jinfo = QLabel("Job Codes without who it is for or without an address. Double-click to open the last day of the "
                       "Job Code. A Job Code with no days can be removed in Job Records → Clean empty Job Codes.")
        jinfo.setWordWrap(True)
        jl.addWidget(jinfo)
        jp_t = make_table(["Job Code", "Days", "Missing"], stretch=2)
        jp_t.setObjectName("table_check_jobcodes")
        jl.addWidget(jp_t, 1)

        def open_code(*_a):
            ids = selected_ids(jp_t)
            if not ids:
                return
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT ID, WORK_DATE FROM work_days WHERE JOB_PROJECT_ID=%s ORDER BY WORK_DATE DESC, ID DESC "
                        "LIMIT 1", (ids[0],))
            row = cur.fetchone()
            cur.close()
            conn.close()
            if not row:
                QMessageBox.information(dialog, "No days", "This Job Code has no work days yet. Add a day to it, or "
                                        "remove it in Job Records → Clean empty Job Codes.")
                return
            dialog.accept()
            self._open_job_by_id(row[0], row[1])
        jp_t.cellDoubleClicked.connect(open_code)

        def load_codes(cur):
            cur.execute(q["jobcodes"][0])
            rows = cur.fetchall()
            fill(jp_t, rows)
            return len(rows)
        pages.append(("jobcodes", jp, "Job Codes missing info", load_codes))

        # ── pagamentos repetidos ──
        dp = QWidget()
        dl = QVBoxLayout(dp)
        dinfo = QLabel("Two payments with the same amount on the same invoice, up to 7 days apart. If the second one was "
                       "typed twice by mistake, select it and click Delete — the invoice's paid total is fixed too.")
        dinfo.setWordWrap(True)
        dl.addWidget(dinfo)
        dp_t = make_table(["Invoice", "First payment", "Second payment", "Amount", "Method"], stretch=0)
        dp_t.setObjectName("table_check_duplicates")
        dl.addWidget(dp_t, 1)
        db = QHBoxLayout()
        b_del = QPushButton("  Delete the second payment")
        b_del.setObjectName("btn_check_delete_duplicate")
        b_del.setIcon(tabler_icon("trash", "#C62828", 16))
        db.addWidget(b_del)
        db.addStretch(1)
        dl.addLayout(db)

        def delete_dup():
            ids = selected_ids(dp_t)
            if not ids:
                QMessageBox.information(dialog, "Nothing selected", "Select the payment first.")
                return
            answer = QMessageBox.question(dialog, "Delete payment",
                                          f"Delete {len(ids)} payment(s)? The invoice's paid total is recalculated.",
                                          QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                          QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                return
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                for pid in ids:
                    cur.execute("SELECT INVOICE_TYPE, INVOICE_ID FROM payments WHERE ID=%s", (pid,))
                    row = cur.fetchone()
                    if not row:
                        continue
                    cur.execute("DELETE FROM payments WHERE ID=%s", (pid,))
                    self._recalc_invoice_paid(cur, row[0], row[1])
                conn.commit()
                cur.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", str(e))
                return
            run([], f"{len(ids)} payment(s) deleted.")
        b_del.clicked.connect(delete_dup)

        def load_dups(cur):
            cur.execute(q["duplicates"][0])
            rows = cur.fetchall()
            fill(dp_t, rows)
            return len(rows)
        pages.append(("duplicates", dp, "Repeated payments", load_dups))

        if read_only:
            for b in (b_zero, b_del):
                b.setEnabled(False)
                b.setToolTip("Your user has read-only access.")
        if not self._role_rule("can_delete"):
            b_del.setEnabled(False)
            b_del.setToolTip("Only an Admin can delete payments.")
        dialog._tables.update({"whopays": wp_t, "future": fp_t, "cancelled": cp_t, "jobcodes": jp_t,
                               "duplicates": dp_t}) if hasattr(dialog, "_tables") else None
        dialog._check_tables = {"whopays": wp_t, "future": fp_t, "cancelled": cp_t, "jobcodes": jp_t,
                                "duplicates": dp_t}
        dialog._check_buttons = {"zero": b_zero, "delete_dup": b_del}
        return pages

    # ═════════════════════════ resumo diário ═════════════════════════
    def _daily_summary_enabled(self):
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT COALESCE(DAILY_SUMMARY, 1) FROM app_settings WHERE ID=1")
            row = cur.fetchone()
            cur.close()
            conn.close()
            return bool(row[0]) if row else True
        except (MySQLError, RuntimeError):
            return False

    def _set_daily_summary_enabled(self, on):
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("UPDATE app_settings SET DAILY_SUMMARY=%s WHERE ID=1", (1 if on else 0,))
            conn.commit()
            cur.close()
            conn.close()
        except (MySQLError, RuntimeError):
            logging.getLogger("vl_flooring").exception("could not save the daily summary option")

    def _daily_summary_data(self, today=None):
        today = today or date.today()
        nxt = today + timedelta(days=1)
        d = {"today": today, "next": nxt}
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT wd.ID, COALESCE(jp.CODE, ''), COALESCE(wd.JOB_ADDRESS, ''),
                       COALESCE(NULLIF(co.COMPANY_NAME, ''), cl.FULL_NAME, NULLIF(ct.COMPANY_NAME, ''), ct.FULL_NAME, ''),
                       wd.STATUS, COALESCE(wd.DAY_FRACTION, 1)
                FROM work_days wd
                LEFT JOIN job_projects jp ON jp.ID = wd.JOB_PROJECT_ID
                LEFT JOIN companies co ON co.ID = wd.COMPANY_ID
                LEFT JOIN clients cl ON cl.ID = wd.CLIENT_ID
                LEFT JOIN contractors ct ON ct.ID = wd.CONTRACTOR_ID
                WHERE wd.WORK_DATE = %s AND COALESCE(wd.STATUS, '') <> 'CANCELLED'
                ORDER BY COALESCE(wd.DAY_SEQUENCE, 999999), wd.ID""", (nxt,))
            jobs = []
            for wid, code, addr, who, status, frac in cur.fetchall():
                cur.execute("SELECT h.FULL_NAME FROM work_day_helpers x JOIN helpers h ON h.ID = x.HELPER_ID "
                            "WHERE x.WORK_DAY_ID=%s ORDER BY h.FULL_NAME", (wid,))
                crew = [r[0] for r in cur.fetchall()]
                jobs.append({"code": code, "address": addr, "who": who, "crew": crew, "fraction": float(frac or 1)})
            d["jobs"] = jobs
            cur.execute("""
                SELECT p.AMOUNT, COALESCE(p.PAYMENT_METHOD, ''), p.INVOICE_TYPE, p.INVOICE_ID
                FROM payments p WHERE p.PAID_DATE = %s ORDER BY p.ID""", (today,))
            d["received"] = [(float(a or 0), m, k, i) for a, m, k, i in cur.fetchall()]
        finally:
            cur.close()
            conn.close()
        open_inv = self._open_invoices_with_due()
        d["overdue"] = [(k, i, n, bal, due) for k, i, n, bal, due in open_inv if bal > 0 and due and due < today]
        week_end = today + timedelta(days=6)
        d["this_week"] = sum(bal for _k, _i, _n, bal, due in open_inv if bal > 0 and due and today <= due <= week_end)
        groups = self._not_invoiced_groups(today=today)
        d["not_invoiced"] = sum(g["total"] for g in groups)
        d["not_invoiced_days"] = sum(len(g["days"]) for g in groups)
        d["expenses_unbilled"] = self._unbilled_expenses_total()
        return d

    def _daily_summary_html(self, d):
        e = html.escape
        td = "style='padding:4px 10px 4px 0;border-bottom:1px solid #E3E8EE'"
        tdr = "style='padding:4px 0 4px 10px;border-bottom:1px solid #E3E8EE;text-align:right'"
        parts = [f"<h2 style='margin:0 0 4px 0'>Daily summary — {d['today']:%A, %b %d}</h2>"]
        parts.append(f"<h3 style='margin:14px 0 4px 0'>Tomorrow ({d['next']:%a %m/%d})</h3>")
        if d["jobs"]:
            parts.append("<table cellspacing='0'>")
            for j in d["jobs"]:
                crew = ", ".join(j["crew"]) or "no helper"
                part = "" if j["fraction"] >= 1 else " · part of the day"
                parts.append(f"<tr><td {td}><b>{e(j['code'] or '—')}</b></td><td {td}>{e(j['address'])}</td>"
                             f"<td {td}>{e(j['who'])}</td><td {td}>{e(crew)}{part}</td></tr>")
            parts.append("</table>")
        else:
            parts.append("<p>Nothing scheduled.</p>")
        total_in = sum(a for a, *_r in d["received"])
        parts.append(f"<h3 style='margin:14px 0 4px 0'>Received today: {money(total_in)}</h3>")
        if d["received"]:
            parts.append("<table cellspacing='0'>")
            for amount, method, kind, iid in d["received"]:
                parts.append(f"<tr><td {td}>{kind} invoice #{iid}</td><td {td}>{e(method)}</td>"
                             f"<td {tdr}>{money(amount)}</td></tr>")
            parts.append("</table>")
        parts.append("<h3 style='margin:14px 0 4px 0'>Money to follow</h3><ul style='margin:0'>")
        if d["overdue"]:
            late = sum(b for *_x, b, _d in d["overdue"])
            names = ", ".join(sorted({n for _k, _i, n, _b, _d in d["overdue"]}))
            parts.append(f"<li><span style='color:#C62828'><b>Overdue: {money(late)}</b></span> "
                         f"({len(d['overdue'])} invoice(s) — {e(names)})</li>")
        else:
            parts.append("<li>No overdue invoices ✔</li>")
        parts.append(f"<li>Expected this week: <b>{money(d['this_week'])}</b></li>")
        if d["not_invoiced"]:
            parts.append(f"<li><span style='color:#E65100'>Not invoiced yet: <b>{money(d['not_invoiced'])}</b></span> "
                         f"({d['not_invoiced_days']} work day(s))</li>")
        exp_total, exp_n = d["expenses_unbilled"]
        if exp_n:
            parts.append(f"<li>Expenses to reimburse, not billed: {money(exp_total)} ({exp_n})</li>")
        parts.append("</ul>")
        return "".join(parts)

    def _daily_summary_text(self, d):
        lines = [f"Daily summary — {d['today']:%A, %b %d}", "", f"Tomorrow ({d['next']:%a %m/%d}):"]
        lines += [f"  {j['code'] or '—'}  {j['address']}  ({j['who']}) — {', '.join(j['crew']) or 'no helper'}"
                  for j in d["jobs"]] or ["  Nothing scheduled."]
        lines += ["", f"Received today: {money(sum(a for a, *_r in d['received']))}"]
        late = sum(b for *_x, b, _d in d["overdue"])
        lines += ["", f"Overdue: {money(late)}", f"Expected this week: {money(d['this_week'])}",
                  f"Not invoiced yet: {money(d['not_invoiced'])}"]
        return "\n".join(lines)

    def _send_daily_summary(self, d, recipient):
        m = EmailMessage()
        m["Subject"] = f"Daily summary {d['today']:%m/%d} — {company_settings.COMPANY_NAME}"
        m["From"] = f"{company_settings.EMAIL_FROM_NAME} <{company_settings.EMAIL_SMTP_USER}>"
        m["To"] = recipient
        m.set_content(self._daily_summary_text(d))
        m.add_alternative(f"<html><body style='font-family:Segoe UI,Arial,sans-serif'>{self._daily_summary_html(d)}"
                          f"</body></html>", subtype="html")
        with smtplib.SMTP(company_settings.EMAIL_SMTP_HOST, company_settings.EMAIL_SMTP_PORT, timeout=20) as server:
            server.starttls()
            server.login(company_settings.EMAIL_SMTP_USER, company_settings.EMAIL_SMTP_PASSWORD)
            server.send_message(m)

    def _start_daily_summary_timer(self):
        """Confere a cada 10 minutos (e logo depois do login) se já passou das 17h."""
        if getattr(self, "_daily_timer", None) is None:
            self._daily_timer = QTimer(self)
            self._daily_timer.setInterval(10 * 60 * 1000)
            self._daily_timer.timeout.connect(self._auto_send_daily_summary)
            self._daily_timer.start()
        self._auto_send_daily_summary()

    def _auto_send_daily_summary(self, now=None):
        now = now or datetime.now()
        if now.hour < DAILY_HOUR or getattr(self, "_db_read_only", False):
            return False
        if not self._role_rule("finance") or not correio.smtp_ready() or not self._daily_summary_enabled():
            return False
        recipient = self._summary_recipient()
        if "@" not in recipient:
            return False
        today = now.date()
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            # "reserva" o dia antes de enviar — o outro computador não manda de novo
            cur.execute("UPDATE app_settings SET DAILY_LAST_SENT=%s WHERE ID=1 "
                        "AND (DAILY_LAST_SENT IS NULL OR DAILY_LAST_SENT <> %s)", (today, today))
            claimed = cur.rowcount
            conn.commit()
            cur.close()
            conn.close()
            if not claimed:
                return False
            data = self._daily_summary_data(today)
        except (MySQLError, RuntimeError):
            logging.getLogger("vl_flooring").exception("daily summary: could not prepare")
            return False
        db_config = dict(self.db_config)
        log = logging.getLogger("vl_flooring")

        def worker():
            try:
                self._send_daily_summary(data, recipient)
                log.info("daily summary %s sent to %s", today, recipient)
            except Exception:
                log.exception("daily summary %s could not be sent", today)
                try:  # libera para tentar de novo daqui a pouco
                    import mysql.connector as _m
                    c = _m.connect(**db_config)
                    cc = c.cursor()
                    cc.execute("UPDATE app_settings SET DAILY_LAST_SENT=NULL WHERE ID=1 AND DAILY_LAST_SENT=%s",
                               (today,))
                    c.commit()
                    c.close()
                except Exception:
                    pass
        threading.Thread(target=worker, daemon=True).start()
        return True

    def open_daily_summary_dialog(self):
        try:
            data = self._daily_summary_data()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not build the summary:\n{e}")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Daily summary")
        dialog.resize(720, 620)
        v = QVBoxLayout(dialog)
        view = QTextBrowser()
        view.setObjectName("view_daily_summary")
        view.setHtml(self._daily_summary_html(data))
        v.addWidget(view, 1)
        row = QHBoxLayout()
        lbl = QLabel(f"Goes to: {self._summary_recipient() or '(set the e-mail in Weekly Summary)'}")
        lbl.setStyleSheet("color:#6B7C93;")
        row.addWidget(lbl, 1)
        btn_send = QPushButton("  Send now")
        btn_send.setIcon(tabler_icon("send", "#37474F", 16))
        btn_close = QPushButton("Close")
        row.addWidget(btn_send)
        row.addWidget(btn_close)
        v.addLayout(row)

        def send():
            recipient = self._summary_recipient()
            if "@" not in recipient or not correio.smtp_ready():
                QMessageBox.warning(dialog, "E-mail", "Set up the e-mail in Settings → Email and the summary address "
                                    "in Weekly Summary first.")
                return
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                self._send_daily_summary(data, recipient)
            except Exception as e:
                QApplication.restoreOverrideCursor()
                QMessageBox.warning(dialog, "E-mail", f"Could not send:\n{e}")
                return
            QApplication.restoreOverrideCursor()
            show_toast(f"Daily summary sent to {recipient}.", "success", self)

        btn_send.clicked.connect(send)
        btn_close.clicked.connect(dialog.accept)
        dialog._view = view
        dialog.exec()

    def _daily_summary_card(self):
        chk = QCheckBox(f"E-mail me a summary every day at {DAILY_HOUR - 12} PM")
        chk.setObjectName("chk_daily_summary")
        chk.setChecked(self._daily_summary_enabled())
        chk.toggled.connect(self._set_daily_summary_enabled)
        btn = QPushButton("  Preview…")
        btn.setIcon(tabler_icon("send", "#4FA3FF", 16))
        btn.clicked.connect(self.open_daily_summary_dialog)
        return self._settings_card(
            "Daily summary e-mail",
            "Tomorrow's jobs with the crew, money received today, overdue invoices, what is not invoiced yet and "
            "what should come in this week. Sent once a day (even with the app open on both computers) to the "
            "Weekly Summary e-mail address.",
            [chk], [btn])
