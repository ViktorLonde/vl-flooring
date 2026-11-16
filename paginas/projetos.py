# -*- coding: utf-8 -*-
"""
Projetos (Job Codes): Projects Dashboard, visão do projeto e limpeza de
Job Codes vazios.

Métodos da MainWindow (mixin) — veja main_.py.
"""

from app_common import *  # noqa: F401,F403


class ProjectsMixin:
    def _setup_projects_dashboard_feature(self):
        """Cria, em tempo de execução (sem editar o .ui), o botão 'Projects
        Dashboard' no submenu Registrations e o painel 'Projects Overview'
        (gráfico de rosca com os projetos por status + 2 KPIs extras) no
        final da página Home — mesmo padrão de sempre: QDialog/QWidget
        montado 100% em Python, nunca mexendo no main_window_vl_flooring_6.ui
        nem no ui_main_window_vl_flooring.py compilado."""
        self.ui.btn_reg_projects_dashboard = QPushButton(self.ui.frame_registrations_submenu)
        self.ui.btn_reg_projects_dashboard.setObjectName(u"btn_reg_projects_dashboard")
        self.ui.btn_reg_projects_dashboard.setCheckable(False)
        self.ui.btn_reg_projects_dashboard.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ui.layout_registrations_submenu.addWidget(self.ui.btn_reg_projects_dashboard)

        # ── Painel "Projects Overview" no final da Home ────────────────
        self.ui.frame_projects_overview = QFrame(self.ui.pg_home)
        self.ui.frame_projects_overview.setObjectName(u"frame_projects_overview")
        self.ui.frame_projects_overview.setStyleSheet(
            "#frame_projects_overview { background-color:#FFFFFF; border:1px solid #E3E8EE; border-radius:10px; }"
            "#frame_projects_overview QLabel { background:transparent; }"
        )
        overview_layout = QVBoxLayout(self.ui.frame_projects_overview)

        title_row = QHBoxLayout()
        lbl_title = QLabel("📊 Projects Overview")
        lbl_title.setStyleSheet("font-weight:700; font-size:14px; color:#1C2B3A;")
        title_row.addWidget(lbl_title)
        title_row.addStretch()
        btn_open_dashboard = QPushButton("Open Full Dashboard")
        btn_open_dashboard.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_open_dashboard.setStyleSheet(
            "QPushButton { background-color:#1565C0; color:#FFFFFF; border:none; "
            "border-radius:5px; padding:5px 12px; font-weight:600; } "
            "QPushButton:hover { background-color:#1976D2; }"
        )
        btn_open_dashboard.clicked.connect(self.open_projects_dashboard_dialog)
        title_row.addWidget(btn_open_dashboard)
        overview_layout.addLayout(title_row)

        content_row = QHBoxLayout()
        self.ui.donut_projects_status = _DonutChartWidget(self.ui.frame_projects_overview)
        self.ui.donut_projects_status.setMinimumSize(150, 150)
        self.ui.donut_projects_status.setMaximumSize(150, 150)
        content_row.addWidget(self.ui.donut_projects_status)

        self.ui.layout_projects_status_legend = QVBoxLayout()
        content_row.addLayout(self.ui.layout_projects_status_legend, 1)

        kpi_col = QVBoxLayout()
        self.ui.lbl_home_compliance_kpi = QLabel("—")
        self.ui.lbl_home_compliance_kpi.setStyleSheet("font-weight:700; font-size:18px; color:#E65100;")
        kpi_compliance_title = QLabel("Compliance due (30d)")
        kpi_compliance_title.setStyleSheet("color:#6B7C93; font-size:11px;")
        kpi_col.addWidget(self.ui.lbl_home_compliance_kpi)
        kpi_col.addWidget(kpi_compliance_title)

        self.ui.lbl_home_bank_kpi = QLabel("—")
        self.ui.lbl_home_bank_kpi.setStyleSheet("font-weight:700; font-size:18px; color:#1565C0;")
        kpi_bank_title = QLabel("Unmatched bank txns")
        kpi_bank_title.setStyleSheet("color:#6B7C93; font-size:11px;")
        kpi_col.addWidget(self.ui.lbl_home_bank_kpi)
        kpi_col.addWidget(kpi_bank_title)
        kpi_col.addStretch()
        content_row.addLayout(kpi_col)

        overview_layout.addLayout(content_row)
        # Dentro da área com rolagem (antes ficava fixo embaixo e cortava o
        # gráfico de receita e a lista de jobs recentes)
        self.ui.layout_home_page.addWidget(self.ui.frame_projects_overview)

    def _classify_project_status(self, total_days, completed_days, cancelled_days):
        """Deriva um status de projeto (Active/Completed/Cancelled/No Jobs
        Yet) a partir dos jobs (work_days) ligados ao Job Code —
        job_projects.STATUS sempre fica 'ACTIVE' desde a criação (nunca é
        atualizado em nenhum lugar do código hoje), então quem manda de
        verdade é o conjunto de jobs daquele projeto."""
        total_days = total_days or 0
        completed_days = completed_days or 0
        cancelled_days = cancelled_days or 0
        if total_days == 0:
            return "NO_JOBS"
        if completed_days == total_days:
            return "COMPLETED"
        if cancelled_days == total_days:
            return "CANCELLED"
        return "ACTIVE"

    def _fetch_projects_overview_rows(self):
        """Busca cada projeto (job_projects) com o total de dias de trabalho,
        quantos estão concluídos/cancelados, orçamento (se a coluna já
        existir — Fase 3) e receita total — usado tanto pelo Projects
        Dashboard quanto pelo gráfico de rosca da Home. Retorna
        (lista_de_dicts, None) ou (None, mensagem_de_erro)."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    SELECT jp.ID, jp.CODE, jp.PROJECT_TYPE,
                           COALESCE(cl.FULL_NAME, '—') AS client_name,
                           COALESCE(co.COMPANY_NAME, '—') AS company_name,
                           COALESCE(c.COMPANY_NAME, c.FULL_NAME, '—') AS contractor_name,
                           COALESCE(jp.JOB_ADDRESS, '—') AS job_address,
                           jp.BUDGET_AMOUNT,
                           COUNT(wd.ID) AS total_days,
                           SUM(CASE WHEN wd.STATUS = 'COMPLETED' THEN 1 ELSE 0 END) AS completed_days,
                           SUM(CASE WHEN wd.STATUS = 'CANCELLED' THEN 1 ELSE 0 END) AS cancelled_days,
                           COALESCE(SUM(wd.VALUE), 0) AS total_value
                    FROM job_projects jp
                    LEFT JOIN clients cl ON cl.ID = jp.CLIENT_ID
                    LEFT JOIN companies co ON co.ID = jp.COMPANY_ID
                    LEFT JOIN contractors c ON c.ID = jp.CONTRACTOR_ID
                    LEFT JOIN work_days wd ON wd.JOB_PROJECT_ID = jp.ID
                    GROUP BY jp.ID, jp.CODE, jp.PROJECT_TYPE, cl.FULL_NAME, co.COMPANY_NAME,
                             c.COMPANY_NAME, c.FULL_NAME, jp.JOB_ADDRESS, jp.BUDGET_AMOUNT
                    ORDER BY jp.ID DESC
                    """
                )
            except MySQLError:
                conn.rollback()
                cursor.execute(
                    """
                    SELECT jp.ID, jp.CODE, jp.PROJECT_TYPE,
                           COALESCE(cl.FULL_NAME, '—') AS client_name,
                           COALESCE(co.COMPANY_NAME, '—') AS company_name,
                           COALESCE(c.COMPANY_NAME, c.FULL_NAME, '—') AS contractor_name,
                           COALESCE(jp.JOB_ADDRESS, '—') AS job_address,
                           NULL AS budget_amount,
                           COUNT(wd.ID) AS total_days,
                           SUM(CASE WHEN wd.STATUS = 'COMPLETED' THEN 1 ELSE 0 END) AS completed_days,
                           SUM(CASE WHEN wd.STATUS = 'CANCELLED' THEN 1 ELSE 0 END) AS cancelled_days,
                           COALESCE(SUM(wd.VALUE), 0) AS total_value
                    FROM job_projects jp
                    LEFT JOIN clients cl ON cl.ID = jp.CLIENT_ID
                    LEFT JOIN companies co ON co.ID = jp.COMPANY_ID
                    LEFT JOIN contractors c ON c.ID = jp.CONTRACTOR_ID
                    LEFT JOIN work_days wd ON wd.JOB_PROJECT_ID = jp.ID
                    GROUP BY jp.ID, jp.CODE, jp.PROJECT_TYPE, cl.FULL_NAME, co.COMPANY_NAME,
                             c.COMPANY_NAME, c.FULL_NAME, jp.JOB_ADDRESS
                    ORDER BY jp.ID DESC
                    """
                )
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            return None, str(e)

        result = []
        for (jp_id, code, ptype, client_name, company_name, contractor_name, address,
             budget, total_days, completed_days, cancelled_days, total_value) in rows:
            status = self._classify_project_status(total_days, completed_days, cancelled_days)
            progress_pct = int(round((completed_days or 0) / total_days * 100)) if total_days else 0
            result.append({
                "ID": jp_id, "CODE": code, "PROJECT_TYPE": ptype,
                "CLIENT": client_name, "COMPANY": company_name, "CONTRACTOR": contractor_name,
                "ADDRESS": address, "BUDGET": budget, "TOTAL_DAYS": total_days or 0,
                "COMPLETED_DAYS": completed_days or 0, "CANCELLED_DAYS": cancelled_days or 0,
                "TOTAL_VALUE": float(total_value or 0), "STATUS": status, "PROGRESS_PCT": progress_pct,
            })
        return result, None

    def _refresh_projects_overview_widget(self):
        """Atualiza o gráfico de rosca + legenda + os 2 KPIs extras do
        painel 'Projects Overview' na Home. Chamado toda vez que a Home é
        carregada (load_home_dashboard) — se não der pra buscar os dados
        (ex: sem conexão), só mostra o gráfico vazio em vez de travar."""
        rows, error = self._fetch_projects_overview_rows()
        if error is not None:
            rows = []

        counts = {"ACTIVE": 0, "COMPLETED": 0, "CANCELLED": 0, "NO_JOBS": 0}
        for r in rows:
            counts[r["STATUS"]] = counts.get(r["STATUS"], 0) + 1

        segments = [
            (PROJECT_STATUS_LABELS[key], counts[key], PROJECT_STATUS_COLORS[key])
            for key in ("ACTIVE", "COMPLETED", "NO_JOBS", "CANCELLED")
        ]
        self.ui.donut_projects_status.set_data(segments)

        legend_layout = self.ui.layout_projects_status_legend
        while legend_layout.count():
            child = legend_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                sub = child.layout()
                while sub.count():
                    sub_child = sub.takeAt(0)
                    if sub_child.widget():
                        sub_child.widget().deleteLater()

        for key in ("ACTIVE", "COMPLETED", "NO_JOBS", "CANCELLED"):
            row = QHBoxLayout()
            dot = QLabel("●")
            dot.setStyleSheet(f"color:{PROJECT_STATUS_COLORS[key].name()}; font-size:14px;")
            row.addWidget(dot)
            lbl = QLabel(f"{PROJECT_STATUS_LABELS[key]}: {counts[key]}")
            lbl.setStyleSheet("color:#4A5568; font-size:12px;")
            row.addWidget(lbl)
            row.addStretch()
            legend_layout.addLayout(row)
        legend_layout.addStretch()

        self.ui.lbl_home_compliance_kpi.setText(str(getattr(self, "_compliance_due_soon", 0)))

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM bank_transactions WHERE STATUS = 'UNMATCHED'")
            unmatched = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            self.ui.lbl_home_bank_kpi.setText(str(unmatched or 0))
        except (MySQLError, RuntimeError):
            self.ui.lbl_home_bank_kpi.setText("—")

    def open_projects_dashboard_dialog(self):
        """Painel geral dos projetos: uma linha por Job Code, com status
        calculado a partir dos jobs (work_days) ligados a ele (Active/
        Completed/Cancelled/No Jobs Yet), barra de progresso, receita total
        e orçamento — inspirado em painéis de 'todos os projetos numa lista
        só, com abas de status e progresso' que ferramentas de gestão de
        obra costumam ter. Dá pra abrir a ficha completa do projeto (mesma
        tela de sempre, open_project_view_dialog) direto daqui."""
        rows, error = self._fetch_projects_overview_rows()
        if error is not None:
            QMessageBox.critical(self, "Database Error", f"Could not load projects:\n{error}")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Projects Dashboard")
        dialog.resize(980, 620)
        dialog.setStyleSheet("""
            QTableWidget { background-color: #FFFFFF; color: #1C2B3A; gridline-color: #E3E8EE; }
            QHeaderView::section { background-color: #F0F4F8; color: #1C2B3A; padding: 6px; border: none; font-weight: 600; }
        """)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(
            "<b>Projects Dashboard</b> — every Job Code, with status figured out from its jobs "
            "(Pending/Started/In Progress → Active), progress and revenue. Double-click a row "
            "(or select it and click 'Open Project') for the full project view."
        ))

        top_row = QHBoxLayout()
        tabs_holder = QHBoxLayout()
        tab_buttons = {}
        filter_state = {"status": None}

        def make_tab_button(label, status_key):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setAutoDefault(False)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                "QPushButton { padding: 6px 14px; border: 1px solid #D7DEE7; border-radius: 6px; "
                "background-color: #FFFFFF; color: #4A5568; font-weight: 600; } "
                "QPushButton:checked { background-color: #1565C0; color: #FFFFFF; border-color: #1565C0; }"
            )
            tab_buttons[status_key] = btn
            tabs_holder.addWidget(btn)

        make_tab_button("All", None)
        make_tab_button("Active", "ACTIVE")
        make_tab_button("Completed", "COMPLETED")
        make_tab_button("No Jobs Yet", "NO_JOBS")
        make_tab_button("Cancelled", "CANCELLED")
        tab_buttons[None].setChecked(True)
        top_row.addLayout(tabs_holder)
        top_row.addStretch()

        txt_search = QLineEdit()
        txt_search.setPlaceholderText("Search code, client, address...")
        txt_search.setMaximumWidth(240)
        top_row.addWidget(txt_search)
        layout.addLayout(top_row)

        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels(
            ["Code", "Client / Company / Contractor", "Address", "Status", "Progress", "Jobs", "Revenue", "Budget"]
        )
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(table, 1)

        row_codes = {}

        def matches_search(row, text):
            if not text:
                return True
            text = text.lower()
            haystack = " ".join([
                str(row["CODE"] or ""), str(row["CLIENT"] or ""), str(row["COMPANY"] or ""),
                str(row["CONTRACTOR"] or ""), str(row["ADDRESS"] or ""),
            ]).lower()
            return text in haystack

        def reload_table():
            status_filter = filter_state["status"]
            search_text = txt_search.text().strip()
            filtered = [
                r for r in rows
                if (status_filter is None or r["STATUS"] == status_filter) and matches_search(r, search_text)
            ]

            table.setRowCount(len(filtered))
            row_codes.clear()
            for i, r in enumerate(filtered):
                who = r["CLIENT"] if r["CLIENT"] != "—" else (r["COMPANY"] if r["COMPANY"] != "—" else r["CONTRACTOR"])

                item_code = QTableWidgetItem(r["CODE"])
                item_code.setFlags(item_code.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(i, 0, item_code)

                item_who = QTableWidgetItem(who)
                item_who.setFlags(item_who.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(i, 1, item_who)

                item_addr = QTableWidgetItem(r["ADDRESS"])
                item_addr.setFlags(item_addr.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(i, 2, item_addr)

                item_status = QTableWidgetItem(PROJECT_STATUS_LABELS.get(r["STATUS"], r["STATUS"]))
                item_status.setFlags(item_status.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item_status.setBackground(PROJECT_STATUS_COLORS.get(r["STATUS"], QColor("#EEEEEE")).lighter(170))
                table.setItem(i, 3, item_status)

                progress_bar = QProgressBar()
                progress_bar.setRange(0, 100)
                progress_bar.setValue(r["PROGRESS_PCT"])
                progress_bar.setTextVisible(True)
                progress_bar.setFormat(f"{r['PROGRESS_PCT']}%")
                progress_bar.setStyleSheet(
                    "QProgressBar { border: 1px solid #D7DEE7; border-radius: 4px; background: #F0F4F8; "
                    "text-align: center; } QProgressBar::chunk { background-color: #2E7D32; border-radius: 4px; }"
                )
                table.setCellWidget(i, 4, progress_bar)

                item_jobs = QTableWidgetItem(str(r["TOTAL_DAYS"]))
                item_jobs.setFlags(item_jobs.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(i, 5, item_jobs)

                item_rev = QTableWidgetItem(f"${r['TOTAL_VALUE']:,.2f}")
                item_rev.setFlags(item_rev.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(i, 6, item_rev)

                budget_text = f"${float(r['BUDGET']):,.2f}" if r["BUDGET"] is not None else "—"
                item_budget = QTableWidgetItem(budget_text)
                item_budget.setFlags(item_budget.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(i, 7, item_budget)

                row_codes[i] = r["CODE"]

        def select_tab(status_key):
            for key, btn in tab_buttons.items():
                btn.setChecked(key == status_key)
            filter_state["status"] = status_key
            reload_table()

        for key, btn in tab_buttons.items():
            btn.clicked.connect(lambda checked, k=key: select_tab(k))

        txt_search.textChanged.connect(reload_table)

        def open_selected_project():
            current = table.currentRow()
            if current < 0:
                QMessageBox.information(dialog, "No selection", "Select a project from the list first.")
                return
            code = row_codes.get(current)
            if not code:
                return
            dialog.close()
            self.open_project_view_dialog(job_code=code)

        table.cellDoubleClicked.connect(lambda r, c: open_selected_project())

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_open = QPushButton("Open Project")
        btn_open.setAutoDefault(False)
        btn_open.clicked.connect(open_selected_project)
        btn_close = QPushButton("Close")
        btn_close.setAutoDefault(False)
        btn_close.clicked.connect(dialog.close)
        btn_row.addWidget(btn_open)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

        reload_table()
        dialog.exec()

    def open_clean_empty_job_codes_dialog(self):
        """Acha os Job Codes que não têm nenhum job (work_days) nem material
        (job_materials) ligado a eles — "códigos fantasma" criados sem querer
        antes da validação existir — e deixa escolher quais apagar."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT jp.ID, jp.CODE, jp.CREATED_AT
                FROM job_projects jp
                LEFT JOIN work_days wd ON wd.JOB_PROJECT_ID = jp.ID
                LEFT JOIN job_materials jm ON jm.JOB_PROJECT_ID = jp.ID
                WHERE wd.ID IS NULL AND jm.ID IS NULL
                ORDER BY jp.CREATED_AT DESC
                """
            )
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not check job codes:\n{e}")
            return

        if not rows:
            QMessageBox.information(self, "All Clean", "No empty Job Codes found — everything is linked to a job.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Clean Empty Job Codes")
        dialog.resize(480, 520)
        dialog.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                color: #1C2B3A;
                gridline-color: #E3E8EE;
            }
            QHeaderView::section {
                background-color: #F0F4F8;
                color: #1C2B3A;
                padding: 6px;
                border: none;
                font-weight: 600;
            }
        """)
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel(
            f"Found {len(rows)} Job Code(s) with no jobs or materials linked. "
            f"Select which ones to delete — this cannot be undone."
        ))

        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["✓", "Code", "Created At"])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.setColumnWidth(0, 30)
        table.setColumnWidth(2, 140)
        table.setRowCount(len(rows))

        row_ids = {}
        for row_idx, (jp_id, code, created_at) in enumerate(rows):
            chk_item = QTableWidgetItem()
            chk_item.setFlags((chk_item.flags() | Qt.ItemFlag.ItemIsUserCheckable) & ~Qt.ItemFlag.ItemIsEditable)
            chk_item.setCheckState(Qt.CheckState.Checked)
            table.setItem(row_idx, 0, chk_item)

            created_str = created_at.strftime("%m/%d/%Y %I:%M %p") if created_at else "—"
            for c, text in enumerate([str(code), created_str], start=1):
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(row_idx, c, item)

            row_ids[row_idx] = jp_id

        layout.addWidget(table)

        bottom_row = QHBoxLayout()
        bottom_row.addStretch()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setAutoDefault(False)
        btn_delete = QPushButton("Delete Selected")
        btn_delete.setAutoDefault(False)
        btn_delete.setStyleSheet(
            "QPushButton { background-color: #C62828; color: #FFFFFF; border: none; "
            "border-radius: 6px; padding: 8px 14px; font-weight: 600; } "
            "QPushButton:hover { background-color: #E53935; }"
        )
        bottom_row.addWidget(btn_cancel)
        bottom_row.addWidget(btn_delete)
        layout.addLayout(bottom_row)

        def delete_selected():
            selected_ids = [
                row_ids[r] for r in range(table.rowCount())
                if table.item(r, 0).checkState() == Qt.CheckState.Checked
            ]
            if not selected_ids:
                QMessageBox.information(dialog, "No selection", "Select at least one Job Code to delete.")
                return

            confirm = QMessageBox.question(
                dialog, "Confirm delete",
                f"Delete {len(selected_ids)} empty Job Code(s)? This cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return

            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                placeholders = ", ".join(["%s"] * len(selected_ids))
                cursor.execute(f"DELETE FROM job_projects WHERE ID IN ({placeholders})", selected_ids)
                conn.commit()
                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not delete job codes:\n{e}")
                return

            QMessageBox.information(dialog, "Deleted", f"{len(selected_ids)} Job Code(s) deleted.")
            self._refresh_job_code_completer()
            dialog.accept()

        btn_cancel.clicked.connect(dialog.reject)
        btn_delete.clicked.connect(delete_selected)
        dialog.exec()

    def open_project_view_dialog(self, job_code=None):
        """Abre uma 'ficha do projeto': mostra todos os Jobs (work_days) e os
        materiais gastos sob um Job Code. Se `job_code` já vier preenchido
        (ex: chamado a partir do Projects Dashboard, com
        self.open_project_view_dialog(job_code="...")), usa ele direto —
        senão (comportamento original, botão "View Project" da lista de
        Work Days) lê da linha selecionada na tabela."""
        if not job_code:
            table = self.ui.table_work_days
            selected = table.currentRow()
            if selected < 0:
                QMessageBox.information(self, "No selection", "Select a job from the list first.")
                return

            job_code = table.item(selected, 15).text().strip()
            if not job_code or job_code == "—":
                QMessageBox.information(self, "No Job Code",
                                         "This job doesn't have a Job Code assigned yet.")
                return

        budget_amount = None
        expense_rows = []
        has_expense_link_column = True
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            try:
                cursor.execute(
                    """
                    SELECT jp.ID, jp.PROJECT_TYPE, COALESCE(cl.FULL_NAME, '—'),
                           COALESCE(co.COMPANY_NAME, '—'), COALESCE(c.COMPANY_NAME, c.FULL_NAME, '—'),
                           COALESCE(jp.JOB_ADDRESS, '—'), jp.BUDGET_AMOUNT
                    FROM job_projects jp
                    LEFT JOIN clients cl ON cl.ID = jp.CLIENT_ID
                    LEFT JOIN companies co ON co.ID = jp.COMPANY_ID
                    LEFT JOIN contractors c ON c.ID = jp.CONTRACTOR_ID
                    WHERE jp.CODE = %s
                    """,
                    (job_code,),
                )
                project_row = cursor.fetchone()
                has_budget_column = True
            except MySQLError:
                # migration_fase3_budget_expenses.sql ainda não rodou nesse banco —
                # carrega sem a coluna de orçamento em vez de travar a tela.
                cursor.execute(
                    """
                    SELECT jp.ID, jp.PROJECT_TYPE, COALESCE(cl.FULL_NAME, '—'),
                           COALESCE(co.COMPANY_NAME, '—'), COALESCE(c.COMPANY_NAME, c.FULL_NAME, '—'),
                           COALESCE(jp.JOB_ADDRESS, '—')
                    FROM job_projects jp
                    LEFT JOIN clients cl ON cl.ID = jp.CLIENT_ID
                    LEFT JOIN companies co ON co.ID = jp.COMPANY_ID
                    LEFT JOIN contractors c ON c.ID = jp.CONTRACTOR_ID
                    WHERE jp.CODE = %s
                    """,
                    (job_code,),
                )
                project_row = cursor.fetchone()
                has_budget_column = False

            if not project_row:
                cursor.close()
                conn.close()
                QMessageBox.warning(self, "Not Found", f"Job Code '{job_code}' was not found.")
                return

            if has_budget_column:
                (job_project_id, project_type, client_name, company_name,
                 contractor_name, job_address, budget_amount) = project_row
            else:
                (job_project_id, project_type, client_name, company_name,
                 contractor_name, job_address) = project_row

            cursor.execute(
                "SELECT COUNT(DISTINCT WORK_DATE), MIN(WORK_DATE), MAX(WORK_DATE), COALESCE(SUM(VALUE), 0) "
                "FROM work_days WHERE JOB_PROJECT_ID = %s",
                (job_project_id,),
            )
            days_count, min_date, max_date, total_value = cursor.fetchone()

            cursor.execute(
                """
                SELECT wd.WORK_DATE, COALESCE(c.COMPANY_NAME, c.FULL_NAME, '—'), wd.VALUE, wd.STATUS
                FROM work_days wd
                LEFT JOIN contractors c ON c.ID = wd.CONTRACTOR_ID
                WHERE wd.JOB_PROJECT_ID = %s
                ORDER BY wd.WORK_DATE
                """,
                (job_project_id,),
            )
            job_rows = cursor.fetchall()

            cursor.execute(
                """
                SELECT COALESCE(p.NAME, '—'), jm.QUANTITY, COALESCE(p.UNIT, ''), jm.UNIT_PRICE
                FROM job_materials jm
                LEFT JOIN products p ON p.ID = jm.PRODUCT_ID
                WHERE jm.JOB_PROJECT_ID = %s
                ORDER BY jm.ID
                """,
                (job_project_id,),
            )
            material_rows = cursor.fetchall()

            try:
                cursor.execute(
                    "SELECT EXPENSE_DATE, CATEGORY, DESCRIPTION, AMOUNT "
                    "FROM expenses WHERE JOB_PROJECT_ID = %s ORDER BY EXPENSE_DATE",
                    (job_project_id,),
                )
                expense_rows = cursor.fetchall()
            except MySQLError:
                # migration_fase3_budget_expenses.sql ainda não rodou nesse banco.
                has_expense_link_column = False

            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not load project:\n{e}")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Project {job_code}")
        dialog.resize(600, 780)
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel(f"<b>Job Code:</b> {job_code}"))
        layout.addWidget(QLabel(f"<b>Client:</b> {client_name} &nbsp;&nbsp; <b>Company:</b> {company_name}"))
        layout.addWidget(QLabel(f"<b>Contractor:</b> {contractor_name} &nbsp;&nbsp; <b>Address:</b> {job_address}"))
        layout.addWidget(QLabel(""))

        days_count = days_count or 0
        if days_count:
            span_days = (max_date - min_date).days + 1 if min_date and max_date else days_count
            gaps = span_days - days_count
            gap_text = f" ({gaps} day{'s' if gaps != 1 else ''} with no work)" if gaps > 0 else ""
            period_text = (
                f"{min_date.strftime('%m/%d/%Y')} to {max_date.strftime('%m/%d/%Y')}{gap_text}"
                if min_date and max_date else ""
            )
        else:
            period_text = "No days recorded yet"
        lbl_days = QLabel(f"<span style='font-size:18px; font-weight:800; color:#1565C0;'>"
                           f"🗓 {days_count} day{'s' if days_count != 1 else ''} worked</span><br/>{period_text}")
        layout.addWidget(lbl_days)
        layout.addWidget(QLabel(f"<b>Total Value:</b> ${float(total_value or 0):,.2f}"))
        layout.addWidget(QLabel(""))

        layout.addWidget(QLabel("<b>Jobs Under This Code</b>"))
        table_jobs = QTableWidget()
        table_jobs.setColumnCount(4)
        table_jobs.setHorizontalHeaderLabels(["Date", "Contractor", "Value", "Status"])
        table_jobs.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table_jobs.horizontalHeader().setStretchLastSection(True)
        table_jobs.setMaximumHeight(180)
        table_jobs.setRowCount(len(job_rows))
        for r, (wdate, cname, val, status) in enumerate(job_rows):
            date_str = wdate.strftime("%m/%d/%Y") if isinstance(wdate, date) else str(wdate)
            for c, text in enumerate([date_str, cname, f"${float(val or 0):,.2f}",
                                       JOB_STATUS_LABELS.get(status, status)]):
                table_jobs.setItem(r, c, QTableWidgetItem(text))
        layout.addWidget(table_jobs)

        layout.addWidget(QLabel("<b>Materials Used</b>"))
        table_materials = QTableWidget()
        table_materials.setColumnCount(3)
        table_materials.setHorizontalHeaderLabels(["Product", "Qty", "Unit"])
        table_materials.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table_materials.horizontalHeader().setStretchLastSection(True)
        table_materials.setMaximumHeight(140)
        table_materials.setRowCount(len(material_rows))
        material_cost_total = 0.0
        for r, (pname, qty, unit, unit_price) in enumerate(material_rows):
            qty = float(qty or 0)
            material_cost_total += qty * float(unit_price or 0)
            for c, text in enumerate([pname, f"{qty:g}", unit]):
                table_materials.setItem(r, c, QTableWidgetItem(text))
        layout.addWidget(table_materials)

        if project_type == "PRIVATE":
            layout.addWidget(QLabel(f"<b>Total Material Cost:</b> ${material_cost_total:,.2f}"))

        # ── Expenses vinculadas a este projeto (job_costing) ──────────
        expense_total = sum(float(amount or 0) for (_edate, _cat, _desc, amount) in expense_rows)
        table_expenses_linked = None
        if has_expense_link_column:
            layout.addWidget(QLabel("<b>Expenses Linked to This Project</b>"))
            table_expenses_linked = QTableWidget()
            table_expenses_linked.setColumnCount(4)
            table_expenses_linked.setHorizontalHeaderLabels(["Date", "Category", "Description", "Amount"])
            table_expenses_linked.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            table_expenses_linked.horizontalHeader().setStretchLastSection(True)
            table_expenses_linked.setMaximumHeight(140)
            table_expenses_linked.setRowCount(len(expense_rows))
            for r, (edate, category, description, amount) in enumerate(expense_rows):
                date_str = edate.strftime("%m/%d/%Y") if isinstance(edate, date) else str(edate or "")
                values = [date_str, category or "", description or "", f"${float(amount or 0):,.2f}"]
                for c, text in enumerate(values):
                    table_expenses_linked.setItem(r, c, QTableWidgetItem(text))
            layout.addWidget(table_expenses_linked)
            if not expense_rows:
                lbl_no_expenses = QLabel(
                    "No expenses linked to this project yet — pick this Job Code in the "
                    "'Job Code (optional)' field on the Expenses tab to link one."
                )
                lbl_no_expenses.setWordWrap(True)
                lbl_no_expenses.setStyleSheet("color:#6B7C93; font-style:italic;")
                layout.addWidget(lbl_no_expenses)
        else:
            lbl_no_expense_link = QLabel(
                "Linking expenses to a project requires migration_fase3_budget_expenses.sql — "
                "not run yet on this database."
            )
            lbl_no_expense_link.setWordWrap(True)
            lbl_no_expense_link.setStyleSheet("color:#C62828; font-style:italic;")
            layout.addWidget(lbl_no_expense_link)

        # ── Budget x Actual (orçado x realizado) ──────────────────────
        layout.addWidget(QLabel(""))
        actual_cost = material_cost_total + expense_total
        estimated_profit = float(total_value or 0) - actual_cost

        def variance_html(budget_value):
            lines = [f"<b>Actual Cost</b> (materials + linked expenses): ${actual_cost:,.2f}"]
            if budget_value:
                variance = budget_value - actual_cost
                color = "#C62828" if variance < 0 else "#2E7D32"
                status = "OVER budget" if variance < 0 else "under budget"
                lines.append(
                    f"<span style='color:{color}; font-weight:700;'>"
                    f"${abs(variance):,.2f} {status}</span> (budget ${budget_value:,.2f})"
                )
            profit_color = "#2E7D32" if estimated_profit >= 0 else "#C62828"
            lines.append(
                f"<b>Estimated Profit</b> (Total Value − Actual Cost): "
                f"<span style='color:{profit_color}; font-weight:700;'>${estimated_profit:,.2f}</span>"
            )
            return "<br/>".join(lines)

        lbl_variance = QLabel(variance_html(float(budget_amount or 0)))
        lbl_variance.setWordWrap(True)

        budget_row = QHBoxLayout()
        budget_row.addWidget(QLabel("<b>Budget:</b>"))
        spin_budget = QDoubleSpinBox()
        spin_budget.setRange(0, 99999999)
        spin_budget.setDecimals(2)
        spin_budget.setPrefix("$ ")
        spin_budget.setValue(float(budget_amount or 0))
        budget_row.addWidget(spin_budget)
        btn_save_budget = QPushButton("Save Budget")

        def save_budget():
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE job_projects SET BUDGET_AMOUNT = %s WHERE ID = %s",
                    (spin_budget.value(), job_project_id),
                )
                conn.commit()
                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(
                    dialog, "Database Error",
                    f"Could not save budget:\n{e}\n\n"
                    f"(Did you run migration_fase3_budget_expenses.sql yet?)",
                )
                return
            lbl_variance.setText(variance_html(spin_budget.value()))
            QMessageBox.information(dialog, "Saved", "Budget updated.")

        btn_save_budget.clicked.connect(save_budget)
        budget_row.addWidget(btn_save_budget)
        budget_row.addStretch()
        layout.addLayout(budget_row)
        layout.addWidget(lbl_variance)
        layout.addWidget(QLabel(""))

        def export_excel():
            path, _ = QFileDialog.getSaveFileName(
                dialog, "Export Project to Excel", f"Project_{job_code}.xlsx", "Excel Files (*.xlsx)"
            )
            if not path:
                return
            if not path.lower().endswith(".xlsx"):
                path += ".xlsx"
            try:
                import openpyxl
                from openpyxl.styles import Font, PatternFill, Alignment
                from openpyxl.utils import get_column_letter
            except ImportError:
                QMessageBox.critical(dialog, "Missing Dependency",
                                      "The 'openpyxl' package is not installed.\n\nRun:\npip install openpyxl")
                return

            try:
                wb = openpyxl.Workbook()
                header_font = Font(bold=True, color="FFFFFF")
                header_fill = PatternFill(start_color="1C2B3A", end_color="1C2B3A", fill_type="solid")

                ws_summary = wb.active
                ws_summary.title = "Summary"
                summary_rows = [
                    ("Job Code", job_code),
                    ("Client", client_name), ("Company", company_name),
                    ("Contractor", contractor_name), ("Address", job_address),
                    ("Days Worked", days_count), ("Period", period_text),
                    ("Total Value", f"${float(total_value or 0):,.2f}"),
                ]
                if project_type == "PRIVATE":
                    summary_rows.append(("Total Material Cost", f"${material_cost_total:,.2f}"))
                if has_expense_link_column:
                    summary_rows.append(("Linked Expenses Total", f"${expense_total:,.2f}"))
                summary_rows.append(("Actual Cost (materials + expenses)", f"${actual_cost:,.2f}"))
                if budget_amount:
                    summary_rows.append(("Budget", f"${float(budget_amount):,.2f}"))
                    summary_rows.append(("Variance", f"${float(budget_amount) - actual_cost:,.2f}"))
                summary_rows.append(("Estimated Profit", f"${estimated_profit:,.2f}"))
                for row_vals in summary_rows:
                    ws_summary.append(row_vals)
                ws_summary.column_dimensions["A"].width = 26
                ws_summary.column_dimensions["B"].width = 40
                for cell in ws_summary["A"]:
                    cell.font = Font(bold=True)

                ws_jobs = wb.create_sheet("Jobs")
                ws_jobs.append(["Date", "Contractor", "Value", "Status"])
                for c in range(1, 5):
                    cell = ws_jobs.cell(row=1, column=c)
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = Alignment(horizontal="center")
                for r in range(table_jobs.rowCount()):
                    ws_jobs.append([table_jobs.item(r, c).text() for c in range(4)])
                for c in range(1, 5):
                    ws_jobs.column_dimensions[get_column_letter(c)].width = 18

                ws_materials = wb.create_sheet("Materials")
                ws_materials.append(["Product", "Qty", "Unit"])
                for c in range(1, 4):
                    cell = ws_materials.cell(row=1, column=c)
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = Alignment(horizontal="center")
                for r in range(table_materials.rowCount()):
                    ws_materials.append([table_materials.item(r, c).text() for c in range(3)])
                for c in range(1, 4):
                    ws_materials.column_dimensions[get_column_letter(c)].width = 20

                if table_expenses_linked is not None and table_expenses_linked.rowCount():
                    ws_expenses = wb.create_sheet("Expenses")
                    ws_expenses.append(["Date", "Category", "Description", "Amount"])
                    for c in range(1, 5):
                        cell = ws_expenses.cell(row=1, column=c)
                        cell.font = header_font
                        cell.fill = header_fill
                        cell.alignment = Alignment(horizontal="center")
                    for r in range(table_expenses_linked.rowCount()):
                        ws_expenses.append([table_expenses_linked.item(r, c).text() for c in range(4)])
                    for c in range(1, 5):
                        ws_expenses.column_dimensions[get_column_letter(c)].width = 18

                wb.save(path)
                QMessageBox.information(dialog, "Export Complete", f"Saved to:\n{path}")
            except Exception as e:
                QMessageBox.critical(dialog, "Export Error", f"Could not export to Excel:\n{e}")

        def export_pdf():
            if not REPORTLAB_AVAILABLE:
                QMessageBox.critical(dialog, "Missing Dependency",
                                      "The 'reportlab' package is not installed.\n\nRun:\npip install reportlab")
                return
            path, _ = QFileDialog.getSaveFileName(
                dialog, "Export Project to PDF", f"Project_{job_code}.pdf", "PDF Files (*.pdf)"
            )
            if not path:
                return
            if not path.lower().endswith(".pdf"):
                path += ".pdf"

            try:
                styles = getSampleStyleSheet()
                doc = SimpleDocTemplate(path, pagesize=letter, topMargin=0.5 * inch, bottomMargin=0.5 * inch,
                                         leftMargin=0.6 * inch, rightMargin=0.6 * inch)
                story = [
                    Paragraph(f"<b>Project {job_code}</b>", styles["Title"]),
                    Spacer(1, 10),
                    Paragraph(f"<b>Client:</b> {client_name} &nbsp;&nbsp; <b>Company:</b> {company_name}",
                              styles["Normal"]),
                    Paragraph(f"<b>Contractor:</b> {contractor_name} &nbsp;&nbsp; <b>Address:</b> {job_address}",
                              styles["Normal"]),
                    Spacer(1, 10),
                    Paragraph(f"<b>{days_count} day(s) worked</b> — {period_text}", styles["Normal"]),
                    Paragraph(f"<b>Total Value:</b> ${float(total_value or 0):,.2f}", styles["Normal"]),
                    Spacer(1, 16),
                    Paragraph("<b>Jobs Under This Code</b>", styles["Heading3"]),
                ]

                jobs_data = [["Date", "Contractor", "Value", "Status"]]
                for r in range(table_jobs.rowCount()):
                    jobs_data.append([table_jobs.item(r, c).text() for c in range(4)])
                jobs_table_pdf = Table(jobs_data, colWidths=[1.1 * inch, 2.0 * inch, 1.1 * inch, 1.4 * inch],
                                        repeatRows=1)
                jobs_table_pdf.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(BRAND_NAVY)),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DDDDDD")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F9FC")]),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]))
                story.append(jobs_table_pdf)

                story.append(Spacer(1, 16))
                story.append(Paragraph("<b>Materials Used</b>", styles["Heading3"]))
                materials_data = [["Product", "Qty", "Unit"]]
                for r in range(table_materials.rowCount()):
                    materials_data.append([table_materials.item(r, c).text() for c in range(3)])
                materials_table_pdf = Table(materials_data, colWidths=[2.6 * inch, 1.3 * inch, 1.3 * inch],
                                             repeatRows=1)
                materials_table_pdf.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#37474F")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DDDDDD")),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]))
                story.append(materials_table_pdf)

                if project_type == "PRIVATE":
                    story.append(Spacer(1, 10))
                    story.append(Paragraph(f"<b>Total Material Cost:</b> ${material_cost_total:,.2f}",
                                            styles["Normal"]))

                if table_expenses_linked is not None and table_expenses_linked.rowCount():
                    story.append(Spacer(1, 16))
                    story.append(Paragraph("<b>Expenses Linked to This Project</b>", styles["Heading3"]))
                    expenses_data = [["Date", "Category", "Description", "Amount"]]
                    for r in range(table_expenses_linked.rowCount()):
                        expenses_data.append([table_expenses_linked.item(r, c).text() for c in range(4)])
                    expenses_table_pdf = Table(
                        expenses_data,
                        colWidths=[1.0 * inch, 1.2 * inch, 2.2 * inch, 1.0 * inch],
                        repeatRows=1,
                    )
                    expenses_table_pdf.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#37474F")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DDDDDD")),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ]))
                    story.append(expenses_table_pdf)

                story.append(Spacer(1, 16))
                story.append(Paragraph("<b>Budget x Actual</b>", styles["Heading3"]))
                story.append(Paragraph(f"<b>Actual Cost</b> (materials + linked expenses): ${actual_cost:,.2f}",
                                        styles["Normal"]))
                if budget_amount:
                    variance = float(budget_amount) - actual_cost
                    status = "OVER budget" if variance < 0 else "under budget"
                    story.append(Paragraph(
                        f"<b>Budget:</b> ${float(budget_amount):,.2f} — ${abs(variance):,.2f} {status}",
                        styles["Normal"],
                    ))
                story.append(Paragraph(f"<b>Estimated Profit</b> (Total Value − Actual Cost): "
                                        f"${estimated_profit:,.2f}", styles["Normal"]))

                doc.build(story)
                QMessageBox.information(dialog, "Export Complete", f"Saved to:\n{path}")
            except Exception as e:
                QMessageBox.critical(dialog, "Export Error", f"Could not export to PDF:\n{e}")

        export_row = QHBoxLayout()
        btn_export_excel = QPushButton("⤓  Excel")
        btn_export_excel.clicked.connect(export_excel)
        btn_export_pdf = QPushButton("⤓  PDF")
        btn_export_pdf.clicked.connect(export_pdf)
        btn_generate_invoice = QPushButton("🧾  Generate Invoice")
        btn_generate_invoice.setStyleSheet(
            "QPushButton { background-color: #1565C0; color: #FFFFFF; border: none; "
            "border-radius: 6px; padding: 8px 14px; font-weight: 600; } "
            "QPushButton:hover { background-color: #1E88E5; }"
        )

        def go_generate_invoice_for_job_code():
            dialog.accept()
            self.open_generate_invoices_dialog(prefill_job_code=job_code)

        btn_generate_invoice.clicked.connect(go_generate_invoice_for_job_code)

        btn_documents = QPushButton("📁  Documents")

        def go_documents_for_project():
            self.open_documents_manager_dialog(prefill_entity_type="PROJECT", prefill_entity_id=job_project_id)

        btn_documents.clicked.connect(go_documents_for_project)

        export_row.addWidget(btn_export_excel)
        export_row.addWidget(btn_export_pdf)
        export_row.addWidget(btn_generate_invoice)
        export_row.addWidget(btn_documents)
        export_row.addStretch()
        layout.addLayout(export_row)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)

        dialog.exec()
