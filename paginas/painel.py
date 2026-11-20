# -*- coding: utf-8 -*-
"""
Painéis de acompanhamento:

• Projects Board (Kanban) — um cartão por Job Code nas colunas
  Pending → In Progress → Completed → Invoiced → Paid. As 3 primeiras vêm
  do status dos dias (work_days); Invoiced / Paid ficam gravados em
  job_projects.STATUS. Arrastar um cartão muda o estágio:
    – para Completed: marca como COMPLETED os dias abertos até hoje;
    – de Pending para In Progress: o primeiro dia pendente vira IN_PROGRESS;
    – para Invoiced / Paid: grava no Job Code; voltar tira a marca (ACTIVE).
• Weekly Summary — resumo da semana (dias, valor produzido, helper pay
  por helper, invoices em aberto, despesas, próxima semana). Na primeira
  vez que o app abre numa semana nova aparece em "Needs your attention" e,
  com o e-mail (SMTP) configurado, é enviado sozinho para o e-mail do
  resumo (app_settings.SUMMARY_EMAIL) — uma vez por semana, mesmo usando
  os dois computadores (app_settings.SUMMARY_LAST_SENT).
• Data Cleanup — o que está bagunçado no banco com o botão para arrumar:
  dias antigos ainda abertos, clientes "— Select —", jobs sem ninguém,
  produtos sem preço.

Métodos da MainWindow (mixin) — veja main_.py.
"""

import html
import threading
from datetime import date, timedelta

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QMenu, QTabWidget, QTextBrowser

from app_common import *  # noqa: F401,F403
from paginas.visual import tabler_icon
from paginas.moderno import show_toast

BOARD_STAGES = [
    ("PENDING", "Pending", "#64748B"),
    ("IN_PROGRESS", "In Progress", "#1565C0"),
    ("COMPLETED", "Completed", "#2E7D32"),
    ("INVOICED", "Invoiced", "#B26A00"),
    ("PAID", "Paid", "#6A1B9A"),
]
MANUAL_STAGES = ("INVOICED", "PAID")
_STAGE_LABEL = {k: label for k, label, _c in BOARD_STAGES}

_BOARD_LIST_QSS = (
    "QListWidget { background-color: #F1F5F9; border: 1px solid #E2E8F0; border-radius: 10px; padding: 4px; }"
    "QListWidget::item { background-color: #FFFFFF; color: #334155; border: 1px solid #E2E8F0; "
    "border-radius: 8px; margin: 4px; padding: 8px; }"
    "QListWidget::item:selected { border: 2px solid #1565C0; color: #334155; background-color: #FFFFFF; }"
)
_PRIMARY_BTN = ("QPushButton { background-color: #1565C0; color: #FFFFFF; border: none; border-radius: 6px; "
                "padding: 8px 16px; font-weight: 700; } QPushButton:hover { background-color: #1E88E5; }")
_SMALL_BTN = ("QPushButton { background-color: #EEF2F7; color: #37474F; border: 1px solid #D0D7DE; "
              "border-radius: 6px; padding: 6px 12px; font-size: 12px; font-weight: 600; } "
              "QPushButton:hover { background-color: #E1E8F0; }")

_PLACEHOLDER_CLIENT_SQL = "(FULL_NAME LIKE '%%— Select —%%' OR FULL_NAME LIKE '— Select%%' OR FULL_NAME = 'Select')"


def _money(v):
    return f"${float(v or 0):,.2f}"


def _week_key(monday):
    y, w, _ = monday.isocalendar()
    return f"{y}-W{w:02d}"


class _StageList(QListWidget):
    """Coluna do quadro: aceita cartões arrastados das outras colunas."""

    def __init__(self, stage, on_drop):
        super().__init__()
        self.stage = stage
        self._on_drop = on_drop
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setWordWrap(True)
        self.setSpacing(2)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setStyleSheet(_BOARD_LIST_QSS)

    def dragEnterEvent(self, event):
        if isinstance(event.source(), _StageList):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if isinstance(event.source(), _StageList) and event.source() is not self:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        src = event.source()
        if not isinstance(src, _StageList) or src is self or src.currentItem() is None:
            event.ignore()
            return
        pid = src.currentItem().data(Qt.ItemDataRole.UserRole)
        # O quadro é recarregado depois — não deixa o Qt mover o item sozinho
        event.setDropAction(Qt.DropAction.IgnoreAction)
        event.accept()
        QTimer.singleShot(0, lambda: self._on_drop(pid, src.stage, self.stage))


class BoardSummaryCleanupMixin:
    # ═════════════════════════ PROJECTS BOARD ═════════════════════════
    def _board_projects(self):
        """[{id, code, stage, who, days, value, first, last, last_day_id, last_date, manual}]"""
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT jp.ID, jp.CODE, COALESCE(jp.STATUS, 'ACTIVE'),
                   COALESCE(MAX(cl.FULL_NAME), MAX(co.COMPANY_NAME), MAX(NULLIF(ct.COMPANY_NAME, '')), MAX(ct.FULL_NAME), ''),
                   COUNT(wd.ID),
                   COALESCE(SUM(wd.STATUS = 'PENDING'), 0),
                   COALESCE(SUM(wd.STATUS = 'COMPLETED'), 0),
                   COALESCE(SUM(wd.STATUS = 'CANCELLED'), 0),
                   COALESCE(SUM(CASE WHEN wd.STATUS <> 'CANCELLED' THEN wd.VALUE ELSE 0 END), 0),
                   MIN(wd.WORK_DATE), MAX(wd.WORK_DATE),
                   SUBSTRING_INDEX(GROUP_CONCAT(wd.ID ORDER BY wd.WORK_DATE DESC, wd.ID DESC), ',', 1),
                   COALESCE(SUM(wd.STATUS <> 'CANCELLED' AND inv.WORK_DAY_ID IS NOT NULL), 0),
                   COALESCE(SUM(wd.STATUS <> 'CANCELLED' AND inv.PAID = 1), 0)
            FROM job_projects jp
            LEFT JOIN work_days wd ON wd.JOB_PROJECT_ID = jp.ID
            LEFT JOIN (
                SELECT x.WORK_DAY_ID, MAX(COALESCE(ci.STATUS, co.STATUS, cl.STATUS) = 'RECEIVED') AS PAID
                FROM invoice_work_days x
                LEFT JOIN contractor_invoices ci ON x.INVOICE_TYPE = 'Contractor' AND ci.ID = x.INVOICE_ID
                LEFT JOIN company_invoices co ON x.INVOICE_TYPE = 'Company' AND co.ID = x.INVOICE_ID
                LEFT JOIN client_invoices cl ON x.INVOICE_TYPE = 'Client' AND cl.ID = x.INVOICE_ID
                WHERE COALESCE(ci.ID, co.ID, cl.ID) IS NOT NULL
                GROUP BY x.WORK_DAY_ID
            ) inv ON inv.WORK_DAY_ID = wd.ID
            LEFT JOIN clients cl ON cl.ID = wd.CLIENT_ID AND NOT (cl.FULL_NAME LIKE '%%Select%%')
            LEFT JOIN companies co ON co.ID = wd.COMPANY_ID
            LEFT JOIN contractors ct ON ct.ID = wd.CONTRACTOR_ID
            WHERE jp.CODE IS NOT NULL
            GROUP BY jp.ID, jp.CODE, jp.STATUS
            ORDER BY MAX(wd.WORK_DATE) DESC, jp.ID DESC
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        out = []
        for (pid, code, status, who, total, pending, completed, cancelled, value, first, last, last_day,
             invoiced, paid) in rows:
            status = (status or "ACTIVE").upper()
            active = (total or 0) - (cancelled or 0)
            invoiced, paid = int(invoiced or 0), int(paid or 0)
            if total and not active:
                continue  # todos os dias cancelados — fora do quadro
            if status in MANUAL_STAGES:
                stage = status
            elif active and paid >= active:
                stage = "PAID"          # todos os dias em invoices já recebidos
            elif active and invoiced >= active:
                stage = "INVOICED"      # todos os dias já entraram em algum invoice
            elif not active or pending == active:
                stage = "PENDING"
            elif completed == active:
                stage = "COMPLETED"
            else:
                stage = "IN_PROGRESS"
            out.append({"id": pid, "code": code, "stage": stage, "who": who or "", "days": active,
                        "value": float(value or 0), "first": first, "last": last,
                        "last_day_id": int(last_day) if last_day else None, "manual": status in MANUAL_STAGES,
                        "invoiced": invoiced, "paid": paid})
        return out

    def _board_stage_of(self, project_id):
        return next((p["stage"] for p in self._board_projects() if p["id"] == project_id), None)

    def _board_move(self, project_id, from_stage, to_stage, confirm=True):
        """Muda o estágio de um Job Code. Devolve o estágio final (ou None)."""
        if from_stage == to_stage:
            return from_stage
        if self._role_rule("read_only"):
            QMessageBox.information(self, "Read-only", "Your user has read-only access.")
            return None
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT CODE FROM job_projects WHERE ID=%s", (project_id,))
            code = (cur.fetchone() or ["?"])[0]
            if to_stage in MANUAL_STAGES:
                if from_stage in ("PENDING", "IN_PROGRESS") and confirm:
                    answer = QMessageBox.question(
                        self, "Move job",
                        f"{code} still has days that are not completed.\n\nMark it as {_STAGE_LABEL[to_stage]} anyway?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
                    if answer != QMessageBox.StandardButton.Yes:
                        cur.close()
                        conn.close()
                        return None
                cur.execute("UPDATE job_projects SET STATUS=%s WHERE ID=%s", (to_stage, project_id))
            else:
                cur.execute("UPDATE job_projects SET STATUS='ACTIVE' WHERE ID=%s", (project_id,))
                if to_stage == "COMPLETED":
                    cur.execute("SELECT COUNT(*) FROM work_days WHERE JOB_PROJECT_ID=%s AND WORK_DATE <= CURDATE() "
                                "AND STATUS NOT IN ('COMPLETED', 'CANCELLED')", (project_id,))
                    n = cur.fetchone()[0] or 0
                    if n:
                        if confirm:
                            answer = QMessageBox.question(
                                self, "Complete job",
                                f"Mark the {n} open day(s) of {code} up to today as COMPLETED?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                QMessageBox.StandardButton.Yes)
                            if answer != QMessageBox.StandardButton.Yes:
                                conn.rollback()
                                cur.close()
                                conn.close()
                                return None
                        cur.execute("UPDATE work_days SET STATUS='COMPLETED' WHERE JOB_PROJECT_ID=%s "
                                    "AND WORK_DATE <= CURDATE() AND STATUS NOT IN ('COMPLETED', 'CANCELLED')",
                                    (project_id,))
                elif to_stage == "IN_PROGRESS" and from_stage == "PENDING":
                    cur.execute("SELECT ID FROM work_days WHERE JOB_PROJECT_ID=%s AND STATUS='PENDING' "
                                "ORDER BY WORK_DATE, ID LIMIT 1", (project_id,))
                    row = cur.fetchone()
                    if row:
                        cur.execute("UPDATE work_days SET STATUS='IN_PROGRESS' WHERE ID=%s", (row[0],))
            conn.commit()
            cur.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not move the job:\n{e}")
            return None
        final = self._board_stage_of(project_id)
        if final != to_stage:
            show_toast(f"{code} is {_STAGE_LABEL.get(final, final)} — that column comes from its days and invoices "
                       f"(open the job to change a day, or Receivables to change an invoice).", "info", self)
        else:
            show_toast(f"{code} → {_STAGE_LABEL[to_stage]}", "success", self)
        logging.getLogger("vl_flooring").info("board: %s %s -> %s (%s)", code, from_stage, to_stage, final)
        return final

    def open_projects_board(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Projects board")
        dialog.resize(1280, 720)
        layout = QVBoxLayout(dialog)
        top = QHBoxLayout()
        hint = QLabel("Invoiced / Paid move by themselves when every day of the job is in an invoice / the "
                      "invoice is received. Drag a card to move it by hand; double-click opens the job.")
        hint.setStyleSheet("color:#64748B;")
        search = QLineEdit()
        search.setObjectName("txt_board_search")
        search.setPlaceholderText("Filter by Job Code or client…")
        search.setClearButtonEnabled(True)
        search.setMaximumWidth(280)
        hide_paid = QCheckBox("Hide Paid older than 60 days")
        hide_paid.setChecked(True)
        top.addWidget(hint, 1)
        top.addWidget(hide_paid)
        top.addWidget(search)
        layout.addLayout(top)
        columns = QHBoxLayout()
        columns.setSpacing(10)
        lists, headers = {}, {}
        state = {"projects": []}

        def on_drop(pid, from_stage, to_stage):
            if self._board_move(pid, from_stage, to_stage) is not None:
                reload()

        for key, label, color in BOARD_STAGES:
            col = QVBoxLayout()
            head = QLabel(label)
            head.setStyleSheet(f"font-weight:700; font-size:14px; color:{color}; padding:4px 2px; "
                               f"border-bottom: 3px solid {color};")
            lst = _StageList(key, on_drop)
            lst.setObjectName(f"list_board_{key.lower()}")
            lst.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            col.addWidget(head)
            col.addWidget(lst, 1)
            columns.addLayout(col, 1)
            lists[key], headers[key] = lst, head
        layout.addLayout(columns, 1)
        bottom = QHBoxLayout()
        totals = QLabel()
        totals.setStyleSheet("color:#475569; font-weight:600;")
        btn_close = QPushButton("Close")
        bottom.addWidget(totals, 1)
        bottom.addWidget(btn_close)
        layout.addLayout(bottom)

        def reload():
            try:
                state["projects"] = self._board_projects()
            except (MySQLError, RuntimeError) as e:
                totals.setText(f"Could not load the projects: {e}")
                return
            text = search.text().strip().lower()
            cutoff = date.today() - timedelta(days=60)
            sums = {k: [0, 0.0] for k in lists}
            for lst in lists.values():
                lst.clear()
            for p in state["projects"]:
                if text and text not in p["code"].lower() and text not in p["who"].lower():
                    continue
                if hide_paid.isChecked() and p["stage"] == "PAID" and p["last"] and p["last"] < cutoff:
                    continue
                dates = ""
                if p["first"]:
                    dates = p["first"].strftime("%m/%d") + (f" – {p['last'].strftime('%m/%d')}"
                                                           if p["last"] and p["last"] != p["first"] else "")
                lines = [p["code"]]
                if p["who"]:
                    lines.append(p["who"][:34])
                lines.append(f"{p['days']} day{'s' if p['days'] != 1 else ''} · {_money(p['value'])}"
                             + (f" · {dates}" if dates else ""))
                if p.get("invoiced") and p["stage"] not in ("INVOICED", "PAID"):
                    lines.append(f"Invoiced {p['invoiced']}/{p['days']} days")
                elif p["stage"] == "INVOICED" and p.get("paid"):
                    lines.append(f"Paid {p['paid']}/{p['days']} days")
                item = QListWidgetItem("\n".join(lines))
                item.setData(Qt.ItemDataRole.UserRole, p["id"])
                item.setToolTip(f"{p['code']} — {p['who']}\n{p['days']} day(s), {_money(p['value'])}")
                lists[p["stage"]].addItem(item)
                sums[p["stage"]][0] += 1
                sums[p["stage"]][1] += p["value"]
            for key, label, _c in BOARD_STAGES:
                n, v = sums[key]
                headers[key].setText(f"{label}  ·  {n}" + (f"  ·  {_money(v)}" if v else ""))
            totals.setText(f"{sum(s[0] for s in sums.values())} Job Codes on the board")

        def open_card(item):
            p = next((x for x in state["projects"] if x["id"] == item.data(Qt.ItemDataRole.UserRole)), None)
            if p and p["last_day_id"]:
                dialog.accept()
                self._open_job_by_id(p["last_day_id"], p["last"])

        def context_menu(lst, pos):
            item = lst.itemAt(pos)
            if item is None:
                return
            menu = QMenu(lst)
            for key, label, _c in BOARD_STAGES:
                if key != lst.stage:
                    act = menu.addAction(f"Move to {label}")
                    act.triggered.connect(lambda _=False, k=key, pid=item.data(Qt.ItemDataRole.UserRole), s=lst.stage:
                                          on_drop(pid, s, k))
            menu.addSeparator()
            menu.addAction("Open job").triggered.connect(lambda: open_card(item))
            menu.exec(lst.mapToGlobal(pos))

        for lst in lists.values():
            lst.itemDoubleClicked.connect(open_card)
            lst.customContextMenuRequested.connect(lambda pos, l=lst: context_menu(l, pos))
            if self._role_rule("read_only"):
                lst.setDragEnabled(False)
        search.textChanged.connect(lambda *_: reload())
        hide_paid.toggled.connect(lambda *_: reload())
        btn_close.clicked.connect(dialog.accept)
        dialog._lists, dialog._reload = lists, reload  # usado nos testes
        reload()
        dialog.exec()

    # ═════════════════════════ WEEKLY SUMMARY ═════════════════════════
    def _weekly_summary_data(self, monday):
        sunday = monday + timedelta(days=6)
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT wd.ID, wd.WORK_DATE, COALESCE(jp.CODE, ''), wd.STATUS, COALESCE(wd.VALUE, 0),
                   COALESCE(NULLIF(co.COMPANY_NAME, ''), NULLIF(ct.COMPANY_NAME, ''), ct.FULL_NAME, cl.FULL_NAME, '')
            FROM work_days wd
            LEFT JOIN job_projects jp ON jp.ID = wd.JOB_PROJECT_ID
            LEFT JOIN clients cl ON cl.ID = wd.CLIENT_ID
            LEFT JOIN companies co ON co.ID = wd.COMPANY_ID
            LEFT JOIN contractors ct ON ct.ID = wd.CONTRACTOR_ID
            WHERE wd.WORK_DATE BETWEEN %s AND %s AND COALESCE(wd.STATUS, '') <> 'CANCELLED'
            ORDER BY wd.WORK_DATE, wd.ID
        """, (monday, sunday))
        days = cur.fetchall()
        cur.execute("""
            SELECT h.FULL_NAME, COUNT(DISTINCT x.WORK_DAY_ID), COALESCE(SUM(x.PAY), 0)
            FROM work_day_helpers x
            JOIN work_days wd ON wd.ID = x.WORK_DAY_ID
            JOIN helpers h ON h.ID = x.HELPER_ID
            WHERE wd.WORK_DATE BETWEEN %s AND %s AND COALESCE(wd.STATUS, '') <> 'CANCELLED'
            GROUP BY h.ID, h.FULL_NAME ORDER BY 3 DESC
        """, (monday, sunday))
        helpers = cur.fetchall()
        cur.execute("SELECT CATEGORY, COUNT(*), COALESCE(SUM(AMOUNT), 0) FROM expenses "
                    "WHERE EXPENSE_DATE BETWEEN %s AND %s GROUP BY CATEGORY ORDER BY 3 DESC", (monday, sunday))
        expenses = cur.fetchall()
        open_inv = []
        for kind, table in (("Contractor", "contractor_invoices"), ("Company", "company_invoices"),
                            ("Client", "client_invoices")):
            cur.execute(f"SELECT COUNT(*), COALESCE(SUM(COALESCE(TOTAL_AMOUNT,0) - COALESCE(AMOUNT_PAID,0)), 0), "
                        f"COALESCE(SUM(DATEDIFF(CURDATE(), GENERATED_AT) > 30), 0) "
                        f"FROM {table} WHERE STATUS IN ('PENDING', 'PARTIAL')")
            n, amount, overdue = cur.fetchone()
            if n:
                open_inv.append((kind, int(n), float(amount or 0), int(overdue or 0)))
        cur.execute("SELECT COUNT(*), COUNT(DISTINCT JOB_PROJECT_ID) FROM work_days "
                    "WHERE WORK_DATE BETWEEN %s AND %s AND COALESCE(STATUS, '') <> 'CANCELLED'",
                    (sunday + timedelta(days=1), sunday + timedelta(days=7)))
        next_week = cur.fetchone()
        cur.close()
        conn.close()
        return {"monday": monday, "sunday": sunday, "days": days, "helpers": helpers, "expenses": expenses,
                "open_invoices": open_inv, "next_week": next_week,
                "value": sum(float(d[4] or 0) for d in days),
                "codes": sorted({d[2] for d in days if d[2]})}

    def _weekly_summary_html(self, data):
        e = html.escape
        period = f"{data['monday'].strftime('%b %d')} – {data['sunday'].strftime('%b %d, %Y')}"
        helper_total = sum(float(h[2] or 0) for h in data["helpers"])
        exp_total = sum(float(x[2] or 0) for x in data["expenses"])
        inv_total = sum(i[2] for i in data["open_invoices"])
        td = "style='padding:3px 10px 3px 0;'"
        tdr = "style='padding:3px 0 3px 10px; text-align:right;'"
        parts = [f"<h2 style='margin:0'>Weekly summary</h2><p style='margin:2px 0 10px 0'>{e(period)} · "
                 f"{e(company_settings.COMPANY_NAME)}</p>",
                 "<table cellspacing='0' style='margin-bottom:10px'>"
                 f"<tr><td {td}><b>Work days</b></td><td {tdr}>{len(data['days'])}</td></tr>"
                 f"<tr><td {td}><b>Job Codes</b></td><td {tdr}>{len(data['codes'])}</td></tr>"
                 f"<tr><td {td}><b>Value produced</b></td><td {tdr}><b>{_money(data['value'])}</b></td></tr>"
                 f"<tr><td {td}><b>Helper pay</b></td><td {tdr}>{_money(helper_total)}</td></tr>"
                 f"<tr><td {td}><b>Expenses</b></td><td {tdr}>{_money(exp_total)}</td></tr>"
                 f"<tr><td {td}><b>Open invoices</b></td><td {tdr}>{_money(inv_total)}</td></tr></table>"]
        parts.append("<h3 style='margin:8px 0 4px 0'>Days worked</h3>")
        if data["days"]:
            parts.append("<table cellspacing='0'>")
            for _id, d, code, status, value, who in data["days"]:
                parts.append(f"<tr><td {td}>{d.strftime('%a %m/%d')}</td><td {td}><b>{e(code or '—')}</b></td>"
                             f"<td {td}>{e((who or '')[:40])}</td><td {td}>{e(status or '')}</td>"
                             f"<td {tdr}>{_money(value)}</td></tr>")
            parts.append("</table>")
        else:
            parts.append("<p>No work days this week.</p>")
        parts.append("<h3 style='margin:12px 0 4px 0'>Helper pay</h3>")
        if data["helpers"]:
            parts.append("<table cellspacing='0'>")
            for name, n, pay in data["helpers"]:
                parts.append(f"<tr><td {td}>{e(name or '')}</td><td {td}>{n} day{'s' if n != 1 else ''}</td>"
                             f"<td {tdr}>{_money(pay)}</td></tr>")
            parts.append("</table>")
        else:
            parts.append("<p>No helpers this week.</p>")
        parts.append("<h3 style='margin:12px 0 4px 0'>Expenses</h3>")
        if data["expenses"]:
            parts.append("<table cellspacing='0'>")
            for cat, n, amount in data["expenses"]:
                parts.append(f"<tr><td {td}>{e(str(cat).title())}</td><td {td}>{n}</td><td {tdr}>{_money(amount)}</td></tr>")
            parts.append("</table>")
        else:
            parts.append("<p>No expenses this week.</p>")
        parts.append("<h3 style='margin:12px 0 4px 0'>Open invoices (today)</h3>")
        if data["open_invoices"]:
            parts.append("<table cellspacing='0'>")
            for kind, n, amount, overdue in data["open_invoices"]:
                late = f" · <span style='color:#C62828'>{overdue} over 30 days</span>" if overdue else ""
                parts.append(f"<tr><td {td}>{kind}</td><td {td}>{n} open{late}</td><td {tdr}>{_money(amount)}</td></tr>")
            parts.append("</table>")
        else:
            parts.append("<p>No open invoices.</p>")
        nd, nc = data["next_week"] or (0, 0)
        parts.append(f"<h3 style='margin:12px 0 4px 0'>Next week</h3><p>{nd or 0} day(s) scheduled"
                     f"{f' in {nc} Job Code(s)' if nc else ''}.</p>")
        return "".join(parts)

    def _weekly_summary_text(self, data):
        lines = [f"Weekly summary — {data['monday'].strftime('%b %d')} to {data['sunday'].strftime('%b %d, %Y')}",
                 "", f"Work days: {len(data['days'])}   Job Codes: {len(data['codes'])}",
                 f"Value produced: {_money(data['value'])}", "", "Helper pay:"]
        lines += [f"  {n}: {d} day(s) — {_money(p)}" for n, d, p in data["helpers"]] or ["  —"]
        lines += ["", "Expenses:"]
        lines += [f"  {str(c).title()}: {_money(a)}" for c, _n, a in data["expenses"]] or ["  —"]
        lines += ["", "Open invoices:"]
        lines += [f"  {k}: {n} open — {_money(a)}" for k, n, a, _o in data["open_invoices"]] or ["  —"]
        return "\n".join(lines)

    def _summary_recipient(self):
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT SUMMARY_EMAIL FROM app_settings WHERE ID=1")
            row = cur.fetchone()
            cur.close()
            conn.close()
            if row and row[0]:
                return row[0].strip()
        except (MySQLError, RuntimeError):
            pass
        return (company_settings.COMPANY_EMAIL or "").strip()

    def _send_weekly_summary(self, data, recipient):
        """Envia o resumo por e-mail. Levanta exceção se falhar."""
        m = EmailMessage()
        m["Subject"] = (f"Weekly summary {data['monday'].strftime('%m/%d')}–{data['sunday'].strftime('%m/%d/%Y')} — "
                        f"{company_settings.COMPANY_NAME}")
        m["From"] = f"{company_settings.EMAIL_FROM_NAME} <{company_settings.EMAIL_SMTP_USER}>"
        m["To"] = recipient
        m.set_content(self._weekly_summary_text(data))
        m.add_alternative(f"<html><body style='font-family:Segoe UI,Arial,sans-serif'>"
                          f"{self._weekly_summary_html(data)}</body></html>", subtype="html")
        with smtplib.SMTP(company_settings.EMAIL_SMTP_HOST, company_settings.EMAIL_SMTP_PORT, timeout=20) as server:
            server.starttls()
            server.login(company_settings.EMAIL_SMTP_USER, company_settings.EMAIL_SMTP_PASSWORD)
            server.send_message(m)

    @staticmethod
    def _last_week_monday(today=None):
        today = today or date.today()
        return today - timedelta(days=today.weekday() + 7)

    def open_weekly_summary_dialog(self, monday=None):
        monday = monday or self._last_week_monday()
        QSettings("VL Flooring", "app").setValue("summary/seen_week", _week_key(date.today()))
        dialog = QDialog(self)
        dialog.setWindowTitle("Weekly summary")
        dialog.resize(760, 720)
        layout = QVBoxLayout(dialog)
        nav = QHBoxLayout()
        prev_btn = QPushButton("◀  Previous week")
        next_btn = QPushButton("Next week  ▶")
        this_btn = QPushButton("This week")
        for b in (prev_btn, this_btn, next_btn):
            b.setStyleSheet(_SMALL_BTN)
        nav.addWidget(prev_btn)
        nav.addStretch(1)
        nav.addWidget(this_btn)
        nav.addWidget(next_btn)
        layout.addLayout(nav)
        view = QTextBrowser()
        view.setObjectName("txt_weekly_summary")
        view.setOpenExternalLinks(False)
        layout.addWidget(view, 1)
        if not self._smtp_ready():
            warn = QLabel("⚠ The e-mail account is not set up yet (Settings → Email). Until then the summary only "
                          "shows here; after that it is also e-mailed every Monday.")
            warn.setWordWrap(True)
            warn.setStyleSheet("background:#FFF3CD; color:#8A6D00; padding:8px; border-radius:6px;")
            layout.addWidget(warn)
        row = QHBoxLayout()
        row.addWidget(QLabel("Send to:"))
        to = QLineEdit(self._summary_recipient())
        to.setObjectName("txt_summary_email")
        row.addWidget(to, 1)
        btn_send = QPushButton("  Send by e-mail")
        btn_send.setObjectName("btn_send_weekly_summary")
        btn_send.setIcon(tabler_icon("send", "#FFFFFF", 16))
        btn_send.setStyleSheet(_PRIMARY_BTN)
        btn_close = QPushButton("Close")
        row.addWidget(btn_send)
        row.addWidget(btn_close)
        layout.addLayout(row)
        state = {"monday": monday, "data": None}

        def load():
            try:
                state["data"] = self._weekly_summary_data(state["monday"])
            except (MySQLError, RuntimeError) as e:
                view.setPlainText(f"Could not build the summary: {e}")
                return
            view.setHtml(self._weekly_summary_html(state["data"]))
            next_btn.setEnabled(state["monday"] + timedelta(days=7) <= date.today())

        def move(days):
            state["monday"] = state["monday"] + timedelta(days=days)
            load()

        def this_week():
            state["monday"] = date.today() - timedelta(days=date.today().weekday())
            load()

        def send():
            recipient = to.text().strip()
            if "@" not in recipient:
                QMessageBox.warning(dialog, "E-mail", "Type the e-mail address that receives the summary.")
                return
            self._save_summary_recipient(recipient)
            if not self._smtp_ready():
                QMessageBox.warning(dialog, "E-mail not set up",
                                    "Set up the e-mail account in Settings first (Gmail address + App Password).")
                return
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                self._send_weekly_summary(state["data"], recipient)
            except Exception as e:
                QApplication.restoreOverrideCursor()
                QMessageBox.warning(dialog, "E-mail", f"Could not send the summary:\n{e}")
                return
            QApplication.restoreOverrideCursor()
            show_toast(f"Summary sent to {recipient}.", "success", self)

        prev_btn.clicked.connect(lambda: move(-7))
        next_btn.clicked.connect(lambda: move(7))
        this_btn.clicked.connect(this_week)
        btn_send.clicked.connect(send)
        btn_close.clicked.connect(dialog.accept)
        dialog._view, dialog._state = view, state  # usado nos testes
        load()
        dialog.exec()

    def _save_summary_recipient(self, recipient):
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("UPDATE app_settings SET SUMMARY_EMAIL=%s WHERE ID=1", (recipient,))
            conn.commit()
            cur.close()
            conn.close()
        except (MySQLError, RuntimeError):
            logging.getLogger("vl_flooring").exception("could not save the summary e-mail")

    def _weekly_summary_attention_item(self):
        """Na primeira abertura de uma semana nova, avisa que o resumo da
        semana passada está pronto (só para quem vê as finanças)."""
        if not self._role_rule("finance"):
            return None
        seen = QSettings("VL Flooring", "app").value("summary/seen_week", "")
        if seen == _week_key(date.today()):
            return None
        return ("calendar", "#1565C0", "Last week's summary is ready", self.open_weekly_summary_dialog)

    def _auto_send_weekly_summary(self):
        """Envia (uma vez por semana, nos dois computadores) o resumo da
        semana passada, se o e-mail estiver configurado. Roda em segundo plano."""
        if not self._role_rule("finance") or not self._smtp_ready() or self._db_read_only:
            return
        monday = self._last_week_monday()
        key = _week_key(monday)
        recipient = self._summary_recipient()
        if "@" not in recipient:
            return
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            # "Reserva" a semana antes de enviar — o outro computador não envia de novo
            cur.execute("UPDATE app_settings SET SUMMARY_LAST_SENT=%s WHERE ID=1 "
                        "AND COALESCE(SUMMARY_LAST_SENT, '') <> %s", (key, key))
            claimed = cur.rowcount
            conn.commit()
            cur.close()
            conn.close()
            if not claimed:
                return
            data = self._weekly_summary_data(monday)
        except (MySQLError, RuntimeError):
            logging.getLogger("vl_flooring").exception("weekly summary: could not prepare")
            return
        db_config = dict(self.db_config)
        log = logging.getLogger("vl_flooring")

        def worker():
            try:
                self._send_weekly_summary(data, recipient)
                log.info("weekly summary %s sent to %s", key, recipient)
            except Exception:
                log.exception("weekly summary %s could not be sent", key)
                try:  # libera para tentar de novo na próxima abertura
                    import mysql.connector as _m
                    c = _m.connect(**db_config)
                    cc = c.cursor()
                    cc.execute("UPDATE app_settings SET SUMMARY_LAST_SENT=NULL WHERE ID=1 AND SUMMARY_LAST_SENT=%s",
                               (key,))
                    c.commit()
                    c.close()
                except Exception:
                    pass
        threading.Thread(target=worker, daemon=True).start()

    # ═════════════════════════ DATA CLEANUP ═════════════════════════
    def _cleanup_counts(self):
        conn = self._get_connection()
        cur = conn.cursor()
        out = {}
        cur.execute("SELECT COUNT(*) FROM work_days WHERE (STATUS = 'PENDING' AND WORK_DATE < CURDATE()) OR "
                    "(STATUS IN ('IN_PROGRESS', 'STARTED') AND WORK_DATE < CURDATE() - INTERVAL 7 DAY)")
        out["days"] = cur.fetchone()[0] or 0
        cur.execute(f"SELECT COUNT(*) FROM clients WHERE {_PLACEHOLDER_CLIENT_SQL}")
        out["clients"] = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*) FROM work_days WHERE CLIENT_ID IS NULL AND COMPANY_ID IS NULL "
                    "AND CONTRACTOR_ID IS NULL")
        out["nobody"] = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*) FROM products WHERE COALESCE(PRICE, 0) = 0")
        out["products"] = cur.fetchone()[0] or 0
        cur.close()
        conn.close()
        return out

    def open_data_cleanup_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Data cleanup")
        dialog.resize(960, 600)
        layout = QVBoxLayout(dialog)
        intro = QLabel("Things in the database that need a fix. Pick the rows and use the buttons — "
                       "nothing changes until you click.")
        intro.setStyleSheet("color:#475569;")
        layout.addWidget(intro)
        tabs = QTabWidget()
        tabs.setObjectName("tabs_data_cleanup")
        layout.addWidget(tabs, 1)
        read_only = self._role_rule("read_only")

        def make_table(headers, stretch=2):
            t = QTableWidget(0, len(headers))
            t.setHorizontalHeaderLabels(headers)
            t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            t.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
            t.horizontalHeader().setSectionResizeMode(stretch, QHeaderView.ResizeMode.Stretch)
            t.verticalHeader().setVisible(False)
            return t

        def fill(t, rows, key_col=0):
            t.setRowCount(len(rows))
            for r, row in enumerate(rows):
                for c, v in enumerate(row[1:]):
                    item = QTableWidgetItem("" if v is None else str(v))
                    if c == 0:
                        item.setData(Qt.ItemDataRole.UserRole, row[0])
                    t.setItem(r, c, item)

        def selected_ids(t):
            rows = sorted({i.row() for i in t.selectedIndexes()})
            return [t.item(r, 0).data(Qt.ItemDataRole.UserRole) for r in rows if t.item(r, 0)]

        def run(sql_list, done_msg):
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                for sql, params in sql_list:
                    cur.execute(sql, params)
                conn.commit()
                cur.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", str(e))
                return False
            show_toast(done_msg, "success", self)
            reload()
            return True

        # ── 1. dias antigos abertos ──
        days_page = QWidget()
        dl = QVBoxLayout(days_page)
        dl.addWidget(QLabel("Past days still PENDING, or IN PROGRESS / STARTED for more than a week:"))
        days_t = make_table(["Job #", "Date", "Job Code", "Who", "Status", "Value"], stretch=3)
        days_t.setObjectName("table_cleanup_days")
        dl.addWidget(days_t, 1)
        db = QHBoxLayout()
        b_all = QPushButton("Select all")
        b_done = QPushButton("  Mark selected COMPLETED")
        b_done.setObjectName("btn_complete_cleanup_days")
        b_done.setIcon(tabler_icon("circle-check", "#FFFFFF", 16))
        b_done.setStyleSheet(_PRIMARY_BTN)
        b_cancel = QPushButton("Mark selected CANCELLED")
        b_cancel.setObjectName("btn_cancel_cleanup_days")
        b_open = QPushButton("Open job")
        for b in (b_all, b_done, b_cancel, b_open):
            if b is not b_done:
                b.setStyleSheet(_SMALL_BTN)
            db.addWidget(b)
        db.addStretch(1)
        dl.addLayout(db)

        def set_days_status(status):
            ids = selected_ids(days_t)
            if not ids:
                QMessageBox.information(dialog, "Nothing selected", "Select the days first (Select all picks them all).")
                return
            answer = QMessageBox.question(dialog, "Change status", f"Mark {len(ids)} day(s) as {status}?",
                                          QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                          QMessageBox.StandardButton.Yes)
            if answer == QMessageBox.StandardButton.Yes:
                marks = ",".join(["%s"] * len(ids))
                run([(f"UPDATE work_days SET STATUS=%s WHERE ID IN ({marks})", (status, *ids))],
                    f"{len(ids)} day(s) marked {status}.")

        def open_day():
            ids = selected_ids(days_t)
            if ids:
                dialog.accept()
                self._open_job_by_id(ids[0], None)
        b_all.clicked.connect(days_t.selectAll)
        b_done.clicked.connect(lambda: set_days_status("COMPLETED"))
        b_cancel.clicked.connect(lambda: set_days_status("CANCELLED"))
        b_open.clicked.connect(open_day)
        days_t.cellDoubleClicked.connect(lambda *_: open_day())

        # ── 2. clientes "— Select —" ──
        cl_page = QWidget()
        cll = QVBoxLayout(cl_page)
        cl_info = QLabel("Clients saved by mistake from the “— Select —” option. Removing them clears the client "
                         "from those jobs (the company / contractor stays) and deletes these fake clients.")
        cl_info.setWordWrap(True)
        cll.addWidget(cl_info)
        cl_t = make_table(["Client ID", "Name", "Jobs using it", "Jobs without company/contractor"], stretch=1)
        cl_t.setObjectName("table_cleanup_clients")
        cll.addWidget(cl_t, 1)
        cb = QHBoxLayout()
        b_fix_clients = QPushButton("  Remove the fake clients")
        b_fix_clients.setObjectName("btn_delete_cleanup_clients")
        b_fix_clients.setIcon(tabler_icon("eraser", "#FFFFFF", 16))
        b_fix_clients.setStyleSheet(_PRIMARY_BTN)
        cb.addWidget(b_fix_clients)
        cb.addStretch(1)
        cll.addLayout(cb)

        def fix_clients():
            ids = [cl_t.item(r, 0).data(Qt.ItemDataRole.UserRole) for r in range(cl_t.rowCount())]
            if not ids:
                return
            jobs = sum(int(cl_t.item(r, 2).text() or 0) for r in range(cl_t.rowCount()))
            answer = QMessageBox.question(
                dialog, "Remove fake clients",
                f"Delete {len(ids)} fake client(s) and clear them from {jobs} job(s)?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                return
            marks = ",".join(["%s"] * len(ids))
            sql = [(f"UPDATE work_days SET CLIENT_ID=NULL WHERE CLIENT_ID IN ({marks})", tuple(ids)),
                   (f"UPDATE job_projects SET CLIENT_ID=NULL WHERE CLIENT_ID IN ({marks})", tuple(ids)),
                   (f"UPDATE expenses SET CLIENT_ID=NULL WHERE CLIENT_ID IN ({marks})", tuple(ids)),
                   (f"DELETE FROM clients WHERE ID IN ({marks}) AND ID NOT IN "
                    f"(SELECT CLIENT_ID FROM client_invoices WHERE CLIENT_ID IS NOT NULL) AND ID NOT IN "
                    f"(SELECT CLIENT_ID FROM estimates WHERE CLIENT_ID IS NOT NULL)", tuple(ids))]
            run(sql, f"{len(ids)} fake client(s) removed.")
        b_fix_clients.clicked.connect(fix_clients)
        if not self._role_rule("can_delete"):
            b_fix_clients.setEnabled(False)
            b_fix_clients.setToolTip("Only an Admin can delete clients.")

        # ── 3. jobs sem ninguém ──
        nb_page = QWidget()
        nbl = QVBoxLayout(nb_page)
        nbl.addWidget(QLabel("Jobs with no client, company or contractor (double-click to open and fill in):"))
        nb_t = make_table(["Job #", "Date", "Job Code", "Address", "Value"], stretch=3)
        nb_t.setObjectName("table_cleanup_nobody")
        nbl.addWidget(nb_t, 1)

        def open_nb(*_a):
            ids = selected_ids(nb_t)
            if ids:
                dialog.accept()
                self._open_job_by_id(ids[0], None)
        nb_t.cellDoubleClicked.connect(open_nb)

        # ── 4. produtos sem preço ──
        pr_page = QWidget()
        prl = QVBoxLayout(pr_page)
        prl.addWidget(QLabel("Products without a price — type the price and click Save prices. Job materials "
                             "launched at $0 get the new price too (or register a supplier Purchase)."))
        pr_t = QTableWidget(0, 5)
        pr_t.setObjectName("table_cleanup_products")
        pr_t.setHorizontalHeaderLabels(["Type", "Product", "Unit", "Used in jobs", "Price"])
        pr_t.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        pr_t.verticalHeader().setVisible(False)
        pr_t.setColumnWidth(4, 130)
        prl.addWidget(pr_t, 1)
        pb = QHBoxLayout()
        b_prices = QPushButton("  Save prices")
        b_prices.setObjectName("btn_save_cleanup_prices")
        b_prices.setIcon(tabler_icon("device-floppy", "#FFFFFF", 16))
        b_prices.setStyleSheet(_PRIMARY_BTN)
        b_purchase = QPushButton("  New supplier purchase…")
        b_purchase.setStyleSheet(_SMALL_BTN)
        pb.addWidget(b_prices)
        pb.addWidget(b_purchase)
        pb.addStretch(1)
        prl.addLayout(pb)

        def save_prices():
            sql, n = [], 0
            for r in range(pr_t.rowCount()):
                spin = pr_t.cellWidget(r, 4)
                pid = pr_t.item(r, 0).data(Qt.ItemDataRole.UserRole)
                if spin is not None and spin.value() > 0:
                    n += 1
                    sql.append(("UPDATE products SET PRICE=%s WHERE ID=%s", (spin.value(), pid)))
                    sql.append(("UPDATE job_materials SET UNIT_PRICE=%s WHERE PRODUCT_ID=%s "
                                "AND COALESCE(UNIT_PRICE, 0) = 0", (spin.value(), pid)))
            if not n:
                QMessageBox.information(dialog, "Prices", "Type at least one price.")
                return
            if run(sql, f"{n} price(s) saved.") and hasattr(self, "_refresh_material_product_combo"):
                self._refresh_material_product_combo()
        b_prices.clicked.connect(save_prices)
        b_purchase.clicked.connect(lambda: hasattr(self, "open_new_purchase_dialog")
                                   and self.open_new_purchase_dialog(parent=dialog) and reload())

        if read_only:
            for b in (b_done, b_cancel, b_fix_clients, b_prices, b_purchase):
                b.setEnabled(False)
                b.setToolTip("Your user has read-only access.")

        pages = [("days", days_page, "Old open days"), ("clients", cl_page, "Fake clients"),
                 ("nobody", nb_page, "Jobs without a customer"), ("products", pr_page, "Products without price")]
        for _k, page, label in pages:
            tabs.addTab(page, label)
        bottom = QHBoxLayout()
        status = QLabel()
        status.setStyleSheet("font-weight:600; color:#2E7D32;")
        close = QPushButton("Close")
        bottom.addWidget(status, 1)
        bottom.addWidget(close)
        layout.addLayout(bottom)
        close.clicked.connect(dialog.accept)

        def reload():
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                cur.execute("""
                    SELECT wd.ID, wd.ID, DATE_FORMAT(wd.WORK_DATE, '%m/%d/%Y'), COALESCE(jp.CODE, ''),
                           COALESCE(NULLIF(co.COMPANY_NAME, ''), NULLIF(ct.COMPANY_NAME, ''), ct.FULL_NAME, cl.FULL_NAME, ''),
                           wd.STATUS, CONCAT('$', FORMAT(COALESCE(wd.VALUE, 0), 2))
                    FROM work_days wd
                    LEFT JOIN job_projects jp ON jp.ID = wd.JOB_PROJECT_ID
                    LEFT JOIN clients cl ON cl.ID = wd.CLIENT_ID
                    LEFT JOIN companies co ON co.ID = wd.COMPANY_ID
                    LEFT JOIN contractors ct ON ct.ID = wd.CONTRACTOR_ID
                    WHERE (wd.STATUS = 'PENDING' AND wd.WORK_DATE < CURDATE())
                       OR (wd.STATUS IN ('IN_PROGRESS', 'STARTED') AND wd.WORK_DATE < CURDATE() - INTERVAL 7 DAY)
                    ORDER BY wd.WORK_DATE""")
                fill(days_t, cur.fetchall())
                cur.execute(f"""
                    SELECT c.ID, c.ID, c.FULL_NAME,
                           (SELECT COUNT(*) FROM work_days w WHERE w.CLIENT_ID = c.ID),
                           (SELECT COUNT(*) FROM work_days w WHERE w.CLIENT_ID = c.ID
                              AND w.COMPANY_ID IS NULL AND w.CONTRACTOR_ID IS NULL)
                    FROM clients c WHERE {_PLACEHOLDER_CLIENT_SQL.replace('FULL_NAME', 'c.FULL_NAME')} ORDER BY c.ID""")
                fill(cl_t, cur.fetchall())
                cur.execute("""
                    SELECT wd.ID, wd.ID, DATE_FORMAT(wd.WORK_DATE, '%m/%d/%Y'), COALESCE(jp.CODE, ''),
                           COALESCE(wd.JOB_ADDRESS, ''), CONCAT('$', FORMAT(COALESCE(wd.VALUE, 0), 2))
                    FROM work_days wd LEFT JOIN job_projects jp ON jp.ID = wd.JOB_PROJECT_ID
                    WHERE wd.CLIENT_ID IS NULL AND wd.COMPANY_ID IS NULL AND wd.CONTRACTOR_ID IS NULL
                    ORDER BY wd.WORK_DATE DESC""")
                fill(nb_t, cur.fetchall())
                cur.execute("""
                    SELECT p.ID, COALESCE(NULLIF(p.TYPE, ''), 'Others'), p.NAME, COALESCE(p.UNIT, ''),
                           (SELECT COUNT(DISTINCT JOB_PROJECT_ID) FROM job_materials m WHERE m.PRODUCT_ID = p.ID)
                    FROM products p WHERE COALESCE(p.PRICE, 0) = 0 ORDER BY 5 DESC, 2, 3""")
                prods = cur.fetchall()
                cur.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                status.setText(f"Could not load: {e}")
                return
            pr_t.setRowCount(len(prods))
            for r, (pid, ptype, name, unit, used) in enumerate(prods):
                for c, v in enumerate([ptype, name, unit, str(used)]):
                    item = QTableWidgetItem(v)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    if c == 0:
                        item.setData(Qt.ItemDataRole.UserRole, pid)
                    pr_t.setItem(r, c, item)
                spin = QDoubleSpinBox()
                spin.setDecimals(2)
                spin.setMaximum(99999.99)
                spin.setPrefix("$ ")
                pr_t.setCellWidget(r, 4, spin)
            counts = {"days": days_t.rowCount(), "clients": cl_t.rowCount(), "nobody": nb_t.rowCount(),
                      "products": pr_t.rowCount()}
            for i, (key, _page, label) in enumerate(pages):
                n = counts[key]
                tabs.setTabText(i, f"{label} ({n})" if n else f"{label} ✓")
            total = sum(counts.values())
            status.setText("Everything is clean ✓" if not total else f"{total} item(s) to look at")
            status.setStyleSheet(f"font-weight:600; color:{'#2E7D32' if not total else '#B26A00'};")
            first = next((i for i, (k, _p, _l) in enumerate(pages) if counts[k]), None)
            if first is not None and not counts[pages[tabs.currentIndex()][0]]:
                tabs.setCurrentIndex(first)

        dialog._tables = {"days": days_t, "clients": cl_t, "nobody": nb_t, "products": pr_t}  # usado nos testes
        dialog._buttons = {"done": b_done, "fix_clients": b_fix_clients, "prices": b_prices}
        dialog._reload = reload
        reload()
        dialog.exec()

    # ═════════════════════════ SETUP ═════════════════════════
    def _setup_board_summary_tools(self):
        """Botões escondidos acionados pelos cartões da página Registrations."""
        for attr, handler in (("btn_tool_purchases", self.open_purchases_dialog),
                              ("btn_tool_stock", lambda: self.open_stock_dialog()),
                              ("btn_tool_board", self.open_projects_board),
                              ("btn_tool_weekly_summary", lambda: self.open_weekly_summary_dialog()),
                              ("btn_tool_cleanup", self.open_data_cleanup_dialog)):
            btn = QPushButton()
            btn.setObjectName(attr)
            btn.clicked.connect(handler)
            setattr(self.ui, attr, btn)
