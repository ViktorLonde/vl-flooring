# -*- coding: utf-8 -*-
"""
Invoices: gerar, enviar por e-mail, listar e ver o detalhe.

Métodos da MainWindow (mixin) — veja main_.py.
"""

from app_common import *  # noqa: F401,F403


class InvoicesMixin:
    def open_send_invoices_dialog(self):
        """Abre uma janela pra enviar os invoices marcados (checkbox na coluna
        'Select') por E-mail (anexa o PDF automaticamente) e/ou WhatsApp (abre
        o chat com uma mensagem pronta — o WhatsApp não permite anexar arquivo
        automaticamente por link, então o PDF precisa ser anexado à mão)."""
        table = self.ui.table_contractor_invoices
        selected_ids = []
        for row in range(table.rowCount()):
            chk_item = table.item(row, 8)
            if chk_item and chk_item.checkState() == Qt.CheckState.Checked:
                invoice_id = int(table.item(row, 0).text())
                selected_ids.append(invoice_id)

        if not selected_ids:
            QMessageBox.information(self, "No invoices selected",
                                     "Mark the checkbox in the 'Select' column for at least one invoice first.")
            return

        entity_type = self.ui.cmb_invoice_entity_type.currentText() or "Contractor"
        contact_table, contact_fk = {
            "Contractor": ("contractors", "CONTRACTOR_ID"),
            "Company": ("companies", "COMPANY_ID"),
            "Client": ("clients", "CLIENT_ID"),
        }[entity_type]
        table_name = {
            "Contractor": "contractor_invoices",
            "Company": "company_invoices",
            "Client": "client_invoices",
        }[entity_type]

        # Busca dados completos (contato + total + período) de cada invoice selecionado
        send_items = []
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            for invoice_id in selected_ids:
                meta = self._invoice_row_meta.get(invoice_id)
                if not meta:
                    continue
                cursor.execute(f"SELECT EMAIL, PHONE_NUMBER FROM {contact_table} WHERE ID = %s", (meta["entity_id"],))
                contact_row = cursor.fetchone()
                email, phone = contact_row if contact_row else (None, None)
                cursor.execute(
                    f"SELECT TOTAL_AMOUNT, PERIOD_FROM, PERIOD_TO FROM {table_name} WHERE ID = %s", (invoice_id,)
                )
                total_amount, period_from, period_to = cursor.fetchone()
                send_items.append({
                    "invoice_id": invoice_id,
                    "entity_name": meta["entity_name"],
                    "pdf_path": meta["pdf_path"],
                    "email": email,
                    "phone": phone,
                    "total_amount": float(total_amount or 0),
                    "period_from": period_from,
                    "period_to": period_to,
                })
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not load invoice details:\n{e}")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Send {len(send_items)} Invoice(s)")
        dialog.resize(520, 560)
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel(f"<b>{len(send_items)} invoice(s) selected:</b>"))
        summary_list = QListWidget()
        summary_list.setMaximumHeight(120)
        for item in send_items:
            flags = []
            if item["email"]:
                flags.append("✉ has email")
            if item["phone"]:
                flags.append("📱 has phone")
            if not flags:
                flags.append("⚠ no contact info")
            summary_list.addItem(f"#{item['invoice_id']} — {item['entity_name']} ({', '.join(flags)})")
        layout.addWidget(summary_list)

        method_row = QHBoxLayout()
        chk_email = QCheckBox("Send by Email (attaches PDF automatically)")
        chk_email.setChecked(True)
        chk_whatsapp = QCheckBox("Send by WhatsApp (opens chat — attach PDF manually)")
        method_row.addWidget(chk_email)
        layout.addLayout(method_row)
        layout.addWidget(chk_whatsapp)

        layout.addWidget(QLabel(
            "<b>Message</b> (use {entity_name}, {total_amount}, {period_from}, {period_to} as placeholders):"
        ))
        txt_message = QTextEdit()
        txt_message.setPlainText(
            f"Hi {{entity_name}},\n\n"
            f"Please find attached your invoice from {company_settings.COMPANY_NAME} for the period "
            f"{{period_from}} to {{period_to}}, totaling ${{total_amount}}.\n\n"
            f"Thank you for your business!\n{company_settings.COMPANY_NAME}"
        )
        txt_message.setMinimumHeight(160)
        layout.addWidget(txt_message)

        lbl_progress = QLabel("")
        layout.addWidget(lbl_progress)

        bottom_row = QHBoxLayout()
        bottom_row.addStretch()
        btn_cancel = QPushButton("Cancel")
        btn_send = QPushButton("Send")
        btn_send.setObjectName("btn_save_job")
        bottom_row.addWidget(btn_cancel)
        bottom_row.addWidget(btn_send)
        layout.addLayout(bottom_row)

        def render_message(template, item):
            period_from_str = (item["period_from"].strftime("%m/%d/%Y")
                                if isinstance(item["period_from"], date) else str(item["period_from"]))
            period_to_str = (item["period_to"].strftime("%m/%d/%Y")
                              if isinstance(item["period_to"], date) else str(item["period_to"]))
            return template.format(
                entity_name=item["entity_name"],
                total_amount=f"{item['total_amount']:,.2f}",
                period_from=period_from_str,
                period_to=period_to_str,
            )

        def send_all():
            template = txt_message.toPlainText()
            send_email = chk_email.isChecked()
            send_whatsapp = chk_whatsapp.isChecked()
            if not send_email and not send_whatsapp:
                QMessageBox.information(dialog, "Choose a method", "Select Email and/or WhatsApp first.")
                return
            if not self._confirm_bank_info_ready(dialog):
                return

            email_ok, email_fail, wa_opened, skipped_no_pdf = 0, [], 0, []

            for item in send_items:
                message_body = render_message(template, item)
                has_pdf = item["pdf_path"] and os.path.exists(item["pdf_path"])
                if not has_pdf:
                    skipped_no_pdf.append(item["entity_name"])

                if send_email:
                    if not item["email"]:
                        email_fail.append(f"{item['entity_name']} (no email on file)")
                    elif not has_pdf:
                        email_fail.append(f"{item['entity_name']} (PDF file not found)")
                    else:
                        try:
                            msg = EmailMessage()
                            msg["Subject"] = f"Invoice from {company_settings.COMPANY_NAME}"
                            msg["From"] = f"{company_settings.EMAIL_FROM_NAME} <{company_settings.EMAIL_SMTP_USER}>"
                            msg["To"] = item["email"]
                            msg.set_content(message_body)
                            with open(item["pdf_path"], "rb") as f:
                                msg.add_attachment(f.read(), maintype="application", subtype="pdf",
                                                    filename=os.path.basename(item["pdf_path"]))
                            with smtplib.SMTP(company_settings.EMAIL_SMTP_HOST, company_settings.EMAIL_SMTP_PORT) as server:
                                server.starttls()
                                server.login(company_settings.EMAIL_SMTP_USER, company_settings.EMAIL_SMTP_PASSWORD)
                                server.send_message(msg)
                            email_ok += 1
                        except Exception as e:
                            email_fail.append(f"{item['entity_name']} ({e})")

                if send_whatsapp:
                    if not item["phone"]:
                        continue
                    phone_digits = "".join(c for c in item["phone"] if c.isdigit())
                    if not phone_digits:
                        continue
                    # WhatsApp precisa do número completo com código do país. Números
                    # americanos são digitados com 10 dígitos (sem o "1" na frente) —
                    # sem isso, o WhatsApp interpreta os primeiros dígitos errado.
                    if len(phone_digits) == 10:
                        phone_digits = "1" + phone_digits
                    from urllib.parse import quote
                    wa_url = f"https://wa.me/{phone_digits}?text={quote(message_body)}"
                    QDesktopServices.openUrl(QUrl(wa_url))
                    wa_opened += 1

            summary_lines = []
            if send_email:
                summary_lines.append(f"Email: {email_ok} sent, {len(email_fail)} failed.")
                if email_fail:
                    summary_lines.append("Failed: " + "; ".join(email_fail))
            if send_whatsapp:
                summary_lines.append(f"WhatsApp: {wa_opened} chat(s) opened "
                                      f"— remember to attach the PDF manually in each chat.")
            if skipped_no_pdf:
                summary_lines.append("No PDF found for: " + ", ".join(skipped_no_pdf))

            QMessageBox.information(dialog, "Send Summary", "\n".join(summary_lines))
            dialog.accept()

        btn_cancel.clicked.connect(dialog.reject)
        btn_send.clicked.connect(send_all)
        dialog.exec()

    def open_generate_invoices_dialog(self, prefill_job_code=None):
        """Abre uma janela pra escolher o tipo (Contractor/Company/Client), o período,
        quem vai receber, e as opções de exibição (agrupar por data, mostrar quantidade)
        e ajustes (desconto/acréscimo/taxa), e gera um PDF de invoice pra cada um."""
        if not REPORTLAB_AVAILABLE:
            QMessageBox.critical(
                self, "Missing Dependency",
                "The 'reportlab' package is not installed.\n\nRun:\npip install reportlab"
            )
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Generate Invoices")
        dialog.resize(940, 760)
        # O estilo global do app (teamviewer_style.py) tem "* { border: none; }",
        # que remove a borda que o QGroupBox usa pra reservar espaço pro título,
        # fazendo o título ficar por cima do conteúdo. Este estilo local corrige
        # isso só dentro desta janela, sem mexer no estilo global do app.
        dialog.setStyleSheet("""
            QGroupBox {
                font-weight: 600;
                border: 1px solid #D0D7DE;
                border-radius: 6px;
                margin-top: 16px;
                padding: 18px 10px 10px 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                top: -2px;
                padding: 0 6px;
                background-color: #F0F4F8;
            }
            QRadioButton::indicator, QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border: 1px solid #8AAEC8;
                border-radius: 3px;
                background-color: #FFFFFF;
            }
            QRadioButton::indicator {
                border-radius: 7px;
            }
            QRadioButton::indicator:checked, QCheckBox::indicator:checked {
                background-color: #1C2B3A;
                border: 1px solid #1C2B3A;
            }
            QTableWidget {
                background-color: #FFFFFF;
                color: #1C2B3A;
                gridline-color: #E3E8EE;
            }
            QTableWidget::item { padding: 4px; }
            QHeaderView::section {
                background-color: #F0F4F8;
                color: #1C2B3A;
                padding: 6px;
                border: none;
                font-weight: 600;
            }
            QTabWidget::pane {
                border: 1px solid #D0D7DE;
                border-radius: 6px;
                top: -1px;
            }
            QTabBar::tab {
                background-color: #F0F4F8;
                color: #37474F;
                padding: 8px 18px;
                border: 1px solid #D0D7DE;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
                font-weight: 600;
            }
            QTabBar::tab:selected {
                background-color: #FFFFFF;
                color: #1565C0;
            }
        """)
        layout = QVBoxLayout(dialog)

        # Tipo de cobrança + Período, tudo na mesma linha (economiza espaço)
        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Bill To:"))
        cmb_bill_to = QComboBox()
        cmb_bill_to.addItems(["Contractor", "Company", "Client"])
        type_row.addWidget(cmb_bill_to)
        type_row.addSpacing(20)
        type_row.addWidget(QLabel("From:"))
        date_from = QDateEdit()
        date_from.setCalendarPopup(True)
        date_from.setDisplayFormat("MM/dd/yyyy")
        date_from.setDate(date.today().replace(day=1))
        date_from.setMinimumWidth(150)
        type_row.addWidget(date_from)
        type_row.addWidget(QLabel("To:"))
        date_to = QDateEdit()
        date_to.setCalendarPopup(True)
        date_to.setDisplayFormat("MM/dd/yyyy")
        date_to.setDate(date.today())
        date_to.setMinimumWidth(150)
        type_row.addWidget(date_to)
        type_row.addSpacing(20)
        type_row.addWidget(QLabel("Job Code (optional):"))
        txt_job_code_filter = QLineEdit()
        txt_job_code_filter.setPlaceholderText("Filter by Job Code…")
        txt_job_code_filter.setCompleter(self._job_code_completer)
        txt_job_code_filter.setMinimumWidth(150)
        type_row.addWidget(txt_job_code_filter)
        type_row.addStretch()
        layout.addLayout(type_row)

        def _autofill_dates_from_job_code():
            """Quando um Job Code é digitado/escolhido, já pega automaticamente
            o período (primeira a última data) dos jobs daquele código, sem
            precisar escolher o intervalo manualmente."""
            code = txt_job_code_filter.text().strip()
            if not code:
                return
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT MIN(wd.WORK_DATE), MAX(wd.WORK_DATE)
                    FROM work_days wd JOIN job_projects jp ON jp.ID = wd.JOB_PROJECT_ID
                    WHERE jp.CODE = %s
                    """,
                    (code,),
                )
                row = cursor.fetchone()
                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError):
                return

            if row and row[0] and row[1]:
                date_from.setDate(QDate(row[0].year, row[0].month, row[0].day))
                date_to.setDate(QDate(row[1].year, row[1].month, row[1].day))

        txt_job_code_filter.editingFinished.connect(_autofill_dates_from_job_code)

        # ── Opções de exibição do invoice ──
        display_group = QGroupBox("Invoice Display Options")
        display_layout = QVBoxLayout(display_group)

        display_layout.addWidget(QLabel("When a date has more than one job:"))
        rb_group_same_date = QRadioButton("Group into one line (addresses listed separately, total value)")
        rb_keep_individual = QRadioButton("Keep individual lines (one row per job)")
        rb_group_same_date.setChecked(True)
        grouping_buttons = QButtonGroup(dialog)
        grouping_buttons.addButton(rb_group_same_date)
        grouping_buttons.addButton(rb_keep_individual)
        display_layout.addWidget(rb_group_same_date)
        display_layout.addWidget(rb_keep_individual)

        chk_show_quantities = QCheckBox("Show quantity next to each Work Type")
        chk_show_quantities.setChecked(True)
        display_layout.addWidget(chk_show_quantities)

        chk_include_expenses = QCheckBox("Include Expenses in Invoice")
        chk_include_expenses.setChecked(True)
        display_layout.addWidget(chk_include_expenses)

        # ── Lista de Contractor/Company/Client (marca/desmarca todos os jobs deles de uma vez) ──
        entity_group = QGroupBox("Select Recipients")
        entity_layout = QVBoxLayout(entity_group)

        btn_find_entities = QPushButton("Find Contractors With Jobs In This Period")
        btn_find_entities.setCursor(Qt.CursorShape.PointingHandCursor)
        entity_layout.addWidget(btn_find_entities)

        entity_scroll = QScrollArea()
        entity_scroll.setWidgetResizable(True)
        entity_checklist_container = QWidget()
        entity_checklist_layout = QVBoxLayout(entity_checklist_container)
        entity_checklist_layout.addStretch()
        entity_scroll.setWidget(entity_checklist_container)
        entity_layout.addWidget(entity_scroll)

        lbl_status = QLabel("")
        entity_layout.addWidget(lbl_status)

        side_by_side = QHBoxLayout()
        side_by_side.addWidget(display_group, 1)
        side_by_side.addWidget(entity_group, 1)
        layout.addLayout(side_by_side)

        # ── Jobs / Expenses em abas (mais compacto que empilhado) ──
        sub_tabs = QTabWidget()

        # -- Aba Jobs --
        tab_jobs_widget = QWidget()
        tab_jobs_layout = QVBoxLayout(tab_jobs_widget)

        select_row = QHBoxLayout()
        lbl_select = QLabel("Only jobs from checked recipients show below — uncheck a specific job to exclude just that one.")
        lbl_select.setWordWrap(True)
        select_row.addWidget(lbl_select)
        select_row.addStretch()
        btn_show_all_jobs = QPushButton("Select All / Deselect All")
        btn_show_all_jobs.setCursor(Qt.CursorShape.PointingHandCursor)
        select_row.addWidget(btn_show_all_jobs)
        tab_jobs_layout.addLayout(select_row)

        table_jobs_select = QTableWidget()
        table_jobs_select.setColumnCount(4)
        table_jobs_select.setHorizontalHeaderLabels(["✓", "Date", "Address", "Value"])
        table_jobs_select.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table_jobs_select.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        table_jobs_select.setColumnWidth(0, 30)
        table_jobs_select.setColumnWidth(1, 90)
        table_jobs_select.setColumnWidth(3, 90)
        tab_jobs_layout.addWidget(table_jobs_select)

        sub_tabs.addTab(tab_jobs_widget, "Jobs")

        # -- Aba Expenses (só relevante pra Contractor) --
        tab_expenses_widget = QWidget()
        tab_expenses_layout = QVBoxLayout(tab_expenses_widget)

        table_expenses_select = QTableWidget()
        table_expenses_select.setColumnCount(4)
        table_expenses_select.setHorizontalHeaderLabels(["✓", "Date", "Description", "Amount"])
        table_expenses_select.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table_expenses_select.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        table_expenses_select.setColumnWidth(0, 30)
        table_expenses_select.setColumnWidth(1, 90)
        table_expenses_select.setColumnWidth(3, 90)
        tab_expenses_layout.addWidget(table_expenses_select)

        expenses_tab_index = sub_tabs.addTab(tab_expenses_widget, "Expenses")

        layout.addWidget(sub_tabs)

        # ── Ajustes (Discount / Additional Fee / Tax) — mais pro final, antes de gerar ──
        adjust_group = QGroupBox("Adjustments (applied to every invoice generated now)")
        adjust_layout = QHBoxLayout(adjust_group)
        adjust_layout.setSpacing(6)

        adjust_layout.addWidget(QLabel("Discount ($):"))
        spin_discount = QDoubleSpinBox()
        spin_discount.setMaximum(999999.99)
        spin_discount.setPrefix("$ ")
        spin_discount.setMaximumWidth(110)
        adjust_layout.addWidget(spin_discount)

        adjust_layout.addSpacing(16)
        adjust_layout.addWidget(QLabel("Additional Fee ($):"))
        spin_addition = QDoubleSpinBox()
        spin_addition.setMaximum(999999.99)
        spin_addition.setPrefix("$ ")
        spin_addition.setMaximumWidth(110)
        adjust_layout.addWidget(spin_addition)

        adjust_layout.addSpacing(16)
        adjust_layout.addWidget(QLabel("Tax (%):"))
        spin_tax = QDoubleSpinBox()
        spin_tax.setMaximum(100.0)
        spin_tax.setSuffix(" %")
        spin_tax.setMaximumWidth(90)
        adjust_layout.addWidget(spin_tax)

        adjust_layout.addStretch()

        layout.addWidget(adjust_group)

        bottom_row = QHBoxLayout()
        bottom_row.addStretch()
        btn_cancel = QPushButton("Cancel")
        btn_preview = QPushButton("👁  Preview First Invoice")
        btn_generate = QPushButton("Generate PDFs")
        btn_generate.setObjectName("btn_save_job")  # reaproveita o estilo azul
        bottom_row.addWidget(btn_cancel)
        bottom_row.addWidget(btn_preview)
        bottom_row.addWidget(btn_generate)
        layout.addLayout(bottom_row)

        job_queries = {
            "Contractor": (
                "SELECT wd.ID, wd.WORK_DATE, c.ID, COALESCE(c.COMPANY_NAME, c.FULL_NAME), wd.JOB_ADDRESS, wd.VALUE "
                "FROM work_days wd JOIN contractors c ON c.ID = wd.CONTRACTOR_ID "
                "LEFT JOIN job_projects jp ON jp.ID = wd.JOB_PROJECT_ID "
                "WHERE wd.WORK_DATE BETWEEN %s AND %s {job_code_clause} "
                "ORDER BY COALESCE(c.COMPANY_NAME, c.FULL_NAME), wd.WORK_DATE, COALESCE(wd.DAY_SEQUENCE, 999999), wd.ID"
            ),
            "Company": (
                "SELECT wd.ID, wd.WORK_DATE, co.ID, co.COMPANY_NAME, wd.JOB_ADDRESS, wd.VALUE "
                "FROM work_days wd JOIN companies co ON co.ID = wd.COMPANY_ID "
                "LEFT JOIN job_projects jp ON jp.ID = wd.JOB_PROJECT_ID "
                "WHERE wd.WORK_DATE BETWEEN %s AND %s {job_code_clause} "
                "ORDER BY co.COMPANY_NAME, wd.WORK_DATE, COALESCE(wd.DAY_SEQUENCE, 999999), wd.ID"
            ),
            "Client": (
                "SELECT wd.ID, wd.WORK_DATE, cl.ID, cl.FULL_NAME, wd.JOB_ADDRESS, wd.VALUE "
                "FROM work_days wd JOIN clients cl ON cl.ID = wd.CLIENT_ID "
                "LEFT JOIN job_projects jp ON jp.ID = wd.JOB_PROJECT_ID "
                "WHERE wd.WORK_DATE BETWEEN %s AND %s {job_code_clause} "
                "ORDER BY cl.FULL_NAME, wd.WORK_DATE, COALESCE(wd.DAY_SEQUENCE, 999999), wd.ID"
            ),
        }

        job_row_data = {}  # linha da tabela -> (job_id, entity_id, entity_name)
        entity_checkboxes = []  # lista de (entity_id, entity_name, checkbox)
        entity_job_rows = {}  # entity_id -> [linhas da tabela de jobs que são dele]
        expense_row_data = {}  # linha da tabela de despesas -> (expense_id, entity_id)
        entity_expense_rows = {}  # entity_id -> [linhas da tabela de despesas que são dele]
        _syncing = {"active": False}  # evita loop entre marcar entidade <-> marcar job

        def update_status_label():
            """Mostra quantos jobs e despesas estão marcados agora (e a soma
            dos valores), considerando só o que está visível (respeitando o
            filtro por nome)."""
            checked_job_rows = [
                r for r in range(table_jobs_select.rowCount())
                if table_jobs_select.item(r, 0) is not None
                and not table_jobs_select.isRowHidden(r)
                and table_jobs_select.item(r, 0).checkState() == Qt.CheckState.Checked
            ]
            jobs_total = sum(
                table_jobs_select.item(r, 0).data(Qt.ItemDataRole.UserRole) or 0 for r in checked_job_rows
            )
            status_text = f"{len(checked_job_rows)} job(s) selected — total ${jobs_total:,.2f}"

            if table_expenses_select.rowCount() > 0:
                checked_expense_rows = [
                    r for r in range(table_expenses_select.rowCount())
                    if table_expenses_select.item(r, 0) is not None
                    and not table_expenses_select.isRowHidden(r)
                    and table_expenses_select.item(r, 0).checkState() == Qt.CheckState.Checked
                ]
                expenses_total = sum(
                    table_expenses_select.item(r, 0).data(Qt.ItemDataRole.UserRole) or 0
                    for r in checked_expense_rows
                )
                status_text += (
                    f"  |  {len(checked_expense_rows)} expense(s) selected — total ${expenses_total:,.2f}"
                )

            lbl_status.setText(status_text)

        def toggle_entity_jobs(entity_id, checked):
            """Quando marca/desmarca um Contractor/Company/Client na lista, marca/
            desmarca os jobs dele na tabela — e a tabela só MOSTRA os jobs de quem
            estiver marcado (desmarcou o nome, some da tabela; marcou, aparece)."""
            if _syncing["active"]:
                return
            _syncing["active"] = True
            state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
            for row_idx in entity_job_rows.get(entity_id, []):
                item = table_jobs_select.item(row_idx, 0)
                if item:
                    item.setCheckState(state)
                table_jobs_select.setRowHidden(row_idx, not checked)
            for row_idx in entity_expense_rows.get(entity_id, []):
                item = table_expenses_select.item(row_idx, 0)
                if item:
                    item.setCheckState(state)
                table_expenses_select.setRowHidden(row_idx, not checked)
            _syncing["active"] = False
            update_status_label()

        def toggle_select_all_jobs():
            """Marca ou desmarca todos os jobs que estão VISÍVEIS na tabela
            agora (respeitando o filtro atual — se só o Marcinho está sendo
            mostrado, só os jobs dele são marcados/desmarcados)."""
            visible_rows = [r for r in range(table_jobs_select.rowCount()) if not table_jobs_select.isRowHidden(r)]
            if not visible_rows:
                return
            any_unchecked = any(
                table_jobs_select.item(r, 0).checkState() != Qt.CheckState.Checked for r in visible_rows
            )
            new_state = Qt.CheckState.Checked if any_unchecked else Qt.CheckState.Unchecked
            for r in visible_rows:
                table_jobs_select.item(r, 0).setCheckState(new_state)
            update_status_label()

        def find_entities():
            """Busca todos os jobs individuais (do tipo/período escolhidos),
            monta a lista de Contractor/Company/Client à direita (todos
            marcados por padrão) e a tabela de jobs de baixo pra afinar."""
            table_jobs_select.setRowCount(0)
            job_row_data.clear()
            entity_job_rows.clear()
            table_expenses_select.setRowCount(0)
            expense_row_data.clear()
            entity_expense_rows.clear()
            for _, _, chk in entity_checkboxes:
                chk.setParent(None)
            entity_checkboxes.clear()

            bill_to = cmb_bill_to.currentText()
            btn_find_entities.setText(f"Find {bill_to}s With Jobs In This Period")

            # Só Contractor tem reembolso de despesas
            sub_tabs.setTabVisible(expenses_tab_index, bill_to == "Contractor")

            d_from = date_from.date().toString("yyyy-MM-dd")
            d_to = date_to.date().toString("yyyy-MM-dd")

            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                job_code_filter = txt_job_code_filter.text().strip()
                job_code_clause = "AND jp.CODE = %s" if job_code_filter else ""
                query = job_queries[bill_to].format(job_code_clause=job_code_clause)
                params = [d_from, d_to] + ([job_code_filter] if job_code_filter else [])
                cursor.execute(query, params)
                rows = cursor.fetchall()

                expense_rows = []
                if bill_to == "Contractor":
                    cursor.execute(
                        "SELECT e.ID, e.EXPENSE_DATE, c.ID, e.DESCRIPTION, e.AMOUNT, "
                        "COALESCE(c.COMPANY_NAME, c.FULL_NAME) "
                        "FROM expenses e JOIN contractors c ON c.ID = e.CONTRACTOR_ID "
                        "WHERE e.EXPENSE_DATE BETWEEN %s AND %s "
                        "ORDER BY COALESCE(c.COMPANY_NAME, c.FULL_NAME), e.EXPENSE_DATE",
                        (d_from, d_to),
                    )
                    expense_rows = cursor.fetchall()

                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not load jobs:\n{e}")
                return

            if not rows:
                lbl_status.setText(f"No {bill_to.lower()}s have jobs in this period.")

            table_expenses_select.blockSignals(True)
            table_expenses_select.setRowCount(len(expense_rows))
            expense_only_entities = {}  # entity_id -> entity_name, pra quem só tem despesa (sem job) no período
            for row_idx, (expense_id, exp_date, entity_id, description, amount, entity_name) in enumerate(expense_rows):
                chk_item = QTableWidgetItem()
                chk_item.setFlags((chk_item.flags() | Qt.ItemFlag.ItemIsUserCheckable) & ~Qt.ItemFlag.ItemIsEditable)
                chk_item.setCheckState(Qt.CheckState.Checked)
                chk_item.setData(Qt.ItemDataRole.UserRole, float(amount or 0))
                table_expenses_select.setItem(row_idx, 0, chk_item)

                exp_date_str = exp_date.strftime("%m/%d/%Y") if isinstance(exp_date, date) else str(exp_date)
                exp_values = [exp_date_str, str(description or ""), f"${float(amount or 0):,.2f}"]
                for c, text in enumerate(exp_values, start=1):
                    item = QTableWidgetItem(text)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    table_expenses_select.setItem(row_idx, c, item)

                expense_row_data[row_idx] = (expense_id, entity_id, entity_name)
                entity_expense_rows.setdefault(entity_id, []).append(row_idx)
                expense_only_entities.setdefault(entity_id, entity_name)
            table_expenses_select.blockSignals(False)

            table_jobs_select.blockSignals(True)
            table_jobs_select.setRowCount(len(rows))
            seen_entities = {}  # entity_id -> entity_name, na ordem em que aparecem
            for row_idx, (job_id, work_date, entity_id, entity_name, address, value) in enumerate(rows):
                chk_item = QTableWidgetItem()
                chk_item.setFlags((chk_item.flags() | Qt.ItemFlag.ItemIsUserCheckable) & ~Qt.ItemFlag.ItemIsEditable)
                chk_item.setCheckState(Qt.CheckState.Checked)
                chk_item.setData(Qt.ItemDataRole.UserRole, float(value or 0))
                table_jobs_select.setItem(row_idx, 0, chk_item)

                date_str = work_date.strftime("%m/%d/%Y") if isinstance(work_date, date) else str(work_date)
                values = [date_str, str(address or ""), f"${float(value or 0):,.2f}"]
                for c, text in enumerate(values, start=1):
                    item = QTableWidgetItem(text)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    table_jobs_select.setItem(row_idx, c, item)

                job_row_data[row_idx] = (job_id, entity_id, entity_name)
                entity_job_rows.setdefault(entity_id, []).append(row_idx)
                seen_entities.setdefault(entity_id, entity_name)
            table_jobs_select.blockSignals(False)

            # Entidades que só têm despesa (sem nenhum job) também entram na lista,
            # senão não haveria como marcar/desmarcar elas pra incluir no invoice.
            for entity_id, entity_name in expense_only_entities.items():
                seen_entities.setdefault(entity_id, entity_name)

            for entity_id, entity_name in seen_entities.items():
                chk = QCheckBox(entity_name)
                chk.setChecked(True)
                chk.stateChanged.connect(
                    lambda _state, eid=entity_id, cb=chk: toggle_entity_jobs(eid, cb.isChecked())
                )
                entity_checklist_layout.insertWidget(entity_checklist_layout.count() - 1, chk)
                entity_checkboxes.append((entity_id, entity_name, chk))

            if rows:
                update_status_label()

        def generate_pdfs():
            """Agrupa os jobs marcados por entidade e gera um PDF de invoice
            pra cada entidade que tiver pelo menos um job selecionado."""
            if not self._confirm_bank_info_ready(dialog):
                return
            bill_to = cmb_bill_to.currentText()

            entities = {}  # entity_id -> {"name": ..., "job_ids": [...], "expense_ids": [...]}
            for row_idx in range(table_jobs_select.rowCount()):
                chk_item = table_jobs_select.item(row_idx, 0)
                if chk_item and chk_item.checkState() == Qt.CheckState.Checked:
                    job_id, entity_id, entity_name = job_row_data[row_idx]
                    entities.setdefault(entity_id, {"name": entity_name, "job_ids": [], "expense_ids": []})
                    entities[entity_id]["job_ids"].append(job_id)

            if chk_include_expenses.isChecked():
                for row_idx in range(table_expenses_select.rowCount()):
                    chk_item = table_expenses_select.item(row_idx, 0)
                    if chk_item and chk_item.checkState() == Qt.CheckState.Checked:
                        expense_id, entity_id, entity_name = expense_row_data[row_idx]
                        entities.setdefault(entity_id, {"name": entity_name, "job_ids": [], "expense_ids": []})
                        entities[entity_id]["expense_ids"].append(expense_id)
                for eid, data in entities.items():
                    if eid not in entity_expense_rows:
                        data["expense_ids"] = None  # essa entidade não tem despesas nesse período
            else:
                for data in entities.values():
                    data["expense_ids"] = []  # "Include Expenses" desmarcado = nenhuma despesa entra

            selected = [(eid, data["name"], data["job_ids"], data["expense_ids"]) for eid, data in entities.items()]
            if not selected:
                QMessageBox.information(dialog, "No selection",
                                         "Select at least one job first.")
                return

            out_dir = QFileDialog.getExistingDirectory(dialog, "Choose folder to save the invoices")
            if not out_dir:
                return

            d_from_qdate = date_from.date()
            d_to_qdate = date_to.date()
            d_from = d_from_qdate.toString("yyyy-MM-dd")
            d_to = d_to_qdate.toString("yyyy-MM-dd")

            options = {
                "group_same_date": rb_group_same_date.isChecked(),
                "show_qty": chk_show_quantities.isChecked(),
                "discount": spin_discount.value(),
                "addition": spin_addition.value(),
                "tax_percent": spin_tax.value(),
            }

            generator = {
                "Contractor": self._generate_single_contractor_invoice,
                "Company": self._generate_single_company_invoice,
                "Client": self._generate_single_client_invoice,
            }[bill_to]

            generated = 0
            errors = []
            for entity_id, entity_name, job_ids, expense_ids in selected:
                try:
                    generator(entity_id, entity_name, d_from, d_to, d_from_qdate, d_to_qdate,
                              out_dir, options, job_ids=job_ids, expense_ids=expense_ids)
                    generated += 1
                except Exception as e:
                    errors.append(f"{entity_name}: {e}")

            msg = f"{generated} invoice(s) generated in:\n{out_dir}"
            if errors:
                msg += "\n\nSome failed:\n" + "\n".join(errors)
            QMessageBox.information(dialog, "Done", msg)
            self.load_receivables_dashboard()
            self.load_contractor_invoices()
            dialog.accept()

        def preview_first_invoice():
            """Monta o PDF do primeiro selecionado num arquivo temporário (sem
            gravar nada no banco) e abre no leitor de PDF padrão, pra conferir
            antes de gerar todos de vez."""
            bill_to = cmb_bill_to.currentText()

            entities = {}
            first_entity_id = None
            for row_idx in range(table_jobs_select.rowCount()):
                chk_item = table_jobs_select.item(row_idx, 0)
                if chk_item and chk_item.checkState() == Qt.CheckState.Checked:
                    job_id, entity_id, entity_name = job_row_data[row_idx]
                    if first_entity_id is None:
                        first_entity_id = entity_id
                    if entity_id != first_entity_id:
                        continue  # o preview mostra só o primeiro Contractor/Company/Client, com todos os jobs dele
                    entities.setdefault(entity_id, {"name": entity_name, "job_ids": []})
                    entities[entity_id]["job_ids"].append(job_id)

            if not entities and chk_include_expenses.isChecked():
                # nenhum job marcado — tenta achar alguém que só tenha despesa marcada
                for row_idx in range(table_expenses_select.rowCount()):
                    chk_item = table_expenses_select.item(row_idx, 0)
                    if chk_item and chk_item.checkState() == Qt.CheckState.Checked:
                        expense_id, entity_id, entity_name = expense_row_data[row_idx]
                        entities.setdefault(entity_id, {"name": entity_name, "job_ids": []})
                        break  # só o primeiro, igual faz com jobs

            if not entities:
                QMessageBox.information(dialog, "No selection", "Select at least one job or expense first.")
                return

            entity_id, first = next(iter(entities.items()))
            entity_name, job_ids = first["name"], first["job_ids"]
            d_from_qdate = date_from.date()
            d_to_qdate = date_to.date()
            d_from = d_from_qdate.toString("yyyy-MM-dd")
            d_to = d_to_qdate.toString("yyyy-MM-dd")
            options = {
                "group_same_date": rb_group_same_date.isChecked(),
                "show_qty": chk_show_quantities.isChecked(),
                "discount": spin_discount.value(),
                "addition": spin_addition.value(),
                "tax_percent": spin_tax.value(),
            }

            try:
                fk_col, ref_table, ref_fk_col, ref_name_col, expense_col = {
                    "Contractor": ("CONTRACTOR_ID", "clients", "CLIENT_ID", "FULL_NAME", "CONTRACTOR_ID"),
                    "Company": ("COMPANY_ID", "clients", "CLIENT_ID", "FULL_NAME", None),
                    "Client": ("CLIENT_ID", "companies", "COMPANY_ID", "COMPANY_NAME", None),
                }[bill_to]

                conn = self._get_connection()
                cursor = conn.cursor()
                wt_lookup = self._get_work_type_lookup(cursor)
                jobs = self._fetch_invoice_jobs(cursor, fk_col, entity_id, d_from, d_to,
                                                 ref_table, ref_fk_col, ref_name_col, job_ids=job_ids)

                expenses_rows, expenses_total, has_expenses = [], 0.0, False
                if expense_col and chk_include_expenses.isChecked():
                    has_expenses = True
                    preview_expense_ids = [
                        expense_row_data[r][0] for r in range(table_expenses_select.rowCount())
                        if expense_row_data.get(r, (None, None))[1] == entity_id
                        and table_expenses_select.item(r, 0).checkState() == Qt.CheckState.Checked
                    ]
                    expense_query = (
                        "SELECT EXPENSE_DATE, CATEGORY, DESCRIPTION, AMOUNT FROM expenses "
                        "WHERE CONTRACTOR_ID = %s AND EXPENSE_DATE BETWEEN %s AND %s"
                    )
                    expense_params = [entity_id, d_from, d_to]
                    if entity_id in entity_expense_rows:
                        # essa entidade tem despesas no período: respeita só as marcadas
                        if preview_expense_ids:
                            placeholders = ", ".join(["%s"] * len(preview_expense_ids))
                            expense_query += f" AND ID IN ({placeholders})"
                            expense_params.extend(preview_expense_ids)
                        else:
                            expense_query += " AND FALSE"  # todas foram desmarcadas
                    cursor.execute(expense_query + " ORDER BY EXPENSE_DATE", expense_params)
                    for exp_date, category, description, amount in cursor.fetchall():
                        amount = float(amount or 0)
                        expenses_total += amount
                        exp_date_str = exp_date.strftime("%m/%d/%Y") if isinstance(exp_date, date) else str(exp_date)
                        expenses_rows.append([exp_date_str, category, description or "", f"${amount:,.2f}"])
                elif expense_col:
                    has_expenses = False  # "Include Expenses" desmarcado: nem mostra a seção

                contact_table = {"Contractor": "contractors", "Company": "companies", "Client": "clients"}[bill_to]
                cursor.execute(f"SELECT EMAIL, PHONE_NUMBER FROM {contact_table} WHERE ID = %s", (entity_id,))
                contact_row = cursor.fetchone()
                contact_lines = []
                if contact_row:
                    c_email, c_phone = contact_row
                    if c_email:
                        contact_lines.append(c_email)
                    if c_phone:
                        contact_lines.append(self._format_phone(c_phone))

                cursor.close()
                conn.close()

                styles = getSampleStyleSheet()
                cell_style = ParagraphStyle("cell_preview", parent=styles["Normal"], fontSize=8.5, leading=11)
                item_rows, jobs_total = self._prepare_invoice_item_rows(jobs, wt_lookup, options, cell_style)

                temp_path = os.path.join(tempfile.gettempdir(), "invoice_preview.pdf")
                self._build_invoice_pdf(
                    temp_path, "PREVIEW", bill_to, entity_name, contact_lines,
                    d_from_qdate, d_to_qdate, item_rows, jobs_total, has_expenses, expenses_rows,
                    expenses_total, options["discount"], options["addition"], options["tax_percent"],
                    "PENDING",
                )
                QDesktopServices.openUrl(QUrl.fromLocalFile(temp_path))
            except Exception as e:
                QMessageBox.critical(dialog, "Preview Error", f"Could not build the preview:\n{e}")

        cmb_bill_to.currentIndexChanged.connect(find_entities)
        btn_find_entities.clicked.connect(find_entities)
        btn_show_all_jobs.clicked.connect(toggle_select_all_jobs)
        table_jobs_select.itemChanged.connect(
            lambda item: update_status_label() if item.column() == 0 else None
        )
        table_expenses_select.itemChanged.connect(
            lambda item: update_status_label() if item.column() == 0 else None
        )
        btn_cancel.clicked.connect(dialog.reject)
        btn_preview.clicked.connect(preview_first_invoice)
        btn_generate.clicked.connect(generate_pdfs)

        if prefill_job_code:
            txt_job_code_filter.setText(prefill_job_code)
            _autofill_dates_from_job_code()

        find_entities()  # já carrega ao abrir, usando o período padrão (mês atual) e tipo Contractor
        dialog.exec()

    def load_contractor_invoices(self):
        """Carrega o histórico de invoices gerados (Contractor, Company ou
        Client, conforme selecionado em cmb_invoice_entity_type), com filtro de status."""
        entity_type = self.ui.cmb_invoice_entity_type.currentText() or "Contractor"
        status_filter = self.ui.cmb_filter_invoice_status.currentText()

        table_name, ref_table, fk_col, name_col = {
            "Contractor": ("contractor_invoices", "contractors", "CONTRACTOR_ID", "COALESCE(r.COMPANY_NAME, r.FULL_NAME)"),
            "Company": ("company_invoices", "companies", "COMPANY_ID", "r.COMPANY_NAME"),
            "Client": ("client_invoices", "clients", "CLIENT_ID", "r.FULL_NAME"),
        }[entity_type]

        # Contractor invoices tem coluna EXPENSES_TOTAL; Company/Client não têm despesas.
        has_expenses = entity_type == "Contractor"
        expenses_select = "ci.EXPENSES_TOTAL" if has_expenses else "0"

        query = f"""
            SELECT ci.ID, COALESCE({name_col}, '—'), ci.PERIOD_FROM, ci.PERIOD_TO,
                   ci.JOBS_TOTAL, {expenses_select}, ci.TOTAL_AMOUNT, ci.AMOUNT_PAID, ci.STATUS,
                   ci.GENERATED_AT, ci.PDF_PATH, ci.{fk_col}
                   {", r.PAYMENT_CYCLE_TYPE, r.PAYMENT_CYCLE_WEEKDAY, r.PAYMENT_CYCLE_DAYS" if entity_type == "Contractor" else ""}
            FROM {table_name} ci
            LEFT JOIN {ref_table} r ON r.ID = ci.{fk_col}
            WHERE 1=1
        """
        params = []
        if status_filter and status_filter != "All Status":
            query += " AND ci.STATUS = %s"
            params.append(status_filter)
        query += " ORDER BY ci.GENERATED_AT DESC, ci.ID DESC"

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not load invoices:\n{e}")
            return

        table = self.ui.table_contractor_invoices
        # Cabeçalho da 2ª coluna muda conforme o tipo selecionado (Contractor/Company/Client)
        table.horizontalHeaderItem(1).setText(entity_type)
        table.setSortingEnabled(False)
        table.setRowCount(0)
        table.setRowCount(len(rows))

        # Guarda os metadados de cada invoice (entidade, pdf) pra usar depois no envio em lote
        self._invoice_row_meta = {}

        status_bg = {
            "PENDING": QColor("#FFF3E0"), "PARTIAL": QColor("#E3F2FD"), "RECEIVED": QColor("#E8F5E9"),
        }
        status_fg = {
            "PENDING": QColor("#E65100"), "PARTIAL": QColor("#1565C0"), "RECEIVED": QColor("#2E7D32"),
        }

        for row_idx, row_data in enumerate(rows):
            if entity_type == "Contractor":
                (invoice_id, entity_name, period_from, period_to,
                 jobs_total, expenses_total, total_amount, amount_paid, status,
                 generated_at, pdf_path, entity_id,
                 cycle_type, cycle_weekday, cycle_days) = row_data
                is_overdue = status in ("PENDING", "PARTIAL") and self._is_contractor_invoice_overdue(
                    generated_at, cycle_type or "CUSTOM_DAYS", cycle_weekday, cycle_days or 30)
            else:
                (invoice_id, entity_name, period_from, period_to,
                 jobs_total, expenses_total, total_amount, amount_paid, status,
                 generated_at, pdf_path, entity_id) = row_data
                is_overdue = False

            self._invoice_row_meta[invoice_id] = {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "entity_name": entity_name,
                "pdf_path": pdf_path,
            }

            jobs_expenses_str = (
                f"${float(jobs_total):,.2f} + ${float(expenses_total):,.2f}"
                if has_expenses else f"${float(jobs_total):,.2f}"
            )
            status_label = PAYMENT_STATUS_LABELS.get(status, str(status))
            if is_overdue:
                status_label += " ⚠ Overdue"
            values = [
                str(invoice_id),
                str(entity_name),
                period_from.strftime("%m/%d/%Y") if isinstance(period_from, date) else str(period_from),
                period_to.strftime("%m/%d/%Y") if isinstance(period_to, date) else str(period_to),
                jobs_expenses_str,
                f"${float(total_amount):,.2f}",
                f"${float(amount_paid):,.2f}",
                status_label,
            ]
            for col_idx, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if col_idx == 7:
                    if is_overdue:
                        item.setBackground(QColor("#FFEBEE"))
                        item.setForeground(QColor("#C62828"))
                    else:
                        bg = status_bg.get(status)
                        fg = status_fg.get(status)
                        if bg: item.setBackground(bg)
                        if fg: item.setForeground(fg)
                table.setItem(row_idx, col_idx, item)

            # Checkbox de seleção (última coluna) pra escolher quais invoices enviar em lote
            chk_item = QTableWidgetItem()
            chk_item.setFlags((chk_item.flags() | Qt.ItemFlag.ItemIsUserCheckable) & ~Qt.ItemFlag.ItemIsEditable)
            chk_item.setCheckState(Qt.CheckState.Unchecked)
            chk_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row_idx, 8, chk_item)

        table.setSortingEnabled(True)

    def open_invoice_detail_dialog(self):
        """Abre um pop-up com os detalhes do invoice selecionado (Contractor,
        Company ou Client, conforme o filtro atual): histórico de pagamentos
        recebidos (quem, quando, quanto, como) e opção de registrar um novo
        pagamento, além de status/nota manuais e reabrir o PDF."""
        table = self.ui.table_contractor_invoices
        selected = table.currentRow()
        if selected < 0:
            return

        invoice_id = int(table.item(selected, 0).text())
        entity_type = self.ui.cmb_invoice_entity_type.currentText() or "Contractor"

        table_name, ref_table, fk_col, name_col = {
            "Contractor": ("contractor_invoices", "contractors", "CONTRACTOR_ID", "COALESCE(r.COMPANY_NAME, r.FULL_NAME)"),
            "Company": ("company_invoices", "companies", "COMPANY_ID", "r.COMPANY_NAME"),
            "Client": ("client_invoices", "clients", "CLIENT_ID", "r.FULL_NAME"),
        }[entity_type]
        has_expenses = entity_type == "Contractor"
        expenses_select = "ci.EXPENSES_TOTAL" if has_expenses else "0"

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT ci.ID, COALESCE({name_col}, '—'), ci.PERIOD_FROM, ci.PERIOD_TO,
                       ci.JOBS_TOTAL, {expenses_select}, ci.TOTAL_AMOUNT, ci.AMOUNT_PAID,
                       ci.STATUS, ci.PDF_PATH, ci.ADJUSTMENT_NOTE
                FROM {table_name} ci
                LEFT JOIN {ref_table} r ON r.ID = ci.{fk_col}
                WHERE ci.ID = %s
                """,
                (invoice_id,),
            )
            row = cursor.fetchone()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not load invoice:\n{e}")
            return

        if not row:
            return

        (_, entity_name, period_from, period_to, jobs_total, expenses_total,
         total_amount, amount_paid, status, pdf_path, adjustment_note) = row

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Invoice #{invoice_id} — {entity_name}")
        dialog.resize(480, 640)
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

        layout.addWidget(QLabel(f"<b>{entity_type}:</b> {entity_name}"))
        layout.addWidget(QLabel(
            f"<b>Period:</b> {period_from.strftime('%m/%d/%Y')} to {period_to.strftime('%m/%d/%Y')}"
        ))
        layout.addWidget(QLabel(f"<b>Jobs:</b> ${float(jobs_total):,.2f}"))
        if has_expenses:
            layout.addWidget(QLabel(f"<b>Expenses:</b> ${float(expenses_total):,.2f}"))
        lbl_total_due = QLabel(f"<b>Total Due:</b> ${float(total_amount):,.2f}")
        layout.addWidget(lbl_total_due)
        lbl_balance = QLabel("")
        layout.addWidget(lbl_balance)
        layout.addWidget(QLabel(""))

        # ── Histórico de pagamentos recebidos (quem/quando/quanto/como) ──
        layout.addWidget(QLabel("<b>Payment History</b>"))
        table_payments = QTableWidget()
        table_payments.setColumnCount(5)
        table_payments.setHorizontalHeaderLabels(["Date", "Amount", "Method", "Note", ""])
        table_payments.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table_payments.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table_payments.horizontalHeader().setStretchLastSection(False)
        table_payments.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        table_payments.setColumnWidth(4, 70)
        table_payments.setMaximumHeight(160)
        layout.addWidget(table_payments)

        def delete_payment(payment_id):
            confirm = QMessageBox.question(
                dialog, "Remove Payment",
                "Remove this payment record? The invoice status and balance will be "
                "recalculated automatically. This cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return
            try:
                conn3 = self._get_connection()
                cur3 = conn3.cursor()
                cur3.execute("DELETE FROM payments WHERE ID = %s", (payment_id,))
                cur3.execute(
                    "SELECT COALESCE(SUM(AMOUNT), 0) FROM payments WHERE INVOICE_TYPE = %s AND INVOICE_ID = %s",
                    (entity_type, invoice_id),
                )
                new_total_paid = float(cur3.fetchone()[0] or 0)
                new_status = _status_for_paid_amount(new_total_paid)
                received_clause = ", RECEIVED_AT = NOW()" if new_status == "RECEIVED" else ", RECEIVED_AT = NULL"
                cur3.execute(
                    f"UPDATE {table_name} SET AMOUNT_PAID = %s, STATUS = %s {received_clause} WHERE ID = %s",
                    (new_total_paid, new_status, invoice_id),
                )
                conn3.commit()
                cur3.close()
                conn3.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not remove payment:\n{e}")
                return
            refresh_payment_history()
            cmb_status.setCurrentText(PAYMENT_STATUS_LABELS.get(new_status, new_status))
            self.load_contractor_invoices()
            self.load_receivables_dashboard()

        def refresh_payment_history():
            """Recarrega a tabela de histórico e recalcula total pago / saldo devedor
            a partir da soma real dos pagamentos registrados (fonte da verdade)."""
            try:
                conn2 = self._get_connection()
                cur2 = conn2.cursor()
                cur2.execute(
                    """
                    SELECT ID, PAID_DATE, AMOUNT, PAYMENT_METHOD, NOTE FROM payments
                    WHERE INVOICE_TYPE = %s AND INVOICE_ID = %s
                    ORDER BY PAID_DATE DESC, ID DESC
                    """,
                    (entity_type, invoice_id),
                )
                payment_rows = cur2.fetchall()
                cur2.close()
                conn2.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.warning(dialog, "Database Error", f"Could not load payment history:\n{e}")
                return 0.0

            table_payments.setRowCount(len(payment_rows))
            total_paid = 0.0
            for r, (payment_id, paid_date, amount, method, note) in enumerate(payment_rows):
                amount = float(amount or 0)
                total_paid += amount
                date_str = paid_date.strftime("%m/%d/%Y") if isinstance(paid_date, date) else str(paid_date)
                values = [date_str, f"${amount:,.2f}", method or "", note or ""]
                for c, val in enumerate(values):
                    item = QTableWidgetItem(val)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    table_payments.setItem(r, c, item)

                btn_delete_payment = QPushButton("✕")
                btn_delete_payment.setAutoDefault(False)
                btn_delete_payment.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_delete_payment.setToolTip("Remove this payment")
                btn_delete_payment.setStyleSheet(
                    "QPushButton { color: #C62828; font-weight: 700; border: none; background: transparent; } "
                    "QPushButton:hover { background-color: #FBE9E7; border-radius: 4px; }"
                )
                btn_delete_payment.clicked.connect(lambda _checked, pid=payment_id: delete_payment(pid))
                table_payments.setCellWidget(r, 4, btn_delete_payment)

            balance = float(total_amount) - total_paid
            lbl_balance.setText(
                f"<b>Total Paid:</b> ${total_paid:,.2f} &nbsp;&nbsp; "
                f"<b>Balance Due:</b> ${balance:,.2f}"
            )
            return total_paid

        current_total_paid = refresh_payment_history()

        # ── Registrar novo pagamento ──
        layout.addWidget(QLabel("<b>Record New Payment</b>"))
        new_payment_row1 = QHBoxLayout()
        new_payment_row1.addWidget(QLabel("Date:"))
        date_paid = QDateEdit()
        date_paid.setCalendarPopup(True)
        date_paid.setDisplayFormat("MM/dd/yyyy")
        date_paid.setDate(QDate.currentDate())
        new_payment_row1.addWidget(date_paid)
        new_payment_row1.addWidget(QLabel("Amount ($):"))
        spin_new_amount = QDoubleSpinBox()
        spin_new_amount.setMaximum(999999.99)
        spin_new_amount.setDecimals(2)
        spin_new_amount.setPrefix("$ ")
        new_payment_row1.addWidget(spin_new_amount)
        layout.addLayout(new_payment_row1)

        new_payment_row2 = QHBoxLayout()
        new_payment_row2.addWidget(QLabel("Method:"))
        cmb_method = QComboBox()
        cmb_method.addItems(company_settings.COMPANY_PAYMENT_METHODS + ["Other"])
        new_payment_row2.addWidget(cmb_method)
        layout.addLayout(new_payment_row2)

        layout.addWidget(QLabel("Note (optional):"))
        txt_payment_note = QLineEdit()
        layout.addWidget(txt_payment_note)

        btn_add_payment = QPushButton("+  Add Payment")
        btn_add_payment.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add_payment.setAutoDefault(False)
        layout.addWidget(btn_add_payment)

        layout.addWidget(QLabel(""))

        # ── Status manual / nota de ajuste (para casos excepcionais, ex: perdão de dívida) ──
        status_row = QHBoxLayout()
        status_row.addWidget(QLabel("Payment Status:"))
        cmb_status = QComboBox()
        for db_value in ["PENDING", "PARTIAL", "RECEIVED"]:
            cmb_status.addItem(PAYMENT_STATUS_LABELS[db_value], db_value)
        cmb_status.setCurrentIndex(cmb_status.findData(status))
        status_row.addWidget(cmb_status)
        layout.addLayout(status_row)

        layout.addWidget(QLabel("Adjustment note (optional):"))
        txt_note = QLineEdit()
        txt_note.setText(adjustment_note or "")
        layout.addWidget(txt_note)

        bottom_row = QHBoxLayout()
        btn_view_pdf = QPushButton("Open PDF")
        btn_view_pdf.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_view_pdf.setAutoDefault(False)
        btn_view_pdf.setDefault(False)
        bottom_row.addWidget(btn_view_pdf)
        btn_export_excel_detail = QPushButton("⤓  Excel")
        btn_export_excel_detail.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_export_excel_detail.setAutoDefault(False)
        btn_export_excel_detail.setDefault(False)
        bottom_row.addWidget(btn_export_excel_detail)
        btn_export_pdf_detail = QPushButton("⤓  PDF")
        btn_export_pdf_detail.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_export_pdf_detail.setAutoDefault(False)
        btn_export_pdf_detail.setDefault(False)
        bottom_row.addWidget(btn_export_pdf_detail)
        btn_delete_invoice = QPushButton("Delete Invoice")
        btn_delete_invoice.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_delete_invoice.setAutoDefault(False)
        btn_delete_invoice.setDefault(False)
        btn_delete_invoice.setStyleSheet(
            "QPushButton { background-color: #C62828; color: #FFFFFF; border: none; "
            "border-radius: 6px; padding: 8px 14px; font-weight: 600; } "
            "QPushButton:hover { background-color: #E53935; }"
        )
        bottom_row.addWidget(btn_delete_invoice)
        bottom_row.addStretch()
        btn_cancel = QPushButton("Close")
        btn_cancel.setAutoDefault(False)
        btn_save = QPushButton("Save")
        btn_save.setObjectName("btn_save_job")
        btn_save.setAutoDefault(False)
        bottom_row.addWidget(btn_cancel)
        bottom_row.addWidget(btn_save)
        layout.addLayout(bottom_row)

        def export_detail_excel():
            path, _ = QFileDialog.getSaveFileName(
                dialog, "Export Invoice to Excel", f"Invoice_{invoice_id}.xlsx", "Excel Files (*.xlsx)"
            )
            if not path:
                return
            if not path.lower().endswith(".xlsx"):
                path += ".xlsx"
            try:
                import openpyxl
                from openpyxl.styles import Font, PatternFill, Alignment
            except ImportError:
                QMessageBox.critical(dialog, "Missing Dependency",
                                      "The 'openpyxl' package is not installed.\n\nRun:\npip install openpyxl")
                return

            try:
                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = "Invoice"
                summary_rows = [
                    ("Invoice #", invoice_id),
                    (f"{entity_type}", entity_name),
                    ("Period", f"{period_from.strftime('%m/%d/%Y')} to {period_to.strftime('%m/%d/%Y')}"),
                    ("Jobs", f"${float(jobs_total):,.2f}"),
                ]
                if has_expenses:
                    summary_rows.append(("Expenses", f"${float(expenses_total):,.2f}"))
                summary_rows.append(("Total Due", f"${float(total_amount):,.2f}"))
                total_paid_now = sum(
                    float(table_payments.item(r, 1).text().replace("$", "").replace(",", ""))
                    for r in range(table_payments.rowCount())
                )
                summary_rows.append(("Total Paid", f"${total_paid_now:,.2f}"))
                summary_rows.append(("Balance Due", f"${float(total_amount) - total_paid_now:,.2f}"))
                for row_vals in summary_rows:
                    ws.append(row_vals)
                ws.column_dimensions["A"].width = 18
                ws.column_dimensions["B"].width = 32
                for cell in ws["A"]:
                    cell.font = Font(bold=True)

                ws.append([])
                header_row_idx = ws.max_row + 1
                ws.append(["Date", "Amount", "Method", "Note"])
                header_font = Font(bold=True, color="FFFFFF")
                header_fill = PatternFill(start_color="1C2B3A", end_color="1C2B3A", fill_type="solid")
                for c in range(1, 5):
                    cell = ws.cell(row=header_row_idx, column=c)
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = Alignment(horizontal="center")
                for r in range(table_payments.rowCount()):
                    ws.append([table_payments.item(r, c).text() for c in range(4)])

                wb.save(path)
                QMessageBox.information(dialog, "Export Complete", f"Saved to:\n{path}")
            except Exception as e:
                QMessageBox.critical(dialog, "Export Error", f"Could not export to Excel:\n{e}")

        def export_detail_pdf():
            if not REPORTLAB_AVAILABLE:
                QMessageBox.critical(dialog, "Missing Dependency",
                                      "The 'reportlab' package is not installed.\n\nRun:\npip install reportlab")
                return
            path, _ = QFileDialog.getSaveFileName(
                dialog, "Export Invoice to PDF", f"Invoice_{invoice_id}.pdf", "PDF Files (*.pdf)"
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
                    Paragraph(f"<b>Invoice #{invoice_id} — {entity_name}</b>", styles["Title"]),
                    Spacer(1, 10),
                    Paragraph(f"<b>{entity_type}:</b> {entity_name}", styles["Normal"]),
                    Paragraph(
                        f"<b>Period:</b> {period_from.strftime('%m/%d/%Y')} to {period_to.strftime('%m/%d/%Y')}",
                        styles["Normal"],
                    ),
                    Paragraph(f"<b>Jobs:</b> ${float(jobs_total):,.2f}", styles["Normal"]),
                ]
                if has_expenses:
                    story.append(Paragraph(f"<b>Expenses:</b> ${float(expenses_total):,.2f}", styles["Normal"]))
                story.append(Paragraph(f"<b>Total Due:</b> ${float(total_amount):,.2f}", styles["Normal"]))
                total_paid_now = sum(
                    float(table_payments.item(r, 1).text().replace("$", "").replace(",", ""))
                    for r in range(table_payments.rowCount())
                )
                story.append(Paragraph(f"<b>Total Paid:</b> ${total_paid_now:,.2f}", styles["Normal"]))
                story.append(Paragraph(
                    f"<b>Balance Due:</b> ${float(total_amount) - total_paid_now:,.2f}", styles["Normal"]
                ))
                story.append(Spacer(1, 16))
                story.append(Paragraph("<b>Payment History</b>", styles["Heading3"]))

                payments_data = [["Date", "Amount", "Method", "Note"]]
                for r in range(table_payments.rowCount()):
                    payments_data.append([table_payments.item(r, c).text() for c in range(4)])
                payments_table_pdf = Table(
                    payments_data,
                    colWidths=[1.2 * inch, 1.2 * inch, 1.2 * inch, 2.4 * inch],
                    repeatRows=1,
                )
                payments_table_pdf.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(BRAND_NAVY)),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DDDDDD")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F9FC")]),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]))
                story.append(payments_table_pdf)

                doc.build(story)
                QMessageBox.information(dialog, "Export Complete", f"Saved to:\n{path}")
            except Exception as e:
                QMessageBox.critical(dialog, "Export Error", f"Could not export to PDF:\n{e}")

        def _status_for_paid_amount(paid_amount):
            """Deriva o status automaticamente a partir do quanto já foi pago."""
            if paid_amount <= 0:
                return "PENDING"
            if paid_amount >= float(total_amount):
                return "RECEIVED"
            return "PARTIAL"

        def add_payment():
            """Registra um novo pagamento (quem já sabemos pelo invoice; quando,
            quanto e como vêm do formulário) e atualiza o total pago / status
            do invoice automaticamente a partir da soma real dos pagamentos."""
            amount = spin_new_amount.value()
            if amount <= 0:
                QMessageBox.warning(dialog, "Invalid amount", "Enter a payment amount greater than zero.")
                return

            paid_date_str = date_paid.date().toString("yyyy-MM-dd")
            method = cmb_method.currentText()
            note = txt_payment_note.text().strip() or None

            try:
                conn3 = self._get_connection()
                cur3 = conn3.cursor()
                cur3.execute(
                    """
                    INSERT INTO payments (INVOICE_TYPE, INVOICE_ID, PAID_DATE, AMOUNT, PAYMENT_METHOD, NOTE)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (entity_type, invoice_id, paid_date_str, amount, method, note),
                )
                cur3.execute(
                    "SELECT COALESCE(SUM(AMOUNT), 0) FROM payments WHERE INVOICE_TYPE = %s AND INVOICE_ID = %s",
                    (entity_type, invoice_id),
                )
                new_total_paid = float(cur3.fetchone()[0] or 0)
                new_status = _status_for_paid_amount(new_total_paid)
                received_at_clause = ", RECEIVED_AT = NOW()" if new_status == "RECEIVED" else ""
                cur3.execute(
                    f"UPDATE {table_name} SET AMOUNT_PAID = %s, STATUS = %s {received_at_clause} WHERE ID = %s",
                    (new_total_paid, new_status, invoice_id),
                )
                conn3.commit()
                cur3.close()
                conn3.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not record payment:\n{e}")
                return

            spin_new_amount.setValue(0)
            txt_payment_note.clear()
            refresh_payment_history()
            cmb_status.setCurrentIndex(cmb_status.findData(new_status))
            self.load_contractor_invoices()
            self.load_receivables_dashboard()
            if hasattr(self, "offer_payment_receipt"):
                self.offer_payment_receipt(dialog, entity_type, invoice_id, amount, paid_date_str, method)

        def open_pdf():
            """Abre o PDF salvo da invoice no visualizador padrao do sistema, se o arquivo ainda existir no caminho salvo."""
            if pdf_path and os.path.exists(pdf_path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(pdf_path))
            else:
                QMessageBox.information(dialog, "File Not Found",
                                         "The PDF file could not be found at its saved location.")

        def save_changes():
            """Atualiza status (override manual) e nota de ajuste da invoice no banco
            de dados (na tabela certa, conforme o tipo). O valor pago em si é
            controlado pelo histórico de pagamentos, não por aqui."""
            new_status = cmb_status.currentData()
            new_note = txt_note.text().strip() or None
            received_at_clause = ", RECEIVED_AT = NOW()" if new_status == "RECEIVED" else ""
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    f"UPDATE {table_name} "
                    f"SET STATUS = %s, ADJUSTMENT_NOTE = %s {received_at_clause} "
                    f"WHERE ID = %s",
                    (new_status, new_note, invoice_id),
                )
                conn.commit()
                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not update invoice:\n{e}")
                return

            self.load_contractor_invoices()
            self.load_receivables_dashboard()
            dialog.accept()

        def delete_invoice():
            """Apaga o invoice (e o histórico de pagamentos ligado a ele) —
            usado quando um invoice foi gerado errado. Não apaga o arquivo
            PDF do disco, só o registro no sistema."""
            current_total_paid_now = sum(
                float(table_payments.item(r, 1).text().replace("$", "").replace(",", ""))
                for r in range(table_payments.rowCount())
            )
            has_payments = current_total_paid_now > 0
            warning_extra = (
                "\n\nThis invoice already has payment(s) recorded — those payment "
                "records will be deleted too."
                if has_payments else ""
            )
            confirm = QMessageBox.question(
                dialog, "Delete Invoice",
                f"Are you sure you want to delete Invoice #{invoice_id} ({entity_name})?"
                f"{warning_extra}\n\nThe PDF file itself will stay on disk, only the "
                f"record in the system will be removed. This cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return

            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM payments WHERE INVOICE_TYPE = %s AND INVOICE_ID = %s",
                    (entity_type, invoice_id),
                )
                cursor.execute(f"DELETE FROM {table_name} WHERE ID = %s", (invoice_id,))
                try:
                    cursor.execute("DELETE FROM invoice_work_days WHERE INVOICE_TYPE = %s AND INVOICE_ID = %s",
                                   (entity_type, invoice_id))
                except MySQLError:
                    pass
                conn.commit()
                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not delete invoice:\n{e}")
                return

            QMessageBox.information(dialog, "Deleted", f"Invoice #{invoice_id} has been deleted.")
            self.load_contractor_invoices()
            self.load_receivables_dashboard()
            dialog.accept()

        btn_add_payment.clicked.connect(add_payment)
        btn_view_pdf.clicked.connect(open_pdf)
        btn_export_excel_detail.clicked.connect(export_detail_excel)
        btn_export_pdf_detail.clicked.connect(export_detail_pdf)
        btn_delete_invoice.clicked.connect(delete_invoice)
        btn_cancel.clicked.connect(dialog.reject)
        btn_save.clicked.connect(save_changes)
        dialog.exec()
