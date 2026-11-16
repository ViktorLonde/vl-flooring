# -*- coding: utf-8 -*-
"""
Perfis de usuário (ADMIN / MANAGER / Viewer), histórico de alterações e a
verificação de jobs com dados faltando.

O que cada perfil pode fazer fica em ROLE_RULES. Para mudar uma regra é só
mexer ali:
  • ADMIN   — tudo.
  • MANAGER — cadastra e edita; não apaga, não vê Users/Settings, conciliação
              bancária nem os relatórios financeiros (P&L e 1099).
  • Viewer  — só consulta: nada é gravado (o próprio MySQL recusa gravações
              na conexão dele) e também não vê as telas acima.

Métodos da MainWindow (mixin) — veja main_.py.
"""

from app_common import *  # noqa: F401,F403

ROLE_RULES = {
    "ADMIN":   {"read_only": False, "can_delete": True,  "admin_pages": True,  "finance": True},
    "MANAGER": {"read_only": False, "can_delete": False, "admin_pages": False, "finance": False},
    "VIEWER":  {"read_only": True,  "can_delete": False, "admin_pages": False, "finance": False},
}

# Botões que gravam algo no banco (pelo começo do objectName)
_WRITE_BUTTON_PREFIXES = (
    "btn_new_", "btn_save_", "btn_delete_", "btn_update_", "btn_generate_", "btn_send_",
    "btn_add_", "btn_remove_", "btn_settings_", "btn_clean_", "btn_split_", "btn_dashboard_record_",
    "btn_home_new_", "btn_home_generate_", "btn_schedule_new_", "btn_expense_attach_",
    "btn_job_go_to_expense", "btn_bulk_", "btn_duplicate_",
)
# Botões criados por código, sem objectName: reconhecidos pelo texto
_WRITE_BUTTON_WORDS = ("save", "delete", "new", "add", "remove", "generate", "send", "record payment",
                       "import", "upload", "mark", "clean", "update", "attach", "match", "split", "pay")

_DIALOG_STYLE = """
    QDialog { background-color: #F7F9FC; }
    QLabel { color: #1C2B3A; }
    QTableWidget { background-color: #FFFFFF; color: #1C2B3A; gridline-color: #E3E8EE; }
    QHeaderView::section { background-color: #F0F4F8; color: #1C2B3A; padding: 6px;
                           border: none; border-bottom: 1px solid #D0D7DE; font-weight: 600; }
    QLineEdit, QComboBox { background-color: #FFFFFF; color: #1C2B3A; border: 1px solid #D0D7DE;
                           border-radius: 6px; padding: 4px 8px; min-height: 24px; }
    QPushButton { background-color: #EEF2F7; color: #37474F; border: 1px solid #D0D7DE;
                  border-radius: 6px; padding: 6px 14px; font-weight: 600; }
    QPushButton:hover { background-color: #E1E8F0; }
"""

_SMALL_BUTTON_STYLE = ("QPushButton { background-color: #EEF2F7; color: #37474F; border: 1px solid #D0D7DE; "
                       "border-radius: 6px; font-size: 12px; font-weight: 600; } "
                       "QPushButton:hover { background-color: #E1E8F0; }")


class PermissionsMixin:
    _current_username = None
    _current_role = None       # None = antes do login (sem restrição)
    _db_read_only = False

    # ── perfil do usuário ──────────────────────────────────────────
    def set_current_user(self, username):
        """Chamado depois do login: descobre o perfil e aplica as regras."""
        full_name, role = username, "VIEWER"
        try:
            conn = mysql.connector.connect(**self.db_config)
            cur = conn.cursor()
            cur.execute("SELECT full_name, role FROM users WHERE username=%s", (username,))
            row = cur.fetchone()
            if row:
                full_name = row[0] or username
                role = (row[1] or "VIEWER").strip().upper()
            # Garante a tabela do histórico (só precisa rodar uma vez, mas é barato)
            if role != "VIEWER":
                historico.ensure_audit_table(conn)
            cur.close()
            conn.close()
        except Exception:
            logging.getLogger("vl_flooring").exception("could not read the role of %s", username)
        if role not in ROLE_RULES:
            role = "VIEWER"  # perfil desconhecido = o mais restrito

        self._current_role = role
        self._current_username = username
        self._db_read_only = ROLE_RULES[role]["read_only"]
        self._apply_role_rules()

        first_name = (full_name or username).split()[0]
        self.ui.lbl_user.setText(f"● {first_name} · {role.title()}")
        self.ui.lbl_user.setToolTip(f"{full_name} ({username}) — {role.title()}")
        logging.getLogger("vl_flooring").info("login: %s (%s)", username, role)

    def _role_rule(self, key):
        if self._current_role is None:
            return ROLE_RULES["ADMIN"][key]
        return ROLE_RULES[self._current_role][key]

    def _apply_role_rules(self):
        rules = ROLE_RULES[self._current_role]
        ui = self.ui

        # Telas só do Admin
        for widget in (ui.btn_user, ui.btn_settings, ui.btn_reg_bank_reconciliation):
            widget.setVisible(rules["admin_pages"])
        if hasattr(self, "_btn_change_history"):
            self._btn_change_history.setVisible(rules["admin_pages"])

        # Relatórios financeiros
        for tab in [ui.tab_pnl, ui.tab_1099] + ([ui.tab_job_profit] if hasattr(ui, "tab_job_profit") else []):
            ui.tabWidget_receivables.setTabVisible(ui.tabWidget_receivables.indexOf(tab), rules["finance"])

        read_only_tip = "Your user has read-only access."
        no_delete_tip = "Only an administrator can delete."
        for btn in self.findChildren(QPushButton):
            name = btn.objectName() or ""
            text = (btn.text() or "").strip().lower()
            is_write = name.startswith(_WRITE_BUTTON_PREFIXES) or (
                not name.startswith("btn_") and any(w in text for w in _WRITE_BUTTON_WORDS))
            is_delete = name.startswith("btn_delete_") or "delete" in text
            if rules["read_only"] and is_write:
                self._block_button(btn, read_only_tip)
            elif not rules["can_delete"] and is_delete:
                self._block_button(btn, no_delete_tip)

    @staticmethod
    def _block_button(btn, tip):
        """Desativa e deixa o botão apagado (sem isso os botões coloridos
        continuavam parecendo clicáveis)."""
        from PySide6.QtWidgets import QGraphicsOpacityEffect
        btn.setEnabled(False)
        btn.setToolTip(tip)
        btn.setCursor(Qt.CursorShape.ForbiddenCursor)
        effect = QGraphicsOpacityEffect(btn)
        effect.setOpacity(0.4)
        btn.setGraphicsEffect(effect)

    # ── histórico de alterações (Admin) ────────────────────────────
    def _setup_change_history_button(self):
        btn = QPushButton("🕘  Change History")
        btn.setObjectName("btn_view_change_history")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(36)
        btn.setStyleSheet(_SMALL_BUTTON_STYLE)
        btn.clicked.connect(self.open_change_history_dialog)
        self.ui.layout_users_row_filters.addWidget(btn)
        self._btn_change_history = btn

    def open_change_history_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Change History")
        dialog.resize(1100, 620)
        dialog.setStyleSheet(_DIALOG_STYLE)
        layout = QVBoxLayout(dialog)

        filters = QHBoxLayout()
        txt_search = QLineEdit()
        txt_search.setPlaceholderText("Search user, table, record or text…")
        cmb_days = QComboBox()
        for label, days in (("Last 7 days", 7), ("Last 30 days", 30), ("Last 90 days", 90), ("Everything", 0)):
            cmb_days.addItem(label, days)
        cmb_days.setCurrentIndex(1)
        filters.addWidget(txt_search, 1)
        filters.addWidget(cmb_days)
        layout.addLayout(filters)

        table = QTableWidget(0, 6)
        table.setHorizontalHeaderLabels(["When", "User", "Action", "Table", "Record", "Details"])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.verticalHeader().setVisible(False)
        header = table.horizontalHeader()
        for col in range(5):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(table, 1)

        lbl_count = QLabel()
        layout.addWidget(lbl_count)

        action_names = {"INSERT": "Created", "REPLACE": "Saved", "UPDATE": "Changed", "DELETE": "Deleted"}

        def reload():
            sql = "SELECT created_at, username, action, table_name, record_id, details FROM audit_log WHERE 1=1"
            params = []
            days = cmb_days.currentData()
            if days:
                sql += " AND created_at >= NOW() - INTERVAL %s DAY"
                params.append(days)
            text = txt_search.text().strip()
            if text:
                like = f"%{text}%"
                sql += (" AND (username LIKE %s OR table_name LIKE %s OR record_id LIKE %s"
                        " OR details LIKE %s)")
                params += [like, like, like, like]
            sql += " ORDER BY id DESC LIMIT 1000"
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                cur.execute(sql, params)
                rows = cur.fetchall()
                cur.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                lbl_count.setText(f"Could not load the history: {e}")
                return
            table.setRowCount(len(rows))
            for r, (when, user, action, tbl, rec, details) in enumerate(rows):
                values = [when.strftime("%m/%d/%Y %H:%M") if when else "", user or "",
                          action_names.get(action, action), tbl or "", rec or "", details or ""]
                for c, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    if c == 5:
                        item.setToolTip(value)
                    table.setItem(r, c, item)
            lbl_count.setText(f"{len(rows)} change(s)" + (" — showing the latest 1000" if len(rows) == 1000 else ""))

        txt_search.textChanged.connect(lambda _t: reload())
        cmb_days.currentIndexChanged.connect(lambda _i: reload())
        reload()
        dialog.exec()

    # ── jobs com dados faltando ────────────────────────────────────
    def _setup_incomplete_jobs_button(self):
        """Coloca o botão "Incomplete Jobs" ao lado de "Clean Empty Job Codes"."""
        layout = self.ui.layout_jobs_left_panel
        clean_btn = self.ui.btn_clean_empty_job_codes
        index = layout.indexOf(clean_btn)
        btn = QPushButton("⚠  Incomplete Jobs")
        btn.setObjectName("btn_view_incomplete_jobs")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(34)
        btn.setStyleSheet(_SMALL_BUTTON_STYLE)
        btn.clicked.connect(self.open_incomplete_jobs_dialog)
        row = QHBoxLayout()
        row.setSpacing(8)
        layout.removeWidget(clean_btn)
        row.addWidget(clean_btn, 1)
        row.addWidget(btn, 1)
        layout.insertLayout(index, row)

    def open_incomplete_jobs_dialog(self):
        """Lista os jobs sem Job Code, cliente, endereço ou valor. Dois cliques
        abre o job no formulário pra completar."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT wd.ID, wd.WORK_DATE, COALESCE(ct.COMPANY_NAME, ct.FULL_NAME, ''), COALESCE(jp.CODE, ''),
                       wd.CLIENT_ID IS NULL, jp.CODE IS NULL OR jp.CODE = '',
                       COALESCE(wd.JOB_ADDRESS, '') = '', COALESCE(wd.VALUE, 0) = 0
                FROM work_days wd
                LEFT JOIN job_projects jp ON jp.ID = wd.JOB_PROJECT_ID
                LEFT JOIN contractors ct ON ct.ID = wd.CONTRACTOR_ID
                WHERE wd.CLIENT_ID IS NULL OR wd.JOB_PROJECT_ID IS NULL
                   OR COALESCE(wd.JOB_ADDRESS, '') = '' OR COALESCE(wd.VALUE, 0) = 0
                ORDER BY wd.WORK_DATE DESC, wd.ID DESC
            """)
            rows = cur.fetchall()
            cur.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not check the jobs:\n{e}")
            return
        if not rows:
            QMessageBox.information(self, "All complete", "Every job has a Job Code, client, address and value.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Incomplete Jobs")
        dialog.resize(820, 560)
        dialog.setStyleSheet(_DIALOG_STYLE)
        layout = QVBoxLayout(dialog)
        counts = [sum(1 for r in rows if r[i]) for i in (4, 5, 6, 7)]
        summary = QLabel(
            f"<b>{len(rows)}</b> job(s) with missing information — "
            f"no client: <b>{counts[0]}</b> · no Job Code: <b>{counts[1]}</b> · "
            f"no address: <b>{counts[2]}</b> · no value: <b>{counts[3]}</b><br>"
            "Double-click a job to open it in the form.")
        layout.addWidget(summary)

        table = QTableWidget(len(rows), 5)
        table.setHorizontalHeaderLabels(["ID", "Work Date", "Contractor", "Job Code", "Missing"])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        for r, (job_id, work_date, contractor, code, no_client, no_code, no_addr, no_value) in enumerate(rows):
            missing = [label for flag, label in ((no_code, "Job Code"), (no_client, "Client"),
                                                 (no_addr, "Address"), (no_value, "Value")) if flag]
            values = [str(job_id), work_date.strftime("%m/%d/%Y") if work_date else "", contractor, code,
                      ", ".join(missing)]
            for c, value in enumerate(values):
                item = QTableWidgetItem(value)
                if c == 0:
                    item.setData(Qt.ItemDataRole.UserRole, (job_id, work_date))
                table.setItem(r, c, item)
        layout.addWidget(table, 1)

        def open_selected(row, _col):
            job_id, work_date = table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            dialog.accept()
            self._open_job_by_id(job_id, work_date)

        table.cellDoubleClicked.connect(open_selected)
        dialog.exec()

    def _open_job_by_id(self, job_id, work_date):
        """Vai pra Job Records e seleciona o job, ajustando os filtros pra
        que ele apareça na lista."""
        self._go_to_page(1, self.ui.btn_jobs)
        ui = self.ui
        ui.tabWidget_jobs.setCurrentWidget(ui.tab_jobs_master)
        ui.txt_search_jobs.blockSignals(True)
        ui.txt_search_jobs.clear()
        ui.txt_search_jobs.blockSignals(False)
        ui.cmb_filter_status.setCurrentIndex(0)  # "All Status"
        if work_date:
            qdate = QDate(work_date.year, work_date.month, work_date.day)
            if ui.date_filter_from.date() > qdate:
                ui.date_filter_from.setDate(qdate)
            if ui.date_filter_to.date() < qdate:
                ui.date_filter_to.setDate(qdate)
        self.load_work_days()
        table = ui.table_work_days
        for r in range(table.rowCount()):
            item = table.item(r, 0)
            if item and item.text() == str(job_id):
                table.selectRow(r)
                table.scrollToItem(item)
                return
        QMessageBox.information(self, "Job not found", f"Job #{job_id} is not in the list with the current filters.")
