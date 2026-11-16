# -*- coding: utf-8 -*-
"""
Tela Settings: carrega/salva os dados da empresa e do SMTP (app_settings) e troca o logo.

Métodos da MainWindow (mixin) — veja main_.py.
"""

from app_common import *  # noqa: F401,F403


class SettingsMixin:
    def _load_app_settings_from_db(self):
        """Carrega as configurações salvas em app_settings e sobrescreve as
        constantes padrão do início do arquivo (COMPANY_NAME etc.), se
        existir algo salvo. Roda cedo no __init__, antes de qualquer invoice
        ser gerado. Se a tabela/linha não existir ainda (primeira vez), os
        valores padrão do código continuam valendo normalmente."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM app_settings WHERE ID = 1")
            columns = [d[0] for d in cursor.description]
            row = cursor.fetchone()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError):
            return  # tabela ainda não existe, ou banco fora do ar — usa os padrões do código

        if not row:
            return
        data = dict(zip(columns, row))

        company_settings.COMPANY_NAME = data.get("COMPANY_NAME") or company_settings.COMPANY_NAME
        company_settings.COMPANY_TAGLINE = data.get("COMPANY_TAGLINE") or company_settings.COMPANY_TAGLINE
        company_settings.COMPANY_PHONE = data.get("COMPANY_PHONE") or company_settings.COMPANY_PHONE
        company_settings.COMPANY_EMAIL = data.get("COMPANY_EMAIL") or company_settings.COMPANY_EMAIL
        company_settings.COMPANY_WEBSITE = data.get("COMPANY_WEBSITE") or company_settings.COMPANY_WEBSITE
        company_settings.COMPANY_BANK_INFO = {
            "account_no": data.get("BANK_ACCOUNT_NO") or company_settings.COMPANY_BANK_INFO["account_no"],
            "account_name": data.get("BANK_ACCOUNT_NAME") or company_settings.COMPANY_BANK_INFO["account_name"],
            "bank_details": data.get("BANK_DETAILS") or company_settings.COMPANY_BANK_INFO["bank_details"],
        }
        if data.get("PAYMENT_METHODS"):
            company_settings.COMPANY_PAYMENT_METHODS = [m.strip() for m in data["PAYMENT_METHODS"].split(",") if m.strip()]
        company_settings.EMAIL_SMTP_HOST = data.get("SMTP_HOST") or company_settings.EMAIL_SMTP_HOST
        company_settings.EMAIL_SMTP_PORT = data.get("SMTP_PORT") or company_settings.EMAIL_SMTP_PORT
        company_settings.EMAIL_SMTP_USER = data.get("SMTP_USER") or company_settings.EMAIL_SMTP_USER
        company_settings.EMAIL_SMTP_PASSWORD = data.get("SMTP_PASSWORD") or company_settings.EMAIL_SMTP_PASSWORD
        company_settings.EMAIL_FROM_NAME = data.get("SMTP_FROM_NAME") or company_settings.EMAIL_FROM_NAME

    def load_settings_form(self):
        """Preenche o formulário de Settings com os valores atuais (já
        carregados do banco no início, ou os padrões do código)."""
        self.ui.txt_settings_company_name.setText(company_settings.COMPANY_NAME)
        self.ui.txt_settings_company_tagline.setText(company_settings.COMPANY_TAGLINE)
        self.ui.txt_settings_company_phone.setText(company_settings.COMPANY_PHONE)
        self.ui.txt_settings_company_email.setText(company_settings.COMPANY_EMAIL)
        self.ui.txt_settings_company_website.setText(company_settings.COMPANY_WEBSITE)

        self.ui.txt_settings_bank_account_no.setText(company_settings.COMPANY_BANK_INFO["account_no"])
        self.ui.txt_settings_bank_account_name.setText(company_settings.COMPANY_BANK_INFO["account_name"])
        self.ui.txt_settings_bank_details.setText(company_settings.COMPANY_BANK_INFO["bank_details"])

        pm_checks = {
            "Zelle": self.ui.chk_settings_pm_zelle,
            "Check": self.ui.chk_settings_pm_check,
            "Cash": self.ui.chk_settings_pm_cash,
            "Bank Transfer": self.ui.chk_settings_pm_bank_transfer,
            "Credit Card": self.ui.chk_settings_pm_credit_card,
        }
        for label, chk in pm_checks.items():
            chk.setChecked(label in company_settings.COMPANY_PAYMENT_METHODS)

        self.ui.txt_settings_smtp_host.setText(company_settings.EMAIL_SMTP_HOST)
        self.ui.spn_settings_smtp_port.setValue(int(company_settings.EMAIL_SMTP_PORT))
        self.ui.txt_settings_smtp_user.setText(company_settings.EMAIL_SMTP_USER)
        self.ui.txt_settings_smtp_password.setText(company_settings.EMAIL_SMTP_PASSWORD)

        if os.path.exists(COMPANY_LOGO_PATH):
            self.ui.lbl_settings_logo_preview.setPixmap(QPixmap(COMPANY_LOGO_PATH))
        else:
            self.ui.lbl_settings_logo_preview.setText("No logo")

    def save_settings_form(self):
        """Salva o formulário de Settings no banco (app_settings) e já
        atualiza as constantes em memória, pra valer imediatamente sem
        precisar reiniciar o app."""

        company_name = self.ui.txt_settings_company_name.text().strip()
        if not company_name:
            QMessageBox.warning(self, "Missing data", "Company Name is required.")
            return

        pm_checks = {
            "Zelle": self.ui.chk_settings_pm_zelle,
            "Check": self.ui.chk_settings_pm_check,
            "Cash": self.ui.chk_settings_pm_cash,
            "Bank Transfer": self.ui.chk_settings_pm_bank_transfer,
            "Credit Card": self.ui.chk_settings_pm_credit_card,
        }
        selected_methods = [label for label, chk in pm_checks.items() if chk.isChecked()]

        data = {
            "COMPANY_NAME": company_name,
            "COMPANY_TAGLINE": self.ui.txt_settings_company_tagline.text().strip(),
            "COMPANY_PHONE": self.ui.txt_settings_company_phone.text().strip(),
            "COMPANY_EMAIL": self.ui.txt_settings_company_email.text().strip(),
            "COMPANY_WEBSITE": self.ui.txt_settings_company_website.text().strip(),
            "BANK_ACCOUNT_NO": self.ui.txt_settings_bank_account_no.text().strip(),
            "BANK_ACCOUNT_NAME": self.ui.txt_settings_bank_account_name.text().strip(),
            "BANK_DETAILS": self.ui.txt_settings_bank_details.text().strip(),
            "PAYMENT_METHODS": ", ".join(selected_methods),
            "SMTP_HOST": self.ui.txt_settings_smtp_host.text().strip(),
            "SMTP_PORT": self.ui.spn_settings_smtp_port.value(),
            "SMTP_USER": self.ui.txt_settings_smtp_user.text().strip(),
            "SMTP_PASSWORD": self.ui.txt_settings_smtp_password.text(),
            "SMTP_FROM_NAME": company_name,
        }

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO app_settings (ID, COMPANY_NAME, COMPANY_TAGLINE, COMPANY_PHONE, COMPANY_EMAIL,
                    COMPANY_WEBSITE, BANK_ACCOUNT_NO, BANK_ACCOUNT_NAME, BANK_DETAILS, PAYMENT_METHODS,
                    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM_NAME)
                VALUES (1, %(COMPANY_NAME)s, %(COMPANY_TAGLINE)s, %(COMPANY_PHONE)s, %(COMPANY_EMAIL)s,
                    %(COMPANY_WEBSITE)s, %(BANK_ACCOUNT_NO)s, %(BANK_ACCOUNT_NAME)s, %(BANK_DETAILS)s,
                    %(PAYMENT_METHODS)s, %(SMTP_HOST)s, %(SMTP_PORT)s, %(SMTP_USER)s, %(SMTP_PASSWORD)s,
                    %(SMTP_FROM_NAME)s)
                ON DUPLICATE KEY UPDATE
                    COMPANY_NAME=VALUES(COMPANY_NAME), COMPANY_TAGLINE=VALUES(COMPANY_TAGLINE),
                    COMPANY_PHONE=VALUES(COMPANY_PHONE), COMPANY_EMAIL=VALUES(COMPANY_EMAIL),
                    COMPANY_WEBSITE=VALUES(COMPANY_WEBSITE), BANK_ACCOUNT_NO=VALUES(BANK_ACCOUNT_NO),
                    BANK_ACCOUNT_NAME=VALUES(BANK_ACCOUNT_NAME), BANK_DETAILS=VALUES(BANK_DETAILS),
                    PAYMENT_METHODS=VALUES(PAYMENT_METHODS), SMTP_HOST=VALUES(SMTP_HOST),
                    SMTP_PORT=VALUES(SMTP_PORT), SMTP_USER=VALUES(SMTP_USER),
                    SMTP_PASSWORD=VALUES(SMTP_PASSWORD), SMTP_FROM_NAME=VALUES(SMTP_FROM_NAME)
                """,
                data,
            )
            conn.commit()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not save settings:\n{e}")
            return

        # Atualiza as constantes em memória pra valer na hora, sem precisar reiniciar
        company_settings.COMPANY_NAME = data["COMPANY_NAME"]
        company_settings.COMPANY_TAGLINE = data["COMPANY_TAGLINE"]
        company_settings.COMPANY_PHONE = data["COMPANY_PHONE"]
        company_settings.COMPANY_EMAIL = data["COMPANY_EMAIL"]
        company_settings.COMPANY_WEBSITE = data["COMPANY_WEBSITE"]
        company_settings.COMPANY_BANK_INFO = {
            "account_no": data["BANK_ACCOUNT_NO"],
            "account_name": data["BANK_ACCOUNT_NAME"],
            "bank_details": data["BANK_DETAILS"],
        }
        company_settings.COMPANY_PAYMENT_METHODS = selected_methods
        company_settings.EMAIL_SMTP_HOST = data["SMTP_HOST"]
        company_settings.EMAIL_SMTP_PORT = data["SMTP_PORT"]
        company_settings.EMAIL_SMTP_USER = data["SMTP_USER"]
        company_settings.EMAIL_SMTP_PASSWORD = data["SMTP_PASSWORD"]
        company_settings.EMAIL_FROM_NAME = data["SMTP_FROM_NAME"]

        QMessageBox.information(self, "Saved", "Settings saved successfully.")

    def change_company_logo(self):
        """Deixa escolher uma imagem nova e substitui o arquivo de logo
        usado nos invoices (assets/logo_icon_only.png)."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose a logo image", "", "Images (*.png *.jpg *.jpeg)"
        )
        if not path:
            return
        try:
            os.makedirs(os.path.dirname(COMPANY_LOGO_PATH), exist_ok=True)
            shutil.copyfile(path, COMPANY_LOGO_PATH)
        except OSError as e:
            QMessageBox.critical(self, "File Error", f"Could not save the logo file:\n{e}")
            return
        self.ui.lbl_settings_logo_preview.setPixmap(QPixmap(COMPANY_LOGO_PATH))
        QMessageBox.information(self, "Logo Updated", "Logo updated successfully.")

    # ── restaurar backup ──────────────────────────────────────────────
    def _setup_restore_backup_button(self):
        """Botão "Restore backup…" no fim da tela Settings (só Admin vê Settings)."""
        from paginas.visual import tabler_icon
        btn = QPushButton("  Restore backup…")
        btn.setObjectName("btn_open_restore_backup")
        btn.setIcon(tabler_icon("database-import", "#37474F", 16))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip("Bring the database back to how it was on an earlier day")
        btn.clicked.connect(self.open_restore_backup_dialog)
        layout = self.ui.layout_settings_contents
        layout.insertWidget(layout.indexOf(self.ui.btn_settings_save) + 1, btn)

    def open_restore_backup_dialog(self):
        import backup_db
        backups = backup_db.list_backups()
        if not backups:
            QMessageBox.warning(self, "No backups", "No backup files were found on this computer.\n\n"
                                f"Folders checked:\n{backup_db.BACKUP_DIR}\n{backup_db.CLOUD_DIR or ''}")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Restore backup")
        dialog.resize(640, 480)
        layout = QVBoxLayout(dialog)
        info = QLabel("Choose the day you want to go back to. <b>Everything entered after that backup "
                      "will be lost.</b> A backup of the current data is made automatically first, "
                      "so this can be undone.")
        info.setWordWrap(True)
        layout.addWidget(info)
        table = QTableWidget(len(backups), 3)
        table.setHorizontalHeaderLabels(["Backup date", "Size", "Folder"])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        for r, (path, when, size_kb, folder) in enumerate(backups):
            for c, v in enumerate([when.strftime("%m/%d/%Y  %I:%M %p"), f"{size_kb:,.0f} KB",
                                   "OneDrive" if "OneDrive" in folder else folder]):
                item = QTableWidgetItem(v)
                if c == 0:
                    item.setData(Qt.ItemDataRole.UserRole, path)
                table.setItem(r, c, item)
        table.selectRow(0)
        layout.addWidget(table, 1)
        row = QHBoxLayout()
        row.addStretch(1)
        btn_cancel = QPushButton("Cancel")
        btn_restore = QPushButton("Restore selected backup")
        btn_restore.setStyleSheet("QPushButton { background-color: #C62828; color: #FFFFFF; border: none; "
                                  "border-radius: 6px; padding: 8px 16px; font-weight: 700; } "
                                  "QPushButton:hover { background-color: #B71C1C; }")
        row.addWidget(btn_cancel)
        row.addWidget(btn_restore)
        layout.addLayout(row)
        btn_cancel.clicked.connect(dialog.reject)

        def do_restore():
            current = table.currentRow()
            if current < 0:
                return
            path = table.item(current, 0).data(Qt.ItemDataRole.UserRole)
            when = table.item(current, 0).text()
            from PySide6.QtWidgets import QInputDialog
            typed, ok = QInputDialog.getText(
                dialog, "Confirm restore",
                f"This will replace ALL current data with the backup from {when}.\n"
                "Anything entered after that will be lost (a safety backup is made first).\n\n"
                "Type RESTORE to continue:")
            if not ok or typed.strip().upper() != "RESTORE":
                return
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                safety = backup_db.run_backup()
                backup_db.restore_backup(path)
            except Exception as e:
                QApplication.restoreOverrideCursor()
                logging.getLogger("vl_flooring").exception("restore failed")
                QMessageBox.critical(dialog, "Restore failed", f"The backup could not be restored:\n{e}")
                return
            QApplication.restoreOverrideCursor()
            logging.getLogger("vl_flooring").warning("database restored from %s (safety backup %s)", path, safety)
            dialog.accept()
            box = QMessageBox(QMessageBox.Icon.Information, "Restore complete",
                              f"The database is back to {when}.\n\n"
                              f"The data from before the restore was saved in:\n{os.path.basename(safety)}\n\n"
                              "The app will now reload — sign in again.", parent=self)
            box.exec()
            self._job_form_dirty = False
            self.signed_out.emit()  # recarrega tudo com os dados restaurados

        btn_restore.clicked.connect(do_restore)
        dialog.exec()
