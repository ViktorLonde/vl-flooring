# -*- coding: utf-8 -*-
"""
Cadastros: Companies, Contractors, Work Types e Products.

Métodos da MainWindow (mixin) — veja main_.py.
"""

from app_common import *  # noqa: F401,F403


class RegistrationsMixin:
    def load_companies(self):
        """Carrega os registros de company na tabela, aplicando filtros de busca e status."""
        search_text = self.ui.txt_search_companies.text().strip()
        status_filter = self.ui.cmb_filter_company_status.currentText()

        query = """
            SELECT
                co.ID, co.COMPANY_NAME, co.CONTACT_NAME, co.EMAIL,
                co.PHONE_NUMBER, co.PHONE_NUMBER2, co.ADDRESS,
                COALESCE(city.CITY, co.CITY_ID) AS CITY_NAME,
                COALESCE(st.STATE_NAME, co.STATE_ID) AS STATE_NAME,
                co.ZIP_CODE, co.WEBSITE, co.STATUS
            FROM companies co
            LEFT JOIN cities city ON city.ID = co.CITY_ID
            LEFT JOIN states st ON st.ID = co.STATE_ID
            WHERE 1=1
        """
        params = []

        if search_text:
            query += """
                AND (co.COMPANY_NAME LIKE %s
                     OR co.CONTACT_NAME LIKE %s
                     OR COALESCE(city.CITY, '') LIKE %s)
            """
            like = f"%{search_text}%"
            params.extend([like, like, like])

        if status_filter and status_filter != "All Status":
            query += " AND co.STATUS = %s"
            params.append(status_filter)

        query += " ORDER BY co.COMPANY_NAME ASC"

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except MySQLError as e:
            QMessageBox.critical(self, "Database Error", f"Could not load companies:\n{e}")
            return
        except RuntimeError as e:
            QMessageBox.warning(self, "Driver Missing", str(e))
            return

        self._populate_companies_table(rows)

    def _populate_companies_table(self, rows):
        """Preenche a tabela de Companies linha a linha."""
        table = self.ui.table_companies
        table.setSortingEnabled(False)
        table.setRowCount(0)
        table.setRowCount(len(rows))

        for row_idx, row_data in enumerate(rows):
            (company_id, name, contact_name, email, phone, phone2,
             address, city, state, zip_code, website, status) = row_data

            values = [
                str(company_id),
                str(name or ""),
                str(contact_name or "—"),
                str(email or ""),
                self._format_phone(phone) or "",
                self._format_phone(phone2) or "",
                str(address or ""),
                str(city or "—"),
                str(state or "—"),
                str(zip_code or ""),
                str(website or ""),
                str(status or ""),
            ]

            for col_idx, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(row_idx, col_idx, item)

        table.setSortingEnabled(True)

    def new_company_record(self):
        """Limpa o formulário para criar uma nova empresa."""
        self._current_company_id = None
        self.ui.txt_company_id.clear()
        self.ui.lbl_company_id_display.setText("#ID: New")
        for field in (self.ui.txt_company_name, self.ui.txt_contact_name,
                      self.ui.txt_company_email, self.ui.txt_company_phone,
                      self.ui.txt_company_phone2, self.ui.txt_company_address,
                      self.ui.txt_company_address2, self.ui.txt_company_zip,
                      self.ui.txt_company_website, self.ui.txt_company_instagram,
                      self.ui.txt_company_facebook, self.ui.txt_company_linkedin,
                      self.ui.txt_company_twitter):
            field.clear()
        self.ui.txt_company_notes.clear()
        self.ui.cmb_company_city.setCurrentIndex(0)
        self.ui.cmb_company_state.setCurrentIndex(0)
        self._reload_city_combo_for_state(self.ui.cmb_company_city, None)
        self.ui.cmb_company_status.setCurrentIndex(0)
        self.ui.tabWidget_companies_page.setCurrentWidget(self.ui.tab_companies_master)

    def load_company_into_form(self):
        """Carrega a empresa selecionada na tabela para edição."""
        table = self.ui.table_companies
        selected = table.currentRow()
        if selected < 0:
            return

        company_id = table.item(selected, 0).text()
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM companies WHERE ID = %s", (company_id,))
            columns = [d[0] for d in cursor.description]
            row = cursor.fetchone()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not load company:\n{e}")
            return

        if not row:
            return

        data = dict(zip(columns, row))
        self._current_company_id = data["ID"]
        self.ui.txt_company_id.setText(str(data["ID"]))
        self.ui.lbl_company_id_display.setText(f"#ID: {data['ID']}")

        self.ui.txt_company_name.setText(data.get("COMPANY_NAME") or "")
        self.ui.txt_contact_name.setText(data.get("CONTACT_NAME") or "")
        self.ui.txt_company_email.setText(data.get("EMAIL") or "")
        self.ui.txt_company_phone.setText(self._format_phone(data.get("PHONE_NUMBER")) or "")
        self.ui.txt_company_phone2.setText(self._format_phone(data.get("PHONE_NUMBER2")) or "")
        self.ui.txt_company_address.setText(data.get("ADDRESS") or "")
        self.ui.txt_company_address2.setText(data.get("ADDRESS2") or "")
        self.ui.txt_company_zip.setText(self._format_zip(data.get("ZIP_CODE")) or "")
        self.ui.txt_company_website.setText(data.get("WEBSITE") or "")
        self.ui.txt_company_instagram.setText(data.get("INSTAGRAM") or "")
        self.ui.txt_company_facebook.setText(data.get("FACEBOOK") or "")
        self.ui.txt_company_linkedin.setText(data.get("LINKEDIN") or "")
        self.ui.txt_company_twitter.setText(data.get("TWITTER") or "")
        self.ui.txt_company_notes.setPlainText(data.get("NOTES") or "")

        self._set_combo_by_data(self.ui.cmb_company_state, data.get("STATE_ID"))
        self._reload_city_combo_for_state(self.ui.cmb_company_city, data.get("STATE_ID"), keep_city_id=data.get("CITY_ID"))
        self._set_combo_by_data(self.ui.cmb_company_status, data.get("STATUS"), by_text=True)

        self.ui.tabWidget_companies_page.setCurrentWidget(self.ui.tab_companies_master)

    def save_company_record(self):
        """Insere ou atualiza um registro em company."""
        name = self.ui.txt_company_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing data", "Company Name is required.")
            return

        data = {
            "COMPANY_NAME": name,
            "CONTACT_NAME": self.ui.txt_contact_name.text(),
            "EMAIL": self.ui.txt_company_email.text(),
            "PHONE_NUMBER": self._format_phone(self.ui.txt_company_phone.text()),
            "PHONE_NUMBER2": self._format_phone(self.ui.txt_company_phone2.text()),
            "ADDRESS": self.ui.txt_company_address.text(),
            "ADDRESS2": self.ui.txt_company_address2.text(),
            "CITY_ID": self.ui.cmb_company_city.currentData(),
            "STATE_ID": self.ui.cmb_company_state.currentData(),
            "ZIP_CODE": self._format_zip(self.ui.txt_company_zip.text()),
            "WEBSITE": self.ui.txt_company_website.text(),
            "INSTAGRAM": self.ui.txt_company_instagram.text(),
            "FACEBOOK": self.ui.txt_company_facebook.text(),
            "LINKEDIN": self.ui.txt_company_linkedin.text(),
            "TWITTER": self.ui.txt_company_twitter.text(),
            "STATUS": self.ui.cmb_company_status.currentText(),
            "NOTES": self.ui.txt_company_notes.toPlainText(),
        }

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            if getattr(self, "_current_company_id", None):
                set_clause = ", ".join(f"{k} = %s" for k in data)
                query = f"UPDATE companies SET {set_clause} WHERE ID = %s"
                cursor.execute(query, list(data.values()) + [self._current_company_id])
            else:
                cols = ", ".join(data.keys())
                placeholders = ", ".join(["%s"] * len(data))
                query = f"INSERT INTO companies ({cols}) VALUES ({placeholders})"
                cursor.execute(query, list(data.values()))

            conn.commit()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not save company:\n{e}")
            return

        QMessageBox.information(self, "Success", "Company saved successfully.")
        self.load_companies()
        self.load_combo_data()  # atualiza combo de company usado no form de Jobs
        self.new_company_record()
        self.ui.tabWidget_companies_page.setCurrentWidget(self.ui.tab_companies_master)

    def delete_company_record(self):
        """Exclui a empresa atualmente carregada no formulário."""
        if not getattr(self, "_current_company_id", None):
            QMessageBox.information(self, "No record selected",
                                     "Select a company from the list before deleting.")
            return

        confirm = QMessageBox.question(
            self, "Confirm delete",
            f"Are you sure you want to delete company #{self._current_company_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM companies WHERE ID = %s", (self._current_company_id,))
            conn.commit()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not delete company:\n{e}")
            return

        QMessageBox.information(self, "Deleted", "Company deleted.")
        self.new_company_record()
        self.load_companies()
        self.ui.tabWidget_companies_page.setCurrentWidget(self.ui.tab_companies_master)

    def load_contractors(self):
        """Carrega os registros de contractor na tabela, aplicando filtros de busca e status."""
        search_text = self.ui.txt_search_contractors.text().strip()
        status_filter = self.ui.cmb_filter_contractor_status.currentText()

        query = """
            SELECT
                c.ID, c.FULL_NAME, c.EMAIL, c.PHONE_NUMBER, c.POSITION,
                c.COMPANY_NAME, c.COMPANY_PHONE_NUMBER,
                COALESCE(city.CITY, c.CITY_ID) AS CITY_NAME,
                COALESCE(st.STATE_NAME, c.STATE_ID) AS STATE_NAME,
                c.STATUS
            FROM contractors c
            LEFT JOIN cities city ON city.ID = c.CITY_ID
            LEFT JOIN states st ON st.ID = c.STATE_ID
            WHERE 1=1
        """
        params = []

        if search_text:
            query += """
                AND (c.FULL_NAME LIKE %s
                     OR c.COMPANY_NAME LIKE %s
                     OR COALESCE(city.CITY, '') LIKE %s)
            """
            like = f"%{search_text}%"
            params.extend([like, like, like])

        if status_filter and status_filter != "All Status":
            query += " AND c.STATUS = %s"
            params.append(status_filter)

        query += " ORDER BY c.FULL_NAME ASC"

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except MySQLError as e:
            QMessageBox.critical(self, "Database Error", f"Could not load contractors:\n{e}")
            return
        except RuntimeError as e:
            QMessageBox.warning(self, "Driver Missing", str(e))
            return

        self._populate_contractors_table(rows)

    def _populate_contractors_table(self, rows):
        """Preenche a tabela de Contractors linha a linha."""
        table = self.ui.table_contractors
        table.setSortingEnabled(False)
        table.setRowCount(0)
        table.setRowCount(len(rows))

        for row_idx, row_data in enumerate(rows):
            (contractor_id, full_name, email, phone, position,
             company_name, company_phone, city, state, status) = row_data

            values = [
                str(contractor_id),
                str(full_name or ""),
                str(email or ""),
                self._format_phone(phone) or "",
                str(position or ""),
                str(company_name or "—"),
                self._format_phone(company_phone) or "",
                str(city or "—"),
                str(state or "—"),
                str(status or ""),
            ]

            for col_idx, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(row_idx, col_idx, item)

        table.setSortingEnabled(True)

    def new_contractor_record(self):
        """Limpa o formulário para criar um novo contractor."""
        self._current_contractor_id = None
        self.ui.txt_contractor_id.clear()
        self.ui.lbl_contractor_id_display.setText("#ID: New")
        for field in (self.ui.txt_contractor_full_name, self.ui.txt_contractor_position,
                      self.ui.txt_contractor_email, self.ui.txt_contractor_phone,
                      self.ui.txt_contractor_phone2, self.ui.txt_contractor_company_name,
                      self.ui.txt_contractor_company_email, self.ui.txt_contractor_company_phone,
                      self.ui.txt_contractor_company_phone2, self.ui.txt_contractor_address,
                      self.ui.txt_contractor_address2, self.ui.txt_contractor_zip,
                      self.ui.txt_contractor_website, self.ui.txt_contractor_instagram,
                      self.ui.txt_contractor_facebook, self.ui.txt_contractor_linkedin,
                      self.ui.txt_contractor_twitter):
            field.clear()
        self.ui.txt_contractor_notes.clear()
        self.ui.cmb_contractor_city.setCurrentIndex(0)
        self.ui.cmb_contractor_state.setCurrentIndex(0)
        self._reload_city_combo_for_state(self.ui.cmb_contractor_city, None)
        self.ui.cmb_contractor_status.setCurrentIndex(0)
        self.ui.cmb_contractor_payment_cycle_type.setCurrentIndex(0)
        self.ui.cmb_contractor_payment_cycle_weekday.setCurrentIndex(5)  # Friday por padrão
        self.ui.spin_contractor_payment_cycle_days.setValue(30)
        self.ui.tabWidget_contractors_page.setCurrentWidget(self.ui.tab_contractors_master)

    def load_contractor_into_form(self):
        """Carrega o contractor selecionado na tabela para edição."""
        table = self.ui.table_contractors
        selected = table.currentRow()
        if selected < 0:
            return

        contractor_id = table.item(selected, 0).text()
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM contractors WHERE ID = %s", (contractor_id,))
            columns = [d[0] for d in cursor.description]
            row = cursor.fetchone()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not load contractor:\n{e}")
            return

        if not row:
            return

        data = dict(zip(columns, row))
        self._current_contractor_id = data["ID"]
        self.ui.txt_contractor_id.setText(str(data["ID"]))
        self.ui.lbl_contractor_id_display.setText(f"#ID: {data['ID']}")

        self.ui.txt_contractor_full_name.setText(data.get("FULL_NAME") or "")
        self.ui.txt_contractor_position.setText(data.get("POSITION") or "")
        self.ui.txt_contractor_email.setText(data.get("EMAIL") or "")
        self.ui.txt_contractor_phone.setText(self._format_phone(data.get("PHONE_NUMBER")) or "")
        self.ui.txt_contractor_phone2.setText(self._format_phone(data.get("PHONE_NUMBER2")) or "")
        self.ui.txt_contractor_company_name.setText(data.get("COMPANY_NAME") or "")
        self.ui.txt_contractor_company_email.setText(data.get("COMPANY_EMAIL") or "")
        self.ui.txt_contractor_company_phone.setText(self._format_phone(data.get("COMPANY_PHONE_NUMBER")) or "")
        self.ui.txt_contractor_company_phone2.setText(self._format_phone(data.get("COMPANY_PHONE_NUMBER2")) or "")
        self.ui.txt_contractor_address.setText(data.get("ADDRESS") or "")
        self.ui.txt_contractor_address2.setText(data.get("ADDRESS2") or "")
        self.ui.txt_contractor_zip.setText(self._format_zip(data.get("ZIP_CODE")) or "")
        self.ui.txt_contractor_website.setText(data.get("WEBSITE") or "")
        self.ui.txt_contractor_instagram.setText(data.get("INSTAGRAM") or "")
        self.ui.txt_contractor_facebook.setText(data.get("FACEBOOK") or "")
        self.ui.txt_contractor_linkedin.setText(data.get("LINKEDIN") or "")
        self.ui.txt_contractor_twitter.setText(data.get("TWITTER") or "")
        self.ui.txt_contractor_notes.setPlainText(data.get("NOTES") or "")

        self._set_combo_by_data(self.ui.cmb_contractor_state, data.get("STATE_ID"))
        self._reload_city_combo_for_state(self.ui.cmb_contractor_city, data.get("STATE_ID"), keep_city_id=data.get("CITY_ID"))
        self._set_combo_by_data(self.ui.cmb_contractor_status, data.get("STATUS"), by_text=True)

        cycle_type = data.get("PAYMENT_CYCLE_TYPE") or "CUSTOM_DAYS"
        cycle_type_display = {"WEEKLY": "Weekly", "BIWEEKLY": "Biweekly", "CUSTOM_DAYS": "Custom Days"}.get(cycle_type, "Custom Days")
        self.ui.cmb_contractor_payment_cycle_type.setCurrentText(cycle_type_display)
        weekday_idx = data.get("PAYMENT_CYCLE_WEEKDAY")
        self.ui.cmb_contractor_payment_cycle_weekday.setCurrentIndex(weekday_idx if weekday_idx is not None else 5)
        self.ui.spin_contractor_payment_cycle_days.setValue(data.get("PAYMENT_CYCLE_DAYS") or 30)

        self.ui.tabWidget_contractors_page.setCurrentWidget(self.ui.tab_contractors_master)

    def save_contractor_record(self):
        """Insere ou atualiza um registro em contractor."""
        full_name = self.ui.txt_contractor_full_name.text().strip()
        company_name = self.ui.txt_contractor_company_name.text().strip()

        if not full_name:
            QMessageBox.warning(self, "Missing data", "Full Name is required.")
            return
        if not company_name:
            QMessageBox.warning(self, "Missing data", "Company Name is required.")
            return

        cycle_type_map = {"Weekly": "WEEKLY", "Biweekly": "BIWEEKLY", "Custom Days": "CUSTOM_DAYS"}

        data = {
            "FULL_NAME": full_name,
            "EMAIL": self.ui.txt_contractor_email.text(),
            "PHONE_NUMBER": self._format_phone(self.ui.txt_contractor_phone.text()),
            "PHONE_NUMBER2": self._format_phone(self.ui.txt_contractor_phone2.text()),
            "COMPANY_NAME": company_name,
            "COMPANY_EMAIL": self.ui.txt_contractor_company_email.text(),
            "COMPANY_PHONE_NUMBER": self._format_phone(self.ui.txt_contractor_company_phone.text()),
            "COMPANY_PHONE_NUMBER2": self._format_phone(self.ui.txt_contractor_company_phone2.text()),
            "ADDRESS": self.ui.txt_contractor_address.text(),
            "ADDRESS2": self.ui.txt_contractor_address2.text(),
            "CITY_ID": self.ui.cmb_contractor_city.currentData(),
            "STATE_ID": self.ui.cmb_contractor_state.currentData(),
            "ZIP_CODE": self._format_zip(self.ui.txt_contractor_zip.text()),
            "INSTAGRAM": self.ui.txt_contractor_instagram.text(),
            "FACEBOOK": self.ui.txt_contractor_facebook.text(),
            "LINKEDIN": self.ui.txt_contractor_linkedin.text(),
            "TWITTER": self.ui.txt_contractor_twitter.text(),
            "WEBSITE": self.ui.txt_contractor_website.text(),
            "STATUS": self.ui.cmb_contractor_status.currentText(),
            "POSITION": self.ui.txt_contractor_position.text(),
            "NOTES": self.ui.txt_contractor_notes.toPlainText(),
            "PAYMENT_CYCLE_TYPE": cycle_type_map.get(self.ui.cmb_contractor_payment_cycle_type.currentText(), "CUSTOM_DAYS"),
            "PAYMENT_CYCLE_WEEKDAY": self.ui.cmb_contractor_payment_cycle_weekday.currentIndex(),
            "PAYMENT_CYCLE_DAYS": self.ui.spin_contractor_payment_cycle_days.value(),
        }

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            if getattr(self, "_current_contractor_id", None):
                set_clause = ", ".join(f"{k} = %s" for k in data)
                query = f"UPDATE contractors SET {set_clause} WHERE ID = %s"
                cursor.execute(query, list(data.values()) + [self._current_contractor_id])
            else:
                cols = ", ".join(data.keys())
                placeholders = ", ".join(["%s"] * len(data))
                query = f"INSERT INTO contractors ({cols}) VALUES ({placeholders})"
                cursor.execute(query, list(data.values()))

            conn.commit()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not save contractor:\n{e}")
            return

        QMessageBox.information(self, "Success", "Contractor saved successfully.")
        self.load_contractors()
        self.load_combo_data()  # atualiza combo de contractor usado no form de Jobs
        self.new_contractor_record()
        self.ui.tabWidget_contractors_page.setCurrentWidget(self.ui.tab_contractors_master)

    def delete_contractor_record(self):
        """Exclui o contractor atualmente carregado no formulário."""
        if not getattr(self, "_current_contractor_id", None):
            QMessageBox.information(self, "No record selected",
                                     "Select a contractor from the list before deleting.")
            return

        confirm = QMessageBox.question(
            self, "Confirm delete",
            f"Are you sure you want to delete contractor #{self._current_contractor_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM contractors WHERE ID = %s", (self._current_contractor_id,))
            conn.commit()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not delete contractor:\n{e}")
            return

        QMessageBox.information(self, "Deleted", "Contractor deleted.")
        self.new_contractor_record()
        self.load_contractors()
        self.ui.tabWidget_contractors_page.setCurrentWidget(self.ui.tab_contractors_master)

    def load_work_types(self):
        """Carrega os registros de work_types na tabela, aplicando filtros de busca e categoria."""
        search_text = self.ui.txt_search_work_types.text().strip()
        category_filter = self.ui.cmb_filter_work_type_category.currentText()

        query = "SELECT ID, CATEGORY, NAME, UNIT FROM work_types WHERE 1=1"
        params = []

        if search_text:
            query += " AND NAME LIKE %s"
            params.append(f"%{search_text}%")

        if category_filter and category_filter != "All Categories":
            query += " AND CATEGORY = %s"
            params.append(category_filter)

        query += " ORDER BY CATEGORY, NAME"

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except MySQLError as e:
            QMessageBox.critical(self, "Database Error", f"Could not load work types:\n{e}")
            return
        except RuntimeError as e:
            QMessageBox.warning(self, "Driver Missing", str(e))
            return

        self._populate_work_types_table(rows)

    def _populate_work_types_table(self, rows):
        """Preenche a tabela de Work Types linha a linha."""
        table = self.ui.table_work_types
        table.setSortingEnabled(False)
        table.setRowCount(0)
        table.setRowCount(len(rows))

        for row_idx, (type_id, category, name, unit) in enumerate(rows):
            values = [str(type_id), str(category or ""), str(name or ""), str(unit or "")]
            for col_idx, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(row_idx, col_idx, item)

        table.setSortingEnabled(True)

    def new_work_type_record(self):
        """Limpa o formulário para criar um novo tipo de trabalho."""
        self._current_work_type_id = None
        self.ui.txt_work_type_id.clear()
        self.ui.lbl_work_type_id_display.setText("#ID: New")
        self.ui.cmb_work_type_category.setCurrentIndex(0)
        self.ui.txt_work_type_unit.clear()
        self.ui.txt_work_type_name.clear()
        self.ui.tabWidget_work_types_page.setCurrentWidget(self.ui.tab_work_types_master)

    def load_work_type_into_form(self):
        """Carrega o tipo de trabalho selecionado na tabela para edição."""
        table = self.ui.table_work_types
        selected = table.currentRow()
        if selected < 0:
            return

        type_id = table.item(selected, 0).text()
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT ID, CATEGORY, NAME, UNIT FROM work_types WHERE ID = %s", (type_id,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not load work type:\n{e}")
            return

        if not row:
            return

        wt_id, category, name, unit = row
        self._current_work_type_id = wt_id
        self.ui.txt_work_type_id.setText(str(wt_id))
        self.ui.lbl_work_type_id_display.setText(f"#ID: {wt_id}")
        self._set_combo_by_data(self.ui.cmb_work_type_category, category, by_text=True)
        self.ui.txt_work_type_unit.setText(unit or "")
        self.ui.txt_work_type_name.setText(name or "")

        self.ui.tabWidget_work_types_page.setCurrentWidget(self.ui.tab_work_types_master)

    def save_work_type_record(self):
        """Insere ou atualiza um registro em work_types."""
        name = self.ui.txt_work_type_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing data", "Name is required.")
            return

        category = self.ui.cmb_work_type_category.currentText()
        unit = self.ui.txt_work_type_unit.text().strip().upper()

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            if getattr(self, "_current_work_type_id", None):
                cursor.execute(
                    "UPDATE work_types SET CATEGORY = %s, NAME = %s, UNIT = %s WHERE ID = %s",
                    (category, name, unit, self._current_work_type_id),
                )
            else:
                cursor.execute(
                    "INSERT INTO work_types (CATEGORY, NAME, UNIT) VALUES (%s, %s, %s)",
                    (category, name, unit),
                )

            conn.commit()
            cursor.close()
            conn.close()
        except MySQLError as e:
            if e.errno == 1062:
                QMessageBox.warning(self, "Duplicate Entry",
                                     "This name already exists for this category.")
            else:
                QMessageBox.critical(self, "Database Error", f"Could not save work type:\n{e}")
            return
        except RuntimeError as e:
            QMessageBox.warning(self, "Driver Missing", str(e))
            return

        QMessageBox.information(self, "Success", "Work type saved successfully.")
        self.load_work_types()
        self.new_work_type_record()
        self.ui.tabWidget_work_types_page.setCurrentWidget(self.ui.tab_work_types_master)

    def delete_work_type_record(self):
        """Exclui o tipo de trabalho atualmente carregado no formulário."""
        if not getattr(self, "_current_work_type_id", None):
            QMessageBox.information(self, "No record selected",
                                     "Select a work type from the list before deleting.")
            return

        confirm = QMessageBox.question(
            self, "Confirm delete",
            f"Are you sure you want to delete work type #{self._current_work_type_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM work_types WHERE ID = %s", (self._current_work_type_id,))
            conn.commit()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not delete work type:\n{e}")
            return

        QMessageBox.information(self, "Deleted", "Work type deleted.")
        self.new_work_type_record()
        self.load_work_types()
        self.ui.tabWidget_work_types_page.setCurrentWidget(self.ui.tab_work_types_master)

    def _setup_product_unit_completer(self):
        """Configura o autocomplete dos campos Type, Name, Unit e Coverage Unit
        (sugere o que já foi usado antes em outros produtos)."""
        self._product_type_completer = QCompleter([], self)
        self._product_type_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._product_type_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._product_type_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.ui.txt_product_type.setCompleter(self._product_type_completer)

        self._product_name_completer = QCompleter([], self)
        self._product_name_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._product_name_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._product_name_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.ui.txt_product_name.setCompleter(self._product_name_completer)

        self._product_brand_completer = QCompleter([], self)
        self._product_brand_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._product_brand_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._product_brand_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.ui.txt_product_brand.setCompleter(self._product_brand_completer)

        self._product_unit_completer = QCompleter([], self)
        self._product_unit_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._product_unit_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._product_unit_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.ui.txt_product_unit.setCompleter(self._product_unit_completer)

        self._product_coverage_unit_completer = QCompleter([], self)
        self._product_coverage_unit_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._product_coverage_unit_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._product_coverage_unit_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.ui.txt_product_coverage_unit.setCompleter(self._product_coverage_unit_completer)

    def _refresh_product_unit_completer(self):
        """Recarrega a lista de valores já usados, pros autocompletes de
        Type, Name, Unit e Coverage Unit."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT DISTINCT TYPE FROM products WHERE TYPE IS NOT NULL AND TYPE != '' ORDER BY TYPE"
            )
            types = [row[0] for row in cursor.fetchall()]
            cursor.execute(
                "SELECT DISTINCT NAME FROM products WHERE NAME IS NOT NULL AND NAME != '' ORDER BY NAME"
            )
            names = [row[0] for row in cursor.fetchall()]
            cursor.execute(
                "SELECT DISTINCT BRAND FROM products WHERE BRAND IS NOT NULL AND BRAND != '' ORDER BY BRAND"
            )
            brands = [row[0] for row in cursor.fetchall()]
            cursor.execute(
                "SELECT DISTINCT UNIT FROM products WHERE UNIT IS NOT NULL AND UNIT != '' ORDER BY UNIT"
            )
            units = [row[0] for row in cursor.fetchall()]
            cursor.execute(
                "SELECT DISTINCT COVERAGE_UNIT FROM products "
                "WHERE COVERAGE_UNIT IS NOT NULL AND COVERAGE_UNIT != '' ORDER BY COVERAGE_UNIT"
            )
            coverage_units = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError):
            types, names, units, coverage_units, brands = [], [], [], [], []
        self._product_type_completer.setModel(QStringListModel(types))
        self._product_name_completer.setModel(QStringListModel(names))
        self._product_brand_completer.setModel(QStringListModel(brands))
        self._product_unit_completer.setModel(QStringListModel(units))
        self._product_coverage_unit_completer.setModel(QStringListModel(coverage_units))

    def _suggest_unit_for_product_type(self):
        """Quando o usuário termina de digitar o Type, sugere automaticamente
        a unidade mais usada nos produtos que já têm esse mesmo Type (ex:
        'Flooring' → sugere 'SF', 'Adhesive' → sugere 'GAL'). Só preenche se
        o campo Unit ainda estiver vazio, pra não sobrescrever o que o
        usuário já escolheu."""
        if self.ui.txt_product_unit.text().strip():
            return  # já tem algo digitado, não mexe
        ptype = self.ui.txt_product_type.text().strip()
        if not ptype:
            return
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT UNIT, COUNT(*) AS cnt FROM products
                WHERE LOWER(TYPE) = LOWER(%s) AND UNIT IS NOT NULL AND UNIT != ''
                GROUP BY UNIT ORDER BY cnt DESC LIMIT 1
                """,
                (ptype,),
            )
            row = cursor.fetchone()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError):
            row = None

        if row:
            self.ui.txt_product_unit.setText(row[0])

    def load_products(self):
        """Carrega os registros de products na tabela, aplicando filtro de busca (nome, tipo ou marca)."""
        search_text = self.ui.txt_search_products.text().strip()

        query = "SELECT ID, TYPE, NAME, SPECIFICATION, PRICE, UNIT, BRAND FROM products WHERE 1=1"
        params = []
        if search_text:
            query += " AND (NAME LIKE %s OR TYPE LIKE %s OR BRAND LIKE %s)"
            like = f"%{search_text}%"
            params.extend([like, like, like])
        query += " ORDER BY TYPE, NAME"

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except MySQLError as e:
            QMessageBox.critical(self, "Database Error", f"Could not load products:\n{e}")
            return
        except RuntimeError as e:
            QMessageBox.warning(self, "Driver Missing", str(e))
            return

        self._populate_products_table(rows)
        self._refresh_product_unit_completer()

    def _populate_products_table(self, rows):
        """Preenche a tabela de Products linha a linha."""
        table = self.ui.table_products
        table.setSortingEnabled(False)
        table.setRowCount(0)
        table.setRowCount(len(rows))

        for row_idx, (product_id, ptype, name, specification, price, unit, brand) in enumerate(rows):
            price_str = f"${float(price or 0):,.2f}"
            if unit:
                price_str += f" / {unit}"
            values = [
                str(product_id), str(ptype or ""), str(name or ""),
                str(specification or ""), price_str, str(brand or ""),
            ]
            for col_idx, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(row_idx, col_idx, item)

        table.setSortingEnabled(True)

    def _update_product_unit_price_display(self):
        """Mostra, em destaque, o preço por unidade de cobertura (ex: $2.13 /
        SF), calculado na hora a partir de Price ÷ Coverage Quantity."""
        price = self.ui.dspn_product_price.value()
        coverage_qty = self.ui.dspn_product_coverage_qty.value()
        coverage_unit = self.ui.txt_product_coverage_unit.text().strip()

        if coverage_qty > 0 and coverage_unit:
            unit_price = price / coverage_qty
            self.ui.lbl_product_unit_price_display.setText(f"${unit_price:,.2f} / {coverage_unit}")
        else:
            self.ui.lbl_product_unit_price_display.setText("—")

    def new_product_record(self):
        """Limpa o formulário para criar um novo produto."""
        self._current_product_id = None
        self.ui.txt_product_id.clear()
        self.ui.lbl_product_id_display.setText("#ID: New")
        self.ui.txt_product_type.clear()
        self.ui.txt_product_name.clear()
        self.ui.txt_product_brand.clear()
        self.ui.txt_product_specification.clear()
        self.ui.dspn_product_price.setValue(0)
        self.ui.txt_product_unit.clear()
        self.ui.dspn_product_coverage_qty.setValue(0)
        self.ui.txt_product_coverage_unit.clear()
        self.ui.chk_product_tax_paid_at_purchase.setChecked(True)
        self._update_product_unit_price_display()
        self.ui.tabWidget_products_page.setCurrentWidget(self.ui.tab_product_form)

    def load_product_into_form(self):
        """Carrega o produto selecionado na tabela para edição."""
        table = self.ui.table_products
        selected = table.currentRow()
        if selected < 0:
            return

        product_id = table.item(selected, 0).text()
        tax_paid_at_purchase = True
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "SELECT ID, TYPE, NAME, SPECIFICATION, PRICE, UNIT, COVERAGE_QTY, COVERAGE_UNIT, BRAND, "
                    "SALES_TAX_PAID_AT_PURCHASE FROM products WHERE ID = %s",
                    (product_id,),
                )
                row = cursor.fetchone()
                has_tax_column = True
            except MySQLError:
                # migration_fase4_w9_salestax.sql ainda não rodou nesse banco —
                # carrega sem a coluna nova em vez de travar a tela.
                cursor.execute(
                    "SELECT ID, TYPE, NAME, SPECIFICATION, PRICE, UNIT, COVERAGE_QTY, COVERAGE_UNIT, BRAND "
                    "FROM products WHERE ID = %s",
                    (product_id,),
                )
                row = cursor.fetchone()
                has_tax_column = False
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not load product:\n{e}")
            return

        if not row:
            return

        if has_tax_column:
            p_id, ptype, name, specification, price, unit, coverage_qty, coverage_unit, brand, tax_flag = row
            tax_paid_at_purchase = bool(tax_flag) if tax_flag is not None else True
        else:
            p_id, ptype, name, specification, price, unit, coverage_qty, coverage_unit, brand = row

        self._current_product_id = p_id
        self.ui.txt_product_id.setText(str(p_id))
        self.ui.lbl_product_id_display.setText(f"#ID: {p_id}")
        self.ui.txt_product_type.setText(ptype or "")
        self.ui.txt_product_name.setText(name or "")
        self.ui.txt_product_brand.setText(brand or "")
        self.ui.txt_product_specification.setText(specification or "")
        self.ui.dspn_product_price.setValue(float(price or 0))
        self.ui.txt_product_unit.setText(unit or "")
        self.ui.dspn_product_coverage_qty.setValue(float(coverage_qty or 0))
        self.ui.txt_product_coverage_unit.setText(coverage_unit or "")
        self.ui.chk_product_tax_paid_at_purchase.setChecked(tax_paid_at_purchase)
        self._update_product_unit_price_display()

        self.ui.tabWidget_products_page.setCurrentWidget(self.ui.tab_product_form)

    def _fill_unpriced_job_materials(self, product_id, price):
        """Materiais lançados em jobs enquanto o produto estava sem preço
        ficam com $0. Quando o preço é salvo, oferece preencher esses
        lançamentos (o custo do job e o Job Profit passam a ficar certos)."""
        if not product_id or not price:
            return
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*), GROUP_CONCAT(DISTINCT jp.CODE ORDER BY jp.CODE SEPARATOR ', ') "
                "FROM job_materials jm LEFT JOIN job_projects jp ON jp.ID = jm.JOB_PROJECT_ID "
                "WHERE jm.PRODUCT_ID = %s AND COALESCE(jm.UNIT_PRICE, 0) = 0", (product_id,))
            count, codes = cursor.fetchone()
            if count:
                answer = QMessageBox.question(
                    self, "Fill in material cost",
                    f"This product was added to {count} job material line(s) without a price ({codes}).\n\n"
                    f"Use ${price:,.2f} for them now?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes)
                if answer == QMessageBox.StandardButton.Yes:
                    cursor.execute("UPDATE job_materials SET UNIT_PRICE = %s "
                                   "WHERE PRODUCT_ID = %s AND COALESCE(UNIT_PRICE, 0) = 0", (price, product_id))
                    conn.commit()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError):
            logging.getLogger("vl_flooring").exception("could not fill unpriced job materials")

    def save_product_record(self):
        """Insere ou atualiza um registro em products."""
        name = self.ui.txt_product_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing data", "Name is required.")
            return

        ptype = self.ui.txt_product_type.text().strip()
        specification = self.ui.txt_product_specification.text().strip()
        price = self.ui.dspn_product_price.value()
        unit = self.ui.txt_product_unit.text().strip().upper()
        coverage_qty = self.ui.dspn_product_coverage_qty.value() or None
        coverage_unit = self.ui.txt_product_coverage_unit.text().strip().upper() or None
        brand = self.ui.txt_product_brand.text().strip()
        tax_paid_at_purchase = 1 if self.ui.chk_product_tax_paid_at_purchase.isChecked() else 0

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            try:
                if getattr(self, "_current_product_id", None):
                    cursor.execute(
                        "UPDATE products SET TYPE = %s, NAME = %s, SPECIFICATION = %s, PRICE = %s, UNIT = %s, "
                        "COVERAGE_QTY = %s, COVERAGE_UNIT = %s, BRAND = %s, SALES_TAX_PAID_AT_PURCHASE = %s "
                        "WHERE ID = %s",
                        (ptype, name, specification, price, unit, coverage_qty, coverage_unit, brand,
                         tax_paid_at_purchase, self._current_product_id),
                    )
                else:
                    cursor.execute(
                        "INSERT INTO products (TYPE, NAME, SPECIFICATION, PRICE, UNIT, COVERAGE_QTY, "
                        "COVERAGE_UNIT, BRAND, SALES_TAX_PAID_AT_PURCHASE) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (ptype, name, specification, price, unit, coverage_qty, coverage_unit, brand,
                         tax_paid_at_purchase),
                    )
                tax_column_saved = True
            except MySQLError:
                # migration_fase4_w9_salestax.sql ainda não rodou nesse banco —
                # salva sem a coluna nova em vez de travar o cadastro de produto.
                conn.rollback()
                if getattr(self, "_current_product_id", None):
                    cursor.execute(
                        "UPDATE products SET TYPE = %s, NAME = %s, SPECIFICATION = %s, PRICE = %s, UNIT = %s, "
                        "COVERAGE_QTY = %s, COVERAGE_UNIT = %s, BRAND = %s WHERE ID = %s",
                        (ptype, name, specification, price, unit, coverage_qty, coverage_unit, brand,
                         self._current_product_id),
                    )
                else:
                    cursor.execute(
                        "INSERT INTO products (TYPE, NAME, SPECIFICATION, PRICE, UNIT, COVERAGE_QTY, "
                        "COVERAGE_UNIT, BRAND) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                        (ptype, name, specification, price, unit, coverage_qty, coverage_unit, brand),
                    )
                tax_column_saved = False

            conn.commit()
            cursor.close()
            conn.close()
        except MySQLError as e:
            QMessageBox.critical(self, "Database Error", f"Could not save product:\n{e}")
            return
        except RuntimeError as e:
            QMessageBox.warning(self, "Driver Missing", str(e))
            return

        self._fill_unpriced_job_materials(getattr(self, "_current_product_id", None), price)

        if not tax_column_saved:
            QMessageBox.information(
                self, "Success",
                "Product saved successfully.\n\n"
                "Note: the 'sales tax paid at purchase' checkbox was NOT saved — "
                "run migration_fase4_w9_salestax.sql on the database to enable it.",
            )
        else:
            QMessageBox.information(self, "Success", "Product saved successfully.")
        self.load_products()
        self.new_product_record()
        self.ui.tabWidget_products_page.setCurrentWidget(self.ui.tab_products_list)

    def delete_product_record(self):
        """Exclui o produto atualmente carregado no formulário."""
        if not getattr(self, "_current_product_id", None):
            QMessageBox.information(self, "No record selected",
                                     "Select a product from the list before deleting.")
            return

        confirm = QMessageBox.question(
            self, "Confirm delete",
            f"Are you sure you want to delete product #{self._current_product_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products WHERE ID = %s", (self._current_product_id,))
            conn.commit()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not delete product:\n{e}")
            return

        QMessageBox.information(self, "Deleted", "Product deleted.")
        self.new_product_record()
        self.load_products()
        self.ui.tabWidget_products_page.setCurrentWidget(self.ui.tab_products_list)
