# -*- coding: utf-8 -*-
"""
Receipt Inbox (recibo por e-mail vira Expense) e Job Site Inbox
(endereço por e-mail vira Job).

Métodos da MainWindow (mixin) — veja main_.py.
"""

from app_common import *  # noqa: F401,F403
import arquivos


class InboxMixin:
    def _setup_receipt_inbox_feature(self):
        """Cria, em tempo de execução, o botão 'Receipt Inbox' no submenu
        de Registrations."""
        self.ui.btn_reg_receipt_inbox = QPushButton(self.ui.frame_registrations_submenu)
        self.ui.btn_reg_receipt_inbox.setObjectName(u"btn_reg_receipt_inbox")
        self.ui.btn_reg_receipt_inbox.setCheckable(False)
        self.ui.btn_reg_receipt_inbox.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ui.layout_registrations_submenu.addWidget(self.ui.btn_reg_receipt_inbox)

    def _setup_job_site_inbox_feature(self):
        """Cria, em tempo de execução, o botão 'Job Site Inbox' no submenu
        de Registrations — mesmo padrão do Receipt Inbox (nenhum widget
        novo no .ui, só um QPushButton criado em runtime)."""
        self.ui.btn_reg_job_site_inbox = QPushButton(self.ui.frame_registrations_submenu)
        self.ui.btn_reg_job_site_inbox.setObjectName(u"btn_reg_job_site_inbox")
        self.ui.btn_reg_job_site_inbox.setCheckable(False)
        self.ui.btn_reg_job_site_inbox.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ui.layout_registrations_submenu.addWidget(self.ui.btn_reg_job_site_inbox)

    def open_receipt_inbox_dialog(self):
        """'Email to Expense': tire foto do recibo no celular (de qualquer
        lugar, sem precisar estar na rede do escritório) e mande por e-mail
        pra própria conta configurada em Settings, com 'receipt' ou
        'recibo' em algum lugar do assunto. Aqui você clica 'Check Inbox'
        pra ver os recibos novos e transformar cada um numa despesa em
        2 cliques — o anexo já vem preenchido no campo de recibo."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Receipt Inbox — Email to Expense")
        dialog.resize(780, 540)
        dialog.setStyleSheet("""
            QTableWidget { background-color: #FFFFFF; color: #1C2B3A; gridline-color: #E3E8EE; }
            QHeaderView::section { background-color: #F0F4F8; color: #1C2B3A; padding: 6px; border: none; font-weight: 600; }
        """)
        layout = QVBoxLayout(dialog)
        lbl_intro = QLabel(
            f"<b>Receipt Inbox</b> — send a photo of a receipt by email to "
            f"<b>{company_settings.EMAIL_SMTP_USER}</b> (same account configured in Settings) with the word "
            f"'<b>receipt</b>' or '<b>recibo</b>' somewhere in the subject line. Works from anywhere "
            f"you have cell signal — you only need to be on your network when you open this app to check."
        )
        # Sem isso, o QLabel tenta caber tudo numa linha só e força a janela
        # inteira a ficar larga demais (e impossível de encolher depois).
        lbl_intro.setWordWrap(True)
        layout.addWidget(lbl_intro)

        btn_check = QPushButton("🔄  Check Inbox")
        btn_check.setStyleSheet(
            "QPushButton { background-color: #1565C0; color: #FFFFFF; border: none; "
            "border-radius: 6px; padding: 8px 14px; font-weight: 600; } "
            "QPushButton:hover { background-color: #1E88E5; }"
        )
        layout.addWidget(btn_check)

        lbl_status = QLabel("")
        lbl_status.setStyleSheet("color:#6B7C93; font-style:italic;")
        layout.addWidget(lbl_status)

        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Date", "From", "Subject", "Attachment"])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(table, 1)

        found_emails = {}

        def imap_connect():
            import imaplib
            imap = imaplib.IMAP4_SSL("imap.gmail.com", 993)
            imap.login(company_settings.EMAIL_SMTP_USER, company_settings.EMAIL_SMTP_PASSWORD)
            imap.select("INBOX")
            return imap

        def check_inbox():
            if not company_settings.EMAIL_SMTP_USER or company_settings.EMAIL_SMTP_USER == "your-email@gmail.com":
                QMessageBox.warning(
                    dialog, "Email Not Configured",
                    "Configure your Gmail account in Settings first (same one used to send invoices).",
                )
                return
            table.setRowCount(0)
            found_emails.clear()
            lbl_status.setText("Connecting…")
            QApplication.processEvents()
            try:
                import email as email_module
                from email.header import decode_header

                imap = imap_connect()
                status, uid_data = imap.uid("search", None, "UNSEEN")
                if status != "OK":
                    raise RuntimeError("IMAP search failed")
                uid_list = uid_data[0].split()

                candidates = []
                for uid in uid_list:
                    status, msg_data = imap.uid("fetch", uid, "(RFC822)")
                    if status != "OK" or not msg_data or not msg_data[0]:
                        continue
                    msg = email_module.message_from_bytes(msg_data[0][1])
                    subject_raw = msg.get("Subject", "") or ""
                    decoded_parts = decode_header(subject_raw)
                    subject = "".join(
                        (part.decode(enc or "utf-8", errors="ignore") if isinstance(part, bytes) else part)
                        for part, enc in decoded_parts
                    )
                    if "receipt" not in subject.lower() and "recibo" not in subject.lower():
                        continue

                    attachment_bytes = None
                    attachment_name = None
                    for part in msg.walk():
                        if part.get_content_maintype() == "multipart":
                            continue
                        filename = part.get_filename()
                        if filename and part.get_content_type() in (
                            "image/jpeg", "image/png", "image/heic", "application/pdf",
                        ):
                            attachment_bytes = part.get_payload(decode=True)
                            attachment_name = filename
                            break
                    if not attachment_bytes:
                        continue

                    candidates.append({
                        "uid": uid, "subject": subject,
                        "from": msg.get("From", "") or "", "date": msg.get("Date", "") or "",
                        "attachment_bytes": attachment_bytes, "attachment_name": attachment_name,
                    })
                imap.logout()
            except Exception as e:
                lbl_status.setText("")
                QMessageBox.critical(
                    dialog, "Connection Error",
                    f"Could not check the inbox:\n{e}\n\n"
                    f"Make sure IMAP is enabled on the Gmail account (Gmail Settings → Forwarding and "
                    f"POP/IMAP) and the app password in Settings is correct.",
                )
                return

            table.setRowCount(len(candidates))
            for i, c in enumerate(candidates):
                values = [c["date"][:25], c["from"], c["subject"], c["attachment_name"] or ""]
                for col, text in enumerate(values):
                    item = QTableWidgetItem(text)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    table.setItem(i, col, item)
                found_emails[i] = c

            lbl_status.setText(
                f"{len(candidates)} new receipt email(s) found."
                if candidates else
                "No new receipt emails found (subject must contain 'receipt' or 'recibo', and it must be unread)."
            )

        btn_check.clicked.connect(check_inbox)

        def mark_seen(uid):
            try:
                imap = imap_connect()
                imap.uid("store", uid, "+FLAGS", "\\Seen")
                imap.logout()
            except Exception:
                pass  # não crítico — se falhar, o e-mail só reaparece na próxima checagem

        def create_expense_from_selected():
            r = table.currentRow()
            if r < 0 or r not in found_emails:
                QMessageBox.information(dialog, "No selection", "Select a receipt email first.")
                return
            c = found_emails[r]

            try:
                receipts_dir = arquivos.folder("receipts")
                safe_name = "".join(ch for ch in c["attachment_name"] if ch.isalnum() or ch in "._-") or "receipt"
                uid_str = c["uid"].decode() if isinstance(c["uid"], bytes) else str(c["uid"])
                dest_path = os.path.join(receipts_dir, f"{uid_str}_{safe_name}")
                with open(dest_path, "wb") as f:
                    f.write(c["attachment_bytes"])
            except Exception as e:
                QMessageBox.critical(dialog, "File Error", f"Could not save the attachment:\n{e}")
                return

            mark_seen(c["uid"])

            dialog.accept()
            self._go_to_page(5, self.ui.btn_nav_receivables)
            self.new_expense_record()
            self.ui.txt_expense_description.setText(c["subject"])
            self._current_expense_receipt_path = dest_path
            self.ui.txt_expense_receipt_path.setText(dest_path)
            QMessageBox.information(
                self, "Receipt Loaded",
                "The receipt photo was loaded into a new Expense — fill in the amount, category, "
                "and vendor, then click Save.",
            )

        def dismiss_selected():
            r = table.currentRow()
            if r < 0 or r not in found_emails:
                QMessageBox.information(dialog, "No selection", "Select a receipt email first.")
                return
            c = found_emails[r]
            mark_seen(c["uid"])
            table.removeRow(r)
            found_emails.pop(r, None)

        btn_row = QHBoxLayout()
        btn_create = QPushButton("✔  Create Expense From This")
        btn_create.setStyleSheet(
            "QPushButton { background-color: #2E7D32; color: #FFFFFF; border: none; "
            "border-radius: 6px; padding: 8px 14px; font-weight: 600; } "
            "QPushButton:hover { background-color: #388E3C; }"
        )
        btn_create.clicked.connect(create_expense_from_selected)
        btn_dismiss = QPushButton("Dismiss (mark as read)")
        btn_dismiss.clicked.connect(dismiss_selected)
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(dialog.accept)
        btn_row.addWidget(btn_create)
        btn_row.addWidget(btn_dismiss)
        btn_row.addStretch()
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

        dialog.exec()

    # Modelo opcional de e-mail: se o corpo tiver linhas "ADDRESS:", "CITY:",
    # "STATE:", "ZIP:" (em vez de um texto livre), lê o valor exato de cada
    # campo em vez de adivinhar — mais rápido pra revisar (State/City/Zip já
    # vêm pré-selecionados) e mais confiável. Se o e-mail não seguir o
    # modelo, nada disso é obrigatório: continua caindo no "chute" de sempre.
    _LABELED_ADDRESS_FIELD_PATTERNS = [
        ("address2", re.compile(
            r"^(address\s*line\s*2|address\s*2|addr\s*2|endere[cç]o\s*2|complemento)\s*[:\-]\s*(.*)$",
            re.IGNORECASE,
        )),
        ("address", re.compile(r"^(address|endere[cç]o)\s*[:\-]\s*(.*)$", re.IGNORECASE)),
        ("city", re.compile(r"^(city|cidade)\s*[:\-]\s*(.*)$", re.IGNORECASE)),
        ("state", re.compile(r"^(state|estado)\s*[:\-]\s*(.*)$", re.IGNORECASE)),
        ("zip", re.compile(r"^(zip\s*code|zip|cep)\s*[:\-]\s*(.*)$", re.IGNORECASE)),
    ]

    @classmethod
    def _parse_labeled_address_fields(cls, body_text):
        """Lê campos no formato 'ADDRESS: ...' / 'CITY: ...' / 'STATE: ...' /
        'ZIP: ...' do corpo do e-mail (um por linha, em qualquer ordem).
        Devolve um dict só com o que encontrou — nunca lança erro, e um
        e-mail sem nenhum desses rótulos simplesmente devolve {}."""
        result = {}
        for line in (body_text or "").splitlines():
            line = line.strip()
            if not line:
                continue
            for key, pattern in cls._LABELED_ADDRESS_FIELD_PATTERNS:
                m = pattern.match(line)
                if m:
                    value = m.group(2).strip()
                    if value and key not in result:
                        result[key] = value
                    break
        return result

    def open_job_site_inbox_dialog(self):
        """'Email to Job Address': na obra, manda um e-mail pra própria
        conta configurada em Settings com 'endereço' (ou 'endereco'/'obra'/
        'job site') em algum lugar do assunto, e o endereço digitado no
        assunto ou no corpo. Aqui você clica 'Check Inbox', revisa/edita o
        endereço, escolhe a qual Job ele pertence numa lista (sem precisar
        digitar/lembrar código nenhum no celular) e confirma."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Job Site Inbox — Email to Job Address")
        dialog.resize(820, 540)
        dialog.setStyleSheet("""
            QTableWidget { background-color: #FFFFFF; color: #1C2B3A; gridline-color: #E3E8EE; }
            QHeaderView::section { background-color: #F0F4F8; color: #1C2B3A; padding: 6px; border: none; font-weight: 600; }
        """)
        layout = QVBoxLayout(dialog)
        lbl_intro = QLabel(
            f"<b>Job Site Inbox</b> — from the job site, send an email to "
            f"<b>{company_settings.EMAIL_SMTP_USER}</b> (same account configured in Settings) with "
            f"'<b>endereço</b>', '<b>endereco</b>', '<b>obra</b>' or '<b>job site</b>' somewhere in the "
            f"subject, and the address in the subject or the body. Works from anywhere you have cell "
            f"signal — you only need to be on your network when you open this app to check. Nothing is "
            f"applied automatically: you always review and pick the Job before it's saved.<br><br>"
            f"<b>Tip:</b> save a template with labeled lines in the body (ADDRESS:, ADDRESS2:, CITY:, "
            f"STATE:, ZIP:) and just fill in the blanks each time — when the app finds those labels, "
            f"it reads the exact values and even pre-selects State/City for you in the review screen."
        )
        # Sem isso, o QLabel tenta caber tudo numa linha só e força a
        # janela inteira a ficar larga demais pra caber o texto — impedindo
        # até de encolher a janela depois. Com wrap, o texto quebra linha e
        # a janela acompanha o tamanho normal do resize() acima.
        lbl_intro.setWordWrap(True)
        layout.addWidget(lbl_intro)

        btn_check = QPushButton("🔄  Check Inbox")
        btn_check.setStyleSheet(
            "QPushButton { background-color: #1565C0; color: #FFFFFF; border: none; "
            "border-radius: 6px; padding: 8px 14px; font-weight: 600; } "
            "QPushButton:hover { background-color: #1E88E5; }"
        )
        layout.addWidget(btn_check)

        lbl_status = QLabel("")
        lbl_status.setStyleSheet("color:#6B7C93; font-style:italic;")
        layout.addWidget(lbl_status)

        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Date", "From", "Subject", "Address (guess)"])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(table, 1)

        found_emails = {}
        JOB_SITE_KEYWORDS = ("endereco", "obra", "job site")

        def imap_connect():
            import imaplib
            imap = imaplib.IMAP4_SSL("imap.gmail.com", 993)
            imap.login(company_settings.EMAIL_SMTP_USER, company_settings.EMAIL_SMTP_PASSWORD)
            imap.select("INBOX")
            return imap

        def guess_address(subject, body_text):
            """Tenta separar o endereço do resto do assunto/corpo — só um
            chute inicial pra pré-preencher o campo editável na revisão;
            nunca trava se não conseguir, porque o usuário sempre revisa e
            corrige antes de aplicar."""
            for sep in (":", "-", "–"):
                if sep in subject:
                    after = subject.split(sep, 1)[1].strip()
                    if after:
                        return after
            norm = self._normalize_keyword_text(subject)
            leftover = subject
            for kw in JOB_SITE_KEYWORDS:
                idx = norm.find(kw)
                if idx >= 0:
                    leftover = (subject[:idx] + subject[idx + len(kw):]).strip(" :-–\t")
                    break
            if leftover.strip():
                return leftover.strip()
            for line in (body_text or "").splitlines():
                line = line.strip()
                if line:
                    return line
            return ""

        def check_inbox():
            if not company_settings.EMAIL_SMTP_USER or company_settings.EMAIL_SMTP_USER == "your-email@gmail.com":
                QMessageBox.warning(
                    dialog, "Email Not Configured",
                    "Configure your Gmail account in Settings first (same one used to send invoices).",
                )
                return
            table.setRowCount(0)
            found_emails.clear()
            lbl_status.setText("Connecting…")
            QApplication.processEvents()
            try:
                import email as email_module
                from email.header import decode_header

                imap = imap_connect()
                status, uid_data = imap.uid("search", None, "UNSEEN")
                if status != "OK":
                    raise RuntimeError("IMAP search failed")
                uid_list = uid_data[0].split()

                candidates = []
                for uid in uid_list:
                    status, msg_data = imap.uid("fetch", uid, "(RFC822)")
                    if status != "OK" or not msg_data or not msg_data[0]:
                        continue
                    msg = email_module.message_from_bytes(msg_data[0][1])
                    subject_raw = msg.get("Subject", "") or ""
                    decoded_parts = decode_header(subject_raw)
                    subject = "".join(
                        (part.decode(enc or "utf-8", errors="ignore") if isinstance(part, bytes) else part)
                        for part, enc in decoded_parts
                    )
                    norm_subject = self._normalize_keyword_text(subject)
                    if not any(kw in norm_subject for kw in JOB_SITE_KEYWORDS):
                        continue

                    body_text = ""
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain" and not part.get_filename():
                            try:
                                charset = part.get_content_charset() or "utf-8"
                                body_text = (part.get_payload(decode=True) or b"").decode(charset, errors="ignore")
                            except Exception:
                                body_text = ""
                            break

                    labeled_fields = self._parse_labeled_address_fields(body_text)
                    candidates.append({
                        "uid": uid, "subject": subject,
                        "from": msg.get("From", "") or "", "date": msg.get("Date", "") or "",
                        "address_guess": labeled_fields.get("address") or guess_address(subject, body_text),
                        "labeled": labeled_fields,
                    })
                imap.logout()
            except Exception as e:
                lbl_status.setText("")
                QMessageBox.critical(
                    dialog, "Connection Error",
                    f"Could not check the inbox:\n{e}\n\n"
                    f"Make sure IMAP is enabled on the Gmail account (Gmail Settings → Forwarding and "
                    f"POP/IMAP) and the app password in Settings is correct.",
                )
                return

            table.setRowCount(len(candidates))
            for i, c in enumerate(candidates):
                values = [c["date"][:25], c["from"], c["subject"], c["address_guess"]]
                for col, text in enumerate(values):
                    item = QTableWidgetItem(text)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    table.setItem(i, col, item)
                found_emails[i] = c

            lbl_status.setText(
                f"{len(candidates)} new job site email(s) found."
                if candidates else
                "No new job site emails found (subject must contain 'endereço'/'endereco'/'obra'/"
                "'job site', and it must be unread)."
            )

        btn_check.clicked.connect(check_inbox)

        def mark_seen(uid):
            try:
                imap = imap_connect()
                imap.uid("store", uid, "+FLAGS", "\\Seen")
                imap.logout()
            except Exception:
                pass  # não crítico — se falhar, o e-mail só reaparece na próxima checagem

        def load_recent_jobs():
            """Lista os Jobs ativos (código + cliente + endereço atual),
            mais recentes primeiro, pra escolher na revisão sem precisar
            digitar/lembrar código nenhum."""
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT jp.ID, jp.CODE, COALESCE(cl.FULL_NAME, ''), COALESCE(jp.JOB_ADDRESS, '')
                    FROM job_projects jp
                    LEFT JOIN clients cl ON cl.ID = jp.CLIENT_ID
                    LEFT JOIN (
                        SELECT JOB_PROJECT_ID, MAX(WORK_DATE) AS LAST_DATE
                        FROM work_days GROUP BY JOB_PROJECT_ID
                    ) last_wd ON last_wd.JOB_PROJECT_ID = jp.ID
                    WHERE jp.STATUS = 'ACTIVE'
                    ORDER BY last_wd.LAST_DATE DESC, jp.ID DESC
                    LIMIT 200
                    """
                )
                rows = cursor.fetchall()
                cursor.close()
                conn.close()
                return rows
            except (MySQLError, RuntimeError):
                return []

        def review_and_apply(c):
            """Tela de revisão: endereço editável + escolha do Job numa
            lista + State/City/Zip — só grava alguma coisa depois de
            confirmado aqui (o e-mail nunca aplica nada sozinho)."""
            review = QDialog(dialog)
            review.setWindowTitle("Review Job Site Address")
            review.resize(520, 440)
            rlayout = QVBoxLayout(review)

            lbl_from_email = QLabel(f"<b>From email:</b> {c['subject']}")
            lbl_from_email.setWordWrap(True)
            rlayout.addWidget(lbl_from_email)

            rlayout.addWidget(QLabel("Job:"))
            cmb_job = QComboBox()
            jobs = load_recent_jobs()
            if not jobs:
                cmb_job.addItem("— No active jobs found —", None)
            for job_id, code, client_name, current_address in jobs:
                label = code + (f" — {client_name}" if client_name else "")
                cmb_job.addItem(label, (job_id, current_address))
            rlayout.addWidget(cmb_job)

            labeled = c.get("labeled") or {}

            rlayout.addWidget(QLabel("Address:"))
            txt_address = QLineEdit(c["address_guess"])
            rlayout.addWidget(txt_address)

            rlayout.addWidget(QLabel("Address Line 2 (optional):"))
            txt_address2 = QLineEdit(labeled.get("address2", ""))
            rlayout.addWidget(txt_address2)

            state_city_row = QHBoxLayout()
            state_col = QVBoxLayout()
            state_col.addWidget(QLabel("State:"))
            cmb_state = QComboBox()
            state_col.addWidget(cmb_state)
            city_col = QVBoxLayout()
            city_col.addWidget(QLabel("City:"))
            cmb_city = QComboBox()
            city_col.addWidget(cmb_city)
            state_city_row.addLayout(state_col)
            state_city_row.addLayout(city_col)
            rlayout.addLayout(state_city_row)

            rlayout.addWidget(QLabel("Zip Code (optional):"))
            txt_zip = QLineEdit(self._format_zip(labeled.get("zip", "")) if labeled.get("zip") else "")
            txt_zip.setPlaceholderText("00000-0000")
            rlayout.addWidget(txt_zip)

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

            # Se o e-mail veio no modelo de campos (STATE:/CITY:), tenta
            # pré-selecionar os combos pelo nome — igual ao usuário teria
            # feito manualmente, só que automático. Sem modelo (ou sem
            # bater o nome exato), os combos continuam em "— Select —"
            # normalmente, sem travar nada.
            labeled_state = (labeled.get("state") or "").strip()
            if labeled_state:
                target = self._normalize_keyword_text(labeled_state)
                for i in range(1, cmb_state.count()):
                    name = self._normalize_keyword_text(cmb_state.itemText(i))
                    if name == target or name.startswith(target) or target.startswith(name):
                        cmb_state.setCurrentIndex(i)  # dispara o reload do City acima
                        break
            labeled_city = (labeled.get("city") or "").strip()
            if labeled_city:
                target = self._normalize_keyword_text(labeled_city)
                for i in range(1, cmb_city.count()):
                    if self._normalize_keyword_text(cmb_city.itemText(i)) == target:
                        cmb_city.setCurrentIndex(i)
                        break

            rbtn_row = QHBoxLayout()
            btn_confirm = QPushButton("✔  Apply to Job")
            btn_confirm.setStyleSheet(
                "QPushButton { background-color: #2E7D32; color: #FFFFFF; border: none; "
                "border-radius: 6px; padding: 8px 14px; font-weight: 600; } "
                "QPushButton:hover { background-color: #388E3C; }"
            )
            btn_cancel = QPushButton("Cancel")
            rbtn_row.addWidget(btn_confirm)
            rbtn_row.addStretch()
            rbtn_row.addWidget(btn_cancel)
            rlayout.addLayout(rbtn_row)
            btn_cancel.clicked.connect(review.reject)

            def confirm_apply():
                job_data = cmb_job.currentData()
                if not job_data or not job_data[0]:
                    QMessageBox.information(review, "No job selected", "Select a Job before applying.")
                    return
                job_id, current_address = job_data
                new_address = txt_address.text().strip()
                if not new_address:
                    QMessageBox.information(review, "Missing address", "Enter an address before applying.")
                    return

                if current_address and current_address.strip() and current_address.strip() != new_address:
                    confirm = QMessageBox.question(
                        review, "Overwrite existing address?",
                        f"This job already has an address saved:\n'{current_address}'\n\n"
                        f"Replace it with:\n'{new_address}'?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No,
                    )
                    if confirm != QMessageBox.StandardButton.Yes:
                        return

                address2 = txt_address2.text().strip()
                state_id = cmb_state.currentData()
                city_id = cmb_city.currentData()
                zip_code = self._format_zip(txt_zip.text())

                from email.utils import parsedate_to_datetime
                try:
                    visit_date = parsedate_to_datetime(c["date"]).date().isoformat()
                except Exception:
                    visit_date = date.today().isoformat()

                try:
                    conn = self._get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE job_projects SET JOB_ADDRESS = %s, CITY_ID = COALESCE(%s, CITY_ID), "
                        "STATE_ID = COALESCE(%s, STATE_ID) WHERE ID = %s",
                        (new_address, city_id, state_id, job_id),
                    )
                    conn.commit()
                    cursor.close()
                    conn.close()
                except (MySQLError, RuntimeError) as e:
                    QMessageBox.critical(review, "Database Error", f"Could not update the job's address:\n{e}")
                    return

                try:
                    conn2 = self._get_connection()
                    cursor2 = conn2.cursor()
                    cursor2.execute(
                        "INSERT INTO job_site_visits (JOB_PROJECT_ID, VISIT_DATE, JOB_ADDRESS, "
                        "JOB_ADDRESS2, CITY_ID, STATE_ID, ZIP_CODE, SOURCE, EMAIL_SUBJECT) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, 'EMAIL', %s)",
                        (job_id, visit_date, new_address, address2, city_id, state_id, zip_code, c["subject"]),
                    )
                    conn2.commit()
                    cursor2.close()
                    conn2.close()
                except (MySQLError, RuntimeError):
                    pass  # job_site_visits ainda não existe (migração pendente) — não bloqueia o resto

                mark_seen(c["uid"])
                review.accept()

            btn_confirm.clicked.connect(confirm_apply)
            return review.exec()

        def use_selected():
            r = table.currentRow()
            if r < 0 or r not in found_emails:
                QMessageBox.information(dialog, "No selection", "Select a job site email first.")
                return
            c = found_emails[r]
            result = review_and_apply(c)
            if result == QDialog.DialogCode.Accepted:
                table.removeRow(r)
                found_emails.pop(r, None)
                QMessageBox.information(dialog, "Address Applied", "The job's address was updated.")

        def dismiss_selected():
            r = table.currentRow()
            if r < 0 or r not in found_emails:
                QMessageBox.information(dialog, "No selection", "Select a job site email first.")
                return
            c = found_emails[r]
            mark_seen(c["uid"])
            table.removeRow(r)
            found_emails.pop(r, None)

        btn_row = QHBoxLayout()
        btn_use = QPushButton("✔  Use This Address")
        btn_use.setStyleSheet(
            "QPushButton { background-color: #2E7D32; color: #FFFFFF; border: none; "
            "border-radius: 6px; padding: 8px 14px; font-weight: 600; } "
            "QPushButton:hover { background-color: #388E3C; }"
        )
        btn_use.clicked.connect(use_selected)
        btn_dismiss = QPushButton("Dismiss (mark as read)")
        btn_dismiss.clicked.connect(dismiss_selected)
        btn_history = QPushButton("📜  View Address History")
        btn_history.clicked.connect(self.open_job_site_history_dialog)
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(dialog.accept)
        btn_row.addWidget(btn_use)
        btn_row.addWidget(btn_dismiss)
        btn_row.addWidget(btn_history)
        btn_row.addStretch()
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

        dialog.exec()

    def open_job_site_history_dialog(self):
        """Mostra (só leitura) o histórico de endereços de obra confirmados
        pelo Job Site Inbox — tabela job_site_visits, mais recente primeiro.
        Se a migração ainda não rodou, avisa e não trava o resto do app."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Job Site Address History")
        dialog.resize(700, 480)
        dialog.setStyleSheet("""
            QTableWidget { background-color: #FFFFFF; color: #1C2B3A; gridline-color: #E3E8EE; }
            QHeaderView::section { background-color: #F0F4F8; color: #1C2B3A; padding: 6px; border: none; font-weight: 600; }
        """)
        layout = QVBoxLayout(dialog)

        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Date", "Job Code", "Client", "Address"])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(table, 1)

        rows = []
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT v.VISIT_DATE, jp.CODE, COALESCE(cl.FULL_NAME, ''),
                       CONCAT(v.JOB_ADDRESS, IF(v.JOB_ADDRESS2 IS NOT NULL AND v.JOB_ADDRESS2 <> '',
                                                 CONCAT(', ', v.JOB_ADDRESS2), ''))
                FROM job_site_visits v
                JOIN job_projects jp ON jp.ID = v.JOB_PROJECT_ID
                LEFT JOIN clients cl ON cl.ID = jp.CLIENT_ID
                ORDER BY v.VISIT_DATE DESC, v.ID DESC
                LIMIT 500
                """
            )
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.information(
                dialog, "History not available yet",
                "This history isn't available yet — the job_site_visits table hasn't been "
                f"created in the database.\n\n({e})",
            )

        table.setRowCount(len(rows))
        for i, (visit_date, code, client_name, address) in enumerate(rows):
            values = [str(visit_date) if visit_date else "", code or "", client_name or "", address or ""]
            for col, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(i, col, item)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(dialog.accept)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(btn_close)
        layout.addLayout(row)

        dialog.exec()
