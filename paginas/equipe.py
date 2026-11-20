# -*- coding: utf-8 -*-
"""
Equipe do dia (vários helpers por job) e relatório de pagamento dos helpers.

• No formulário de Job, o botão "Helpers (N) · $total" abre a lista de
  helpers daquele dia, cada um com o seu pagamento. A lista fica guardada na
  tabela work_day_helpers (uma linha por helper por dia).
• work_days.HELPER_ID / HELPER_PAY continuam existindo como RESUMO do dia
  (primeiro helper / soma dos pagamentos), assim o Job Profit, o View
  Project e o resto do app seguem funcionando sem mudar.
• Receivables → aba "Helper Pay": quanto cada helper recebeu no período,
  com os dias trabalhados e a forma de pagamento dele.

Métodos da MainWindow (mixin) — veja main_.py.
"""

from datetime import timedelta

from app_common import *  # noqa: F401,F403
from paginas.fracao import fmt_days, make_portion_combo, portion_label
from paginas.visual import tabler_icon
from paginas.moderno import show_toast

_BTN_QSS = ("QPushButton { background-color: #F5F8FC; color: #1C2B3A; border: 1px solid #CBD5E1; "
            "border-radius: 6px; padding: 7px 12px; font-size: 13px; text-align: left; } "
            "QPushButton:hover { background-color: #EEF4FB; border-color: #1E88E5; }")


class CrewMixin:
    # ── formulário ───────────────────────────────────────────────────
    def _setup_crew_ui(self):
        """Troca o combo Helper + Helper Pay por um botão que abre a equipe."""
        ui = self.ui
        self._job_helpers = []  # lista de [helper_id, pay]
        for widget in (ui.cmb_helper, getattr(ui, "dspn_helper_pay", None), getattr(ui, "lbl_helper_pay", None)):
            if widget is not None:
                widget.setVisible(False)
        ui.lbl_helper.setText("HELPERS")
        btn = QPushButton()
        btn.setObjectName("btn_job_helpers")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setIcon(tabler_icon("users", "#37474F", 16))
        btn.setMinimumHeight(36)
        btn.setStyleSheet(_BTN_QSS)
        btn.setToolTip("Who worked on this day and how much each one was paid")
        btn.clicked.connect(self.open_job_helpers_dialog)
        ui.grid_job_info.addWidget(btn, 5, 0, 1, 2)
        ui.btn_job_helpers = btn
        self._refresh_helpers_button()

    def _crew_table_ready(self):
        return self._table_column_exists("work_day_helpers", "WORK_DAY_ID")

    def _helper_names(self):
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cols = "ID, COALESCE(NULLIF(FULL_NAME, ''), COMPANY_NAME)"
            cur.execute(f"SELECT {cols} FROM helpers ORDER BY 2")
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return rows
        except (MySQLError, RuntimeError):
            return []

    def _refresh_helpers_button(self):
        btn = getattr(self.ui, "btn_job_helpers", None)
        if btn is None:
            return
        crew = getattr(self, "_job_helpers", [])
        if not crew:
            btn.setText("  No helpers — click to add")
            return
        total = sum(float(c[1] or 0) for c in crew)
        names = dict(self._helper_names())
        first = ", ".join((names.get(c[0]) or f"#{c[0]}").split()[0] for c in crew[:3])
        more = f" +{len(crew) - 3}" if len(crew) > 3 else ""
        btn.setText(f"  Helpers ({len(crew)}) · ${total:,.2f}   —  {first}{more}")

    def _reset_job_helpers(self):
        self._job_helpers = []
        self._refresh_helpers_button()

    def _load_job_helpers(self, work_day_id, data=None):
        """Carrega a equipe de um dia salvo (ou o resumo antigo, se a tabela
        de equipe não tiver nada para esse dia)."""
        crew = []
        if work_day_id and self._crew_table_ready():
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                cur.execute("SELECT HELPER_ID, PAY, DAY_FRACTION FROM work_day_helpers WHERE WORK_DAY_ID=%s "
                            "ORDER BY ID", (work_day_id,))
                crew = [[h, float(p or 0), float(f if f is not None else 1)] for h, p, f in cur.fetchall()]
                cur.close()
                conn.close()
            except (MySQLError, RuntimeError):
                crew = []
        if not crew and data and data.get("HELPER_ID"):
            crew = [[data["HELPER_ID"], float(data.get("HELPER_PAY") or 0), 1.0]]
        self._job_helpers = crew
        self._refresh_helpers_button()

    def _load_crew_from_latest_day(self, job_project_id):
        """Novo dia de um Job Code: sugere a mesma equipe do último dia."""
        if not job_project_id or not self._crew_table_ready():
            return
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT h.HELPER_ID, h.PAY, h.DAY_FRACTION FROM work_day_helpers h
                WHERE h.WORK_DAY_ID = (
                    SELECT wd.ID FROM work_days wd
                    WHERE wd.JOB_PROJECT_ID = %s AND EXISTS (SELECT 1 FROM work_day_helpers x WHERE x.WORK_DAY_ID = wd.ID)
                    ORDER BY wd.WORK_DATE DESC, wd.ID DESC LIMIT 1)
                ORDER BY h.ID
            """, (job_project_id,))
            crew = [[h, float(p or 0), float(f if f is not None else 1)] for h, p, f in cur.fetchall()]
            cur.close()
            conn.close()
        except (MySQLError, RuntimeError):
            return
        if crew:
            self._job_helpers = crew
            self._refresh_helpers_button()

    def _crew_summary_fields(self):
        """HELPER_ID (primeiro) e HELPER_PAY (soma) gravados em work_days."""
        crew = getattr(self, "_job_helpers", [])
        if not crew:
            return None, None
        return crew[0][0], round(sum(float(c[1] or 0) for c in crew), 2)

    def _save_job_helpers(self, cursor, work_day_id):
        """Grava a equipe do dia (na mesma transação do Save do job)."""
        if not work_day_id or not self._crew_table_ready():
            return
        cursor.execute("DELETE FROM work_day_helpers WHERE WORK_DAY_ID=%s", (work_day_id,))
        for entry in getattr(self, "_job_helpers", []):
            helper_id, pay = entry[0], entry[1]
            fraction = entry[2] if len(entry) > 2 else 1.0
            if helper_id:
                cursor.execute("INSERT INTO work_day_helpers (WORK_DAY_ID, HELPER_ID, PAY, DAY_FRACTION) "
                               "VALUES (%s, %s, %s, %s)", (work_day_id, helper_id, pay, fraction))

    # ── janela da equipe ─────────────────────────────────────────────
    def open_job_helpers_dialog(self):
        if not self._crew_table_ready():
            QMessageBox.warning(self, "Not available", "The helpers table is missing in the database.")
            return
        read_only = getattr(self, "_db_read_only", False)
        dialog = QDialog(self)
        dialog.setWindowTitle("Helpers of this day")
        dialog.resize(700, 420)
        layout = QVBoxLayout(dialog)
        date_text = self.ui.date_work_date.date().toString("MM/dd/yyyy")
        code = self.ui.cmb_job_code.currentText().strip()
        layout.addWidget(QLabel(f"<b>{date_text}</b>" + (f" · {code}" if code else "") +
                                " — who worked, how much of the day and how much each one was paid."))

        table = QTableWidget(0, 4)
        table.setHorizontalHeaderLabels(["Helper", "Day", "Pay ($)", ""])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.setColumnWidth(1, 130)
        table.setColumnWidth(2, 140)
        table.setColumnWidth(3, 48)
        table.verticalHeader().setVisible(False)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        table.setStyleSheet("QComboBox, QDoubleSpinBox { min-height: 20px; padding: 4px 8px; margin: 4px 4px; }")
        layout.addWidget(table, 1)
        lbl_total = QLabel()
        lbl_total.setStyleSheet("font-weight:700; font-size:14px;")
        layout.addWidget(lbl_total)

        helpers = self._helper_names()
        daily_rates = self._helper_daily_rates() if hasattr(self, "_helper_daily_rates") else {}

        def update_total():
            total = 0.0
            for r in range(table.rowCount()):
                total += table.cellWidget(r, 2).value()
            lbl_total.setText(f"Total: ${total:,.2f}  ·  {table.rowCount()} helper(s)")

        def add_row(helper_id=None, pay=0.0, fraction=None):
            r = table.rowCount()
            table.insertRow(r)
            combo = QComboBox()
            combo.addItem("— Select —", None)
            for hid, name in helpers:
                combo.addItem(name or f"#{hid}", hid)
            idx = combo.findData(helper_id)
            combo.setCurrentIndex(idx if idx >= 0 else 0)
            spin = QDoubleSpinBox()
            spin.setRange(0, 99999.99)
            spin.setDecimals(2)
            spin.setPrefix("$ ")
            spin.setValue(float(pay or 0))
            spin.valueChanged.connect(lambda *_a: update_total())
            portion = make_portion_combo(self._day_portion_value() if fraction is None else fraction)
            auto = {"pay": None}

            def auto_pay(*_a):
                # Pay em $0 (ou ainda com o valor que o cálculo pôs) segue a diária × parte do dia
                rate = daily_rates.get(combo.currentData())
                if not rate:
                    return
                if spin.value() == 0 or (auto["pay"] is not None and abs(spin.value() - auto["pay"]) < 0.005):
                    auto["pay"] = round(rate * float(portion.currentData() or 1), 2)
                    spin.setValue(auto["pay"])
            combo.currentIndexChanged.connect(auto_pay)
            portion.currentIndexChanged.connect(auto_pay)
            combo.setToolTip("Helpers with a daily rate get the pay filled in (rate × part of the day)")
            btn_remove = QPushButton()
            btn_remove.setIcon(tabler_icon("x", "#C62828", 16))
            btn_remove.setToolTip("Remove this helper")
            btn_remove.setCursor(Qt.CursorShape.PointingHandCursor)

            def remove():
                for row in range(table.rowCount()):
                    if table.cellWidget(row, 3) is btn_remove:
                        table.removeRow(row)
                        break
                update_total()
            btn_remove.clicked.connect(remove)
            for w in (combo, portion, spin, btn_remove):
                w.setEnabled(not read_only)
            table.setCellWidget(r, 0, combo)
            table.setCellWidget(r, 1, portion)
            table.setCellWidget(r, 2, spin)
            table.setCellWidget(r, 3, btn_remove)
            table.setRowHeight(r, 50)
            update_total()

        for entry in getattr(self, "_job_helpers", []):
            add_row(entry[0], entry[1], entry[2] if len(entry) > 2 else 1.0)
        if not self._job_helpers:
            add_row()

        row = QHBoxLayout()
        btn_add = QPushButton("  Add helper")
        btn_add.setIcon(tabler_icon("plus", "#37474F", 16))
        btn_new = QPushButton("  New helper…")
        btn_new.setIcon(tabler_icon("user-plus", "#37474F", 16))
        btn_new.setToolTip("Register a new helper (Registrations → Helpers)")
        for b in (btn_add, btn_new):
            b.setEnabled(not read_only)
            row.addWidget(b)
        row.addStretch(1)
        btn_cancel, btn_ok = QPushButton("Cancel"), QPushButton("OK")
        btn_ok.setObjectName("btn_job_helpers_ok")
        row.addWidget(btn_cancel)
        row.addWidget(btn_ok)
        layout.addLayout(row)
        hint = QLabel("The helpers are saved together with the job when you click Save.")
        hint.setStyleSheet("color:#6B7C93; font-size:11px;")
        layout.addWidget(hint)

        btn_add.clicked.connect(lambda: add_row())
        btn_cancel.clicked.connect(dialog.reject)

        def new_helper():
            self.open_helpers_manager_dialog()
            nonlocal helpers
            helpers = self._helper_names()
            for r in range(table.rowCount()):
                combo = table.cellWidget(r, 0)
                current = combo.currentData()
                combo.clear()
                combo.addItem("— Select —", None)
                for hid, name in helpers:
                    combo.addItem(name or f"#{hid}", hid)
                idx = combo.findData(current)
                combo.setCurrentIndex(idx if idx >= 0 else 0)
            if hasattr(self, "load_combo_data"):
                self.load_combo_data()
        btn_new.clicked.connect(new_helper)

        def accept():
            crew, seen = [], set()
            for r in range(table.rowCount()):
                hid = table.cellWidget(r, 0).currentData()
                fraction = float(table.cellWidget(r, 1).currentData() or 1)
                pay = table.cellWidget(r, 2).value()
                if hid is None:
                    if pay:
                        QMessageBox.warning(dialog, "Choose the helper", "A row has a pay amount but no helper selected.")
                        return
                    continue
                if hid in seen:
                    QMessageBox.warning(dialog, "Repeated helper", "The same helper is listed twice.")
                    return
                seen.add(hid)
                crew.append([hid, round(pay, 2), fraction])
            if crew != getattr(self, "_job_helpers", []):
                self._job_helpers = crew
                self._mark_job_form_dirty()
            self._refresh_helpers_button()
            dialog.accept()
        btn_ok.clicked.connect(accept)
        dialog.exec()

    # ── relatório de pagamento dos helpers ───────────────────────────
    def _setup_helper_pay_tab(self):
        tab = QWidget()
        tab.setObjectName("tab_helper_pay")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        top = QHBoxLayout()
        top.addWidget(QLabel("Period:"))
        cmb = QComboBox()
        for label in ("This week", "Last week", "This month", "Last month", "This year", "Custom"):
            cmb.addItem(label)
        date_from, date_to = QDateEdit(), QDateEdit()
        for d in (date_from, date_to):
            d.setCalendarPopup(True)
            d.setDisplayFormat("MM/dd/yyyy")
            d.setMinimumWidth(140)
        top.addWidget(cmb)
        top.addWidget(date_from)
        top.addWidget(QLabel("to"))
        top.addWidget(date_to)
        top.addStretch(1)
        btn_excel = QPushButton("  Excel")
        btn_excel.setIcon(tabler_icon("download", "#37474F", 16))
        top.addWidget(btn_excel)
        layout.addLayout(top)
        summary = QLabel()
        summary.setStyleSheet("font-size:14px; font-weight:700; background:transparent;")
        layout.addWidget(summary)

        table = QTableWidget(0, 4)
        table.setHorizontalHeaderLabels(["Helper", "Days", "Total pay", "Pay via"])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(table, 1)
        lbl_detail = QLabel("Click a helper to see the days.")
        lbl_detail.setStyleSheet("color:#6B7C93; background:transparent;")
        layout.addWidget(lbl_detail)
        detail = QTableWidget(0, 4)
        detail.setHorizontalHeaderLabels(["Date", "Job Code", "Address", "Pay"])
        detail.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        detail.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(detail, 1)

        self.ui.tabWidget_receivables.addTab(tab, "Helper Pay")
        self.ui.tab_helper_pay = tab
        self._helper_pay_widgets = (cmb, date_from, date_to, summary, table, detail, lbl_detail)

        def apply_period():
            today = date.today()
            choice = cmb.currentText()
            custom = choice == "Custom"
            date_from.setEnabled(custom)
            date_to.setEnabled(custom)
            if not custom:
                if choice == "This week":
                    start = today - timedelta(days=today.weekday()); end = start + timedelta(days=6)
                elif choice == "Last week":
                    end = today - timedelta(days=today.weekday() + 1); start = end - timedelta(days=6)
                elif choice == "This month":
                    start = today.replace(day=1)
                    end = (start.replace(month=start.month % 12 + 1, year=start.year + start.month // 12)
                           - timedelta(days=1))
                elif choice == "Last month":
                    end = today.replace(day=1) - timedelta(days=1); start = end.replace(day=1)
                else:
                    start, end = date(today.year, 1, 1), date(today.year, 12, 31)
                for widget, d in ((date_from, start), (date_to, end)):
                    widget.blockSignals(True)
                    widget.setDate(QDate(d.year, d.month, d.day))
                    widget.blockSignals(False)
            self.load_helper_pay_report()

        cmb.currentIndexChanged.connect(lambda *_a: apply_period())
        date_from.dateChanged.connect(lambda *_a: self.load_helper_pay_report())
        date_to.dateChanged.connect(lambda *_a: self.load_helper_pay_report())
        table.itemSelectionChanged.connect(self._load_helper_pay_detail)
        btn_excel.clicked.connect(lambda: self._export_table_to_excel(
            table, f"Helper_Pay_{date_from.date().toString('yyyy-MM-dd')}_to_{date_to.date().toString('yyyy-MM-dd')}.xlsx"))
        self.ui.tabWidget_receivables.currentChanged.connect(
            lambda i: apply_period() if self.ui.tabWidget_receivables.widget(i) is tab else None)
        self._helper_pay_apply_period = apply_period

    def load_helper_pay_report(self):
        cmb, date_from, date_to, summary, table, detail, lbl_detail = self._helper_pay_widgets
        start, end = date_from.date().toPython(), date_to.date().toPython()
        detail.setRowCount(0)
        lbl_detail.setText("Click a helper to see the days.")
        if not self._crew_table_ready():
            summary.setText("The helpers table is missing in the database.")
            return
        pay_cols = [c for c in ("PAYMENT_ZELLE", "PAYMENT_CASHAPP", "PAYMENT_VENMO", "PAYMENT_CHECK_NAME")
                    if self._table_column_exists("helpers", c)]
        pay_sql = ", ".join(f"MAX(he.{c})" for c in pay_cols) if pay_cols else "NULL"
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(f"""
                SELECT h.HELPER_ID, COALESCE(MAX(NULLIF(he.FULL_NAME, '')), MAX(he.COMPANY_NAME), CONCAT('#', h.HELPER_ID)),
                       COALESCE(SUM(h.DAY_FRACTION), 0), COALESCE(SUM(h.PAY), 0), {pay_sql}
                FROM work_day_helpers h
                JOIN work_days wd ON wd.ID = h.WORK_DAY_ID
                LEFT JOIN helpers he ON he.ID = h.HELPER_ID
                WHERE wd.WORK_DATE BETWEEN %s AND %s AND COALESCE(wd.STATUS, '') <> 'CANCELLED'
                GROUP BY h.HELPER_ID
                ORDER BY 4 DESC
            """, (start, end))
            rows = cur.fetchall()
            cur.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            summary.setText(f"Could not load the report: {e}")
            return
        labels = {"PAYMENT_ZELLE": "Zelle", "PAYMENT_CASHAPP": "Cash App", "PAYMENT_VENMO": "Venmo",
                  "PAYMENT_CHECK_NAME": "Check"}
        table.setRowCount(len(rows))
        grand = 0.0
        for r, row in enumerate(rows):
            hid, name, days, total = row[0], row[1], row[2], float(row[3] or 0)
            grand += total
            via = " · ".join(f"{labels[c]}: {v}" for c, v in zip(pay_cols, row[4:4 + len(pay_cols)]) if v)
            for c, text in enumerate([name, fmt_days(days), f"${total:,.2f}", via or "—"]):
                item = QTableWidgetItem(text)
                if c == 0:
                    item.setData(Qt.ItemDataRole.UserRole, hid)
                if c in (1, 2):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                table.setItem(r, c, item)
        summary.setText(f"{start:%m/%d/%Y} – {end:%m/%d/%Y}  ·  {len(rows)} helper(s)  ·  Total ${grand:,.2f}")

    def _load_helper_pay_detail(self):
        cmb, date_from, date_to, summary, table, detail, lbl_detail = self._helper_pay_widgets
        row = table.currentRow()
        if row < 0 or table.item(row, 0) is None:
            return
        hid = table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        start, end = date_from.date().toPython(), date_to.date().toPython()
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT wd.WORK_DATE, COALESCE(jp.CODE, '—'), COALESCE(wd.JOB_ADDRESS, ''), h.PAY, h.DAY_FRACTION
                FROM work_day_helpers h JOIN work_days wd ON wd.ID = h.WORK_DAY_ID
                LEFT JOIN job_projects jp ON jp.ID = wd.JOB_PROJECT_ID
                WHERE h.HELPER_ID = %s AND wd.WORK_DATE BETWEEN %s AND %s AND COALESCE(wd.STATUS, '') <> 'CANCELLED'
                ORDER BY wd.WORK_DATE
            """, (hid, start, end))
            rows = cur.fetchall()
            cur.close()
            conn.close()
        except (MySQLError, RuntimeError):
            return
        detail.setRowCount(len(rows))
        for r, (wdate, code, address, pay, fraction) in enumerate(rows):
            for c, text in enumerate([wdate.strftime("%m/%d/%Y") if wdate else "", code, address,
                                      f"${float(pay or 0):,.2f}  ·  {portion_label(fraction)}"]):
                detail.setItem(r, c, QTableWidgetItem(text))
        lbl_detail.setText(f"Days worked by {table.item(row, 0).text()}:")
