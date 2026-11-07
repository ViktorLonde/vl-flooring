# -*- coding: utf-8 -*-
"""
Users: lista e formulário dos usuários do sistema.

Métodos da MainWindow (mixin) — veja main_.py.
"""

from app_common import *  # noqa: F401,F403


class UsersMixin:
    def load_users(self):
        """Carrega os registros de users na tabela, aplicando filtros de busca e status."""
        search_text = self.ui.txt_search_users.text().strip()
        status_filter = self.ui.cmb_filter_user_status.currentText()

        query = """
            SELECT id, full_name, email, phone_number, username,
                   role, status, last_login, created_at
            FROM users
            WHERE 1=1
        """
        params = []

        if search_text:
            query += """
                AND (full_name LIKE %s
                     OR username LIKE %s
                     OR email LIKE %s)
            """
            like = f"%{search_text}%"
            params.extend([like, like, like])

        if status_filter and status_filter != "All Status":
            query += " AND status = %s"
            params.append(status_filter)

        query += " ORDER BY full_name ASC"

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except MySQLError as e:
            QMessageBox.critical(self, "Database Error", f"Could not load users:\n{e}")
            return
        except RuntimeError as e:
            QMessageBox.warning(self, "Driver Missing", str(e))
            return

        self._populate_users_table(rows)

    def _populate_users_table(self, rows):
        """Preenche a tabela de Users linha a linha."""
        table = self.ui.table_users
        table.setSortingEnabled(False)
        table.setRowCount(0)
        table.setRowCount(len(rows))

        for row_idx, row_data in enumerate(rows):
            (user_id, full_name, email, phone, username,
             role, status, last_login, created_at) = row_data

            values = [
                str(user_id),
                str(full_name or ""),
                str(email or ""),
                self._format_phone(phone) or "",
                str(username or ""),
                str(role or ""),
                str(status or ""),
                last_login.strftime("%m/%d/%Y %H:%M") if isinstance(last_login, datetime) else str(last_login or "—"),
                created_at.strftime("%m/%d/%Y %H:%M") if isinstance(created_at, datetime) else str(created_at or "—"),
            ]

            for col_idx, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(row_idx, col_idx, item)

        table.setSortingEnabled(True)

    def new_user_record(self):
        """Limpa o formulário para criar um novo usuário."""
        self._current_user_id = None
        self.ui.txt_user_id.clear()
        self.ui.lbl_user_id_display.setText("#ID: New")
        for field in (self.ui.txt_user_full_name, self.ui.txt_user_username,
                      self.ui.txt_user_email, self.ui.txt_user_phone,
                      self.ui.txt_user_phone2, self.ui.txt_user_password,
                      self.ui.txt_user_confirm_password):
            field.clear()
        self.ui.txt_user_last_login.clear()
        self.ui.txt_user_created_at.clear()
        self.ui.cmb_user_role.setCurrentIndex(0)
        self.ui.cmb_user_status.setCurrentIndex(0)
        self.ui.tabWidget_user.setCurrentWidget(self.ui.tab_users_master)

    def load_user_into_form(self):
        """Carrega o usuário selecionado na tabela para edição (dispara ao
        clicar numa linha — padrão master-detail)."""
        table = self.ui.table_users
        selected = table.currentRow()
        if selected < 0:
            return

        user_id = table.item(selected, 0).text()
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            columns = [d[0] for d in cursor.description]
            row = cursor.fetchone()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not load user:\n{e}")
            return

        if not row:
            return

        data = dict(zip(columns, row))
        self._current_user_id = data["id"]
        self.ui.txt_user_id.setText(str(data["id"]))
        self.ui.lbl_user_id_display.setText(f"#ID: {data['id']}")

        self.ui.txt_user_full_name.setText(data.get("full_name") or "")
        self.ui.txt_user_username.setText(data.get("username") or "")
        self.ui.txt_user_email.setText(data.get("email") or "")
        self.ui.txt_user_phone.setText(self._format_phone(data.get("phone_number")) or "")
        self.ui.txt_user_phone2.setText(self._format_phone(data.get("phone_number2")) or "")

        # Senha nunca é preenchida de volta — deixe em branco para manter a atual
        self.ui.txt_user_password.clear()
        self.ui.txt_user_confirm_password.clear()

        last_login = data.get("last_login")
        created_at = data.get("created_at")
        self.ui.txt_user_last_login.setText(
            last_login.strftime("%m/%d/%Y %H:%M") if isinstance(last_login, datetime) else str(last_login or "—")
        )
        self.ui.txt_user_created_at.setText(
            created_at.strftime("%m/%d/%Y %H:%M") if isinstance(created_at, datetime) else str(created_at or "—")
        )

        self._set_combo_by_data(self.ui.cmb_user_role, data.get("role"), by_text=True)
        self._set_combo_by_data(self.ui.cmb_user_status, data.get("status"), by_text=True)

        self.ui.tabWidget_user.setCurrentWidget(self.ui.tab_users_master)

    def save_user_record(self):
        """Insere ou atualiza um registro em users.

        Se a senha for deixada em branco numa atualização, o password_hash
        atual é preservado — só é sobrescrito se o usuário digitar uma nova senha.
        """
        full_name = self.ui.txt_user_full_name.text().strip()
        username = self.ui.txt_user_username.text().strip()
        email = self.ui.txt_user_email.text().strip()

        if not full_name or not username or not email:
            QMessageBox.warning(self, "Missing data", "Full Name, Username and Email are required.")
            return

        password = self.ui.txt_user_password.text()
        confirm_password = self.ui.txt_user_confirm_password.text()
        is_update = bool(getattr(self, "_current_user_id", None))

        if not is_update and not password:
            QMessageBox.warning(self, "Missing data", "Password is required for a new user.")
            return

        if password != confirm_password:
            QMessageBox.warning(self, "Password mismatch", "Passwords do not match.")
            return

        data = {
            "full_name": full_name,
            "email": email,
            "phone_number": self._format_phone(self.ui.txt_user_phone.text()),
            "phone_number2": self._format_phone(self.ui.txt_user_phone2.text()),
            "username": username,
            "role": self.ui.cmb_user_role.currentText(),
            "status": self.ui.cmb_user_status.currentText(),
        }

        if password:
            data["password_hash"] = hash_password(password)

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            if is_update:
                set_clause = ", ".join(f"{k} = %s" for k in data)
                query = f"UPDATE users SET {set_clause} WHERE id = %s"
                cursor.execute(query, list(data.values()) + [self._current_user_id])
            else:
                cols = ", ".join(data.keys())
                placeholders = ", ".join(["%s"] * len(data))
                query = f"INSERT INTO users ({cols}) VALUES ({placeholders})"
                cursor.execute(query, list(data.values()))

            conn.commit()
            cursor.close()
            conn.close()
        except MySQLError as e:
            if e.errno == 1062:  # Duplicate entry (violação de UNIQUE)
                error_text = str(e)
                if "email" in error_text.lower():
                    QMessageBox.warning(self, "Duplicate Email",
                                         "This email is already in use by another user.")
                elif "username" in error_text.lower():
                    QMessageBox.warning(self, "Duplicate Username",
                                         "This username is already in use by another user.")
                else:
                    QMessageBox.warning(self, "Duplicate Entry",
                                         "Email or Username is already in use by another user.")
            else:
                QMessageBox.critical(self, "Database Error", f"Could not save user:\n{e}")
            return
        except RuntimeError as e:
            QMessageBox.warning(self, "Driver Missing", str(e))
            return

        QMessageBox.information(self, "Success", "User saved successfully.")
        self.load_users()
        self.new_user_record()
        self.ui.tabWidget_user.setCurrentWidget(self.ui.tab_users_master)

    def delete_user_record(self):
        """Exclui o usuário atualmente carregado no formulário."""
        if not getattr(self, "_current_user_id", None):
            QMessageBox.information(self, "No record selected",
                                     "Select a user from the list (Update) before deleting.")
            return

        confirm = QMessageBox.question(
            self, "Confirm delete",
            f"Are you sure you want to delete user #{self._current_user_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = %s", (self._current_user_id,))
            conn.commit()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not delete user:\n{e}")
            return

        QMessageBox.information(self, "Deleted", "User deleted.")
        self.new_user_record()
        self.load_users()
        self.ui.tabWidget_user.setCurrentWidget(self.ui.tab_users_master)
