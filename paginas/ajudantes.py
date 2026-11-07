# -*- coding: utf-8 -*-
"""
Helpers: cadastro dos ajudantes de obra e o campo Helper do Job.

Métodos da MainWindow (mixin) — veja main_.py.
"""

from app_common import *  # noqa: F401,F403


class HelpersMixin:
    def _setup_helpers_feature(self):
        """Cria, em tempo de execução, o botão 'Helpers' no submenu de
        Registrations — mesmo padrão dos outros botões novos (nenhum
        widget novo no .ui)."""
        self.ui.btn_reg_helpers = QPushButton(self.ui.frame_registrations_submenu)
        self.ui.btn_reg_helpers.setObjectName(u"btn_reg_helpers")
        self.ui.btn_reg_helpers.setCheckable(False)
        self.ui.btn_reg_helpers.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ui.layout_registrations_submenu.addWidget(self.ui.btn_reg_helpers)

    def _setup_helper_field(self):
        """Adiciona o campo 'Helper' ao formulário de New/Edit Job, em tempo
        de execução, reaproveitando a grade (`grid_job_info`) que já existia
        no .ui — as linhas 0 a 3 dessa grade já estavam todas ocupadas
        (Work Date/Job Code/Payment na linha 0-1, Contractor/Company/
        Status/Value na linha 2-3), então o campo novo entra nas linhas 4-5,
        mesmo estilo do Contractor. Como todo o formulário de Job já fica
        dentro de um QScrollArea (`scroll_job_form`), a grade ficando um
        pouco mais alta não corta nem sobrepõe nada — só rola um pouco mais.
        O Helper é opcional (ao contrário do Contractor, que é obrigatório)."""
        self.ui.lbl_helper = QLabel(self.ui.frame_job_info_body)
        self.ui.lbl_helper.setObjectName(u"lbl_helper")
        self.ui.lbl_helper.setText("Helper")
        self.ui.grid_job_info.addWidget(self.ui.lbl_helper, 4, 0, 1, 1)

        self.ui.cmb_helper = QComboBox(self.ui.frame_job_info_body)
        self.ui.cmb_helper.setObjectName(u"cmb_helper")
        self.ui.cmb_helper.setMinimumSize(QSize(190, 46))
        self.ui.cmb_helper.setMaximumSize(QSize(190, 36))
        self.ui.cmb_helper.setStyleSheet(u"font: 9pt \"MS Shell Dlg 2\";")
        self.ui.grid_job_info.addWidget(self.ui.cmb_helper, 5, 0, 1, 1)

    def open_helpers_manager_dialog(self):
        """Cadastro de Helpers: lista à esquerda/tabela em cima, formulário
        embaixo. Clica numa linha da tabela pra editar, ou preenche o
        formulário do zero (depois de '+ New') pra cadastrar um novo."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Helpers")
        dialog.resize(760, 640)
        dialog.setStyleSheet("""
            QTableWidget { background-color: #FFFFFF; color: #1C2B3A; gridline-color: #E3E8EE; }
            QHeaderView::section { background-color: #F0F4F8; color: #1C2B3A; padding: 6px; border: none; font-weight: 600; }
        """)
        layout = QVBoxLayout(dialog)
        lbl_intro = QLabel(
            "<b>Helpers</b> — helpers who assist on jobs (name, company, contact and address, "
            "same level of detail as Contractor). Click a row below to edit it, or click "
            "'+ New' and fill the form to add one."
        )
        lbl_intro.setWordWrap(True)
        layout.addWidget(lbl_intro)

        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Name", "Company", "Phone", "Email"])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        table.setMinimumHeight(120)
        table.setMaximumHeight(180)
        layout.addWidget(table)

        form_frame = QFrame()
        form_layout = QGridLayout(form_frame)

        txt_full_name = QLineEdit()
        txt_company_name = QLineEdit()
        txt_email = QLineEdit()
        txt_phone = QLineEdit()
        txt_phone.setPlaceholderText("(000) 000 - 0000")
        txt_phone2 = QLineEdit()
        txt_phone2.setPlaceholderText("(000) 000 - 0000")
        txt_address = QLineEdit()
        txt_address2 = QLineEdit()
        cmb_state = QComboBox()
        cmb_city = QComboBox()
        txt_zip = QLineEdit()
        txt_zip.setPlaceholderText("00000-0000")

        # Formas de pagamento — todas opcionais, e um Helper pode ter mais de
        # uma preenchida ao mesmo tempo (ex: Zelle E Cash App). Cada uma tem
        # seu próprio campo específico (mais organizado do que um campo
        # único de texto livre pra tudo).
        txt_zelle = QLineEdit()
        txt_zelle.setPlaceholderText("Phone or email used on Zelle")
        txt_cashapp = QLineEdit()
        txt_cashapp.setPlaceholderText("$cashtag")
        txt_venmo = QLineEdit()
        txt_venmo.setPlaceholderText("@username")
        txt_check_name = QLineEdit()
        txt_check_name.setPlaceholderText("Pay to the order of...")
        txt_bank_routing = QLineEdit()
        txt_bank_routing.setPlaceholderText("Routing number")
        txt_bank_account = QLineEdit()
        txt_bank_account.setPlaceholderText("Account number")
        # Mapa coluna do banco -> campo, reaproveitado por load/save — assim
        # cada forma nova entra num só lugar sem duplicar lista em vários
        # pontos da função.
        payment_fields = {
            "PAYMENT_ZELLE": txt_zelle,
            "PAYMENT_CASHAPP": txt_cashapp,
            "PAYMENT_VENMO": txt_venmo,
            "PAYMENT_CHECK_NAME": txt_check_name,
            "PAYMENT_BANK_ROUTING": txt_bank_routing,
            "PAYMENT_BANK_ACCOUNT": txt_bank_account,
        }

        field_rows = [
            ("Full Name*:", txt_full_name), ("Company:", txt_company_name),
            ("Email:", txt_email), ("Phone:", txt_phone), ("Phone 2:", txt_phone2),
            ("Address:", txt_address), ("Address Line 2:", txt_address2),
        ]
        for i, (label_text, widget) in enumerate(field_rows):
            form_layout.addWidget(QLabel(label_text), i, 0)
            form_layout.addWidget(widget, i, 1)
        next_row = len(field_rows)
        form_layout.addWidget(QLabel("State:"), next_row, 0)
        form_layout.addWidget(cmb_state, next_row, 1)
        form_layout.addWidget(QLabel("City:"), next_row + 1, 0)
        form_layout.addWidget(cmb_city, next_row + 1, 1)
        form_layout.addWidget(QLabel("Zip Code:"), next_row + 2, 0)
        form_layout.addWidget(txt_zip, next_row + 2, 1)

        lbl_payment_section = QLabel(
            "Payment Methods (optional — fill in whichever this helper uses; you can fill more than one)"
        )
        lbl_payment_section.setWordWrap(True)
        payment_section_row = next_row + 3
        form_layout.addWidget(lbl_payment_section, payment_section_row, 0, 1, 2)
        payment_rows = [
            ("Zelle:", txt_zelle),
            ("Cash App:", txt_cashapp),
            ("Venmo:", txt_venmo),
            ("Check — Pay to the order of:", txt_check_name),
            ("Bank Transfer — Routing #:", txt_bank_routing),
            ("Bank Transfer — Account #:", txt_bank_account),
        ]
        for offset, (label_text, widget) in enumerate(payment_rows, start=1):
            form_layout.addWidget(QLabel(label_text), payment_section_row + offset, 0)
            form_layout.addWidget(widget, payment_section_row + offset, 1)

        # Formulário agora tem mais campos (com as formas de pagamento) do
        # que cabe numa tela só — envolve num QScrollArea pra dar rolagem
        # vertical em vez de estourar o tamanho da janela.
        form_scroll = QScrollArea()
        form_scroll.setWidgetResizable(True)
        form_scroll.setFrameShape(QFrame.Shape.NoFrame)
        form_scroll.setWidget(form_frame)
        layout.addWidget(form_scroll, 1)

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT ID, STATE_NAME FROM states ORDER BY STATE_NAME")
            state_rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError):
            state_rows = []
        cmb_state.addItem("— Select —", None)
        for state_id, state_name in state_rows:
            cmb_state.addItem(state_name, state_id)
        self._reload_city_combo_for_state(cmb_city, None)
        cmb_state.currentIndexChanged.connect(
            lambda: self._reload_city_combo_for_state(cmb_city, cmb_state.currentData())
        )
        for phone_field in (txt_phone, txt_phone2):
            phone_field.editingFinished.connect(lambda f=phone_field: f.setText(self._format_phone(f.text())))
        txt_zip.editingFinished.connect(lambda: txt_zip.setText(self._format_zip(txt_zip.text())))

        current_helper_id = {"value": None}  # None = formulário em modo "novo"

        def clear_form():
            current_helper_id["value"] = None
            for w in (txt_full_name, txt_company_name, txt_email, txt_phone, txt_phone2,
                      txt_address, txt_address2, txt_zip):
                w.clear()
            for w in payment_fields.values():
                w.clear()
            cmb_state.setCurrentIndex(0)
            self._reload_city_combo_for_state(cmb_city, None)
            table.clearSelection()

        def load_helpers():
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT ID, FULL_NAME, COMPANY_NAME, PHONE_NUMBER, EMAIL FROM helpers ORDER BY FULL_NAME"
                )
                rows = cursor.fetchall()
                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.information(
                    dialog, "Helpers not available yet",
                    "This list isn't available yet — the 'helpers' table hasn't been created in "
                    f"the database.\n\n({e})",
                )
                rows = []
            table.setRowCount(len(rows))
            for i, (hid, name, company, phone, email) in enumerate(rows):
                values = [name or "", company or "", self._format_phone(phone) or "", email or ""]
                for col, text in enumerate(values):
                    item = QTableWidgetItem(text)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    if col == 0:
                        item.setData(Qt.ItemDataRole.UserRole, hid)
                    table.setItem(i, col, item)

        def load_selected_into_form():
            r = table.currentRow()
            if r < 0:
                return
            helper_id = table.item(r, 0).data(Qt.ItemDataRole.UserRole)
            base_cols = ["FULL_NAME", "COMPANY_NAME", "EMAIL", "PHONE_NUMBER", "PHONE_NUMBER2",
                         "ADDRESS", "ADDRESS2", "CITY_ID", "STATE_ID", "ZIP_CODE"]
            # As colunas de pagamento só entram na consulta se a migração
            # correspondente já tiver rodado — assim, carregar um Helper
            # continua funcionando mesmo antes de você rodar a migração nova.
            payment_cols = [col for col in payment_fields if self._table_column_exists("helpers", col)]
            all_cols = base_cols + payment_cols
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(f"SELECT {', '.join(all_cols)} FROM helpers WHERE ID = %s", (helper_id,))
                row = cursor.fetchone()
                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.warning(dialog, "Database Error", f"Could not load this helper:\n{e}")
                return
            if not row:
                return
            values = dict(zip(all_cols, row))
            current_helper_id["value"] = helper_id
            txt_full_name.setText(values.get("FULL_NAME") or "")
            txt_company_name.setText(values.get("COMPANY_NAME") or "")
            txt_email.setText(values.get("EMAIL") or "")
            txt_phone.setText(self._format_phone(values.get("PHONE_NUMBER")) or "")
            txt_phone2.setText(self._format_phone(values.get("PHONE_NUMBER2")) or "")
            txt_address.setText(values.get("ADDRESS") or "")
            txt_address2.setText(values.get("ADDRESS2") or "")
            txt_zip.setText(self._format_zip(values.get("ZIP_CODE")) or "")
            self._set_combo_by_data(cmb_state, values.get("STATE_ID"))
            self._reload_city_combo_for_state(cmb_city, values.get("STATE_ID"), keep_city_id=values.get("CITY_ID"))
            for col, widget in payment_fields.items():
                widget.setText(values.get(col) or "")

        table.itemSelectionChanged.connect(load_selected_into_form)

        def save_helper():
            full_name = txt_full_name.text().strip()
            if not full_name:
                QMessageBox.warning(dialog, "Required field", "Full Name is required.")
                return
            data = {
                "FULL_NAME": full_name,
                "COMPANY_NAME": txt_company_name.text().strip(),
                "EMAIL": txt_email.text().strip(),
                "PHONE_NUMBER": self._format_phone(txt_phone.text()),
                "PHONE_NUMBER2": self._format_phone(txt_phone2.text()),
                "ADDRESS": txt_address.text().strip(),
                "ADDRESS2": txt_address2.text().strip(),
                "CITY_ID": cmb_city.currentData(),
                "STATE_ID": cmb_state.currentData(),
                "ZIP_CODE": self._format_zip(txt_zip.text()),
            }
            # Cada campo de pagamento só entra no INSERT/UPDATE se a coluna
            # já existir — se a migração nova ainda não rodou, o resto do
            # Helper continua salvando normal, só sem os dados de pagamento.
            for col, widget in payment_fields.items():
                if self._table_column_exists("helpers", col):
                    data[col] = widget.text().strip()
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                if current_helper_id["value"]:
                    set_clause = ", ".join(f"{k} = %s" for k in data)
                    cursor.execute(
                        f"UPDATE helpers SET {set_clause} WHERE ID = %s",
                        list(data.values()) + [current_helper_id["value"]],
                    )
                else:
                    cols = ", ".join(data.keys())
                    placeholders = ", ".join(["%s"] * len(data))
                    cursor.execute(f"INSERT INTO helpers ({cols}) VALUES ({placeholders})", list(data.values()))
                conn.commit()
                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not save this helper:\n{e}")
                return
            QMessageBox.information(dialog, "Saved", "Helper saved successfully.")
            clear_form()
            load_helpers()
            self.load_combo_data()  # atualiza o combo Helper no formulário de Job na hora

        def delete_helper():
            if not current_helper_id["value"]:
                QMessageBox.information(dialog, "No selection", "Select a helper from the list first.")
                return
            confirm = QMessageBox.question(
                dialog, "Confirm delete",
                "Are you sure you want to delete this helper?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM helpers WHERE ID = %s", (current_helper_id["value"],))
                conn.commit()
                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not delete this helper:\n{e}")
                return
            clear_form()
            load_helpers()
            self.load_combo_data()

        btn_row = QHBoxLayout()
        btn_new = QPushButton("+ New")
        btn_new.clicked.connect(clear_form)
        btn_save = QPushButton("✔  Save")
        btn_save.setStyleSheet(
            "QPushButton { background-color: #2E7D32; color: #FFFFFF; border: none; "
            "border-radius: 6px; padding: 8px 14px; font-weight: 600; } "
            "QPushButton:hover { background-color: #388E3C; }"
        )
        btn_save.clicked.connect(save_helper)
        btn_delete = QPushButton("Delete")
        btn_delete.clicked.connect(delete_helper)
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(dialog.accept)
        btn_row.addWidget(btn_new)
        btn_row.addWidget(btn_save)
        btn_row.addWidget(btn_delete)
        btn_row.addStretch()
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

        load_helpers()
        dialog.exec()
