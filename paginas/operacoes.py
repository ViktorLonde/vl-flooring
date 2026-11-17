# -*- coding: utf-8 -*-
"""
Ferramentas do dia a dia:

• Editar vários jobs de uma vez (status, cliente, Job Code) — selecione
  várias linhas em Job Records (Ctrl/Shift + clique).
• Duplicar um job para outros dias (trabalhos de vários dias).
• Agenda da semana para os helpers (texto pro WhatsApp ou PDF).
• Lucro por Job Code (aba "Job Profit" em Receivables).
• Lembrete por e-mail das invoices atrasadas (30+ dias).

Métodos da MainWindow (mixin) — veja main_.py.
"""

from datetime import timedelta
from urllib.parse import quote

from PySide6.QtWidgets import QCheckBox

from app_common import *  # noqa: F401,F403
from paginas.visual import tabler_icon
from paginas.moderno import show_toast

_SMALL_BTN = ("QPushButton { background-color: #EEF2F7; color: #37474F; border: 1px solid #D0D7DE; "
              "border-radius: 6px; padding: 6px 12px; font-size: 12px; font-weight: 600; } "
              "QPushButton:hover { background-color: #E1E8F0; }")
_DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
_WT_PREFIXES = ["DEMOLITION_1", "DEMOLITION_2", "DEMOLITION_3", "DEMOLITION_4",
                "INSTALLATION_1", "INSTALLATION_2", "INSTALLATION_3", "INSTALLATION_4",
                "PREPARATION_1", "PREPARATION_2", "PREPARATION_3", "PREPARATION_4",
                "OTHERS_1", "OTHERS_2", "REPARO_1", "REPARO_2"]
REMINDER_TEMPLATE = (
    "Hello {name},\n\n"
    "This is a friendly reminder that invoice #{invoice} from {company}, issued on {date}, "
    "has an open balance of {amount} ({days} days).\n\n"
    "If you have already sent the payment, please disregard this message. "
    "Let us know if you have any questions.\n\n"
    "Thank you,\n{company}"
)


def _fmt_date(d):
    return d.strftime("%m/%d/%Y") if d else ""


class OperationsMixin:
    def _setup_operations(self):
        self._setup_bulk_edit()
        self._setup_duplicate_job()
        self._setup_week_schedule_button()
        self._setup_profit_tab()
        self._setup_reminders_button()
        self._setup_complete_job_button()

    # ══ concluir o trabalho (todos os dias do Job Code) ══════════════
    def _setup_complete_job_button(self):
        btn = QPushButton("  Complete job")
        btn.setObjectName("btn_complete_job")
        btn.setIcon(tabler_icon("circle-check", "#15803D", 16))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip("Mark the days of this Job Code as COMPLETED at once")
        btn.setStyleSheet("QPushButton { background-color: #DCFCE7; color: #166534; border: 1px solid #86EFAC; "
                          "border-radius: 6px; padding: 6px 10px; font-size: 12px; font-weight: 600; } "
                          "QPushButton:hover { background-color: #BBF7D0; }")
        btn.setVisible(False)
        btn.clicked.connect(self.open_complete_job_dialog)
        layout = self.ui.layout_job_code_field_row
        layout.insertWidget(layout.indexOf(self.ui.lbl_days_worked_value) + 1, btn)
        self._btn_complete_job = btn

    def open_complete_job_dialog(self):
        code = self.ui.cmb_job_code.currentText().strip().upper()
        project_id = self._job_code_to_id.get(code)
        if not project_id:
            return
        if getattr(self, "_job_form_dirty", False):
            QMessageBox.information(self, "Save first", "Save the current changes before completing the job.")
            return
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT ID, WORK_DATE, STATUS, VALUE FROM work_days WHERE JOB_PROJECT_ID=%s "
                        "ORDER BY WORK_DATE, ID", (project_id,))
            days = cur.fetchall()
            cur.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not load the days:\n{e}")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Complete job {code}")
        dialog.resize(520, 420)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(f"Tick the days of <b>{code}</b> that were finished. "
                                "Future dates start unticked — check if they are correct."))
        table = QTableWidget(len(days), 4)
        table.setHorizontalHeaderLabels(["Complete", "Date", "Current status", "Value"])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        today = date.today()
        for r, (jid, wdate, status, value) in enumerate(days):
            chk = QTableWidgetItem(f"#{jid}")
            chk.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            done = status in ("COMPLETED", "CANCELLED")
            future = bool(wdate and wdate > today)
            chk.setCheckState(Qt.CheckState.Unchecked if (done or future) else Qt.CheckState.Checked)
            if done:
                chk.setFlags(Qt.ItemFlag.ItemIsEnabled)
            chk.setData(Qt.ItemDataRole.UserRole, jid)
            table.setItem(r, 0, chk)
            date_text = _fmt_date(wdate) + ("  (future date!)" if future else "")
            for c, v in enumerate([date_text, JOB_STATUS_LABELS.get(status, status or ""),
                                   f"${float(value or 0):,.2f}"], start=1):
                table.setItem(r, c, QTableWidgetItem(v))
        layout.addWidget(table, 1)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        btn_cancel, btn_ok = QPushButton("Cancel"), QPushButton("Mark as COMPLETED")
        btn_ok.setObjectName("btn_complete_job_confirm")
        buttons.addWidget(btn_cancel)
        buttons.addWidget(btn_ok)
        layout.addLayout(buttons)
        btn_cancel.clicked.connect(dialog.reject)

        def apply():
            ids = [table.item(r, 0).data(Qt.ItemDataRole.UserRole) for r in range(table.rowCount())
                   if table.item(r, 0).checkState() == Qt.CheckState.Checked]
            if not ids:
                QMessageBox.information(dialog, "Nothing selected", "Tick at least one day.")
                return
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                cur.execute(f"UPDATE work_days SET STATUS='COMPLETED' WHERE ID IN ({','.join(['%s'] * len(ids))})", ids)
                conn.commit()
                cur.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not update the days:\n{e}")
                return
            dialog.accept()
            current = getattr(self, "_current_job_id", None)
            self.load_work_days()
            if current in ids:
                self._loading_job_form = True
                self._set_combo_by_data(self.ui.cmb_status_form, "COMPLETED", by_text=True)
                self._loading_job_form = False
                self._job_form_dirty = False
            self._update_days_worked_label()
            show_toast(f"{code}: {len(ids)} day{'s' if len(ids) != 1 else ''} marked as COMPLETED.", "success", self)

        btn_ok.clicked.connect(apply)
        dialog.exec()

    # ══ editar vários jobs ═══════════════════════════════════════════
    def _setup_bulk_edit(self):
        table = self.ui.table_work_days
        table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        btn = QPushButton()
        btn.setObjectName("btn_bulk_edit_jobs")
        btn.setIcon(tabler_icon("pencil", "#FFFFFF", 16))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(34)
        btn.setStyleSheet("QPushButton { background-color: #1565C0; color: #FFFFFF; border: none; "
                          "border-radius: 6px; font-weight: 600; } QPushButton:hover { background-color: #1E88E5; }")
        btn.setVisible(False)
        btn.clicked.connect(self.open_bulk_edit_dialog)
        layout = self.ui.layout_jobs_left_panel
        layout.insertWidget(layout.indexOf(table), btn)
        self._btn_bulk_edit = btn
        table.itemSelectionChanged.connect(self._update_bulk_edit_button)
        hint = "Tip: Ctrl+click or Shift+click to select several jobs and edit them together."
        table.setToolTip(hint)

    def _selected_job_ids(self):
        table = self.ui.table_work_days
        rows = sorted({i.row() for i in table.selectedIndexes()})
        ids = []
        for r in rows:
            item = table.item(r, 0)
            if item and item.text().isdigit():
                ids.append(int(item.text()))
        return ids

    def _update_bulk_edit_button(self):
        n = len(self._selected_job_ids())
        self._btn_bulk_edit.setVisible(n > 1)
        self._btn_bulk_edit.setText(f"  Edit {n} selected jobs")

    def open_bulk_edit_dialog(self):
        ids = self._selected_job_ids()
        if len(ids) < 2:
            return
        if getattr(self, "_db_read_only", False):
            QMessageBox.warning(self, "Read-only", "Your user has read-only access.")
            return
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT ID, FULL_NAME FROM clients ORDER BY FULL_NAME")
            clients = cur.fetchall()
            cur.execute("SELECT ID, CODE FROM job_projects WHERE CODE IS NOT NULL ORDER BY CODE")
            codes = cur.fetchall()
            cur.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not load the lists:\n{e}")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit {len(ids)} jobs")
        dialog.resize(460, 260)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(f"Tick what you want to change on the <b>{len(ids)}</b> selected jobs. "
                                "Everything else stays as it is."))
        grid = QGridLayout()
        chk_status, chk_client, chk_code = QCheckBox("Status"), QCheckBox("Client"), QCheckBox("Job Code")
        cmb_status = QComboBox()
        for i in range(self.ui.cmb_status_form.count()):
            cmb_status.addItem(self.ui.cmb_status_form.itemText(i))
        cmb_client = QComboBox()
        cmb_client.addItem("— none —", None)
        for cid, name in clients:
            cmb_client.addItem(name or f"#{cid}", cid)
        cmb_client.setEditable(True)
        cmb_client.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        cmb_code = QComboBox()
        cmb_code.setEditable(True)
        cmb_code.addItem("")
        for _pid, code in codes:
            cmb_code.addItem(code)
        for row, (chk, widget) in enumerate(((chk_status, cmb_status), (chk_client, cmb_client), (chk_code, cmb_code))):
            widget.setEnabled(False)
            chk.toggled.connect(widget.setEnabled)
            grid.addWidget(chk, row, 0)
            grid.addWidget(widget, row, 1)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)
        layout.addStretch(1)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        btn_cancel, btn_apply = QPushButton("Cancel"), QPushButton("Apply")
        btn_apply.setObjectName("btn_save_bulk_edit")
        buttons.addWidget(btn_cancel)
        buttons.addWidget(btn_apply)
        layout.addLayout(buttons)
        btn_cancel.clicked.connect(dialog.reject)

        def apply():
            sets, params, changed = [], [], []
            if chk_status.isChecked():
                sets.append("STATUS=%s")
                params.append(cmb_status.currentText())
                changed.append("status")
            if chk_client.isChecked():
                idx = cmb_client.findText(cmb_client.currentText())
                sets.append("CLIENT_ID=%s")
                params.append(cmb_client.itemData(idx) if idx >= 0 else None)
                changed.append("client")
            project_id = None
            if chk_code.isChecked():
                code = cmb_code.currentText().strip().upper()
                changed.append("Job Code")
                sets.append("JOB_PROJECT_ID=%s")
                if code:
                    project_id = dict((c.upper(), p) for p, c in codes).get(code)
                params.append(project_id)
            if not sets:
                QMessageBox.information(dialog, "Nothing to change", "Tick at least one field.")
                return
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                if chk_code.isChecked() and cmb_code.currentText().strip() and project_id is None:
                    cur.execute("INSERT INTO job_projects (CODE, PROJECT_TYPE, STATUS) VALUES (%s, 'DAY_WORK', 'ACTIVE')",
                                (cmb_code.currentText().strip().upper(),))
                    params[sets.index("JOB_PROJECT_ID=%s")] = cur.lastrowid
                placeholders = ",".join(["%s"] * len(ids))
                cur.execute(f"UPDATE work_days SET {', '.join(sets)} WHERE ID IN ({placeholders})", params + ids)
                conn.commit()
                cur.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not update the jobs:\n{e}")
                return
            dialog.accept()
            self.load_work_days()
            if hasattr(self, "_refresh_job_code_completer"):
                self._refresh_job_code_completer()
            show_toast(f"{len(ids)} jobs updated ({', '.join(changed)}).", "success", self)

        btn_apply.clicked.connect(apply)
        dialog.exec()

    # ══ duplicar job ═════════════════════════════════════════════════
    def _setup_duplicate_job(self):
        btn = QPushButton("  Duplicate")
        btn.setObjectName("btn_duplicate_job")
        btn.setIcon(tabler_icon("calendar", "#37474F", 16))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip("Copy this job to other days (same client, address and work types)")
        btn.setStyleSheet(_SMALL_BTN)
        btn.clicked.connect(self.open_duplicate_job_dialog)
        layout = self.ui.hboxLayout
        layout.insertWidget(layout.indexOf(self.ui.btn_job_go_to_expense) + 1, btn)
        self._btn_duplicate_job = btn

    def open_duplicate_job_dialog(self):
        job_id = getattr(self, "_current_job_id", None)
        if not job_id:
            QMessageBox.information(self, "Choose a job", "Select a saved job in the list first, then click Duplicate.")
            return
        if getattr(self, "_job_form_dirty", False):
            QMessageBox.information(self, "Save first", "Save the current changes before duplicating this job.")
            return
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT * FROM work_days WHERE ID=%s", (job_id,))
            row = cur.fetchone()
            cur.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not read the job:\n{e}")
            return
        if not row:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Duplicate job #{job_id}")
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(f"Copies job #{job_id} ({_fmt_date(row['WORK_DATE'])}) with the same client, "
                                "address, contractor and work types.\nThe copies start as PENDING."))
        grid = QGridLayout()
        date_start = QDateEdit()
        date_start.setCalendarPopup(True)
        date_start.setDisplayFormat("MM/dd/yyyy")
        start = (row["WORK_DATE"] or date.today()) + timedelta(days=1)
        date_start.setDate(QDate(start.year, start.month, start.day))
        spin_days = QSpinBox()
        spin_days.setRange(1, 30)
        spin_days.setValue(1)
        chk_skip_sunday = QCheckBox("Skip Sundays")
        chk_skip_sunday.setChecked(True)
        chk_keep_value = QCheckBox("Keep the same value ($)")
        chk_keep_value.setChecked(True)
        grid.addWidget(QLabel("First day"), 0, 0)
        grid.addWidget(date_start, 0, 1)
        grid.addWidget(QLabel("Number of days"), 1, 0)
        grid.addWidget(spin_days, 1, 1)
        grid.addWidget(chk_skip_sunday, 2, 1)
        grid.addWidget(chk_keep_value, 3, 1)
        layout.addLayout(grid)
        preview = QLabel()
        preview.setStyleSheet("color:#6B7C93;")
        layout.addWidget(preview)

        def dates():
            d = date_start.date().toPython()
            out = []
            while len(out) < spin_days.value():
                if not (chk_skip_sunday.isChecked() and d.weekday() == 6):
                    out.append(d)
                d += timedelta(days=1)
            return out

        def refresh_preview():
            ds = dates()
            text = ", ".join(f"{_DAY_NAMES[d.weekday()]} {d:%m/%d}" for d in ds[:8])
            preview.setText(f"New jobs: {text}{' …' if len(ds) > 8 else ''}")

        for sig in (date_start.dateChanged, spin_days.valueChanged, chk_skip_sunday.toggled):
            sig.connect(lambda *_a: refresh_preview())
        refresh_preview()
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        btn_cancel, btn_ok = QPushButton("Cancel"), QPushButton("Create copies")
        btn_ok.setObjectName("btn_save_duplicate")
        buttons.addWidget(btn_cancel)
        buttons.addWidget(btn_ok)
        layout.addLayout(buttons)
        btn_cancel.clicked.connect(dialog.reject)

        def create():
            skip = {"ID", "CREATED_AT", "UPDATED_AT"}
            cols = [c for c in row if c not in skip]
            created = 0
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                for d in dates():
                    values = dict(row)
                    values["WORK_DATE"] = d
                    values["STATUS"] = "PENDING"
                    if not chk_keep_value.isChecked():
                        values["VALUE"] = 0
                    cur.execute(f"INSERT INTO work_days ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(cols))})",
                                [values[c] for c in cols])
                    if self._crew_table_ready():  # a cópia leva a mesma equipe
                        cur.execute("INSERT INTO work_day_helpers (WORK_DAY_ID, HELPER_ID, PAY) "
                                    "SELECT %s, HELPER_ID, PAY FROM work_day_helpers WHERE WORK_DAY_ID=%s",
                                    (cur.lastrowid, job_id))
                    created += 1
                conn.commit()
                cur.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not create the copies:\n{e}")
                return
            dialog.accept()
            # garante que as cópias aparecem com o filtro de datas atual
            last = dates()[-1]
            if self.ui.date_filter_to.date().toPython() < last:
                self.ui.date_filter_to.setDate(QDate(last.year, last.month, last.day))
            self.load_work_days()
            show_toast(f"{created} cop{'y' if created == 1 else 'ies'} of job #{job_id} created.", "success", self)

        btn_ok.clicked.connect(create)
        dialog.exec()

    # ══ agenda da semana ═════════════════════════════════════════════
    def _setup_week_schedule_button(self):
        btn = QPushButton("  Share week")
        btn.setObjectName("btn_share_week_schedule")
        btn.setIcon(tabler_icon("send", "#37474F", 16))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip("Weekly schedule for the helpers — WhatsApp text or PDF")
        btn.clicked.connect(self.open_week_schedule_dialog)
        layout = self.ui.layout_schedule_side
        layout.insertWidget(layout.indexOf(self.ui.btn_schedule_new_job) + 1, btn)

    def _week_schedule_rows(self, monday):
        sunday = monday + timedelta(days=6)
        conn = self._get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SHOW COLUMNS FROM work_days LIKE 'HELPER_ID'")
        has_helper = cur.fetchone() is not None
        cur.execute("SELECT ID, NAME FROM work_types")
        wt_names = {r["ID"]: r["NAME"] for r in cur.fetchall()}
        if self._crew_table_ready():
            helper_sql = ("(SELECT GROUP_CONCAT(COALESCE(NULLIF(he.FULL_NAME, ''), he.COMPANY_NAME) "
                          "ORDER BY x.ID SEPARATOR ', ') FROM work_day_helpers x "
                          "JOIN helpers he ON he.ID = x.HELPER_ID WHERE x.WORK_DAY_ID = wd.ID)")
        else:
            helper_sql = ("(SELECT h.FULL_NAME FROM helpers h WHERE h.ID = wd.HELPER_ID)" if has_helper else "NULL")
        cur.execute(f"""
            SELECT wd.*, jp.CODE AS JOB_CODE, ci.CITY AS CITY_NAME, cl.FULL_NAME AS CLIENT_NAME,
                   co.COMPANY_NAME AS COMPANY_NAME, COALESCE(NULLIF(ct.COMPANY_NAME, ''), ct.FULL_NAME) AS CONTRACTOR_NAME,
                   {helper_sql} AS HELPER_NAME
            FROM work_days wd
            LEFT JOIN job_projects jp ON jp.ID = wd.JOB_PROJECT_ID
            LEFT JOIN cities ci ON ci.ID = wd.CITY_ID
            LEFT JOIN clients cl ON cl.ID = wd.CLIENT_ID
            LEFT JOIN companies co ON co.ID = wd.COMPANY_ID
            LEFT JOIN contractors ct ON ct.ID = wd.CONTRACTOR_ID
            WHERE wd.WORK_DATE BETWEEN %s AND %s AND COALESCE(wd.STATUS, '') <> 'CANCELLED'
            ORDER BY wd.WORK_DATE, wd.ID
        """, (monday, sunday))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        for r in rows:
            names = []
            for prefix in _WT_PREFIXES:
                wid = r.get(f"{prefix}_ID")
                if wid and wt_names.get(wid) and wt_names[wid] not in names:
                    names.append(wt_names[wid])
            r["WORK_TYPES"] = ", ".join(names)
        return rows

    def _week_schedule_text(self, monday, rows):
        sunday = monday + timedelta(days=6)
        lines = [f"*{company_settings.COMPANY_NAME}*", f"Schedule {monday:%m/%d} – {sunday:%m/%d/%Y}", ""]
        for i in range(7):
            day = monday + timedelta(days=i)
            day_rows = [r for r in rows if r["WORK_DATE"] == day]
            if not day_rows and i == 6:
                continue
            lines.append(f"*{_DAY_NAMES[i]} {day:%m/%d}*")
            if not day_rows:
                lines.append("  — no jobs")
            for r in day_rows:
                place = ", ".join(x for x in (r.get("JOB_ADDRESS"), r.get("CITY_NAME")) if x) or "address not set"
                who = r.get("CLIENT_NAME") or r.get("COMPANY_NAME") or r.get("CONTRACTOR_NAME") or ""
                code = f" ({r['JOB_CODE']})" if r.get("JOB_CODE") else ""
                lines.append(f"• {place}{code}")
                details = " · ".join(x for x in (who, r.get("WORK_TYPES"),
                                                 (f"Helpers: {r['HELPER_NAME']}" if "," in r["HELPER_NAME"]
                                                  else f"Helper: {r['HELPER_NAME']}") if r.get("HELPER_NAME") else "") if x)
                if details:
                    lines.append(f"   {details}")
            lines.append("")
        return "\n".join(lines).strip()

    def open_week_schedule_dialog(self):
        selected = self.ui.calendar_schedule.selectedDate().toPython()
        dialog = QDialog(self)
        dialog.setWindowTitle("Weekly schedule")
        dialog.resize(560, 620)
        layout = QVBoxLayout(dialog)
        top = QHBoxLayout()
        top.addWidget(QLabel("Week of"))
        date_week = QDateEdit()
        date_week.setCalendarPopup(True)
        date_week.setDisplayFormat("MM/dd/yyyy")
        monday = selected - timedelta(days=selected.weekday())
        date_week.setDate(QDate(monday.year, monday.month, monday.day))
        top.addWidget(date_week)
        top.addStretch(1)
        layout.addLayout(top)
        text = QTextEdit()
        text.setReadOnly(True)
        layout.addWidget(text, 1)
        buttons = QHBoxLayout()
        btn_copy = QPushButton("  Copy text")
        btn_copy.setIcon(tabler_icon("clipboard-list", "#37474F", 16))
        btn_wa = QPushButton("  Send by WhatsApp")
        btn_wa.setIcon(tabler_icon("send", "#37474F", 16))
        btn_pdf = QPushButton("  Save PDF")
        btn_pdf.setIcon(tabler_icon("download", "#37474F", 16))
        for b in (btn_copy, btn_wa, btn_pdf):
            buttons.addWidget(b)
        buttons.addStretch(1)
        layout.addLayout(buttons)
        state = {"monday": monday, "rows": []}

        def reload():
            d = date_week.date().toPython()
            state["monday"] = d - timedelta(days=d.weekday())
            try:
                state["rows"] = self._week_schedule_rows(state["monday"])
            except (MySQLError, RuntimeError) as e:
                text.setPlainText(f"Could not load the schedule: {e}")
                return
            text.setPlainText(self._week_schedule_text(state["monday"], state["rows"]))

        def copy():
            QApplication.clipboard().setText(text.toPlainText())
            show_toast("Schedule copied — paste it in WhatsApp.", "success", self)

        def whatsapp():
            QDesktopServices.openUrl(QUrl("https://wa.me/?text=" + quote(text.toPlainText())))

        def save_pdf():
            if not REPORTLAB_AVAILABLE:
                QMessageBox.critical(dialog, "Missing Dependency", "The 'reportlab' package is not installed.")
                return
            m = state["monday"]
            path, _ = QFileDialog.getSaveFileName(dialog, "Save schedule PDF", f"Schedule_{m:%Y-%m-%d}.pdf",
                                                  "PDF Files (*.pdf)")
            if not path:
                return
            if not path.lower().endswith(".pdf"):
                path += ".pdf"
            styles = getSampleStyleSheet()
            story = []
            for line in text.toPlainText().split("\n"):
                clean = line.replace("*", "")
                if not clean.strip():
                    story.append(Spacer(1, 6))
                elif line.startswith("*"):
                    story.append(Paragraph(f"<b>{clean}</b>", styles["Heading3"]))
                else:
                    story.append(Paragraph(clean.replace("&", "&amp;").replace("<", "&lt;"), styles["Normal"]))
            try:
                SimpleDocTemplate(path, pagesize=letter, leftMargin=50, rightMargin=50,
                                  topMargin=50, bottomMargin=50).build(story)
            except OSError as e:
                QMessageBox.critical(dialog, "File Error", f"Could not save the PDF:\n{e}")
                return
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))

        date_week.dateChanged.connect(lambda *_a: reload())
        btn_copy.clicked.connect(copy)
        btn_wa.clicked.connect(whatsapp)
        btn_pdf.clicked.connect(save_pdf)
        reload()
        dialog.exec()

    # ══ lucro por job ════════════════════════════════════════════════
    def _setup_profit_tab(self):
        tab = QWidget()
        tab.setObjectName("tab_job_profit")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        top = QHBoxLayout()
        top.addWidget(QLabel("Period:"))
        cmb = QComboBox()
        for label, days in (("Last 90 days", 90), ("This year", -1), ("Last 12 months", 365), ("All time", 0)):
            cmb.addItem(label, days)
        top.addWidget(cmb)
        top.addStretch(1)
        layout.addLayout(top)
        summary = QLabel()
        summary.setStyleSheet("font-size:14px; font-weight:700; color:#1C2B3A; background:transparent;")
        layout.addWidget(summary)
        table = QTableWidget(0, 9)
        table.setHorizontalHeaderLabels(["Job Code", "Customer / Company", "Days", "Revenue",
                                         "Expenses", "Materials", "Helper pay", "Profit", "Margin"])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSortingEnabled(True)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(table, 1)
        note = QLabel("Profit = revenue − expenses linked to the job − materials − helper pay "
                      "(the HELPER PAY field of each day in Job Records).")
        note.setWordWrap(True)
        note.setStyleSheet("color:#6B7C93; font-size:11px; background:transparent;")
        layout.addWidget(note)
        self.ui.tabWidget_receivables.addTab(tab, "Job Profit")
        self.ui.tab_job_profit = tab
        self._profit_widgets = (cmb, summary, table)
        cmb.currentIndexChanged.connect(lambda *_a: self.load_job_profit())
        self.ui.tabWidget_receivables.currentChanged.connect(
            lambda i: self.load_job_profit() if self.ui.tabWidget_receivables.widget(i) is tab else None)

    def load_job_profit(self):
        cmb, summary, table = self._profit_widgets
        days = cmb.currentData()
        if days == -1:
            since = date(date.today().year, 1, 1)
        elif days:
            since = date.today() - timedelta(days=days)
        else:
            since = date(1900, 1, 1)
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            helper_pay_sql = ("COALESCE(SUM(wd.HELPER_PAY), 0)"
                              if self._table_column_exists("work_days", "HELPER_PAY") else "0")
            cur.execute(f"""
                SELECT jp.ID, jp.CODE,
                       COALESCE(MAX(cl.FULL_NAME), MAX(co.COMPANY_NAME), MAX(NULLIF(ct.COMPANY_NAME, '')), MAX(ct.FULL_NAME), ''),
                       COUNT(wd.ID), COALESCE(SUM(wd.VALUE), 0), {helper_pay_sql}
                FROM job_projects jp
                JOIN work_days wd ON wd.JOB_PROJECT_ID = jp.ID AND COALESCE(wd.STATUS, '') <> 'CANCELLED'
                LEFT JOIN clients cl ON cl.ID = wd.CLIENT_ID
                LEFT JOIN companies co ON co.ID = wd.COMPANY_ID
                LEFT JOIN contractors ct ON ct.ID = wd.CONTRACTOR_ID
                WHERE wd.WORK_DATE >= %s
                GROUP BY jp.ID, jp.CODE
            """, (since,))
            jobs = cur.fetchall()
            cur.execute("""
                SELECT COALESCE(e.JOB_PROJECT_ID, wd.JOB_PROJECT_ID) AS pid, SUM(e.AMOUNT)
                FROM expenses e LEFT JOIN work_days wd ON wd.ID = e.WORK_DAY_ID
                GROUP BY pid
            """)
            expenses = {pid: float(v or 0) for pid, v in cur.fetchall() if pid}
            cur.execute("SELECT JOB_PROJECT_ID, SUM(QUANTITY * UNIT_PRICE) FROM job_materials GROUP BY JOB_PROJECT_ID")
            materials = {pid: float(v or 0) for pid, v in cur.fetchall() if pid}
            cur.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            summary.setText(f"Could not calculate profit: {e}")
            return

        table.setSortingEnabled(False)
        table.setRowCount(len(jobs))
        totals = [0.0, 0.0, 0.0]
        for r, (pid, code, who, n_days, revenue, helper_pay) in enumerate(jobs):
            revenue, helper_pay = float(revenue or 0), float(helper_pay or 0)
            exp, mat = expenses.get(pid, 0.0), materials.get(pid, 0.0)
            profit = revenue - exp - mat - helper_pay
            totals[0] += revenue
            totals[1] += exp + mat + helper_pay
            totals[2] += profit
            margin = (profit / revenue * 100) if revenue else 0.0
            cells = [(code, None), (who, None), (str(n_days), n_days), (f"${revenue:,.2f}", revenue),
                     (f"${exp:,.2f}", exp), (f"${mat:,.2f}", mat), (f"${helper_pay:,.2f}", helper_pay),
                     (f"${profit:,.2f}", profit), (f"{margin:.0f}%", margin)]
            for c, (text, sort_value) in enumerate(cells):
                item = QTableWidgetItem(text)
                if sort_value is not None:
                    item.setData(Qt.ItemDataRole.UserRole, sort_value)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if c == 7 and profit < 0:
                    item.setForeground(QColor("#C62828"))
                table.setItem(r, c, item)
        table.setSortingEnabled(True)
        table.sortItems(7, Qt.SortOrder.DescendingOrder)
        margin = (totals[2] / totals[0] * 100) if totals[0] else 0
        summary.setText(f"{len(jobs)} job codes  ·  Revenue ${totals[0]:,.2f}  ·  Costs ${totals[1]:,.2f}  ·  "
                        f"Profit ${totals[2]:,.2f} ({margin:.0f}%)")

    # ══ lembretes de invoices atrasadas ══════════════════════════════
    def _setup_reminders_button(self):
        btn = QPushButton("  Send payment reminders")
        btn.setObjectName("btn_send_payment_reminders")
        btn.setIcon(tabler_icon("send", "#37474F", 16))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip("E-mail the customers with invoices open for more than 30 days")
        btn.setStyleSheet(_SMALL_BTN)
        btn.clicked.connect(self.open_reminders_dialog)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(btn)
        self.ui.layout_receivables_invoices.insertLayout(0, row)

    def _overdue_invoices(self):
        sources = [
            ("Contractor", "contractor_invoices", "CONTRACTOR_ID", "contractors",
             "COALESCE(NULLIF(p.COMPANY_NAME, ''), p.FULL_NAME)", "COALESCE(NULLIF(p.COMPANY_EMAIL, ''), p.EMAIL)"),
            ("Company", "company_invoices", "COMPANY_ID", "companies", "p.COMPANY_NAME", "p.EMAIL"),
            ("Client", "client_invoices", "CLIENT_ID", "clients", "p.FULL_NAME", "p.EMAIL"),
        ]
        result = []
        conn = self._get_connection()
        cur = conn.cursor()
        for kind, table, fk, partner, name_sql, email_sql in sources:
            cur.execute(f"""
                SELECT i.ID, {name_sql}, {email_sql}, i.GENERATED_AT, COALESCE(i.TOTAL_AMOUNT, 0),
                       COALESCE(i.AMOUNT_PAID, 0), i.PDF_PATH, DATEDIFF(CURDATE(), i.GENERATED_AT)
                FROM {table} i LEFT JOIN {partner} p ON p.ID = i.{fk}
                WHERE i.STATUS IN ('PENDING', 'PARTIAL') AND DATEDIFF(CURDATE(), i.GENERATED_AT) > 30
                ORDER BY i.GENERATED_AT
            """)
            for iid, name, email, gen, total, paid, pdf, days in cur.fetchall():
                result.append({"kind": kind, "id": iid, "name": name or "", "email": (email or "").strip(),
                               "date": gen, "open": float(total) - float(paid), "pdf": pdf, "days": days})
        cur.close()
        conn.close()
        return result

    @staticmethod
    def _smtp_ready():
        user = (company_settings.EMAIL_SMTP_USER or "").strip()
        pw = (company_settings.EMAIL_SMTP_PASSWORD or "").strip()
        return bool(user) and "your-email" not in user and bool(pw) and pw != "your-app-password"

    def open_reminders_dialog(self):
        try:
            invoices = self._overdue_invoices()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not load the invoices:\n{e}")
            return
        if not invoices:
            QMessageBox.information(self, "No overdue invoices", "No invoice is open for more than 30 days.")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Payment reminders")
        dialog.resize(780, 620)
        layout = QVBoxLayout(dialog)
        if not self._smtp_ready():
            warn = QLabel("⚠ The e-mail account is not set up yet. Go to Settings → Email (for sending invoices) "
                          "and enter your Gmail address and App Password before sending.")
            warn.setWordWrap(True)
            warn.setStyleSheet("background:#FFF3CD; color:#8A6D00; padding:8px; border-radius:6px;")
            layout.addWidget(warn)
        table = QTableWidget(len(invoices), 6)
        table.setHorizontalHeaderLabels(["Send", "Type", "Name", "E-mail", "Open", "Days"])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        for r, inv in enumerate(invoices):
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            chk.setCheckState(Qt.CheckState.Checked if inv["email"] else Qt.CheckState.Unchecked)
            table.setItem(r, 0, chk)
            for c, v in enumerate([inv["kind"], inv["name"], inv["email"] or "no e-mail", f"${inv['open']:,.2f}",
                                   str(inv["days"])], start=1):
                table.setItem(r, c, QTableWidgetItem(v))
        layout.addWidget(table, 1)
        layout.addWidget(QLabel("Message ({name}, {invoice}, {amount}, {days}, {date} and {company} are filled in):"))
        msg = QTextEdit()
        msg.setPlainText(REMINDER_TEMPLATE)
        msg.setMinimumHeight(150)
        layout.addWidget(msg)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        btn_cancel, btn_send = QPushButton("Cancel"), QPushButton("Send reminders")
        btn_send.setObjectName("btn_send_reminders_confirm")
        buttons.addWidget(btn_cancel)
        buttons.addWidget(btn_send)
        layout.addLayout(buttons)
        btn_cancel.clicked.connect(dialog.reject)

        def send():
            chosen = [inv for r, inv in enumerate(invoices)
                      if table.item(r, 0).checkState() == Qt.CheckState.Checked and inv["email"]]
            if not chosen:
                QMessageBox.information(dialog, "Nothing selected", "Tick at least one invoice that has an e-mail.")
                return
            if not self._smtp_ready():
                QMessageBox.warning(dialog, "E-mail not set up",
                                    "Set up the e-mail account in Settings first (Gmail address + App Password).")
                return
            answer = QMessageBox.question(dialog, "Send reminders",
                                          f"Send {len(chosen)} reminder e-mail(s) now?",
                                          QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                          QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                return
            sent, failed = 0, []
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                with smtplib.SMTP(company_settings.EMAIL_SMTP_HOST, company_settings.EMAIL_SMTP_PORT, timeout=20) as server:
                    server.starttls()
                    server.login(company_settings.EMAIL_SMTP_USER, company_settings.EMAIL_SMTP_PASSWORD)
                    for inv in chosen:
                        try:
                            body = msg.toPlainText().format(
                                name=inv["name"], invoice=inv["id"], amount=f"${inv['open']:,.2f}",
                                days=inv["days"], date=_fmt_date(inv["date"]), company=company_settings.COMPANY_NAME)
                            m = EmailMessage()
                            m["Subject"] = f"Payment reminder — invoice #{inv['id']} — {company_settings.COMPANY_NAME}"
                            m["From"] = f"{company_settings.EMAIL_FROM_NAME} <{company_settings.EMAIL_SMTP_USER}>"
                            m["To"] = inv["email"]
                            m.set_content(body)
                            if inv["pdf"] and os.path.exists(inv["pdf"]):
                                with open(inv["pdf"], "rb") as f:
                                    m.add_attachment(f.read(), maintype="application", subtype="pdf",
                                                     filename=os.path.basename(inv["pdf"]))
                            server.send_message(m)
                            sent += 1
                        except Exception as e:  # um e-mail com problema não para os outros
                            failed.append(f"{inv['name']}: {e}")
            except Exception as e:
                failed.append(f"Could not connect to the e-mail server: {e}")
            finally:
                QApplication.restoreOverrideCursor()
            logging.getLogger("vl_flooring").info("payment reminders: %d sent, %d failed", sent, len(failed))
            if failed:
                QMessageBox.warning(dialog, "Reminders", f"{sent} sent.\n\nProblems:\n" + "\n".join(failed[:8]))
            else:
                dialog.accept()
                show_toast(f"{sent} reminder e-mail(s) sent.", "success", self)

        btn_send.clicked.connect(send)
        dialog.exec()
