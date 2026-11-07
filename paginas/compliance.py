# -*- coding: utf-8 -*-
"""
Compliance (LLC Annual Report, Business Tax Receipt, seguro/licença) e
Documents (repositório central de contratos, propostas, apólices).

Métodos da MainWindow (mixin) — veja main_.py.
"""

from app_common import *  # noqa: F401,F403


class ComplianceMixin:
    COMPLIANCE_TYPE_LABELS = {
        "LLC_ANNUAL_REPORT": "LLC Annual Report",
        "BUSINESS_TAX_RECEIPT": "Local Business Tax Receipt",
        "INSURANCE": "Insurance",
        "LICENSE": "License",
        "OTHER": "Other",
    }

    def _setup_compliance_feature(self):
        """Cria, em tempo de execução (sem precisar editar o .ui), o botão
        'Compliance' dentro do submenu de Registrations e o aviso amarelo no
        topo da Home. Feito assim de propósito: evita mexer no
        main_window_vl_flooring_6.ui (12948 linhas) e no
        ui_main_window_vl_flooring.py compilado (6934 linhas) só pra isso —
        mesmo padrão que open_project_view_dialog/open_clean_empty_job_codes_dialog
        já usam (QDialog montado 100% em Python)."""
        self._compliance_due_soon = 0
        self._compliance_overdue = 0

        # Botão no submenu "Registrations" — herda o QSS de
        # "#frame_registrations_submenu QPushButton" automaticamente por ser
        # filho do mesmo frame.
        self.ui.btn_reg_compliance = QPushButton(self.ui.frame_registrations_submenu)
        self.ui.btn_reg_compliance.setObjectName(u"btn_reg_compliance")
        self.ui.btn_reg_compliance.setCheckable(False)
        self.ui.btn_reg_compliance.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ui.layout_registrations_submenu.addWidget(self.ui.btn_reg_compliance)

        # Aviso no topo da Home — escondido até ter algo vencido/vencendo.
        self.ui.frame_compliance_alert = QFrame(self.ui.pg_home)
        self.ui.frame_compliance_alert.setObjectName(u"frame_compliance_alert")
        self.ui.frame_compliance_alert.setVisible(False)
        self.ui.frame_compliance_alert.setStyleSheet(
            "#frame_compliance_alert { background-color:#FFF3CD; border:1px solid #FFE08A; border-radius:8px; }"
            "#frame_compliance_alert QLabel { color:#8A6D00; background:transparent; }"
        )
        alert_layout = QHBoxLayout(self.ui.frame_compliance_alert)
        alert_layout.setContentsMargins(14, 10, 14, 10)
        self.ui.lbl_compliance_alert = QLabel("")
        self.ui.lbl_compliance_alert.setWordWrap(True)
        self.ui.lbl_compliance_alert.setStyleSheet("font-weight:600;")
        alert_layout.addWidget(self.ui.lbl_compliance_alert, 1)
        btn_view = QPushButton("View")
        btn_view.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_view.setStyleSheet(
            "QPushButton { background-color:#FFFFFF; color:#8A6D00; border:none; "
            "border-radius:5px; padding:5px 12px; font-weight:700; } "
            "QPushButton:hover { background-color:#FFE9A8; }"
        )
        btn_view.clicked.connect(self.open_compliance_manager_dialog)
        alert_layout.addWidget(btn_view)
        self.ui.layout_pg_home_outer.insertWidget(0, self.ui.frame_compliance_alert)

    def _apply_compliance_button_label(self):
        """Só formata o texto/tooltip do botão Compliance a partir da
        contagem já em cache (self._compliance_due_soon) — não bate no banco.
        Chamado sempre que a sidebar expande/colapsa."""
        show_text = getattr(self, "_sidebar_expanded", False)
        due_soon = getattr(self, "_compliance_due_soon", 0)
        label = "  📋 Compliance"
        if due_soon:
            label += f"  ({due_soon})"
        self.ui.btn_reg_compliance.setText(label if show_text else "📋")
        self.ui.btn_reg_compliance.setToolTip("" if show_text else "Compliance")

    def _refresh_compliance_alerts(self):
        """Reconta itens de compliance vencidos/a vencer em 30 dias (LLC
        Annual Report, Business Tax Receipt, seguro, licença) e atualiza o
        botão do menu + o aviso amarelo na Home. Se a tabela compliance_items
        ainda não existir (migração não rodada), simplesmente não mostra
        nada — não trava o app."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*), SUM(CASE WHEN DUE_DATE < CURDATE() THEN 1 ELSE 0 END) "
                "FROM compliance_items "
                "WHERE STATUS = 'ACTIVE' AND DUE_DATE <= DATE_ADD(CURDATE(), INTERVAL 30 DAY)"
            )
            due_soon, overdue = cursor.fetchone()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError):
            due_soon, overdue = 0, 0

        self._compliance_due_soon = due_soon or 0
        self._compliance_overdue = overdue or 0
        self._apply_compliance_button_label()

        if not self._compliance_due_soon:
            self.ui.frame_compliance_alert.setVisible(False)
            return

        if self._compliance_overdue:
            still_due = self._compliance_due_soon - self._compliance_overdue
            msg = f"⚠️  {self._compliance_overdue} compliance item(s) OVERDUE"
            if still_due:
                msg += f", {still_due} more due in the next 30 days."
            else:
                msg += "."
        else:
            msg = f"🗓️  {self._compliance_due_soon} compliance item(s) due in the next 30 days."
        self.ui.lbl_compliance_alert.setText(msg)
        self.ui.frame_compliance_alert.setVisible(True)

    def open_compliance_manager_dialog(self):
        """Tela de gestão de Compliance: LLC Annual Report, Local Business
        Tax Receipt, seguro e licença — da própria empresa (Vertex Londe
        Flooring LLC) ou de um Contractor/Company específico. Lista tudo por
        data de vencimento, deixa criar/editar, marcar como feito (renovando
        automaticamente se for anual) e apagar."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Compliance Tracker")
        dialog.resize(780, 580)
        dialog.setStyleSheet("""
            QTableWidget { background-color: #FFFFFF; color: #1C2B3A; gridline-color: #E3E8EE; }
            QHeaderView::section { background-color: #F0F4F8; color: #1C2B3A; padding: 6px; border: none; font-weight: 600; }
        """)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(
            "<b>Compliance Tracker</b> — LLC Annual Report, Local Business Tax Receipt, "
            "insurance and license expirations. Items due within 30 days show up as a warning on Home."
        ))

        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["", "Type", "Name", "Linked To", "Due Date", "Recurs"])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        table.setColumnWidth(0, 26)
        layout.addWidget(table, 1)

        row_data = {}
        entity_name_cache = {}

        def entity_label(entity_type, entity_id):
            if entity_type != "COMPANY_SELF" and entity_id:
                key = (entity_type, entity_id)
                if key not in entity_name_cache:
                    try:
                        conn2 = self._get_connection()
                        cur2 = conn2.cursor()
                        table_name = "contractors" if entity_type == "CONTRACTOR" else "companies"
                        cur2.execute(
                            f"SELECT COALESCE(COMPANY_NAME, FULL_NAME) FROM {table_name} WHERE ID = %s",
                            (entity_id,),
                        )
                        r = cur2.fetchone()
                        entity_name_cache[key] = r[0] if r else "—"
                        cur2.close()
                        conn2.close()
                    except (MySQLError, RuntimeError):
                        entity_name_cache[key] = "—"
                return entity_name_cache[key]
            return "Vertex Londe Flooring LLC"

        def reload_table():
            table.setRowCount(0)
            row_data.clear()
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT ID, ITEM_TYPE, ENTITY_TYPE, ENTITY_ID, NAME, DUE_DATE, RECURRENCE, STATUS, NOTES "
                    "FROM compliance_items WHERE STATUS != 'ARCHIVED' ORDER BY DUE_DATE ASC"
                )
                rows = cursor.fetchall()
                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(
                    dialog, "Database Error",
                    f"Could not load compliance items:\n{e}\n\n"
                    f"(Did you run migration_compliance_items.sql on the real database yet?)",
                )
                return

            table.setRowCount(len(rows))
            today = date.today()
            for r, (cid, item_type, entity_type, entity_id, name, due_date,
                    recurrence, status, notes) in enumerate(rows):
                days_left = (due_date - today).days if due_date else None
                if status == "DONE":
                    dot = "✅"
                elif days_left is not None and days_left < 0:
                    dot = "🔴"
                elif days_left is not None and days_left <= 30:
                    dot = "🟡"
                else:
                    dot = "🟢"
                values = [
                    dot,
                    self.COMPLIANCE_TYPE_LABELS.get(item_type, item_type),
                    name or "",
                    entity_label(entity_type, entity_id),
                    due_date.strftime("%m/%d/%Y") if due_date else "—",
                    "Annual" if recurrence == "ANNUAL" else "—",
                ]
                for c, text in enumerate(values):
                    item = QTableWidgetItem(text)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    table.setItem(r, c, item)
                row_data[r] = {
                    "ID": cid, "ITEM_TYPE": item_type, "ENTITY_TYPE": entity_type,
                    "ENTITY_ID": entity_id, "NAME": name, "DUE_DATE": due_date,
                    "RECURRENCE": recurrence, "STATUS": status, "NOTES": notes or "",
                }

        # ── Formulário (criar / editar) ──────────────────────────────
        form_box = QFrame()
        form_layout = QVBoxLayout(form_box)

        row1 = QHBoxLayout()
        cmb_type = QComboBox()
        for key, lbl in self.COMPLIANCE_TYPE_LABELS.items():
            cmb_type.addItem(lbl, key)
        row1.addWidget(QLabel("Type:"))
        row1.addWidget(cmb_type)

        cmb_entity_type = QComboBox()
        cmb_entity_type.addItem("My Company (Vertex Londe Flooring LLC)", "COMPANY_SELF")
        cmb_entity_type.addItem("Contractor", "CONTRACTOR")
        cmb_entity_type.addItem("Company (GC/Client)", "COMPANY")
        row1.addWidget(QLabel("For:"))
        row1.addWidget(cmb_entity_type)

        cmb_entity = QComboBox()
        cmb_entity.setEnabled(False)
        row1.addWidget(cmb_entity, 1)
        form_layout.addLayout(row1)

        def reload_entity_combo():
            entity_type = cmb_entity_type.currentData()
            cmb_entity.clear()
            if entity_type == "COMPANY_SELF":
                cmb_entity.setEnabled(False)
                return
            cmb_entity.setEnabled(True)
            table_name = "contractors" if entity_type == "CONTRACTOR" else "companies"
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(f"SELECT ID, COALESCE(COMPANY_NAME, FULL_NAME) FROM {table_name} ORDER BY 2")
                for eid, ename in cursor.fetchall():
                    cmb_entity.addItem(ename, eid)
                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError):
                pass

        cmb_entity_type.currentIndexChanged.connect(reload_entity_combo)
        reload_entity_combo()

        row2 = QHBoxLayout()
        txt_name = QLineEdit()
        txt_name.setPlaceholderText("e.g. General Liability Insurance — Progressive")
        row2.addWidget(QLabel("Name:"))
        row2.addWidget(txt_name, 1)
        form_layout.addLayout(row2)

        row3 = QHBoxLayout()
        date_due = QDateEdit()
        date_due.setCalendarPopup(True)
        date_due.setDisplayFormat("MM/dd/yyyy")
        date_due.setDate(QDate.currentDate())
        row3.addWidget(QLabel("Due Date:"))
        row3.addWidget(date_due)
        chk_annual = QCheckBox("Renews every year")
        row3.addWidget(chk_annual)
        row3.addStretch()
        form_layout.addLayout(row3)

        row4 = QHBoxLayout()
        txt_notes = QLineEdit()
        txt_notes.setPlaceholderText("Notes (policy number, county, link, etc.)")
        row4.addWidget(QLabel("Notes:"))
        row4.addWidget(txt_notes, 1)
        form_layout.addLayout(row4)

        layout.addWidget(form_box)

        editing_id = {"value": None}

        def clear_form():
            editing_id["value"] = None
            cmb_type.setCurrentIndex(0)
            cmb_entity_type.setCurrentIndex(0)
            txt_name.clear()
            date_due.setDate(QDate.currentDate())
            chk_annual.setChecked(False)
            txt_notes.clear()
            table.clearSelection()

        def load_selected_into_form():
            r = table.currentRow()
            if r < 0 or r not in row_data:
                return
            d = row_data[r]
            editing_id["value"] = d["ID"]
            type_keys = list(self.COMPLIANCE_TYPE_LABELS.keys())
            cmb_type.setCurrentIndex(type_keys.index(d["ITEM_TYPE"]) if d["ITEM_TYPE"] in type_keys else 0)
            entity_idx = {"COMPANY_SELF": 0, "CONTRACTOR": 1, "COMPANY": 2}.get(d["ENTITY_TYPE"], 0)
            cmb_entity_type.setCurrentIndex(entity_idx)
            reload_entity_combo()
            if d["ENTITY_ID"]:
                pos = cmb_entity.findData(d["ENTITY_ID"])
                if pos >= 0:
                    cmb_entity.setCurrentIndex(pos)
            txt_name.setText(d["NAME"] or "")
            if d["DUE_DATE"]:
                date_due.setDate(QDate(d["DUE_DATE"].year, d["DUE_DATE"].month, d["DUE_DATE"].day))
            chk_annual.setChecked(d["RECURRENCE"] == "ANNUAL")
            txt_notes.setText(d["NOTES"] or "")

        table.itemSelectionChanged.connect(load_selected_into_form)

        def save_item():
            name = txt_name.text().strip()
            if not name:
                QMessageBox.warning(dialog, "Missing data", "Name is required.")
                return
            item_type = cmb_type.currentData()
            entity_type = cmb_entity_type.currentData()
            entity_id = cmb_entity.currentData() if entity_type != "COMPANY_SELF" else None
            due = date_due.date().toPython()
            recurrence = "ANNUAL" if chk_annual.isChecked() else "NONE"
            notes = txt_notes.text().strip()

            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                if editing_id["value"]:
                    cursor.execute(
                        "UPDATE compliance_items SET ITEM_TYPE=%s, ENTITY_TYPE=%s, ENTITY_ID=%s, "
                        "NAME=%s, DUE_DATE=%s, RECURRENCE=%s, NOTES=%s WHERE ID=%s",
                        (item_type, entity_type, entity_id, name, due, recurrence, notes, editing_id["value"]),
                    )
                else:
                    cursor.execute(
                        "INSERT INTO compliance_items (ITEM_TYPE, ENTITY_TYPE, ENTITY_ID, NAME, DUE_DATE, "
                        "RECURRENCE, STATUS, NOTES) VALUES (%s, %s, %s, %s, %s, %s, 'ACTIVE', %s)",
                        (item_type, entity_type, entity_id, name, due, recurrence, notes),
                    )
                conn.commit()
                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not save compliance item:\n{e}")
                return

            clear_form()
            reload_table()
            self._refresh_compliance_alerts()

        def mark_done_selected():
            r = table.currentRow()
            if r < 0 or r not in row_data:
                QMessageBox.information(dialog, "No selection", "Select an item first.")
                return
            d = row_data[r]
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE compliance_items SET STATUS='DONE' WHERE ID=%s", (d["ID"],))
                if d["RECURRENCE"] == "ANNUAL" and d["DUE_DATE"]:
                    next_due = d["DUE_DATE"].replace(year=d["DUE_DATE"].year + 1)
                    cursor.execute(
                        "INSERT INTO compliance_items (ITEM_TYPE, ENTITY_TYPE, ENTITY_ID, NAME, DUE_DATE, "
                        "RECURRENCE, STATUS, NOTES) VALUES (%s, %s, %s, %s, %s, %s, 'ACTIVE', %s)",
                        (d["ITEM_TYPE"], d["ENTITY_TYPE"], d["ENTITY_ID"], d["NAME"], next_due,
                         d["RECURRENCE"], d["NOTES"]),
                    )
                conn.commit()
                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not update item:\n{e}")
                return
            clear_form()
            reload_table()
            self._refresh_compliance_alerts()

        def delete_selected():
            r = table.currentRow()
            if r < 0 or r not in row_data:
                QMessageBox.information(dialog, "No selection", "Select an item first.")
                return
            d = row_data[r]
            confirm = QMessageBox.question(
                dialog, "Confirm delete", f"Delete '{d['NAME']}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM compliance_items WHERE ID=%s", (d["ID"],))
                conn.commit()
                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not delete item:\n{e}")
                return
            clear_form()
            reload_table()
            self._refresh_compliance_alerts()

        btn_row = QHBoxLayout()
        btn_new = QPushButton("New")
        btn_new.clicked.connect(clear_form)
        btn_save = QPushButton("Save")
        btn_save.setStyleSheet(
            "QPushButton { background-color: #1565C0; color: #FFFFFF; border: none; "
            "border-radius: 6px; padding: 8px 14px; font-weight: 600; } "
            "QPushButton:hover { background-color: #1E88E5; }"
        )
        btn_save.clicked.connect(save_item)
        btn_done = QPushButton("Mark Done")
        btn_done.setStyleSheet(
            "QPushButton { background-color: #2E7D32; color: #FFFFFF; border: none; "
            "border-radius: 6px; padding: 8px 14px; font-weight: 600; } "
            "QPushButton:hover { background-color: #388E3C; }"
        )
        btn_done.clicked.connect(mark_done_selected)
        btn_delete = QPushButton("Delete")
        btn_delete.setStyleSheet(
            "QPushButton { background-color: #C62828; color: #FFFFFF; border: none; "
            "border-radius: 6px; padding: 8px 14px; font-weight: 600; } "
            "QPushButton:hover { background-color: #E53935; }"
        )
        btn_delete.clicked.connect(delete_selected)
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(dialog.accept)

        btn_row.addWidget(btn_new)
        btn_row.addWidget(btn_save)
        btn_row.addWidget(btn_done)
        btn_row.addWidget(btn_delete)
        btn_row.addStretch()
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

        reload_table()
        dialog.exec()

    DOCUMENT_CATEGORY_LABELS = {
        "CONTRACT": "Contract",
        "PROPOSAL": "Proposal",
        "INSURANCE_POLICY": "Insurance Policy",
        "LIEN_WAIVER": "Lien Waiver",
        "LICENSE": "License",
        "OTHER": "Other",
    }

    DOCUMENT_ENTITY_LABELS = {
        "COMPANY_SELF": "My Company (Vertex Londe Flooring LLC)",
        "CONTRACTOR": "Contractor",
        "COMPANY": "Company (GC/Client)",
        "CLIENT": "Client",
        "PROJECT": "Project (Job Code)",
    }

    def _setup_documents_feature(self):
        """Cria, em tempo de execução (sem editar o .ui), o botão
        'Documents' no submenu de Registrations — mesmo padrão de
        Compliance: QDialog 100% em Python."""
        self.ui.btn_reg_documents = QPushButton(self.ui.frame_registrations_submenu)
        self.ui.btn_reg_documents.setObjectName(u"btn_reg_documents")
        self.ui.btn_reg_documents.setCheckable(False)
        self.ui.btn_reg_documents.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ui.layout_registrations_submenu.addWidget(self.ui.btn_reg_documents)

    def open_documents_manager_dialog(self, prefill_entity_type=None, prefill_entity_id=None):
        """Repositório central de documentos: contratos, propostas, apólices
        de seguro, lien waivers etc. — vinculados à própria empresa, a um
        Contractor, Company, Client ou Project (Job Code). Guarda só a
        referência do caminho do arquivo (mesmo padrão do anexo de recibo em
        Expenses) — não copia o arquivo pra dentro do banco."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Document Repository")
        dialog.resize(820, 600)
        dialog.setStyleSheet("""
            QTableWidget { background-color: #FFFFFF; color: #1C2B3A; gridline-color: #E3E8EE; }
            QHeaderView::section { background-color: #F0F4F8; color: #1C2B3A; padding: 6px; border: none; font-weight: 600; }
        """)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(
            "<b>Document Repository</b> — contracts, proposals, insurance policies, lien waivers "
            "and any other document, linked to your company, a contractor, a company, a client, or a project. "
            "Double-click a row to open the file."
        ))

        filter_row = QHBoxLayout()
        cmb_filter_entity_type = QComboBox()
        cmb_filter_entity_type.addItem("All", None)
        for key, lbl in self.DOCUMENT_ENTITY_LABELS.items():
            cmb_filter_entity_type.addItem(lbl, key)
        filter_row.addWidget(QLabel("Filter by:"))
        filter_row.addWidget(cmb_filter_entity_type)
        filter_row.addStretch()
        layout.addLayout(filter_row)

        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Category", "Name", "Linked To", "Uploaded", "File"])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(table, 1)

        row_data = {}
        entity_name_cache = {}

        def entity_label(entity_type, entity_id):
            if entity_type == "COMPANY_SELF":
                return "Vertex Londe Flooring LLC"
            if not entity_id:
                return "—"
            key = (entity_type, entity_id)
            if key not in entity_name_cache:
                try:
                    conn2 = self._get_connection()
                    cur2 = conn2.cursor()
                    if entity_type == "PROJECT":
                        cur2.execute("SELECT CODE FROM job_projects WHERE ID = %s", (entity_id,))
                    else:
                        tname = {"CONTRACTOR": "contractors", "COMPANY": "companies",
                                  "CLIENT": "clients"}.get(entity_type)
                        cur2.execute(
                            f"SELECT COALESCE(COMPANY_NAME, FULL_NAME) FROM {tname} WHERE ID = %s", (entity_id,)
                        )
                    r = cur2.fetchone()
                    entity_name_cache[key] = r[0] if r else "—"
                    cur2.close()
                    conn2.close()
                except (MySQLError, RuntimeError):
                    entity_name_cache[key] = "—"
            return entity_name_cache[key]

        def reload_table():
            table.setRowCount(0)
            row_data.clear()
            filter_type = cmb_filter_entity_type.currentData()
            query = "SELECT ID, CATEGORY, ENTITY_TYPE, ENTITY_ID, NAME, FILE_PATH, NOTES, UPLOADED_AT FROM documents"
            params = []
            if filter_type:
                query += " WHERE ENTITY_TYPE = %s"
                params.append(filter_type)
            query += " ORDER BY UPLOADED_AT DESC"
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(
                    dialog, "Database Error",
                    f"Could not load documents:\n{e}\n\n"
                    f"(Did you run migration_fase5_documents.sql on the real database yet?)",
                )
                return

            table.setRowCount(len(rows))
            for r, (did, category, entity_type, entity_id, name, file_path, notes, uploaded_at) in enumerate(rows):
                values = [
                    self.DOCUMENT_CATEGORY_LABELS.get(category, category),
                    name or "",
                    entity_label(entity_type, entity_id),
                    uploaded_at.strftime("%m/%d/%Y") if uploaded_at else "—",
                    os.path.basename(file_path) if file_path else "—",
                ]
                for c, text in enumerate(values):
                    item = QTableWidgetItem(text)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    table.setItem(r, c, item)
                row_data[r] = {
                    "ID": did, "CATEGORY": category, "ENTITY_TYPE": entity_type, "ENTITY_ID": entity_id,
                    "NAME": name, "FILE_PATH": file_path, "NOTES": notes or "", "UPLOADED_AT": uploaded_at,
                }

        cmb_filter_entity_type.currentIndexChanged.connect(reload_table)

        # ── Formulário ──────────────────────────────────────────────
        form_box = QFrame()
        form_layout = QVBoxLayout(form_box)

        row1 = QHBoxLayout()
        cmb_category = QComboBox()
        for key, lbl in self.DOCUMENT_CATEGORY_LABELS.items():
            cmb_category.addItem(lbl, key)
        row1.addWidget(QLabel("Category:"))
        row1.addWidget(cmb_category)

        cmb_entity_type = QComboBox()
        for key, lbl in self.DOCUMENT_ENTITY_LABELS.items():
            cmb_entity_type.addItem(lbl, key)
        row1.addWidget(QLabel("For:"))
        row1.addWidget(cmb_entity_type)

        cmb_entity = QComboBox()
        row1.addWidget(cmb_entity, 1)
        form_layout.addLayout(row1)

        def reload_entity_combo():
            entity_type = cmb_entity_type.currentData()
            cmb_entity.clear()
            if entity_type == "COMPANY_SELF":
                cmb_entity.setEnabled(False)
                return
            cmb_entity.setEnabled(True)
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                if entity_type == "PROJECT":
                    cursor.execute("SELECT ID, CODE FROM job_projects ORDER BY CODE DESC")
                else:
                    tname = {"CONTRACTOR": "contractors", "COMPANY": "companies", "CLIENT": "clients"}[entity_type]
                    cursor.execute(f"SELECT ID, COALESCE(COMPANY_NAME, FULL_NAME) FROM {tname} ORDER BY 2")
                for eid, ename in cursor.fetchall():
                    cmb_entity.addItem(ename, eid)
                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError):
                pass

        cmb_entity_type.currentIndexChanged.connect(reload_entity_combo)
        reload_entity_combo()

        row2 = QHBoxLayout()
        txt_name = QLineEdit()
        txt_name.setPlaceholderText("e.g. Signed Contract — Smith Residence")
        row2.addWidget(QLabel("Name:"))
        row2.addWidget(txt_name, 1)
        form_layout.addLayout(row2)

        row3 = QHBoxLayout()
        txt_file_path = QLineEdit()
        txt_file_path.setPlaceholderText("Pick a file…")
        txt_file_path.setReadOnly(True)
        btn_browse = QPushButton("Browse…")

        def browse_file():
            filepath, _ = QFileDialog.getOpenFileName(dialog, "Select Document File")
            if filepath:
                txt_file_path.setText(filepath)

        btn_browse.clicked.connect(browse_file)
        row3.addWidget(QLabel("File:"))
        row3.addWidget(txt_file_path, 1)
        row3.addWidget(btn_browse)
        form_layout.addLayout(row3)

        row4 = QHBoxLayout()
        txt_notes = QLineEdit()
        txt_notes.setPlaceholderText("Notes (optional)")
        row4.addWidget(QLabel("Notes:"))
        row4.addWidget(txt_notes, 1)
        form_layout.addLayout(row4)

        layout.addWidget(form_box)

        editing_id = {"value": None}

        def clear_form():
            editing_id["value"] = None
            cmb_category.setCurrentIndex(0)
            cmb_entity_type.setCurrentIndex(0)
            reload_entity_combo()
            txt_name.clear()
            txt_file_path.clear()
            txt_notes.clear()
            table.clearSelection()

        def load_selected_into_form():
            r = table.currentRow()
            if r < 0 or r not in row_data:
                return
            d = row_data[r]
            editing_id["value"] = d["ID"]
            cat_keys = list(self.DOCUMENT_CATEGORY_LABELS.keys())
            cmb_category.setCurrentIndex(cat_keys.index(d["CATEGORY"]) if d["CATEGORY"] in cat_keys else 0)
            ent_keys = list(self.DOCUMENT_ENTITY_LABELS.keys())
            cmb_entity_type.setCurrentIndex(ent_keys.index(d["ENTITY_TYPE"]) if d["ENTITY_TYPE"] in ent_keys else 0)
            reload_entity_combo()
            if d["ENTITY_ID"]:
                pos = cmb_entity.findData(d["ENTITY_ID"])
                if pos >= 0:
                    cmb_entity.setCurrentIndex(pos)
            txt_name.setText(d["NAME"] or "")
            txt_file_path.setText(d["FILE_PATH"] or "")
            txt_notes.setText(d["NOTES"] or "")

        table.itemSelectionChanged.connect(load_selected_into_form)

        def open_selected_file():
            r = table.currentRow()
            if r < 0 or r not in row_data:
                QMessageBox.information(dialog, "No selection", "Select a document first.")
                return
            file_path = row_data[r]["FILE_PATH"]
            if not file_path or not os.path.exists(file_path):
                QMessageBox.warning(dialog, "File Not Found",
                                     "This file's path doesn't exist on this computer.\n\n"
                                     f"{file_path or '(no path saved)'}")
                return
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))

        table.cellDoubleClicked.connect(lambda *_: open_selected_file())

        def save_item():
            name = txt_name.text().strip()
            file_path = txt_file_path.text().strip()
            if not name:
                QMessageBox.warning(dialog, "Missing data", "Name is required.")
                return
            if not file_path:
                QMessageBox.warning(dialog, "Missing data", "Pick a file first.")
                return
            category = cmb_category.currentData()
            entity_type = cmb_entity_type.currentData()
            entity_id = cmb_entity.currentData() if entity_type != "COMPANY_SELF" else None
            notes = txt_notes.text().strip()

            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                if editing_id["value"]:
                    cursor.execute(
                        "UPDATE documents SET CATEGORY=%s, ENTITY_TYPE=%s, ENTITY_ID=%s, NAME=%s, "
                        "FILE_PATH=%s, NOTES=%s WHERE ID=%s",
                        (category, entity_type, entity_id, name, file_path, notes, editing_id["value"]),
                    )
                else:
                    cursor.execute(
                        "INSERT INTO documents (CATEGORY, ENTITY_TYPE, ENTITY_ID, NAME, FILE_PATH, NOTES) "
                        "VALUES (%s, %s, %s, %s, %s, %s)",
                        (category, entity_type, entity_id, name, file_path, notes),
                    )
                conn.commit()
                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(
                    dialog, "Database Error",
                    f"Could not save document:\n{e}\n\n"
                    f"(Did you run migration_fase5_documents.sql on the real database yet?)",
                )
                return

            clear_form()
            reload_table()

        def delete_selected():
            r = table.currentRow()
            if r < 0 or r not in row_data:
                QMessageBox.information(dialog, "No selection", "Select a document first.")
                return
            d = row_data[r]
            confirm = QMessageBox.question(
                dialog, "Confirm delete",
                f"Remove '{d['NAME']}' from the repository?\n\n"
                f"(This only removes the reference — the file itself is not deleted from your computer.)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM documents WHERE ID=%s", (d["ID"],))
                conn.commit()
                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not delete document:\n{e}")
                return
            clear_form()
            reload_table()

        btn_row = QHBoxLayout()
        btn_new = QPushButton("New")
        btn_new.clicked.connect(clear_form)
        btn_save = QPushButton("Save")
        btn_save.setStyleSheet(
            "QPushButton { background-color: #1565C0; color: #FFFFFF; border: none; "
            "border-radius: 6px; padding: 8px 14px; font-weight: 600; } "
            "QPushButton:hover { background-color: #1E88E5; }"
        )
        btn_save.clicked.connect(save_item)
        btn_open = QPushButton("Open File")
        btn_open.clicked.connect(open_selected_file)
        btn_delete = QPushButton("Delete")
        btn_delete.setStyleSheet(
            "QPushButton { background-color: #C62828; color: #FFFFFF; border: none; "
            "border-radius: 6px; padding: 8px 14px; font-weight: 600; } "
            "QPushButton:hover { background-color: #E53935; }"
        )
        btn_delete.clicked.connect(delete_selected)
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(dialog.accept)

        btn_row.addWidget(btn_new)
        btn_row.addWidget(btn_save)
        btn_row.addWidget(btn_open)
        btn_row.addWidget(btn_delete)
        btn_row.addStretch()
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

        # Se veio de um atalho (ex: botão "Documents" na tela Project View),
        # já deixa o formulário pronto pra cadastrar um documento pra aquela
        # entidade — não filtra a lista, só pré-seleciona o formulário.
        if prefill_entity_type:
            ent_keys = list(self.DOCUMENT_ENTITY_LABELS.keys())
            if prefill_entity_type in ent_keys:
                cmb_entity_type.setCurrentIndex(ent_keys.index(prefill_entity_type))
                reload_entity_combo()
                if prefill_entity_id:
                    pos = cmb_entity.findData(prefill_entity_id)
                    if pos >= 0:
                        cmb_entity.setCurrentIndex(pos)

        reload_table()
        dialog.exec()
