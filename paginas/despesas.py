# -*- coding: utf-8 -*-
"""
Expenses: lista e formulário de despesas, Sales Tax e Job Costing
(vincular despesa a um Job Code).

Métodos da MainWindow (mixin) — veja main_.py.
"""

from app_common import *  # noqa: F401,F403


class ExpensesMixin:
    def _setup_sales_tax_feature(self):
        """Adiciona, em tempo de execução (sem editar o .ui), uma checkbox no
        formulário de Products: 'Sales tax already paid when I buy this
        material'. Na Flórida, contratado que compra material no varejo já
        paga sales tax na hora da compra — então, ao revender/cobrar isso do
        cliente num contrato fechado (lump-sum), normalmente NÃO se cobra
        sales tax de novo. Isso só marca a situação de cada produto pra você
        ter esse controle; não mexe em cálculo de fatura."""
        self.ui.chk_product_tax_paid_at_purchase = QCheckBox(
            "Sales tax already paid when I buy this material (most retail purchases)",
            self.ui.tab_product_form,
        )
        self.ui.chk_product_tax_paid_at_purchase.setObjectName(u"chk_product_tax_paid_at_purchase")
        self.ui.chk_product_tax_paid_at_purchase.setChecked(True)
        insert_at = max(0, self.ui.layout_tab_product_form.count() - 1)
        self.ui.layout_tab_product_form.insertWidget(insert_at, self.ui.chk_product_tax_paid_at_purchase)

    def _setup_project_budget_feature(self):
        """Injeta, em tempo de execução (sem editar o .ui), o combo 'Job
        Code (optional)' no formulário de Expenses — é o que permite marcar
        que uma despesa pertence a um projeto específico, pra depois
        aparecer somada em 'Budget x Actual' na tela de Project View."""
        row = QWidget(self.ui.frame_expense_card)
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 6, 0, 6)
        row_layout.addWidget(QLabel("Job Code (optional):"))
        self.ui.cmb_expense_job_code = QComboBox()
        self.ui.cmb_expense_job_code.setObjectName(u"cmb_expense_job_code")
        row_layout.addWidget(self.ui.cmb_expense_job_code, 1)
        self.ui.layout_expense_card.insertWidget(2, row)
        self._refresh_expense_job_code_combo()

    def _refresh_expense_job_code_combo(self):
        """Recarrega a lista de Job Codes disponíveis no combo da despesa,
        preservando a seleção atual quando possível."""
        combo = self.ui.cmb_expense_job_code
        current = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("— None —", None)
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT ID, CODE FROM job_projects ORDER BY CODE DESC")
            for jp_id, code in cursor.fetchall():
                combo.addItem(code, jp_id)
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError):
            pass
        if current:
            pos = combo.findData(current)
            if pos >= 0:
                combo.setCurrentIndex(pos)
        combo.blockSignals(False)

    def load_expenses(self):
        """Carrega os registros de expenses na tabela, aplicando filtros."""
        search_text = self.ui.txt_search_expenses.text().strip()
        category_filter = self.ui.cmb_filter_expense_category.currentText()
        contractor_id_filter = self.ui.cmb_filter_expense_contractor.currentData()

        query = """
            SELECT e.ID, e.EXPENSE_DATE, e.CATEGORY, e.DESCRIPTION, e.AMOUNT,
                   COALESCE(c.COMPANY_NAME, c.FULL_NAME, co.COMPANY_NAME, cl.FULL_NAME, e.OTHER_NAME, '—') AS ENTITY_NAME,
                   e.SUBMITTED_BY
            FROM expenses e
            LEFT JOIN contractors c ON c.ID = e.CONTRACTOR_ID
            LEFT JOIN companies co ON co.ID = e.COMPANY_ID
            LEFT JOIN clients cl ON cl.ID = e.CLIENT_ID
            WHERE 1=1
        """
        params = []

        if search_text:
            query += " AND e.DESCRIPTION LIKE %s"
            params.append(f"%{search_text}%")

        if category_filter and category_filter != "All Categories":
            query += " AND e.CATEGORY = %s"
            params.append(category_filter)

        if contractor_id_filter:
            query += " AND e.CONTRACTOR_ID = %s"
            params.append(contractor_id_filter)

        query += " ORDER BY e.EXPENSE_DATE DESC, e.ID DESC"

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except MySQLError as e:
            QMessageBox.critical(self, "Database Error", f"Could not load expenses:\n{e}")
            return
        except RuntimeError as e:
            QMessageBox.warning(self, "Driver Missing", str(e))
            return

        self._populate_expenses_table(rows)
        self._refresh_expense_vendor_completer()

    def _populate_expenses_table(self, rows):
        """Preenche a tabela de Expenses linha a linha."""
        table = self.ui.table_expenses
        table.setSortingEnabled(False)
        table.setRowCount(0)
        table.setRowCount(len(rows))

        for row_idx, row_data in enumerate(rows):
            (expense_id, expense_date, category, description, amount,
             contractor_name, submitted_by) = row_data

            values = [
                str(expense_id),
                expense_date.strftime("%m/%d/%Y") if isinstance(expense_date, date) else str(expense_date or ""),
                str(category or ""),
                str(description or ""),
                f"${float(amount or 0):,.2f}",
                str(contractor_name or "—"),
                str(submitted_by or ""),
            ]

            for col_idx, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(row_idx, col_idx, item)

        table.setSortingEnabled(True)

    def _refresh_expense_entity_combo(self):
        """Repopula o combo de Name (cmb_expense_contractor) de acordo com o
        tipo escolhido (Contractor/Company/Client mostram só os cadastrados
        desse tipo; Others deixa livre pra digitar qualquer nome)."""
        entity_type = self.ui.cmb_expense_entity_type.currentText()
        combo = self.ui.cmb_expense_contractor
        combo.blockSignals(True)
        combo.clear()

        if entity_type == "Others":
            combo.setEditable(True)
            combo.blockSignals(False)
            return

        combo.setEditable(True)  # continua editável, mas populado com sugestões
        query_map = {
            "Contractor": "SELECT ID, COALESCE(COMPANY_NAME, FULL_NAME) FROM contractors ORDER BY COALESCE(COMPANY_NAME, FULL_NAME)",
            "Company": "SELECT ID, COMPANY_NAME FROM companies ORDER BY COMPANY_NAME",
            "Client": "SELECT ID, FULL_NAME FROM clients ORDER BY FULL_NAME",
        }
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query_map[entity_type])
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError):
            rows = []

        combo.addItem("— Select —", None)
        for entity_id, name in rows:
            combo.addItem(name or "", entity_id)
        combo.blockSignals(False)

    def _refresh_expense_vendor_completer(self):
        """Recarrega a lista de vendors/lojas já usados antes, pro combo
        de Vendor / Store (editável, com sugestões)."""
        combo = self.ui.cmb_expense_vendor
        current_text = combo.currentText()
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT DISTINCT VENDOR FROM expenses WHERE VENDOR IS NOT NULL AND VENDOR != '' ORDER BY VENDOR"
            )
            vendors = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError):
            vendors = []
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(vendors)
        combo.setCurrentText(current_text)
        combo.blockSignals(False)

    def new_expense_record(self):
        """Limpa o formulário para criar uma nova despesa."""
        self._current_expense_id = None
        self._current_expense_receipt_path = None
        self.ui.txt_expense_id.clear()
        self.ui.lbl_expense_id_display.setText("#ID: New")
        self.ui.date_expense.setDate(date.today())
        self.ui.cmb_expense_category.setCurrentIndex(0)
        self.ui.txt_expense_description.clear()
        self.ui.cmb_expense_vendor.setCurrentText("")
        self.ui.dspn_expense_amount.setValue(0)
        self.ui.cmb_expense_submitted_by.setCurrentIndex(0)
        self.ui.cmb_expense_entity_type.setCurrentIndex(0)
        self._refresh_expense_entity_combo()
        self.ui.cmb_expense_contractor.setCurrentIndex(0)
        self._refresh_expense_job_code_combo()
        self.ui.cmb_expense_job_code.setCurrentIndex(0)
        self.ui.txt_expense_receipt_path.clear()
        self.ui.tabWidget_receivables.setCurrentWidget(self.ui.tab_expenses_master)

    def load_expense_into_form(self):
        """Carrega a despesa selecionada na tabela para edição."""
        table = self.ui.table_expenses
        selected = table.currentRow()
        if selected < 0:
            return

        expense_id = table.item(selected, 0).text()
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM expenses WHERE ID = %s", (expense_id,))
            columns = [d[0] for d in cursor.description]
            row = cursor.fetchone()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not load expense:\n{e}")
            return

        if not row:
            return

        data = dict(zip(columns, row))
        self._current_expense_id = data["ID"]
        self._current_expense_receipt_path = data.get("RECEIPT_PATH")
        self.ui.txt_expense_id.setText(str(data["ID"]))
        self.ui.lbl_expense_id_display.setText(f"#ID: {data['ID']}")

        expense_date = data.get("EXPENSE_DATE")
        self.ui.date_expense.setDate(expense_date if isinstance(expense_date, date) else date.today())

        self._set_combo_by_data(self.ui.cmb_expense_category, data.get("CATEGORY"), by_text=True)
        self.ui.txt_expense_description.setText(data.get("DESCRIPTION") or "")
        self.ui.cmb_expense_vendor.setCurrentText(data.get("VENDOR") or "")
        try:
            self.ui.dspn_expense_amount.setValue(float(data.get("AMOUNT") or 0))
        except (TypeError, ValueError):
            self.ui.dspn_expense_amount.setValue(0)
        self._set_combo_by_data(self.ui.cmb_expense_submitted_by, data.get("SUBMITTED_BY"), by_text=True)

        entity_type = data.get("ENTITY_TYPE") or "Contractor"
        self._set_combo_by_data(self.ui.cmb_expense_entity_type, entity_type, by_text=True)
        self._refresh_expense_entity_combo()
        if entity_type == "Contractor":
            self._set_combo_by_data(self.ui.cmb_expense_contractor, data.get("CONTRACTOR_ID"))
        elif entity_type == "Company":
            self._set_combo_by_data(self.ui.cmb_expense_contractor, data.get("COMPANY_ID"))
        elif entity_type == "Client":
            self._set_combo_by_data(self.ui.cmb_expense_contractor, data.get("CLIENT_ID"))
        else:
            self.ui.cmb_expense_contractor.setCurrentText(data.get("OTHER_NAME") or "")

        self._refresh_expense_job_code_combo()
        self._set_combo_by_data(self.ui.cmb_expense_job_code, data.get("JOB_PROJECT_ID"))

        self.ui.txt_expense_receipt_path.setText(data.get("RECEIPT_PATH") or "")

        self.ui.tabWidget_receivables.setCurrentWidget(self.ui.tab_expenses_master)

    def attach_expense_receipt(self):
        """Abre um seletor de arquivo pra anexar o recibo (foto ou PDF) da despesa."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select Receipt File", "", "Images and PDFs (*.png *.jpg *.jpeg *.pdf)"
        )
        if filepath:
            self._current_expense_receipt_path = filepath
            self.ui.txt_expense_receipt_path.setText(filepath)

    def save_expense_record(self):
        """Insere ou atualiza um registro em expenses."""
        amount = self.ui.dspn_expense_amount.value()
        if amount <= 0:
            QMessageBox.warning(self, "Missing data", "Amount must be greater than zero.")
            return

        entity_type = self.ui.cmb_expense_entity_type.currentText()
        contractor_id = company_id = client_id = other_name = None
        if entity_type == "Contractor":
            contractor_id = self.ui.cmb_expense_contractor.currentData()
        elif entity_type == "Company":
            company_id = self.ui.cmb_expense_contractor.currentData()
        elif entity_type == "Client":
            client_id = self.ui.cmb_expense_contractor.currentData()
        else:
            other_name = self.ui.cmb_expense_contractor.currentText().strip() or None

        data = {
            "EXPENSE_DATE": self.ui.date_expense.date().toString("yyyy-MM-dd"),
            "CATEGORY": self.ui.cmb_expense_category.currentText(),
            "DESCRIPTION": self.ui.txt_expense_description.text(),
            "VENDOR": self.ui.cmb_expense_vendor.currentText().strip() or None,
            "AMOUNT": amount,
            "ENTITY_TYPE": entity_type,
            "CONTRACTOR_ID": contractor_id,
            "COMPANY_ID": company_id,
            "CLIENT_ID": client_id,
            "OTHER_NAME": other_name,
            "SUBMITTED_BY": self.ui.cmb_expense_submitted_by.currentText(),
            "RECEIPT_PATH": self.ui.txt_expense_receipt_path.text() or None,
        }
        data_with_job = dict(data, JOB_PROJECT_ID=self.ui.cmb_expense_job_code.currentData())

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            try:
                if getattr(self, "_current_expense_id", None):
                    set_clause = ", ".join(f"{k} = %s" for k in data_with_job)
                    query = f"UPDATE expenses SET {set_clause} WHERE ID = %s"
                    cursor.execute(query, list(data_with_job.values()) + [self._current_expense_id])
                else:
                    cols = ", ".join(data_with_job.keys())
                    placeholders = ", ".join(["%s"] * len(data_with_job))
                    query = f"INSERT INTO expenses ({cols}) VALUES ({placeholders})"
                    cursor.execute(query, list(data_with_job.values()))
                job_link_saved = True
            except MySQLError:
                # migration_fase3_budget_expenses.sql ainda não rodou nesse banco —
                # salva sem o vínculo de Job Code em vez de travar o cadastro de despesa.
                conn.rollback()
                if getattr(self, "_current_expense_id", None):
                    set_clause = ", ".join(f"{k} = %s" for k in data)
                    query = f"UPDATE expenses SET {set_clause} WHERE ID = %s"
                    cursor.execute(query, list(data.values()) + [self._current_expense_id])
                else:
                    cols = ", ".join(data.keys())
                    placeholders = ", ".join(["%s"] * len(data))
                    query = f"INSERT INTO expenses ({cols}) VALUES ({placeholders})"
                    cursor.execute(query, list(data.values()))
                job_link_saved = False

            conn.commit()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not save expense:\n{e}")
            return

        if not job_link_saved and self.ui.cmb_expense_job_code.currentData():
            QMessageBox.information(
                self, "Success",
                "Expense saved successfully.\n\n"
                "Note: the Job Code link was NOT saved — run migration_fase3_budget_expenses.sql "
                "on the database to enable it.",
            )
        else:
            QMessageBox.information(self, "Success", "Expense saved successfully.")
        self.load_expenses()
        self.new_expense_record()
        self.ui.tabWidget_receivables.setCurrentWidget(self.ui.tab_expenses_master)

    def delete_expense_record(self):
        """Exclui a despesa atualmente carregada no formulário."""
        if not getattr(self, "_current_expense_id", None):
            QMessageBox.information(self, "No record selected",
                                     "Select an expense from the list before deleting.")
            return

        confirm = QMessageBox.question(
            self, "Confirm delete",
            f"Are you sure you want to delete expense #{self._current_expense_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM expenses WHERE ID = %s", (self._current_expense_id,))
            conn.commit()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not delete expense:\n{e}")
            return

        QMessageBox.information(self, "Deleted", "Expense deleted.")
        self.new_expense_record()
        self.load_expenses()
        self.ui.tabWidget_receivables.setCurrentWidget(self.ui.tab_expenses_master)
