# -*- coding: utf-8 -*-
"""
Tela Settings: carrega/salva os dados da empresa e do SMTP (app_settings) e troca o logo.

Métodos da MainWindow (mixin) — veja main_.py.
"""

import json

from PySide6.QtCore import QSettings

from app_common import *  # noqa: F401,F403
import arquivos


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
        if data.get("PAYMENT_DETAILS"):
            try:
                company_settings.COMPANY_PAYMENT_DETAILS = dict(json.loads(data["PAYMENT_DETAILS"]))
            except (ValueError, TypeError):
                pass
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

        details = company_settings.COMPANY_PAYMENT_DETAILS
        for label, (chk, txt) in self._settings_payment_widgets().items():
            chk.setChecked(label in company_settings.COMPANY_PAYMENT_METHODS)
            if txt is not None:
                txt.setText(details.get(label, ""))

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

        pm_widgets = self._settings_payment_widgets()
        selected_methods = [label for label, (chk, _txt) in pm_widgets.items() if chk.isChecked()]
        payment_details = {label: txt.text().strip() for label, (_chk, txt) in pm_widgets.items()
                           if txt is not None and txt.text().strip()}

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
            "PAYMENT_DETAILS": json.dumps(payment_details, ensure_ascii=False),
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
                    PAYMENT_DETAILS, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM_NAME)
                VALUES (1, %(COMPANY_NAME)s, %(COMPANY_TAGLINE)s, %(COMPANY_PHONE)s, %(COMPANY_EMAIL)s,
                    %(COMPANY_WEBSITE)s, %(BANK_ACCOUNT_NO)s, %(BANK_ACCOUNT_NAME)s, %(BANK_DETAILS)s,
                    %(PAYMENT_METHODS)s, %(PAYMENT_DETAILS)s, %(SMTP_HOST)s, %(SMTP_PORT)s, %(SMTP_USER)s,
                    %(SMTP_PASSWORD)s, %(SMTP_FROM_NAME)s)
                ON DUPLICATE KEY UPDATE
                    COMPANY_NAME=VALUES(COMPANY_NAME), COMPANY_TAGLINE=VALUES(COMPANY_TAGLINE),
                    COMPANY_PHONE=VALUES(COMPANY_PHONE), COMPANY_EMAIL=VALUES(COMPANY_EMAIL),
                    COMPANY_WEBSITE=VALUES(COMPANY_WEBSITE), BANK_ACCOUNT_NO=VALUES(BANK_ACCOUNT_NO),
                    BANK_ACCOUNT_NAME=VALUES(BANK_ACCOUNT_NAME), BANK_DETAILS=VALUES(BANK_DETAILS),
                    PAYMENT_METHODS=VALUES(PAYMENT_METHODS), PAYMENT_DETAILS=VALUES(PAYMENT_DETAILS),
                    SMTP_HOST=VALUES(SMTP_HOST),
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
        company_settings.COMPANY_PAYMENT_DETAILS = payment_details
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
        self.ui.btn_open_restore_backup = btn

    # ── formas de pagamento com detalhe ───────────────────────────────
    # (nome salvo, nome do checkbox no .ui ou None = criado aqui, dica do campo;
    #  dica None = sem campo de detalhe)
    _PAYMENT_METHOD_ROWS = [
        ("Zelle", "chk_settings_pm_zelle", "Phone or e-mail registered in Zelle"),
        ("Venmo", None, "@username"),
        ("Cash App", None, "$cashtag"),
        ("PayPal", None, "PayPal e-mail or paypal.me link"),
        ("Check", "chk_settings_pm_check", "Payable to (e.g. Vertex Londe Flooring LLC)"),
        ("Cash", "chk_settings_pm_cash", "Optional note"),
        ("Bank Transfer", "chk_settings_pm_bank_transfer", None),
        ("Credit Card", "chk_settings_pm_credit_card", "Payment link or note (e.g. 3% card fee)"),
    ]

    def _settings_payment_widgets(self):
        """{forma: (checkbox, campo de detalhe ou None)} na ordem da tela."""
        if not hasattr(self, "_pm_widgets"):
            self._setup_payment_method_rows()
        return self._pm_widgets

    def _setup_payment_method_rows(self):
        """Troca a fileira de checkboxes de 'Accepted Payment Methods' por uma
        lista: cada forma com o seu detalhe ao lado (Zelle → telefone, Venmo →
        @usuário…). O detalhe sai na invoice junto do nome. Venmo, Cash App e
        PayPal são criados aqui; os outros checkboxes vêm do .ui."""
        ui = self.ui
        grp = ui.grp_settings_payment_methods
        hbox = ui.layout_settings_payment_methods
        while hbox.count():
            item = hbox.takeAt(0)
            if item.widget() is not None:
                item.widget().setParent(None)

        holder = QWidget(grp)
        grid = QGridLayout(holder)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(8)
        grid.setColumnMinimumWidth(0, 150)
        grid.setColumnStretch(1, 1)

        self._pm_widgets = {}
        for row, (label, chk_name, hint) in enumerate(self._PAYMENT_METHOD_ROWS):
            chk = getattr(ui, chk_name) if chk_name else QCheckBox()
            if not chk_name:
                attr = "chk_settings_pm_" + label.lower().replace(" ", "_")
                chk.setObjectName(attr)
                setattr(ui, attr, chk)
            chk.setText(label)
            chk.setParent(holder)
            grid.addWidget(chk, row, 0)
            if hint is None:
                lbl = QLabel("Uses the Bank Information above")
                lbl.setStyleSheet("color:#6B7C93;")
                grid.addWidget(lbl, row, 1)
                txt = None
            else:
                txt = QLineEdit(holder)
                txt.setObjectName("txt_settings_pm_" + label.lower().replace(" ", "_"))
                txt.setPlaceholderText(hint)
                txt.setMaximumWidth(520)
                txt.setEnabled(chk.isChecked())
                chk.toggled.connect(txt.setEnabled)
                grid.addWidget(txt, row, 1)
            self._pm_widgets[label] = (chk, txt)
        hbox.addWidget(holder, 1)

    # ── preview do bloco de pagamento da invoice ──────────────────────
    def _build_invoice_payment_preview(self):
        """Cartão 'Invoice preview' ao lado dos campos da aba Invoices: mostra,
        enquanto você digita, como o bloco Payment Info / Accepted Methods vai
        sair na invoice — com os valores da tela, mesmo antes de salvar.
        Usa a mesma função que monta o PDF (_invoice_payment_info_lines)."""
        ui = self.ui
        box = QGroupBox("Invoice preview")
        box.setObjectName("grp_settings_invoice_preview")
        box.setMinimumWidth(260)
        box.setMaximumWidth(380)
        v = QVBoxLayout(box)
        v.setContentsMargins(12, 20, 12, 12)

        card = QLabel()
        card.setObjectName("lbl_settings_invoice_preview")
        card.setTextFormat(Qt.TextFormat.RichText)
        card.setWordWrap(True)
        card.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        card.setMinimumHeight(160)
        card.setStyleSheet("QLabel { background-color: #FFFFFF; color: #1C2B3A; border: 1px solid #D0D7DE; "
                           "border-radius: 6px; padding: 14px; font-size: 12px; }")
        v.addWidget(card)

        hint = QLabel("Updates as you type. Click <b>Save Settings</b> to use it on new invoices.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#6B7C93;")
        v.addWidget(hint)
        ui.lbl_settings_invoice_preview = card

        def refresh(*_args):
            pm = self._settings_payment_widgets()
            info = {"account_no": ui.txt_settings_bank_account_no.text().strip(),
                    "account_name": ui.txt_settings_bank_account_name.text().strip(),
                    "bank_details": ui.txt_settings_bank_details.text().strip()}
            methods = [m for m, (chk, _t) in pm.items() if chk.isChecked()]
            details = {m: t.text().strip() for m, (_c, t) in pm.items() if t is not None}
            lines = self._invoice_payment_info_lines(info, methods, details)
            if not methods:
                lines.append("<i style='color:#C62828'>No payment method selected</i>")
            card.setText("<br/>".join(lines))

        for txt in (ui.txt_settings_bank_account_no, ui.txt_settings_bank_account_name,
                    ui.txt_settings_bank_details):
            txt.textChanged.connect(refresh)
        for chk, txt in self._settings_payment_widgets().values():
            chk.toggled.connect(refresh)
            if txt is not None:
                txt.textChanged.connect(refresh)
        self._refresh_invoice_payment_preview = refresh
        refresh()
        return box

    # ── abas da tela Settings ─────────────────────────────────────────
    def _setup_settings_tabs(self):
        """Reorganiza a tela Settings (que no .ui é uma coluna só) em abas:
        Company · Invoices · Email · System. Só move os widgets que já
        existem — os nomes (txt_settings_*, chk_settings_*) e o que é salvo
        em app_settings continuam iguais. O botão Save fica abaixo das abas
        e salva tudo de uma vez; some na aba System, que não tem campos."""
        ui = self.ui
        layout = ui.layout_settings_contents
        restore_btn = getattr(ui, "btn_open_restore_backup", None)
        self._settings_payment_widgets()

        moved = [ui.grp_settings_company, ui.grp_settings_logo, ui.grp_settings_bank,
                 ui.grp_settings_payment_methods, ui.grp_settings_email, ui.btn_settings_save]
        if restore_btn is not None:
            moved.append(restore_btn)
        for w in moved:
            layout.removeWidget(w)

        ui.grp_settings_bank.setTitle("Bank Information")
        ui.grp_settings_payment_methods.setTitle("Accepted Payment Methods")
        ui.grp_settings_email.setTitle("Email Account")

        def note(text):
            lbl = QLabel(text)
            lbl.setWordWrap(True)
            lbl.setStyleSheet("color:#6B7C93; padding: 2px 4px;")
            return lbl

        def make_tab(widgets):
            page = QWidget()
            v = QVBoxLayout(page)
            v.setContentsMargins(4, 12, 4, 4)
            v.setSpacing(12)
            for w in widgets:
                v.addWidget(w)
            v.addStretch(1)
            return page

        tabs = QTabWidget(ui.scroll_settings_page_contents)
        tabs.setObjectName("tabs_settings")
        tabs.setDocumentMode(True)
        tabs.addTab(make_tab([ui.grp_settings_company, ui.grp_settings_logo]), "Company")
        invoices_left = make_tab([
            ui.grp_settings_bank,
            note("Shown in the <b>Payment Info</b> block of every invoice. While these are still the "
                 "example values (123456789 / Routing 000000000), invoices leave the bank block out "
                 "and don't list Bank Transfer — it comes back by itself once the real details are saved."),
            ui.grp_settings_payment_methods,
        ])
        invoices_page = QWidget()
        h = QHBoxLayout(invoices_page)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(16)
        h.addWidget(invoices_left, 1)
        h.addWidget(self._build_invoice_payment_preview(), 0, Qt.AlignmentFlag.AlignTop)
        tabs.addTab(invoices_page, "Invoices")
        tabs.addTab(make_tab([
            ui.grp_settings_email,
            note("This account <b>sends</b> invoices and other e-mails from the app, and is also the inbox "
                 "the app <b>reads</b>: send receipts to it with 'recibo' or 'receipt' in the subject "
                 "(Registrations → Receipt Inbox) and job addresses with 'endereço' or 'obra' "
                 "(Registrations → Job Site Inbox)."),
        ]), "Email")
        system_widgets = [self._files_folder_box()]
        if hasattr(self, "_daily_summary_card"):
            system_widgets.append(self._daily_summary_card())
        if restore_btn is not None:
            restore_btn.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
            system_widgets.append(self._settings_card(
                "Database backup",
                "Bring the database back to how it was on an earlier day. "
                "A backup of the current data is made first, so it can be undone.",
                [], [restore_btn]))
        tabs.addTab(make_tab(system_widgets), "System")
        ui.tabs_settings = tabs

        layout.insertWidget(0, tabs)
        layout.insertWidget(1, ui.btn_settings_save)
        layout.addStretch(1)

        system_index = tabs.count() - 1
        tabs.currentChanged.connect(lambda i: ui.btn_settings_save.setVisible(i != system_index))

    # ── pasta de arquivos (invoices, fotos, recibos…) ─────────────────
    def _settings_card(self, title, description, body_widgets, buttons):
        """Cartão da aba System: título, explicação, conteúdo e botões numa linha."""
        card = QFrame()
        card.setObjectName("settings_card")
        card.setStyleSheet("QFrame#settings_card { border: 1px solid rgba(127,127,127,0.30); border-radius: 8px; }")
        v = QVBoxLayout(card)
        v.setContentsMargins(18, 14, 18, 16)
        v.setSpacing(8)
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 15px; font-weight: 600; border: none;")
        v.addWidget(lbl_title)
        lbl_desc = QLabel(description)
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("color:#8A9AB0; border: none;")
        v.addWidget(lbl_desc)
        for w in body_widgets:
            v.addWidget(w)
        if buttons:
            row = QHBoxLayout()
            row.setSpacing(8)
            row.setContentsMargins(0, 6, 0, 0)
            for b in buttons:
                row.addWidget(b)
            row.addStretch(1)
            v.addLayout(row)
        return card

    def _files_folder_box(self):
        from paginas.visual import tabler_icon
        self._txt_files_root = QLineEdit()
        self._txt_files_root.setReadOnly(True)
        self._txt_files_root.setMinimumHeight(34)
        self._lbl_files_status = QLabel()
        self._lbl_files_status.setWordWrap(True)
        self._lbl_files_status.setStyleSheet("border: none;")
        btn_open = QPushButton("  Open files folder")
        btn_open.setIcon(tabler_icon("folder-open", "#4FA3FF", 16))
        btn_change = QPushButton("  Change location…")
        btn_change.setIcon(tabler_icon("pencil", "#8A9AB0", 16))
        btn_move = QPushButton("  Move old files here")
        btn_move.setIcon(tabler_icon("arrows-exchange", "#8A9AB0", 16))
        btn_open.clicked.connect(self.open_files_folder)
        btn_change.clicked.connect(self.change_files_folder)
        btn_move.clicked.connect(lambda: self.move_old_files(ask=True))
        subs = ", ".join(arquivos.SUBFOLDERS.values())
        card = self._settings_card(
            "Files folder",
            "Invoices and estimates are saved here automatically, together with job photos and receipts. "
            f"Subfolders: {subs}.",
            [self._txt_files_root, self._lbl_files_status], [btn_open, btn_change, btn_move])
        self._refresh_files_folder_label()
        return card

    def _refresh_files_folder_label(self):
        txt = getattr(self, "_txt_files_root", None)
        if txt is None:
            return
        root = arquivos.files_root()
        txt.setText(root)
        if arquivos.using_google_drive(root):
            status = "<span style='color:#43A047'>✔ Inside Google Drive — saved in the cloud.</span>"
        else:
            status = ("<span style='color:#F57C00'>⚠ Not backed up yet.</span> "
                      "<span style='color:#8A9AB0'>In Google Drive for desktop: Preferences → "
                      "<b>Folders from my computer</b> → Add folder → choose this folder.</span>")
        self._lbl_files_status.setText(status)

    def open_files_folder(self):
        root = arquivos.ensure_structure()
        QDesktopServices.openUrl(QUrl.fromLocalFile(root))

    def change_files_folder(self):
        start = arquivos.find_google_drive() or arquivos.files_root()
        chosen = QFileDialog.getExistingDirectory(self, "Choose where the VL Flooring files go", start)
        if not chosen:
            return
        chosen = os.path.normpath(chosen)
        if os.path.basename(chosen) != arquivos.ROOT_NAME:
            chosen = os.path.join(chosen, arquivos.ROOT_NAME)
        old = arquivos.files_root()
        arquivos.set_root(chosen)
        arquivos.ensure_structure(chosen)
        self._refresh_files_folder_label()
        if os.path.normcase(old) != os.path.normcase(chosen):
            self.move_old_files(ask=True, old_root=old)
        QMessageBox.information(self, "Files folder",
                                f"New files will be saved in:\n{chosen}\n\n"
                                "Restart the app so every screen uses the new folder.")

    def move_old_files(self, ask=True, old_root=None):
        n = arquivos.pending_moves()
        extra = old_root and os.path.isdir(old_root)
        if not n and not extra:
            if ask:
                QMessageBox.information(self, "Files folder", "Nothing to move — all files are already here.")
            return
        if ask:
            answer = QMessageBox.question(
                self, "Move files",
                f"Move the existing photos, receipts and PDFs into\n{arquivos.files_root()}?\n\n"
                "The jobs, invoices and expenses keep pointing to them.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes)
            if answer != QMessageBox.StandardButton.Yes:
                return
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            conn = self._get_connection()
            try:
                files, rows = arquivos.move_everything(conn, old_root=old_root)
            finally:
                conn.close()
        except Exception as e:
            QApplication.restoreOverrideCursor()
            logging.getLogger("vl_flooring").exception("move files failed")
            QMessageBox.critical(self, "Move files", f"Could not move the files:\n{e}")
            return
        QApplication.restoreOverrideCursor()
        from paginas.moderno import show_toast
        show_toast(f"{files} file(s) moved to the files folder ({rows} record(s) updated).", "success", self)

    def _check_files_folder_on_start(self):
        """Ao abrir: cria as subpastas e, se ainda há arquivos nas pastas
        antigas (job_photos, receipts_received, D:\\VL_Flooring\\Files…),
        oferece mover (uma vez por dia)."""
        try:
            arquivos.ensure_structure()
        except OSError as e:
            logging.getLogger("vl_flooring").warning("could not create files folder: %s", e)
            return
        if not arquivos.pending_moves():
            return
        settings = QSettings("VL Flooring", "app")
        today = date.today().isoformat()
        if settings.value("files/move_asked") == today:
            return
        settings.setValue("files/move_asked", today)
        QTimer.singleShot(1500, lambda: self.move_old_files(ask=True))

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
