# -*- coding: utf-8 -*-
"""
Dia a dia e quanto rende o trabalho:

• Log today — botão na Home: escolhe o(s) Job Code(s) em que trabalhou hoje
  e quanto do dia ficou em cada um (ex.: ⅓ num e ⅔ no outro). Cria o dia de
  cada um copiando o último dia daquele código (cliente, endereço,
  contractor/company, serviços e equipe), com a parte do dia, o Value pelas
  Service Rates (ou proporcional ao último dia) e o pagamento dos helpers
  pela diária. Depois abre o primeiro dia para conferir.
• Earnings per day — quanto rende um DIA INTEIRO de trabalho (somando as
  frações): por mês, por Job Code e por cliente/empresa.
• Meta do mês — cartão na Home com o valor do mês, $/dia e barra da meta
  (QSettings goal/monthly).

Métodos da MainWindow (mixin) — veja main_.py.
"""

from datetime import date, timedelta

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QCheckBox, QDateEdit, QInputDialog, QProgressBar

from app_common import *  # noqa: F401,F403
from paginas.visual import tabler_icon
from paginas.moderno import show_toast
from paginas.fracao import fmt_days, days_word, make_portion_combo, portion_label

_PRIMARY_BTN = ("QPushButton { background-color: #1565C0; color: #FFFFFF; border: none; border-radius: 8px; "
                "padding: 10px 18px; font-weight: 700; font-size: 14px; } QPushButton:hover { background-color: #1E88E5; }")
_SMALL_BTN = ("QPushButton { background-color: #EEF2F7; color: #37474F; border: 1px solid #D0D7DE; "
              "border-radius: 6px; padding: 6px 12px; font-size: 12px; font-weight: 600; } "
              "QPushButton:hover { background-color: #E1E8F0; }")
_CARD_QSS = ("QFrame#frame_home_today { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; }"
             "QLabel { background: transparent; }")
_SKIP_COPY = {"ID", "CREATED_AT", "UPDATED_AT"}


def _money(v):
    return f"${float(v or 0):,.2f}"


class TodayMixin:
    # ═════════════════════════ LOG TODAY ═════════════════════════
    def _recent_job_codes(self, limit=10):
        """Job Codes trabalhados por último: [(project_id, code, who, last_day_id, last_date)]."""
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT jp.ID, jp.CODE,
                   COALESCE(NULLIF(co.COMPANY_NAME, ''), NULLIF(ct.COMPANY_NAME, ''), ct.FULL_NAME, ''),
                   wd.ID, wd.WORK_DATE, COALESCE(NULLIF(wd.JOB_ADDRESS, ''), '')
            FROM job_projects jp
            JOIN work_days wd ON wd.ID = (SELECT w2.ID FROM work_days w2 WHERE w2.JOB_PROJECT_ID = jp.ID
                                          AND COALESCE(w2.STATUS, '') <> 'CANCELLED'
                                          ORDER BY w2.WORK_DATE DESC, w2.ID DESC LIMIT 1)
            LEFT JOIN companies co ON co.ID = wd.COMPANY_ID
            LEFT JOIN contractors ct ON ct.ID = wd.CONTRACTOR_ID
            WHERE jp.CODE IS NOT NULL AND COALESCE(jp.STATUS, 'ACTIVE') NOT IN ('PAID')
            ORDER BY wd.WORK_DATE DESC, wd.ID DESC LIMIT %s""", (limit,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows

    def _helper_daily_rates(self):
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT ID, DAILY_RATE FROM helpers WHERE COALESCE(DAILY_RATE, 0) > 0")
            rates = {hid: float(r) for hid, r in cur.fetchall()}
            cur.close()
            conn.close()
            return rates
        except (MySQLError, RuntimeError):
            return {}

    def log_work_days(self, work_date, entries, status="IN_PROGRESS"):
        """entries: [(project_id, fraction)]. Cria um dia por Job Code copiando o
        último dia dele. Devolve [novo work_day_id]."""
        helper_rates = self._helper_daily_rates()
        conn = self._get_connection()
        cur = conn.cursor(dictionary=True)
        created = []
        try:
            for project_id, fraction in entries:
                cur.execute("SELECT * FROM work_days WHERE JOB_PROJECT_ID=%s AND COALESCE(STATUS, '') <> 'CANCELLED' "
                            "ORDER BY WORK_DATE DESC, ID DESC LIMIT 1", (project_id,))
                last = cur.fetchone()
                if not last:
                    continue
                last_fraction = float(last.get("DAY_FRACTION") or 1) or 1.0
                cur.execute("SELECT CATEGORY, WORK_TYPE_ID, QTY, SORT_ORDER FROM work_day_work_types "
                            "WHERE WORK_DAY_ID=%s ORDER BY SORT_ORDER", (last["ID"],))
                work_types = cur.fetchall()
                cur.execute("SELECT HELPER_ID, PAY, DAY_FRACTION FROM work_day_helpers WHERE WORK_DAY_ID=%s "
                            "ORDER BY ID", (last["ID"],))
                crew = cur.fetchall()
                # Value: pelas Service Rates se houver; senão, proporcional ao último dia
                value = None
                if work_types and hasattr(self, "_calculate_value_from_rates"):
                    items = [(w["CATEGORY"], w["WORK_TYPE_ID"], float(w["QTY"] or 0)) for w in work_types]
                    total, priced, _missing = self._calculate_value_from_rates(
                        items, last.get("CONTRACTOR_ID"), last.get("COMPANY_ID"))
                    if priced:
                        value = total
                if value is None:
                    value = round(float(last.get("VALUE") or 0) * fraction / last_fraction, 2)
                new_crew = []
                for h in crew:
                    rate = helper_rates.get(h["HELPER_ID"])
                    old_fr = float(h.get("DAY_FRACTION") or 1) or 1.0
                    pay = round(rate * fraction, 2) if rate else round(float(h["PAY"] or 0) * fraction / old_fr, 2)
                    new_crew.append((h["HELPER_ID"], pay, fraction))
                values = {k: v for k, v in last.items() if k not in _SKIP_COPY}
                values.update({"WORK_DATE": work_date, "STATUS": status, "DAY_FRACTION": fraction, "VALUE": value,
                               "DAY_SEQUENCE": None})
                if "HELPER_PAY" in values:
                    values["HELPER_PAY"] = round(sum(p for _h, p, _f in new_crew), 2) if new_crew else None
                if "HELPER_ID" in values:
                    values["HELPER_ID"] = new_crew[0][0] if new_crew else None
                cols = list(values)
                cur.execute(f"INSERT INTO work_days ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(cols))})",
                            [values[c] for c in cols])
                new_id = cur.lastrowid
                for w in work_types:
                    cur.execute("INSERT INTO work_day_work_types (WORK_DAY_ID, CATEGORY, WORK_TYPE_ID, QTY, SORT_ORDER) "
                                "VALUES (%s,%s,%s,%s,%s)", (new_id, w["CATEGORY"], w["WORK_TYPE_ID"], w["QTY"],
                                                            w["SORT_ORDER"]))
                for hid, pay, fr in new_crew:
                    cur.execute("INSERT INTO work_day_helpers (WORK_DAY_ID, HELPER_ID, PAY, DAY_FRACTION) "
                                "VALUES (%s,%s,%s,%s)", (new_id, hid, pay, fr))
                created.append(new_id)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()
        logging.getLogger("vl_flooring").info("log today %s: %s", work_date, created)
        return created

    def open_log_today_dialog(self):
        if self._role_rule("read_only"):
            QMessageBox.information(self, "Read-only", "Your user has read-only access.")
            return
        try:
            recent = self._recent_job_codes()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not load the recent jobs:\n{e}")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Log a work day")
        dialog.resize(720, 520)
        layout = QVBoxLayout(dialog)
        top = QHBoxLayout()
        top.addWidget(QLabel("Day:"))
        when = QDateEdit(date.today())
        when.setObjectName("date_log_today")
        when.setCalendarPopup(True)
        when.setDisplayFormat("MM/dd/yyyy")
        top.addWidget(when)
        top.addStretch(1)
        layout.addLayout(top)
        intro = QLabel("Tick where you worked and how much of the day was spent on each one. Each job gets a new "
                       "day copied from its last day (client, address, services and crew), ready to review.")
        intro.setWordWrap(True)
        intro.setStyleSheet("color:#475569;")
        layout.addWidget(intro)
        table = QTableWidget(len(recent), 4)
        table.setObjectName("table_log_today")
        table.setHorizontalHeaderLabels(["", "Job Code", "Last day", "Part of the day"])
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.setColumnWidth(0, 52)
        table.setColumnWidth(2, 120)
        table.setColumnWidth(3, 150)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(50)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        rows = []
        for r, (pid, code, who, last_id, last_date, address) in enumerate(recent):
            chk = QCheckBox()
            chk.setStyleSheet("QCheckBox::indicator { width: 18px; height: 18px; border: 2px solid #94A3B8; border-radius: 4px; background-color: #FFFFFF; } QCheckBox::indicator:checked { background-color: #1565C0; border-color: #1565C0; }")
            box = QWidget()
            bl = QHBoxLayout(box)
            bl.setContentsMargins(0, 0, 0, 0)
            bl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            bl.addWidget(chk)
            portion = make_portion_combo(1.0)
            portion.setEnabled(False)
            chk.toggled.connect(portion.setEnabled)
            table.setCellWidget(r, 0, box)
            label = f"{code}  ·  {who}" + (f"  ·  {address}" if address else "")
            table.setItem(r, 1, QTableWidgetItem(label))
            table.setItem(r, 2, QTableWidgetItem(last_date.strftime("%m/%d/%Y") if last_date else ""))
            table.setCellWidget(r, 3, portion)
            rows.append({"pid": pid, "code": code, "chk": chk, "portion": portion})
        layout.addWidget(table, 1)
        total_lbl = QLabel()
        total_lbl.setStyleSheet("font-weight:600; color:#334155;")
        layout.addWidget(total_lbl)
        bottom = QHBoxLayout()
        btn_new = QPushButton("  A new job instead")
        btn_new.setStyleSheet(_SMALL_BTN)
        btn_new.setIcon(tabler_icon("plus", "#37474F", 16))
        bottom.addWidget(btn_new)
        bottom.addStretch(1)
        cancel = QPushButton("Cancel")
        ok = QPushButton("  Create the day")
        ok.setObjectName("btn_save_log_today")
        ok.setIcon(tabler_icon("check", "#FFFFFF", 16))
        ok.setStyleSheet(_PRIMARY_BTN)
        bottom.addWidget(cancel)
        bottom.addWidget(ok)
        layout.addLayout(bottom)

        def refresh_total(*_a):
            chosen = [r for r in rows if r["chk"].isChecked()]
            # dois ou mais marcados e todos ainda em "Full day": divide igualmente
            if len(chosen) >= 2 and all(abs(r["portion"].currentData() - 1) < 0.01 for r in chosen):
                share = {2: 0.5, 3: 0.333, 4: 0.25}.get(len(chosen))
                if share:
                    for r in chosen:
                        r["portion"].blockSignals(True)
                        r["portion"].setCurrentIndex(r["portion"].findData(share))
                        r["portion"].blockSignals(False)
            total = sum(float(r["portion"].currentData()) for r in chosen)
            if not chosen:
                total_lbl.setText("Nothing ticked yet.")
            else:
                warn = "  — more than one full day!" if total > 1.02 else ""
                total_lbl.setText(f"Total: {fmt_days(total)} {days_word(total)}{warn}")
        for r in rows:
            r["chk"].toggled.connect(refresh_total)
            r["portion"].currentIndexChanged.connect(refresh_total)
        if rows:
            rows[0]["chk"].setChecked(True)
        refresh_total()

        def new_job():
            dialog.reject()
            self._go_to_page(1, self.ui.btn_jobs)
            if hasattr(self.ui, "tabWidget_jobs"):
                self.ui.tabWidget_jobs.setCurrentWidget(self.ui.tab_jobs_master)
            self.new_job_record()

        def create():
            chosen = [(r["pid"], float(r["portion"].currentData()), r["code"]) for r in rows if r["chk"].isChecked()]
            if not chosen:
                QMessageBox.information(dialog, "Log a work day", "Tick at least one Job Code.")
                return
            day = when.date().toPython()
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                marks = ",".join(["%s"] * len(chosen))
                cur.execute(f"SELECT DISTINCT jp.CODE FROM work_days wd JOIN job_projects jp ON jp.ID = wd.JOB_PROJECT_ID "
                            f"WHERE wd.WORK_DATE=%s AND wd.JOB_PROJECT_ID IN ({marks})", (day, *[c[0] for c in chosen]))
                already = [r[0] for r in cur.fetchall()]
                cur.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", str(e))
                return
            if already:
                answer = QMessageBox.question(
                    dialog, "Already logged",
                    f"{', '.join(already)} already has a day on {day:%m/%d/%Y}. Create another one anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
                if answer != QMessageBox.StandardButton.Yes:
                    return
            try:
                created = self.log_work_days(day, [(pid, fr) for pid, fr, _c in chosen])
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not create the day:\n{e}")
                return
            dialog.accept()
            parts = ", ".join(f"{c} ({portion_label(fr)})" for _p, fr, c in chosen)
            show_toast(f"{day:%m/%d} logged: {parts}. Review the services and Save if anything changed.",
                       "success", self)
            if created:
                self._open_job_by_id(created[0], day)
            self.refresh_today_card()

        ok.clicked.connect(create)
        cancel.clicked.connect(dialog.reject)
        btn_new.clicked.connect(new_job)
        dialog._rows, dialog._when = rows, when  # usado nos testes
        dialog.exec()

    # ═════════════════════════ EARNINGS ═════════════════════════
    def _earnings(self, start, end):
        """{'month': [...], 'job': [...], 'customer': [...]} com (rótulo, dias, valor)."""
        conn = self._get_connection()
        cur = conn.cursor()
        base = ("FROM work_days wd LEFT JOIN job_projects jp ON jp.ID = wd.JOB_PROJECT_ID "
                "LEFT JOIN companies co ON co.ID = wd.COMPANY_ID LEFT JOIN contractors ct ON ct.ID = wd.CONTRACTOR_ID "
                "WHERE wd.WORK_DATE BETWEEN %s AND %s AND COALESCE(wd.STATUS, '') <> 'CANCELLED'")
        out = {}
        cur.execute(f"SELECT CONCAT(YEAR(wd.WORK_DATE), '-', LPAD(MONTH(wd.WORK_DATE), 2, '0')), SUM(wd.DAY_FRACTION), SUM(COALESCE(wd.VALUE, 0)) "
                    f"{base} GROUP BY 1 ORDER BY 1 DESC", (start, end))
        out["month"] = cur.fetchall()
        cur.execute(f"SELECT COALESCE(jp.CODE, '(no code)'), SUM(wd.DAY_FRACTION), SUM(COALESCE(wd.VALUE, 0)) "
                    f"{base} GROUP BY 1 ORDER BY 3 DESC", (start, end))
        out["job"] = cur.fetchall()
        cur.execute(f"SELECT COALESCE(NULLIF(co.COMPANY_NAME, ''), NULLIF(ct.COMPANY_NAME, ''), ct.FULL_NAME, '—'), "
                    f"SUM(wd.DAY_FRACTION), SUM(COALESCE(wd.VALUE, 0)) {base} GROUP BY 1 ORDER BY 3 DESC", (start, end))
        out["customer"] = cur.fetchall()
        cur.close()
        conn.close()
        return out

    def open_earnings_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Earnings per day")
        dialog.resize(900, 620)
        layout = QVBoxLayout(dialog)
        top = QHBoxLayout()
        top.addWidget(QLabel("Period:"))
        period = QComboBox()
        period.setObjectName("cmb_earnings_period")
        today = date.today()
        first_this = today.replace(day=1)
        last_month_end = first_this - timedelta(days=1)
        options = [("This month", first_this, today),
                   ("Last month", last_month_end.replace(day=1), last_month_end),
                   ("This year", date(today.year, 1, 1), today),
                   ("Last 12 months", today - timedelta(days=365), today),
                   ("All time", date(2000, 1, 1), date(2100, 1, 1))]
        for label, a, b in options:
            period.addItem(label, (a.isoformat(), b.isoformat()))
        period.setCurrentIndex(2)
        top.addWidget(period)
        top.addStretch(1)
        layout.addLayout(top)
        summary = QLabel()
        summary.setStyleSheet("font-size:15px; font-weight:700; color:#1565C0;")
        layout.addWidget(summary)
        hint = QLabel("$/day = value ÷ days worked, where ⅓ of a day counts as ⅓ — so it is what a FULL day of work "
                      "brings in.")
        hint.setStyleSheet("color:#64748B; font-size:12px;")
        layout.addWidget(hint)
        from PySide6.QtWidgets import QTabWidget
        tabs = QTabWidget()
        tabs.setObjectName("tabs_earnings")
        tables = {}
        for key, title in (("month", "By month"), ("job", "By Job Code"), ("customer", "By customer")):
            t = QTableWidget(0, 4)
            t.setObjectName(f"table_earnings_{key}")
            t.setHorizontalHeaderLabels([{"month": "Month", "job": "Job Code", "customer": "Customer"}[key],
                                         "Days", "Value", "$/day"])
            t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            t.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            for c in (1, 2, 3):
                t.setColumnWidth(c, 150)
            t.verticalHeader().setVisible(False)
            t.setSortingEnabled(key != "month")  # meses ficam em ordem de data
            tabs.addTab(t, title)
            tables[key] = t
        layout.addWidget(tabs, 1)
        close = QPushButton("Close")
        close.clicked.connect(dialog.accept)
        b = QHBoxLayout()
        b.addStretch(1)
        b.addWidget(close)
        layout.addLayout(b)

        def load(*_a):
            a, z = period.currentData()
            try:
                data = self._earnings(date.fromisoformat(a), date.fromisoformat(z))
            except (MySQLError, RuntimeError) as e:
                summary.setText(f"Could not load: {e}")
                return
            for key, t in tables.items():
                rows = data[key]
                t.setSortingEnabled(False)
                t.setRowCount(len(rows))
                for r, (label, days, value) in enumerate(rows):
                    days, value = float(days or 0), float(value or 0)
                    if key == "month":
                        try:
                            label = date.fromisoformat(f"{label}-01").strftime("%b %Y")
                        except ValueError:
                            pass
                    per = value / days if days else 0.0
                    for c, (text, sort) in enumerate([(label, None), (fmt_days(days), days),
                                                      (_money(value), value), (_money(per), per)]):
                        item = QTableWidgetItem(text)
                        if sort is not None:
                            item.setData(Qt.ItemDataRole.UserRole, sort)
                            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                        t.setItem(r, c, item)
                t.setSortingEnabled(key != "month")
            days = sum(float(d or 0) for _l, d, _v in data["job"])
            value = sum(float(v or 0) for _l, _d, v in data["job"])
            summary.setText(f"{period.currentText()}: {fmt_days(days)} {days_word(days)} · {_money(value)} · "
                            f"{_money(value / days if days else 0)} per full day")
            dialog._data = data  # usado nos testes

        period.currentIndexChanged.connect(load)
        load()
        dialog.exec()

    # ═════════════════════════ HOME CARD ═════════════════════════
    def _monthly_goal(self):
        return QSettings("VL Flooring", "app").value("goal/monthly", 0.0, type=float)

    def _setup_today_card(self):
        frame = QFrame()
        frame.setObjectName("frame_home_today")
        frame.setStyleSheet(_CARD_QSS)
        row = QHBoxLayout(frame)
        row.setContentsMargins(18, 14, 18, 14)
        row.setSpacing(18)
        btn = QPushButton("  Log today")
        btn.setObjectName("btn_new_log_today")
        btn.setIcon(tabler_icon("plus", "#FFFFFF", 18))
        btn.setStyleSheet(_PRIMARY_BTN)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip("Create today's day for the job(s) you worked on — with the part of the day of each")
        btn.clicked.connect(self.open_log_today_dialog)
        row.addWidget(btn)
        info = QVBoxLayout()
        info.setSpacing(4)
        lbl = QLabel()
        lbl.setObjectName("lbl_home_month_earnings")
        lbl.setStyleSheet("font-size:14px; font-weight:700; color:#334155;")
        bar = QProgressBar()
        bar.setObjectName("bar_home_month_goal")
        bar.setMaximumHeight(14)
        bar.setTextVisible(False)
        bar.setStyleSheet("QProgressBar { background-color: #E2E8F0; border: none; border-radius: 7px; } "
                          "QProgressBar::chunk { background-color: #15803D; border-radius: 7px; }")
        sub = QLabel()
        sub.setObjectName("lbl_home_month_goal")
        sub.setStyleSheet("font-size:12px; color:#64748B;")
        info.addWidget(lbl)
        info.addWidget(bar)
        info.addWidget(sub)
        row.addLayout(info, 1)
        btn_goal = QPushButton("Set goal")
        btn_goal.setStyleSheet(_SMALL_BTN)
        btn_goal.clicked.connect(self._ask_monthly_goal)
        btn_more = QPushButton("  Earnings per day")
        btn_more.setIcon(tabler_icon("chart-bar", "#37474F", 16))
        btn_more.setStyleSheet(_SMALL_BTN)
        btn_more.clicked.connect(self.open_earnings_dialog)
        row.addWidget(btn_goal)
        row.addWidget(btn_more)
        self.ui.layout_home_page.insertWidget(0, frame)
        self._today_card = {"frame": frame, "label": lbl, "bar": bar, "sub": sub, "money": (btn_goal, btn_more, info)}
        self.ui.Pages.currentChanged.connect(lambda i: i == 0 and self.refresh_today_card())
        btn_hidden = QPushButton()
        btn_hidden.setObjectName("btn_tool_earnings")
        btn_hidden.clicked.connect(self.open_earnings_dialog)
        self.ui.btn_tool_earnings = btn_hidden

    def _ask_monthly_goal(self):
        value, ok = QInputDialog.getDouble(self, "Monthly goal", "How much do you want to produce per month ($)?",
                                           self._monthly_goal() or 8000.0, 0, 10_000_000, 2)
        if ok:
            QSettings("VL Flooring", "app").setValue("goal/monthly", value)
            self.refresh_today_card()

    def refresh_today_card(self):
        card = getattr(self, "_today_card", None)
        if not card:
            return
        finance = self._role_rule("finance")
        for w in card["money"][:2]:
            w.setVisible(finance)
        for w in (card["label"], card["bar"], card["sub"]):
            w.setVisible(finance)
        if not finance:
            return
        today = date.today()
        try:
            data = self._earnings(today.replace(day=1), today)
        except (MySQLError, RuntimeError):
            return
        days = sum(float(d or 0) for _l, d, _v in data["job"])
        value = sum(float(v or 0) for _l, _d, v in data["job"])
        per = value / days if days else 0
        card["label"].setText(f"{today:%B}: {_money(value)}  ·  {fmt_days(days)} {days_word(days)}  ·  "
                              f"{_money(per)} per day")
        goal = self._monthly_goal()
        if goal > 0:
            pct = value / goal * 100
            card["bar"].setVisible(True)
            card["bar"].setMaximum(1000)
            card["bar"].setValue(int(min(pct, 100) * 10))
            left = max(goal - value, 0)
            card["sub"].setText(f"Goal {_money(goal)} — {pct:.0f}%" + (f" · {_money(left)} to go" if left else " · reached!"))
        else:
            card["bar"].setVisible(False)
            card["sub"].setText("No monthly goal yet — click Set goal.")
