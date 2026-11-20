# -*- coding: utf-8 -*-
"""
Rateio de despesa entre Job Codes (ex.: gasolina da semana).

Botão "Split across jobs" na tela de Expenses: pega os Job Codes
trabalhados no período (padrão: a semana da despesa, segunda a domingo) e
divide o valor proporcional aos dias trabalhados em cada um (⅓ de dia conta
⅓). Os valores podem ser ajustados. Fica em expense_allocations; o Job
Profit usa o rateio em vez do Job Code único da despesa. O total da despesa
(P&L, contador) não muda.

Métodos da MainWindow (mixin) — veja main_.py.
"""

from datetime import timedelta

from PySide6.QtWidgets import QDateEdit

from app_common import *  # noqa: F401,F403
from paginas.visual import tabler_icon
from paginas.moderno import show_toast
from paginas.fracao import fmt_days

_PRIMARY_BTN = ("QPushButton { background-color: #1565C0; color: #FFFFFF; border: none; border-radius: 6px; "
                "padding: 8px 16px; font-weight: 700; } QPushButton:hover { background-color: #1E88E5; }")


class ExpenseSplitMixin:
    def _setup_expense_split_button(self):
        btn = QPushButton("  Split across jobs")
        btn.setObjectName("btn_save_expense_split")
        btn.setIcon(tabler_icon("arrows-split-2", "#37474F", 16))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip("Divide this expense (e.g. the week's gas) between the jobs worked, by days")
        btn.clicked.connect(lambda: self.open_expense_split_dialog(getattr(self, "_current_expense_id", None)))
        layout = getattr(self.ui, "layout_expenses_row_actions", None)
        if layout is not None:
            layout.addWidget(btn)
        self.ui.btn_save_expense_split = btn

    def _jobs_worked_between(self, start, end):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT jp.ID, jp.CODE, SUM(wd.DAY_FRACTION)
            FROM work_days wd JOIN job_projects jp ON jp.ID = wd.JOB_PROJECT_ID
            WHERE wd.WORK_DATE BETWEEN %s AND %s AND COALESCE(wd.STATUS, '') <> 'CANCELLED'
            GROUP BY jp.ID, jp.CODE ORDER BY jp.CODE""", (start, end))
        rows = [(pid, code, float(d or 0)) for pid, code, d in cur.fetchall()]
        cur.close()
        conn.close()
        return rows

    def open_expense_split_dialog(self, expense_id):
        if not expense_id:
            QMessageBox.information(self, "Split expense", "Open (double-click) an expense from the list first.")
            return
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT EXPENSE_DATE, AMOUNT, CATEGORY, COALESCE(DESCRIPTION, ''), COALESCE(VENDOR, '') "
                        "FROM expenses WHERE ID=%s", (expense_id,))
            row = cur.fetchone()
            cur.execute("SELECT JOB_PROJECT_ID, AMOUNT FROM expense_allocations WHERE EXPENSE_ID=%s", (expense_id,))
            existing = {pid: float(a) for pid, a in cur.fetchall()}
            cur.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", str(e))
            return
        if not row:
            return
        exp_date, amount, category, desc, vendor = row
        amount = float(amount or 0)
        dialog = QDialog(self)
        dialog.setWindowTitle("Split expense across jobs")
        dialog.resize(640, 520)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(f"<b>Expense #{expense_id}</b> — {exp_date:%m/%d/%Y} · {category} · "
                                f"{vendor or desc} · <b>${amount:,.2f}</b>"))
        period = QHBoxLayout()
        period.addWidget(QLabel("Jobs worked from"))
        d_from, d_to = QDateEdit(), QDateEdit()
        for d in (d_from, d_to):
            d.setCalendarPopup(True)
            d.setDisplayFormat("MM/dd/yyyy")
        monday = exp_date - timedelta(days=exp_date.weekday())
        d_from.setDate(monday)
        d_to.setDate(monday + timedelta(days=6))
        period.addWidget(d_from)
        period.addWidget(QLabel("to"))
        period.addWidget(d_to)
        period.addStretch(1)
        layout.addLayout(period)
        table = QTableWidget(0, 3)
        table.setObjectName("table_expense_split")
        table.setHorizontalHeaderLabels(["Job Code", "Days worked", "Amount"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.setColumnWidth(2, 150)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(48)
        layout.addWidget(table, 1)
        total_lbl = QLabel()
        total_lbl.setStyleSheet("font-weight:700;")
        layout.addWidget(total_lbl)
        bottom = QHBoxLayout()
        btn_clear = QPushButton("Remove split")
        btn_clear.setEnabled(bool(existing))
        bottom.addWidget(btn_clear)
        bottom.addStretch(1)
        cancel = QPushButton("Cancel")
        save = QPushButton("  Save split")
        save.setObjectName("btn_save_split_confirm")
        save.setStyleSheet(_PRIMARY_BTN)
        bottom.addWidget(cancel)
        bottom.addWidget(save)
        layout.addLayout(bottom)
        if self._role_rule("read_only"):
            save.setEnabled(False)
            btn_clear.setEnabled(False)
        spins = []

        def update_total(*_a):
            total = sum(s.value() for _pid, s in spins)
            diff = round(amount - total, 2)
            total_lbl.setText(f"Split: ${total:,.2f} of ${amount:,.2f}" +
                              ("  ✓" if abs(diff) < 0.01 else f"  — ${diff:,.2f} left"))
            total_lbl.setStyleSheet(f"font-weight:700; color:{'#15803D' if abs(diff) < 0.01 else '#B26A00'};")

        def load(*_a, use_existing=False):
            try:
                jobs = self._jobs_worked_between(d_from.date().toPython(), d_to.date().toPython())
            except (MySQLError, RuntimeError):
                jobs = []
            if use_existing and existing:
                known = {pid for pid, _c, _d in jobs}
                for pid in existing:  # rateio salvo com job fora do período: mostra também
                    if pid not in known:
                        jobs.append((pid, f"#{pid}", 0.0))
            spins.clear()
            table.setRowCount(len(jobs))
            total_days = sum(d for _p, _c, d in jobs)
            shares = []
            for pid, code, days in jobs:
                if use_existing and existing:
                    shares.append(existing.get(pid, 0.0))
                else:
                    shares.append(round(amount * days / total_days, 2) if total_days else 0.0)
            if shares and not (use_existing and existing):  # centavos que sobram vão pro maior
                drift = round(amount - sum(shares), 2)
                if drift:
                    i = max(range(len(shares)), key=lambda k: shares[k])
                    shares[i] = round(shares[i] + drift, 2)
            for r, ((pid, code, days), share) in enumerate(zip(jobs, shares)):
                table.setItem(r, 0, QTableWidgetItem(code))
                table.setItem(r, 1, QTableWidgetItem(fmt_days(days)))
                spin = QDoubleSpinBox()
                spin.setDecimals(2)
                spin.setMaximum(999999.99)
                spin.setPrefix("$ ")
                spin.setValue(share)
                spin.valueChanged.connect(update_total)
                table.setCellWidget(r, 2, spin)
                spins.append((pid, spin))
            update_total()

        def do_save():
            parts = [(pid, round(s.value(), 2)) for pid, s in spins if s.value() > 0]
            if not parts:
                QMessageBox.information(dialog, "Split", "No job in this period — change the dates.")
                return
            total = round(sum(a for _p, a in parts), 2)
            if abs(total - amount) >= 0.01:
                QMessageBox.warning(dialog, "Split", f"The parts add up to ${total:,.2f}, but the expense is "
                                                     f"${amount:,.2f}. Adjust the amounts.")
                return
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                cur.execute("DELETE FROM expense_allocations WHERE EXPENSE_ID=%s", (expense_id,))
                for pid, a in parts:
                    cur.execute("INSERT INTO expense_allocations (EXPENSE_ID, JOB_PROJECT_ID, AMOUNT) VALUES (%s,%s,%s)",
                                (expense_id, pid, a))
                conn.commit()
                cur.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", str(e))
                return
            dialog.accept()
            show_toast(f"Expense #{expense_id} split across {len(parts)} job(s).", "success", self)

        def clear():
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                cur.execute("DELETE FROM expense_allocations WHERE EXPENSE_ID=%s", (expense_id,))
                conn.commit()
                cur.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", str(e))
                return
            dialog.accept()
            show_toast(f"Split of expense #{expense_id} removed.", "info", self)

        d_from.dateChanged.connect(lambda *_: load())
        d_to.dateChanged.connect(lambda *_: load())
        save.clicked.connect(do_save)
        cancel.clicked.connect(dialog.reject)
        btn_clear.clicked.connect(clear)
        load(use_existing=True)
        dialog._spins, dialog._from, dialog._to = spins, d_from, d_to  # usado nos testes
        dialog.exec()
