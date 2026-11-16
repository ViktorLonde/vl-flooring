# -*- coding: utf-8 -*-
"""
Home: dashboard inicial (cards, jobs recentes, gráficos e atalhos).

Métodos da MainWindow (mixin) — veja main_.py.
"""

from app_common import *  # noqa: F401,F403


class HomeMixin:
    def load_home_dashboard(self):
        """Atualiza os 4 cards de resumo, a lista de Jobs recentes e o
        gráfico de faturamento dos últimos 6 meses, na página Home."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT COUNT(*), COALESCE(SUM(VALUE), 0) FROM work_days "
                "WHERE MONTH(WORK_DATE) = MONTH(CURDATE()) AND YEAR(WORK_DATE) = YEAR(CURDATE())"
            )
            jobs_month, revenue_month = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) FROM work_days WHERE STATUS IN ('PENDING', 'STARTED')")
            pending_jobs = cursor.fetchone()[0]

            overdue = 0
            for table in ("contractor_invoices", "company_invoices", "client_invoices"):
                cursor.execute(
                    f"SELECT COUNT(*) FROM {table} "
                    f"WHERE STATUS IN ('PENDING','PARTIAL') AND DATEDIFF(CURDATE(), GENERATED_AT) > 30"
                )
                overdue += cursor.fetchone()[0] or 0

            cursor.execute(
                """
                SELECT wd.WORK_DATE, COALESCE(c.COMPANY_NAME, c.FULL_NAME, '—'), COALESCE(cl.FULL_NAME, '—'),
                       wd.VALUE, wd.STATUS
                FROM work_days wd
                LEFT JOIN contractors c ON c.ID = wd.CONTRACTOR_ID
                LEFT JOIN clients cl ON cl.ID = wd.CLIENT_ID
                ORDER BY wd.WORK_DATE DESC, wd.ID DESC
                LIMIT 10
                """
            )
            recent_jobs = cursor.fetchall()

            cursor.execute(
                """
                SELECT DATE_FORMAT(WORK_DATE, '%Y-%m') AS ym, COALESCE(SUM(VALUE), 0)
                FROM work_days
                WHERE WORK_DATE >= DATE_FORMAT(CURDATE() - INTERVAL 5 MONTH, '%Y-%m-01')
                  AND WORK_DATE < DATE_FORMAT(CURDATE() + INTERVAL 1 MONTH, '%Y-%m-01')
                GROUP BY ym
                ORDER BY ym
                """
            )
            revenue_by_month = cursor.fetchall()

            wt_columns = [
                "DEMOLITION_1_ID", "DEMOLITION_2_ID", "DEMOLITION_3_ID", "DEMOLITION_4_ID",
                "INSTALLATION_1_ID", "INSTALLATION_2_ID", "INSTALLATION_3_ID", "INSTALLATION_4_ID",
                "PREPARATION_1_ID", "PREPARATION_2_ID", "PREPARATION_3_ID", "PREPARATION_4_ID",
                "OTHERS_1_ID", "OTHERS_2_ID", "REPARO_1_ID", "REPARO_2_ID",
            ]
            union_query = " UNION ALL ".join(
                f"SELECT {col} AS WT_ID FROM work_days WHERE {col} IS NOT NULL" for col in wt_columns
            )
            cursor.execute(
                f"""
                SELECT wt.NAME, COUNT(*) AS cnt
                FROM ({union_query}) t
                JOIN work_types wt ON wt.ID = t.WT_ID
                GROUP BY wt.ID, wt.NAME
                ORDER BY cnt DESC
                LIMIT 8
                """
            )
            work_type_counts = cursor.fetchall()

            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.warning(self, "Database Error", f"Could not load the Home dashboard:\n{e}")
            return

        self.ui.lbl_home_jobs_month_value.setText(str(jobs_month or 0))
        self.ui.lbl_home_revenue_month_value.setText(f"${float(revenue_month or 0):,.2f}")
        self.ui.lbl_home_overdue_value.setText(str(overdue))
        self.ui.lbl_home_pending_jobs_value.setText(str(pending_jobs or 0))

        table = self.ui.table_home_recent_jobs
        table.setRowCount(len(recent_jobs))
        for r, (wdate, contractor, client, value, status) in enumerate(recent_jobs):
            date_str = wdate.strftime("%m/%d/%Y") if isinstance(wdate, date) else str(wdate)
            values = [date_str, contractor, client, f"${float(value or 0):,.2f}",
                      JOB_STATUS_LABELS.get(status, status)]
            for c, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(r, c, item)

        self._draw_home_revenue_chart(revenue_by_month)

        # Cards + gráfico dos tipos de trabalho mais feitos
        wt_cards = [
            (self.ui.lbl_home_work_type_1_value, self.ui.lbl_home_work_type_1_label),
            (self.ui.lbl_home_work_type_2_value, self.ui.lbl_home_work_type_2_label),
            (self.ui.lbl_home_work_type_3_value, self.ui.lbl_home_work_type_3_label),
            (self.ui.lbl_home_work_type_4_value, self.ui.lbl_home_work_type_4_label),
        ]
        for i, (value_lbl, name_lbl) in enumerate(wt_cards):
            if i < len(work_type_counts):
                name, count = work_type_counts[i]
                value_lbl.setText(str(count))
                name_lbl.setText(str(name))
            else:
                value_lbl.setText("—")
                name_lbl.setText("—")

        self._draw_home_work_types_chart(work_type_counts)
        self._refresh_projects_overview_widget()

    def _draw_home_work_types_chart(self, work_type_counts):
        """Desenha um gráfico de barras simples com a frequência de cada
        tipo de trabalho (quantas vezes cada Work Type foi usado em jobs)."""
        layout = self.ui.layout_home_work_types_chart
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not work_type_counts:
            layout.addWidget(QLabel("No work type data yet"))
            return

        max_count = max(count for _, count in work_type_counts) or 1

        for name, count in work_type_counts:
            col = QVBoxLayout()
            col.addStretch()

            count_lbl = QLabel(str(count))
            count_lbl.setStyleSheet("font-size:10px; font-weight:700; color:#6A1B9A; background:transparent;")
            count_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.addWidget(count_lbl)

            bar_height = max(6, int((count / max_count) * 90))
            bar = QFrame()
            bar.setMinimumHeight(bar_height)
            bar.setMaximumHeight(bar_height)
            bar.setStyleSheet("background-color: #6A1B9A; border-radius: 4px;")
            col.addWidget(bar)

            name_lbl = QLabel(name if len(name) <= 12 else name[:11] + "…")
            name_lbl.setToolTip(name)
            name_lbl.setStyleSheet("font-size:10px; font-weight:600; color:#6B7C93; background:transparent;")
            name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_lbl.setWordWrap(True)
            col.addWidget(name_lbl)

            layout.addLayout(col)

    def _draw_home_revenue_chart(self, revenue_by_month):
        """Gráfico de barras do faturamento dos últimos 6 meses (incluindo o
        atual). Meses sem trabalho aparecem com barra zerada, pra dar pra
        comparar; o valor exato aparece em cima e ao passar o mouse."""
        layout = self.ui.layout_home_revenue_chart
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                sub = child.layout()
                while sub.count():
                    item = sub.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()

        values = {ym: float(v or 0) for ym, v in revenue_by_month}
        today = date.today()
        months = []
        for back in range(5, -1, -1):
            y, m = today.year, today.month - back
            while m <= 0:
                m += 12
                y -= 1
            months.append((f"{y:04d}-{m:02d}", m))
        if not any(values.get(ym) for ym, _ in months):
            empty = QLabel("No revenue in the last 6 months")
            empty.setStyleSheet("color:#94A3B8; font-size:12px; background:transparent;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(empty)
            return

        max_value = max(values.get(ym, 0) for ym, _ in months) or 1.0
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        layout.setSpacing(6)
        for ym, month in months:
            value = values.get(ym, 0.0)
            current = ym == f"{today.year:04d}-{today.month:02d}"
            col = QVBoxLayout()
            col.setSpacing(3)
            col.addStretch()

            if value >= 1000:
                short = f"${value / 1000:.1f}k".replace(".0k", "k")
            else:
                short = f"${value:,.0f}"
            value_lbl = QLabel(short if value else "")
            value_lbl.setStyleSheet("font-size:10px; font-weight:700; color:#1565C0; background:transparent;")
            value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.addWidget(value_lbl)

            bar_height = max(3, int((value / max_value) * 80)) if value else 3
            bar = QFrame()
            bar.setFixedHeight(bar_height)
            bar.setMinimumWidth(18)
            color = BRAND_ORANGE if current else ("#F4A06B" if value else "#E3E8EE")
            bar.setStyleSheet(f"background-color: {color}; border-radius: 4px;")
            bar.setToolTip(f"{month_names[month - 1]} {ym[:4]}: ${value:,.2f}")
            col.addWidget(bar)

            month_lbl = QLabel(month_names[month - 1])
            month_lbl.setStyleSheet("font-size:11px; font-weight:600; color:#6B7C93; background:transparent;"
                                    + (" color:#1C2B3A;" if current else ""))
            month_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.addWidget(month_lbl)
            layout.addLayout(col)

    def _go_home_new_job(self):
        self._go_to_page(1, self.ui.btn_jobs)
        self._on_new_job_button_clicked()

    def _go_home_generate_invoices(self):
        self._go_to_page(5, self.ui.btn_nav_receivables)
        self.open_generate_invoices_dialog()

    def _go_home_schedule(self):
        self._go_to_page(1, self.ui.btn_jobs)
        self.ui.tabWidget_jobs.setCurrentWidget(self.ui.tab_schedule)

    def _go_home_new_customer(self):
        self._go_to_page(6, self.ui.btn_customer)
        self.new_customer_record()
