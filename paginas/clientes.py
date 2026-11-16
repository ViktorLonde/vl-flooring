# -*- coding: utf-8 -*-
"""
Customer: lista, formulário e histórico de jobs do cliente.

Métodos da MainWindow (mixin) — veja main_.py.
"""

from app_common import *  # noqa: F401,F403


class CustomersMixin:
    def load_customers(self):
        """Carrega os clientes na tabela, aplicando filtro de busca (nome, email ou telefone)."""
        search_text = self.ui.txt_search_customers.text().strip()

        query = """
            SELECT cl.ID, cl.FULL_NAME, cl.EMAIL, cl.PHONE_NUMBER,
                   COALESCE(city.CITY, '—') AS CITY_NAME,
                   COALESCE(st.STATE_NAME, '—') AS STATE_NAME
            FROM clients cl
            LEFT JOIN cities city ON city.ID = cl.CITY_ID
            LEFT JOIN states st ON st.ID = cl.STATE_ID
            WHERE 1=1
        """
        params = []
        if search_text:
            query += " AND (cl.FULL_NAME LIKE %s OR cl.EMAIL LIKE %s OR cl.PHONE_NUMBER LIKE %s)"
            like = f"%{search_text}%"
            params.extend([like, like, like])
        query += " ORDER BY cl.FULL_NAME"

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except MySQLError as e:
            QMessageBox.critical(self, "Database Error", f"Could not load customers:\n{e}")
            return
        except RuntimeError as e:
            QMessageBox.warning(self, "Driver Missing", str(e))
            return

        table = self.ui.table_customers
        table.setSortingEnabled(False)
        table.setRowCount(0)
        table.setRowCount(len(rows))
        for row_idx, (cid, name, email, phone, city, state) in enumerate(rows):
            values = [str(cid), str(name or ""), str(email or ""), self._format_phone(phone) or "",
                      str(city or "—"), str(state or "—")]
            for col_idx, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(row_idx, col_idx, item)
        table.setSortingEnabled(True)

    def new_customer_record(self):
        """Limpa o formulário para criar um novo cliente."""
        self._current_customer_id = None
        self.ui.table_customers.clearSelection()
        self.ui.table_customers.setCurrentCell(-1, -1)
        self.ui.txt_customer_id.clear()
        self.ui.lbl_customer_id_display.setText("#ID: New")
        self.ui.txt_customer_name.clear()
        self.ui.txt_customer_email.clear()
        self.ui.txt_customer_phone.clear()
        self.ui.txt_customer_phone2.clear()
        self.ui.txt_customer_address.clear()
        self.ui.txt_customer_address2.clear()
        self.ui.txt_customer_zip.clear()
        self.ui.cmb_customer_state.setCurrentIndex(0)
        self._reload_city_combo_for_state(self.ui.cmb_customer_city, None)
        self.ui.table_customer_job_history.setRowCount(0)
        self.ui.lbl_customer_job_history_total.setText("Total: $0.00")

    def load_customer_into_form(self):
        """Carrega o cliente selecionado na tabela para edição, junto com o
        histórico de Jobs feitos para ele."""
        table = self.ui.table_customers
        selected = table.currentRow()
        if selected < 0:
            return

        customer_id = table.item(selected, 0).text()
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clients WHERE ID = %s", (customer_id,))
            columns = [d[0] for d in cursor.description]
            row = cursor.fetchone()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not load customer:\n{e}")
            return

        if not row:
            return
        data = dict(zip(columns, row))

        self._current_customer_id = data.get("ID")
        self.ui.txt_customer_id.setText(str(data.get("ID")))
        self.ui.lbl_customer_id_display.setText(f"#ID: {data.get('ID')}")
        self.ui.txt_customer_name.setText(data.get("FULL_NAME") or "")
        self.ui.txt_customer_email.setText(data.get("EMAIL") or "")
        self.ui.txt_customer_phone.setText(self._format_phone(data.get("PHONE_NUMBER")) or "")
        self.ui.txt_customer_phone2.setText(self._format_phone(data.get("PHONE_NUMBER2")) or "")
        self.ui.txt_customer_address.setText(data.get("ADDRESS") or "")
        self.ui.txt_customer_address2.setText(data.get("ADDRESS2") or "")
        self.ui.txt_customer_zip.setText(self._format_zip(data.get("ZIP_CODE")) or "")
        self._set_combo_by_data(self.ui.cmb_customer_state, data.get("STATE_ID"))
        self._reload_city_combo_for_state(self.ui.cmb_customer_city, data.get("STATE_ID"),
                                           keep_city_id=data.get("CITY_ID"))

        self._load_customer_job_history(data.get("ID"))

    def _load_customer_job_history(self, customer_id):
        """Mostra todos os Jobs (work_days) feitos para esse cliente."""
        table = self.ui.table_customer_job_history
        table.setRowCount(0)
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT wd.WORK_DATE, COALESCE(c.COMPANY_NAME, c.FULL_NAME, '—'), COALESCE(co.COMPANY_NAME, '—'),
                       wd.JOB_ADDRESS, wd.VALUE, wd.STATUS
                FROM work_days wd
                LEFT JOIN contractors c ON c.ID = wd.CONTRACTOR_ID
                LEFT JOIN companies co ON co.ID = wd.COMPANY_ID
                WHERE wd.CLIENT_ID = %s
                ORDER BY wd.WORK_DATE DESC
                """,
                (customer_id,),
            )
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.warning(self, "Database Error", f"Could not load job history:\n{e}")
            return

        table.setRowCount(len(rows))
        total = 0.0
        for r, (wdate, contractor, company, address, value, status) in enumerate(rows):
            value = float(value or 0)
            total += value
            date_str = wdate.strftime("%m/%d/%Y") if isinstance(wdate, date) else str(wdate)
            values = [date_str, contractor, company, address or "", f"${value:,.2f}",
                      JOB_STATUS_LABELS.get(status, status)]
            for c, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(r, c, item)
        # Resumo financeiro do cliente (invoices geradas e pagas)
        billed = paid = 0.0
        n_invoices = 0
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*), COALESCE(SUM(TOTAL_AMOUNT),0), COALESCE(SUM(AMOUNT_PAID),0) "
                           "FROM client_invoices WHERE CLIENT_ID = %s AND STATUS <> 'CANCELLED'", (customer_id,))
            n_invoices, billed, paid = cursor.fetchone()
            billed, paid = float(billed or 0), float(paid or 0)
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError):
            logging.getLogger("vl_flooring").exception("customer invoice summary failed")
        jobs_text = f"{len(rows)} job{'s' if len(rows) != 1 else ''}"
        summary = f"{jobs_text} · Work total ${total:,.2f}"
        if n_invoices:
            summary += f"  ·  Invoiced ${billed:,.2f} · Paid ${paid:,.2f} · Open ${max(billed - paid, 0):,.2f}"
        else:
            summary += "  ·  No invoices yet"
        self.ui.lbl_customer_job_history_total.setText(summary)
        self.ui.lbl_customer_job_history_total.setWordWrap(True)
        self._customer_history_id = customer_id
        btn = getattr(self, "_btn_customer_invoices", None)
        if btn is not None:
            btn.setVisible(bool(n_invoices))

    def _setup_customer_invoices_button(self):
        """Botão "Invoices" ao lado do resumo do histórico do cliente."""
        from paginas.visual import tabler_icon
        label = self.ui.lbl_customer_job_history_total
        parent_layout = label.parentWidget().layout()
        btn = QPushButton("  Invoices")
        btn.setIcon(tabler_icon("receipt", "#37474F", 16))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setVisible(False)
        btn.clicked.connect(self.open_customer_invoices_dialog)
        idx = parent_layout.indexOf(label)
        row = QHBoxLayout()
        parent_layout.removeWidget(label)
        row.addWidget(label, 1)
        row.addWidget(btn)
        if hasattr(parent_layout, "insertLayout"):
            parent_layout.insertLayout(idx, row)
        else:
            parent_layout.addLayout(row)
        self._btn_customer_invoices = btn

    def open_customer_invoices_dialog(self):
        customer_id = getattr(self, "_customer_history_id", None)
        if not customer_id:
            return
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT ID, GENERATED_AT, PERIOD_FROM, PERIOD_TO, TOTAL_AMOUNT, AMOUNT_PAID, STATUS, PDF_PATH "
                           "FROM client_invoices WHERE CLIENT_ID = %s ORDER BY GENERATED_AT DESC", (customer_id,))
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.warning(self, "Database Error", f"Could not load invoices:\n{e}")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Customer invoices")
        dialog.resize(760, 420)
        layout = QVBoxLayout(dialog)
        table = QTableWidget(len(rows), 7)
        table.setHorizontalHeaderLabels(["#", "Generated", "Period", "Total", "Paid", "Open", "Status"])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        fmt = lambda d: d.strftime("%m/%d/%Y") if d else ""
        for r, (iid, gen, pfrom, pto, tot, pd, status, pdf) in enumerate(rows):
            tot, pd = float(tot or 0), float(pd or 0)
            vals = [str(iid), fmt(gen), f"{fmt(pfrom)} – {fmt(pto)}", f"${tot:,.2f}", f"${pd:,.2f}",
                    f"${max(tot - pd, 0):,.2f}", status or ""]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                if c == 0:
                    item.setData(Qt.ItemDataRole.UserRole, pdf)
                table.setItem(r, c, item)

        def open_pdf(row, _col):
            pdf = table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if pdf and os.path.exists(pdf):
                QDesktopServices.openUrl(QUrl.fromLocalFile(pdf))
            else:
                QMessageBox.information(dialog, "PDF not found", "The PDF of this invoice was not found on this computer.")

        table.cellDoubleClicked.connect(open_pdf)
        layout.addWidget(QLabel("Double-click an invoice to open its PDF."))
        layout.addWidget(table)
        dialog.exec()

    def save_customer_record(self):
        """Insere ou atualiza um registro em clients."""
        name = self.ui.txt_customer_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing data", "Full Name is required.")
            return

        data = (
            name,
            self.ui.txt_customer_email.text(),
            self._format_phone(self.ui.txt_customer_phone.text()),
            self._format_phone(self.ui.txt_customer_phone2.text()),
            self.ui.txt_customer_address.text(),
            self.ui.txt_customer_address2.text(),
            self.ui.cmb_customer_city.currentData(),
            self.ui.cmb_customer_state.currentData(),
            self._format_zip(self.ui.txt_customer_zip.text()),
        )

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            if getattr(self, "_current_customer_id", None):
                cursor.execute(
                    "UPDATE clients SET FULL_NAME=%s, EMAIL=%s, PHONE_NUMBER=%s, PHONE_NUMBER2=%s, "
                    "ADDRESS=%s, ADDRESS2=%s, CITY_ID=%s, STATE_ID=%s, ZIP_CODE=%s WHERE ID=%s",
                    data + (self._current_customer_id,),
                )
            else:
                cursor.execute(
                    "INSERT INTO clients (FULL_NAME, EMAIL, PHONE_NUMBER, PHONE_NUMBER2, ADDRESS, "
                    "ADDRESS2, CITY_ID, STATE_ID, ZIP_CODE) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    data,
                )
            conn.commit()
            cursor.close()
            conn.close()
        except MySQLError as e:
            QMessageBox.critical(self, "Database Error", f"Could not save customer:\n{e}")
            return
        except RuntimeError as e:
            QMessageBox.warning(self, "Driver Missing", str(e))
            return

        QMessageBox.information(self, "Success", "Customer saved successfully.")
        self.load_customers()
        self._refresh_client_name_completer()
        self.new_customer_record()

    def delete_customer_record(self):
        """Exclui o cliente atualmente carregado no formulário."""
        if not getattr(self, "_current_customer_id", None):
            QMessageBox.information(self, "No record selected",
                                     "Select a customer from the list before deleting.")
            return

        confirm = QMessageBox.question(
            self, "Confirm delete",
            f"Are you sure you want to delete customer #{self._current_customer_id}? "
            f"This may fail if this customer has Jobs linked to them.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM clients WHERE ID = %s", (self._current_customer_id,))
            conn.commit()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error",
                                  f"Could not delete customer (it may have Jobs linked to it):\n{e}")
            return

        QMessageBox.information(self, "Deleted", "Customer deleted.")
        self.new_customer_record()
        self.load_customers()
        self._refresh_client_name_completer()
