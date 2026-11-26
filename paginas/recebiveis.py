# -*- coding: utf-8 -*-
"""
Receivables: dashboard (totais, aging, gráfico) e registro de pagamentos.

Métodos da MainWindow (mixin) — veja main_.py.
"""

from app_common import *  # noqa: F401,F403


class ReceivablesMixin:
    def _setup_dashboard_period_filter(self):
        """Popula os combos de Mês/Ano do Dashboard de Receivables (dinâmico, não dá pra fazer isso direto no Designer)."""
        self.ui.cmb_dashboard_month.blockSignals(True)
        self.ui.cmb_dashboard_month.addItem("All Months", 0)
        month_names = ["January", "February", "March", "April", "May", "June",
                       "July", "August", "September", "October", "November", "December"]
        for i, name in enumerate(month_names, start=1):
            self.ui.cmb_dashboard_month.addItem(name, i)
        self.ui.cmb_dashboard_month.setCurrentIndex(date.today().month)  # mês atual selecionado por padrão
        self.ui.cmb_dashboard_month.blockSignals(False)

        self.ui.cmb_dashboard_year.blockSignals(True)
        self.ui.cmb_dashboard_year.addItem("All Years", 0)
        current_year = date.today().year
        for y in range(current_year - 4, current_year + 1):
            self.ui.cmb_dashboard_year.addItem(str(y), y)
        self.ui.cmb_dashboard_year.setCurrentIndex(self.ui.cmb_dashboard_year.count() - 1)  # ano atual
        self.ui.cmb_dashboard_year.blockSignals(False)

    def _is_contractor_invoice_overdue(self, generated_at, cycle_type, cycle_weekday, cycle_days):
        """Decide se um invoice de Contractor está atrasado, respeitando a
        regra de pagamento configurada NAQUELE contractor (semanal num dia
        da semana específico, quinzenal, ou um número de dias corridos)."""
        if generated_at is None:
            return False
        generated_date = generated_at.date() if hasattr(generated_at, "date") else generated_at
        today = date.today()

        if cycle_type == "WEEKLY" or cycle_type == "BIWEEKLY":
            # O combo na tela usa Sunday=0..Saturday=6; o Python usa Monday=0..Sunday=6.
            combo_weekday = cycle_weekday if cycle_weekday is not None else 5  # Friday por padrão
            target_weekday = (combo_weekday - 1) % 7
            days_ahead = (target_weekday - generated_date.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7  # cai no mesmo dia da semana em que foi gerado: só vence na ocorrência seguinte
            due_date = generated_date + timedelta(days=days_ahead)
            if cycle_type == "BIWEEKLY":
                due_date += timedelta(days=7)
        else:  # CUSTOM_DAYS
            due_date = generated_date + timedelta(days=cycle_days or 30)

        return today > due_date

    def load_receivables_dashboard(self):
        """Atualiza os 4 cards de resumo e a tabela de detalhamento por
        Contractor/Company/Client do Dashboard de Receivables, respeitando
        o filtro de Mês/Ano selecionado."""
        month = self.ui.cmb_dashboard_month.currentData() or 0
        year = self.ui.cmb_dashboard_year.currentData() or 0

        # Monta a clausula de periodo (aplicada em cima de PERIOD_FROM de cada invoice)
        period_clause = ""
        period_params: list = []
        if month:
            period_clause += " AND MONTH(PERIOD_FROM) = %s"
            period_params.append(month)
        if year:
            period_clause += " AND YEAR(PERIOD_FROM) = %s"
            period_params.append(year)

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            total_receivable = 0.0
            received_month = 0.0
            open_entities = set()
            overdue = 0
            breakdown_rows = []  # (type, name, total, received, pending)
            aging_buckets = {"0_30": 0.0, "31_60": 0.0, "61_90": 0.0, "90_plus": 0.0}

            entity_tables = [
                ("Contractor", "contractor_invoices", "contractors", "CONTRACTOR_ID", "COALESCE(r.COMPANY_NAME, r.FULL_NAME)"),
                ("Company", "company_invoices", "companies", "COMPANY_ID", "r.COMPANY_NAME"),
                ("Client", "client_invoices", "clients", "CLIENT_ID", "r.FULL_NAME"),
            ]

            for label, table, ref_table, fk_col, name_col in entity_tables:
                # Totais gerais: sempre o que está em aberto AGORA (o filtro de
                # período vale só para a tabela de detalhamento e formas de pagamento)
                cursor.execute(
                    f"""
                    SELECT COALESCE(SUM(TOTAL_AMOUNT - AMOUNT_PAID), 0),
                           COUNT(DISTINCT {fk_col})
                    FROM {table}
                    WHERE STATUS IN ('PENDING','PARTIAL')
                    """
                )
                pending_sum, open_count = cursor.fetchone()
                total_receivable += float(pending_sum or 0)
                if open_count:
                    open_entities.add((label, open_count))

                cursor.execute(
                    f"""
                    SELECT COALESCE(SUM(AMOUNT_PAID), 0) FROM {table}
                    WHERE RECEIVED_AT IS NOT NULL
                    AND MONTH(RECEIVED_AT)=MONTH(CURDATE()) AND YEAR(RECEIVED_AT)=YEAR(CURDATE())
                    """
                )
                received_month += float(cursor.fetchone()[0] or 0)

                if label == "Contractor":
                    # Regra por contractor: cada um pode ter um ciclo de pagamento diferente
                    # (semanal num dia específico, quinzenal, ou N dias corridos).
                    cursor.execute(
                        f"""
                        SELECT t.GENERATED_AT, COALESCE(r.PAYMENT_CYCLE_TYPE, 'CUSTOM_DAYS'),
                               r.PAYMENT_CYCLE_WEEKDAY, COALESCE(r.PAYMENT_CYCLE_DAYS, 30)
                        FROM {table} t
                        LEFT JOIN {ref_table} r ON r.ID = t.{fk_col}
                        WHERE t.STATUS IN ('PENDING','PARTIAL')
                        """
                    )
                    for generated_at, cycle_type, cycle_weekday, cycle_days in cursor.fetchall():
                        if self._is_contractor_invoice_overdue(generated_at, cycle_type, cycle_weekday, cycle_days):
                            overdue += 1
                else:
                    cursor.execute(
                        f"""
                        SELECT COUNT(*) FROM {table}
                        WHERE STATUS IN ('PENDING','PARTIAL') AND DATEDIFF(CURDATE(), GENERATED_AT) > 30
                        """
                    )
                    overdue += cursor.fetchone()[0] or 0

                # Aging report: idade (em dias, a partir de GENERATED_AT) de cada saldo em aberto
                cursor.execute(
                    f"""
                    SELECT DATEDIFF(CURDATE(), GENERATED_AT), (TOTAL_AMOUNT - AMOUNT_PAID)
                    FROM {table} WHERE STATUS IN ('PENDING','PARTIAL')
                    """
                )
                for days_old, pending_amount in cursor.fetchall():
                    pending_amount = float(pending_amount or 0)
                    days_old = days_old or 0
                    if days_old <= 30:
                        aging_buckets["0_30"] += pending_amount
                    elif days_old <= 60:
                        aging_buckets["31_60"] += pending_amount
                    elif days_old <= 90:
                        aging_buckets["61_90"] += pending_amount
                    else:
                        aging_buckets["90_plus"] += pending_amount

                # Detalhamento por entidade (nome), respeitando o filtro de periodo
                cursor.execute(
                    f"""
                    SELECT COALESCE({name_col}, '—') AS NAME,
                           COALESCE(SUM(t.TOTAL_AMOUNT), 0) AS TOTAL,
                           COALESCE(SUM(t.AMOUNT_PAID), 0) AS RECEIVED
                    FROM {table} t
                    LEFT JOIN {ref_table} r ON r.ID = t.{fk_col}
                    WHERE 1=1 {period_clause}
                    GROUP BY t.{fk_col}, {name_col}
                    ORDER BY TOTAL DESC
                    """,
                    period_params,
                )
                for name, total, received in cursor.fetchall():
                    total = float(total or 0)
                    received = float(received or 0)
                    breakdown_rows.append((label, name, total, received, total - received))

            # Recebido por forma de pagamento (respeitando o filtro de mês/ano, se houver)
            pm_clause = ""
            pm_params: list = []
            if month:
                pm_clause += " AND MONTH(PAID_DATE) = %s"
                pm_params.append(month)
            if year:
                pm_clause += " AND YEAR(PAID_DATE) = %s"
                pm_params.append(year)
            cursor.execute(
                f"""
                SELECT COALESCE(PAYMENT_METHOD, 'Other'), COALESCE(SUM(AMOUNT), 0)
                FROM payments WHERE 1=1 {pm_clause}
                GROUP BY PAYMENT_METHOD ORDER BY SUM(AMOUNT) DESC
                """,
                pm_params,
            )
            payment_method_rows = cursor.fetchall()

            # Recebido por mês, últimos 6 meses (pra o gráfico)
            cursor.execute(
                """
                SELECT DATE_FORMAT(PAID_DATE, '%Y-%m') AS ym, COALESCE(SUM(AMOUNT), 0)
                FROM payments
                WHERE PAID_DATE >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
                GROUP BY ym ORDER BY ym
                """
            )
            received_by_month = cursor.fetchall()

            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.warning(self, "Database Error", f"Could not load dashboard:\n{e}")
            return

        open_count_total = sum(c for _, c in open_entities)

        self.ui.lbl_receivables_total_value.setText(f"${total_receivable:,.2f}")
        self.ui.lbl_receivables_month_value.setText(f"${received_month:,.2f}")
        self.ui.lbl_receivables_open_value.setText(str(open_count_total))
        self.ui.lbl_receivables_overdue_value.setText(str(overdue))

        # Preenche a tabela de detalhamento
        table_widget = self.ui.table_receivables_breakdown
        table_widget.setSortingEnabled(False)
        table_widget.setRowCount(0)
        table_widget.setRowCount(len(breakdown_rows))
        for row_idx, (label, name, total, received, pending) in enumerate(breakdown_rows):
            values = [label, str(name), f"${total:,.2f}", f"${received:,.2f}", f"${pending:,.2f}"]
            for col_idx, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table_widget.setItem(row_idx, col_idx, item)
        table_widget.setSortingEnabled(True)

        # Aging report
        self.ui.lbl_aging_0_30_value.setText(f"${aging_buckets['0_30']:,.2f}")
        self.ui.lbl_aging_31_60_value.setText(f"${aging_buckets['31_60']:,.2f}")
        self.ui.lbl_aging_61_90_value.setText(f"${aging_buckets['61_90']:,.2f}")
        self.ui.lbl_aging_90_plus_value.setText(f"${aging_buckets['90_plus']:,.2f}")

        # Recebido por forma de pagamento
        pm_table = self.ui.table_dashboard_payment_methods
        pm_table.setRowCount(len(payment_method_rows))
        for r, (method, amount) in enumerate(payment_method_rows):
            for c, text in enumerate([method, f"${float(amount or 0):,.2f}"]):
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                pm_table.setItem(r, c, item)

        # Top devedores: mesmas linhas do detalhamento, ordenadas por saldo pendente
        top_debtors = sorted(breakdown_rows, key=lambda row: row[4], reverse=True)[:10]
        debtors_table = self.ui.table_dashboard_top_debtors
        debtors_table.setRowCount(len(top_debtors))
        for r, (label, name, total, received, pending) in enumerate(top_debtors):
            for c, text in enumerate([label, str(name), f"${pending:,.2f}"]):
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                debtors_table.setItem(r, c, item)

        self._draw_dashboard_received_chart(received_by_month)
        if hasattr(self, "_refresh_receivables_extra"):
            self._refresh_receivables_extra()

    def _draw_dashboard_received_chart(self, received_by_month):
        """Desenha o gráfico de barras de valores recebidos por mês (últimos
        6 meses), no mesmo estilo simples usado na Home."""
        layout = self.ui.layout_dashboard_received_chart
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not received_by_month:
            layout.addWidget(QLabel("No payments received yet"))
            return

        max_value = max(float(v) for _, v in received_by_month) or 1.0
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        for ym, value in received_by_month:
            value = float(value or 0)
            _, month_str = ym.split("-")
            label_text = month_names[int(month_str) - 1]

            col = QVBoxLayout()
            col.addStretch()
            value_lbl = QLabel(f"${value:,.0f}")
            value_lbl.setStyleSheet("font-size:10px; font-weight:700; color:#2E7D32; background:transparent;")
            value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.addWidget(value_lbl)

            bar_height = max(6, int((value / max_value) * 90))
            bar = QFrame()
            bar.setMinimumHeight(bar_height)
            bar.setMaximumHeight(bar_height)
            bar.setStyleSheet("background-color: #2E7D32; border-radius: 4px;")
            col.addWidget(bar)

            month_lbl = QLabel(label_text)
            month_lbl.setStyleSheet("font-size:11px; font-weight:600; color:#6B7C93; background:transparent;")
            month_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.addWidget(month_lbl)

            layout.addLayout(col)

    def open_record_payment_dialog(self, *_args, preselect=None):
        """Atalho do Dashboard: acha um invoice em aberto (Contractor/Company/
        Client) e registra um pagamento nele, sem precisar navegar até a
        lista de Invoices primeiro. preselect=(tipo, id) já deixa a invoice
        escolhida (ação "Record payment" da lista de Invoices)."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Record Payment")
        dialog.resize(480, 480)
        dialog.setStyleSheet("""
            QDoubleSpinBox, QSpinBox {
                background-color: #FFFFFF;
                color: #1C2B3A;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 13px;
            }
            QDoubleSpinBox:focus, QSpinBox:focus { border: 1px solid #1E88E5; }
            QLineEdit, QDateEdit, QComboBox {
                background-color: #FFFFFF;
                color: #1C2B3A;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 6px 8px;
            }
        """)
        layout = QVBoxLayout(dialog)

        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Bill To:"))
        cmb_type = QComboBox()
        cmb_type.addItems(["Contractor", "Company", "Client"])
        type_row.addWidget(cmb_type)
        layout.addLayout(type_row)

        txt_search = QLineEdit()
        txt_search.setPlaceholderText("🔍  Search by name…")
        layout.addWidget(txt_search)

        layout.addWidget(QLabel("Open invoices:"))
        list_invoices = QListWidget()
        layout.addWidget(list_invoices)

        invoice_data = {}  # texto da linha -> (invoice_id, table_name, balance)

        def refresh_list():
            list_invoices.clear()
            invoice_data.clear()
            entity_type = cmb_type.currentText()
            table_name, ref_table, fk_col, name_col = {
                "Contractor": ("contractor_invoices", "contractors", "CONTRACTOR_ID", "COALESCE(r.COMPANY_NAME, r.FULL_NAME)"),
                "Company": ("company_invoices", "companies", "COMPANY_ID", "r.COMPANY_NAME"),
                "Client": ("client_invoices", "clients", "CLIENT_ID", "r.FULL_NAME"),
            }[entity_type]
            search_text = txt_search.text().strip()
            query = f"""
                SELECT ci.ID, COALESCE({name_col}, '—'), ci.TOTAL_AMOUNT - ci.AMOUNT_PAID
                FROM {table_name} ci
                LEFT JOIN {ref_table} r ON r.ID = ci.{fk_col}
                WHERE ci.STATUS IN ('PENDING','PARTIAL')
            """
            params = []
            if search_text:
                query += f" AND COALESCE({name_col}, '') LIKE %s"
                params.append(f"%{search_text}%")
            query += " ORDER BY ci.GENERATED_AT DESC"
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not load invoices:\n{e}")
                return
            for invoice_id, name, balance in rows:
                balance = float(balance or 0)
                text = f"#{invoice_id} — {name} — Balance: ${balance:,.2f}"
                list_invoices.addItem(text)
                invoice_data[text] = (invoice_id, table_name, balance)

        cmb_type.currentIndexChanged.connect(refresh_list)
        txt_search.textChanged.connect(refresh_list)

        layout.addWidget(QLabel("Payment details:"))
        pay_row1 = QHBoxLayout()
        pay_row1.addWidget(QLabel("Date:"))
        date_paid = QDateEdit()
        date_paid.setCalendarPopup(True)
        date_paid.setDisplayFormat("MM/dd/yyyy")
        date_paid.setDate(QDate.currentDate())
        pay_row1.addWidget(date_paid)
        pay_row1.addWidget(QLabel("Amount ($):"))
        spin_amount = QDoubleSpinBox()
        spin_amount.setMaximum(999999.99)
        spin_amount.setPrefix("$ ")
        pay_row1.addWidget(spin_amount)
        layout.addLayout(pay_row1)

        pay_row2 = QHBoxLayout()
        pay_row2.addWidget(QLabel("Method:"))
        cmb_method = QComboBox()
        cmb_method.addItems(company_settings.COMPANY_PAYMENT_METHODS + ["Other"])
        pay_row2.addWidget(cmb_method)
        layout.addLayout(pay_row2)

        txt_note = QLineEdit()
        txt_note.setPlaceholderText("Note (optional)")
        layout.addWidget(txt_note)

        def fill_full_balance():
            selected = list_invoices.currentItem()
            if selected and selected.text() in invoice_data:
                spin_amount.setValue(invoice_data[selected.text()][2])

        list_invoices.itemSelectionChanged.connect(fill_full_balance)

        bottom_row = QHBoxLayout()
        bottom_row.addStretch()
        btn_cancel = QPushButton("Cancel")
        btn_record = QPushButton("Record Payment")
        btn_record.setObjectName("btn_save_job")
        bottom_row.addWidget(btn_cancel)
        bottom_row.addWidget(btn_record)
        layout.addLayout(bottom_row)

        def record_payment():
            selected = list_invoices.currentItem()
            if not selected or selected.text() not in invoice_data:
                QMessageBox.information(dialog, "No invoice selected", "Select an invoice from the list first.")
                return
            invoice_id, table_name, _ = invoice_data[selected.text()]
            amount = spin_amount.value()
            if amount <= 0:
                QMessageBox.warning(dialog, "Invalid amount", "Enter a payment amount greater than zero.")
                return

            entity_type = cmb_type.currentText()
            is_extra = False
            if hasattr(self, "_check_overpayment"):
                checked = self._check_overpayment(dialog, entity_type, invoice_id, amount)
                if checked is None:
                    return
                amount, is_extra = checked
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO payments (INVOICE_TYPE, INVOICE_ID, PAID_DATE, AMOUNT, PAYMENT_METHOD, NOTE) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (entity_type, invoice_id, date_paid.date().toString("yyyy-MM-dd"), amount,
                     cmb_method.currentText(), txt_note.text().strip() or None),
                )
                cursor.execute(
                    "SELECT COALESCE(SUM(AMOUNT), 0) FROM payments WHERE INVOICE_TYPE = %s AND INVOICE_ID = %s",
                    (entity_type, invoice_id),
                )
                total_paid = float(cursor.fetchone()[0] or 0)
                cursor.execute(f"SELECT TOTAL_AMOUNT FROM {table_name} WHERE ID = %s", (invoice_id,))
                total_amount = float(cursor.fetchone()[0] or 0)
                new_status = "RECEIVED" if total_paid >= total_amount else ("PARTIAL" if total_paid > 0 else "PENDING")
                received_clause = ", RECEIVED_AT = NOW()" if new_status == "RECEIVED" else ""
                cursor.execute(
                    f"UPDATE {table_name} SET AMOUNT_PAID = %s, STATUS = %s {received_clause} WHERE ID = %s",
                    (total_paid, new_status, invoice_id),
                )
                conn.commit()
                cursor.close()
                conn.close()
                if is_extra:
                    self._mark_invoice_extra(entity_type, invoice_id)
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not record payment:\n{e}")
                return

            self.load_receivables_dashboard()
            sent = False
            if hasattr(self, "offer_payment_receipt"):
                sent = self.offer_payment_receipt(dialog, entity_type, invoice_id, amount,
                                                  date_paid.date().toString("yyyy-MM-dd"), cmb_method.currentText())
            if not sent:
                QMessageBox.information(dialog, "Success", "Payment recorded successfully.")
            dialog.accept()

        btn_cancel.clicked.connect(dialog.reject)
        btn_record.clicked.connect(record_payment)

        refresh_list()
        if preselect:
            kind, wanted_id = preselect
            if cmb_type.currentText() != kind:
                cmb_type.setCurrentText(kind)  # recarrega a lista pelo sinal
            for i in range(list_invoices.count()):
                if list_invoices.item(i).text().startswith(f"#{wanted_id} —"):
                    list_invoices.setCurrentRow(i)
                    break
        dialog.exec()
