# -*- coding: utf-8 -*-
"""
Bank Reconciliation: importa o extrato CSV e compara com payments/expenses.

Métodos da MainWindow (mixin) — veja main_.py.
"""

from app_common import *  # noqa: F401,F403


class BankReconciliationMixin:
    def _setup_bank_reconciliation_feature(self):
        """Cria, em tempo de execução, o botão 'Bank Reconciliation' no
        submenu de Registrations — mesmo padrão das outras telas novas
        (QDialog 100% em Python, sem editar o .ui)."""
        self.ui.btn_reg_bank_reconciliation = QPushButton(self.ui.frame_registrations_submenu)
        self.ui.btn_reg_bank_reconciliation.setObjectName(u"btn_reg_bank_reconciliation")
        self.ui.btn_reg_bank_reconciliation.setCheckable(False)
        self.ui.btn_reg_bank_reconciliation.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ui.layout_registrations_submenu.addWidget(self.ui.btn_reg_bank_reconciliation)

    def _import_bank_statement_csv(self, parent_dialog):
        """Importa um extrato bancário em CSV: mostra uma prévia, deixa
        escolher qual coluna é Data/Descrição/Valor (ou Débito+Crédito
        separados, formato comum em muitos bancos), evita importar a mesma
        transação duas vezes, e insere o resto em bank_transactions como
        'UNMATCHED'."""
        filepath, _ = QFileDialog.getOpenFileName(
            parent_dialog, "Select Bank Statement CSV", "", "CSV Files (*.csv)"
        )
        if not filepath:
            return

        import csv as csv_module
        try:
            with open(filepath, "r", encoding="utf-8-sig", newline="") as f:
                all_rows = list(csv_module.reader(f))
        except Exception as e:
            QMessageBox.critical(parent_dialog, "File Error", f"Could not read the CSV file:\n{e}")
            return

        if len(all_rows) < 2:
            QMessageBox.warning(parent_dialog, "Empty File", "This CSV doesn't seem to have any data rows.")
            return

        header = all_rows[0]
        data_rows = all_rows[1:]

        # ── Diálogo de mapeamento de colunas ──────────────────────────
        map_dialog = QDialog(parent_dialog)
        map_dialog.setWindowTitle("Map CSV Columns")
        map_dialog.resize(600, 440)
        map_layout = QVBoxLayout(map_dialog)
        map_layout.addWidget(QLabel(
            f"<b>{os.path.basename(filepath)}</b> — {len(data_rows)} row(s) found. "
            f"Tell us which column is which (most banks export Date, Description, Amount):"
        ))

        preview = QTableWidget()
        preview.setColumnCount(len(header))
        preview.setHorizontalHeaderLabels(header)
        preview.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        preview_rows = data_rows[:5]
        preview.setRowCount(len(preview_rows))
        for r, row in enumerate(preview_rows):
            for c in range(len(header)):
                preview.setItem(r, c, QTableWidgetItem(row[c] if c < len(row) else ""))
        preview.setMaximumHeight(150)
        map_layout.addWidget(preview)

        def make_col_combo(default_index=0):
            combo = QComboBox()
            for i, name in enumerate(header):
                combo.addItem(name or f"Column {i + 1}", i)
            if default_index < combo.count():
                combo.setCurrentIndex(default_index)
            return combo

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Date column:"))
        cmb_date_col = make_col_combo(0)
        row1.addWidget(cmb_date_col)
        row1.addWidget(QLabel("Description column:"))
        cmb_desc_col = make_col_combo(1 if len(header) > 1 else 0)
        row1.addWidget(cmb_desc_col)
        map_layout.addLayout(row1)

        chk_separate = QCheckBox(
            "My bank uses separate Debit and Credit columns (instead of one signed Amount column)"
        )
        map_layout.addWidget(chk_separate)

        row2 = QHBoxLayout()
        lbl_amount = QLabel("Amount column (negative = money out):")
        cmb_amount_col = make_col_combo(2 if len(header) > 2 else 0)
        row2.addWidget(lbl_amount)
        row2.addWidget(cmb_amount_col)
        map_layout.addLayout(row2)

        row3 = QHBoxLayout()
        lbl_debit = QLabel("Debit column (money out):")
        cmb_debit_col = make_col_combo(2 if len(header) > 2 else 0)
        lbl_credit = QLabel("Credit column (money in):")
        cmb_credit_col = make_col_combo(3 if len(header) > 3 else 0)
        row3.addWidget(lbl_debit)
        row3.addWidget(cmb_debit_col)
        row3.addWidget(lbl_credit)
        row3.addWidget(cmb_credit_col)
        map_layout.addLayout(row3)

        def toggle_amount_mode():
            separate = chk_separate.isChecked()
            lbl_amount.setVisible(not separate)
            cmb_amount_col.setVisible(not separate)
            lbl_debit.setVisible(separate)
            cmb_debit_col.setVisible(separate)
            lbl_credit.setVisible(separate)
            cmb_credit_col.setVisible(separate)

        chk_separate.toggled.connect(toggle_amount_mode)
        toggle_amount_mode()

        map_result = {"ok": False}
        map_btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(map_dialog.reject)
        btn_ok = QPushButton("Import")
        btn_ok.setStyleSheet(
            "QPushButton { background-color: #1565C0; color: #FFFFFF; border: none; "
            "border-radius: 6px; padding: 8px 14px; font-weight: 600; } "
            "QPushButton:hover { background-color: #1E88E5; }"
        )

        def confirm_mapping():
            map_result["ok"] = True
            map_dialog.accept()

        btn_ok.clicked.connect(confirm_mapping)
        map_btn_row.addStretch()
        map_btn_row.addWidget(btn_cancel)
        map_btn_row.addWidget(btn_ok)
        map_layout.addLayout(map_btn_row)

        map_dialog.exec()
        if not map_result["ok"]:
            return

        date_col = cmb_date_col.currentData()
        desc_col = cmb_desc_col.currentData()
        separate = chk_separate.isChecked()
        amount_col = cmb_amount_col.currentData()
        debit_col = cmb_debit_col.currentData()
        credit_col = cmb_credit_col.currentData()

        def parse_date(raw):
            raw = (raw or "").strip()
            for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y", "%d/%m/%Y", "%m/%d/%y"):
                try:
                    return datetime.strptime(raw, fmt).date()
                except ValueError:
                    continue
            return None

        def parse_amount(raw):
            raw = (raw or "").strip().replace("$", "").replace(",", "")
            if not raw:
                return None
            neg = raw.startswith("(") and raw.endswith(")")
            if neg:
                raw = raw[1:-1]
            try:
                val = float(raw)
            except ValueError:
                return None
            return -val if neg else val

        parsed = []
        failed = 0
        for row in data_rows:
            if date_col >= len(row) or desc_col >= len(row):
                failed += 1
                continue
            txn_date = parse_date(row[date_col])
            raw_desc = row[desc_col].strip()
            if not txn_date:
                failed += 1
                continue
            if separate:
                debit = parse_amount(row[debit_col]) if debit_col < len(row) else None
                credit = parse_amount(row[credit_col]) if credit_col < len(row) else None
                if credit:
                    amount = abs(credit)
                elif debit:
                    amount = -abs(debit)
                else:
                    failed += 1
                    continue
            else:
                amount = parse_amount(row[amount_col]) if amount_col < len(row) else None
                if amount is None:
                    failed += 1
                    continue
            parsed.append((txn_date, raw_desc, amount))

        if not parsed:
            QMessageBox.warning(parent_dialog, "Nothing to Import",
                                 f"Could not parse any rows from this file ({failed} failed).")
            return

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT TXN_DATE, DESCRIPTION, AMOUNT FROM bank_transactions")
            existing = cursor.fetchall()
            inserted = 0
            skipped_dupe = 0
            for txn_date, desc, amount in parsed:
                is_dupe = any(
                    e[0] == txn_date and e[1] == desc and abs(float(e[2]) - amount) < 0.005
                    for e in existing
                )
                if is_dupe:
                    skipped_dupe += 1
                    continue
                cursor.execute(
                    "INSERT INTO bank_transactions (TXN_DATE, DESCRIPTION, AMOUNT, STATUS) "
                    "VALUES (%s, %s, %s, 'UNMATCHED')",
                    (txn_date, desc, amount),
                )
                inserted += 1
            conn.commit()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(
                parent_dialog, "Database Error",
                f"Could not import transactions:\n{e}\n\n"
                f"(Did you run migration_fase6_bank_reconciliation.sql yet?)",
            )
            return

        QMessageBox.information(
            parent_dialog, "Import Complete",
            f"{inserted} transaction(s) imported.\n"
            f"{skipped_dupe} duplicate(s) skipped (already imported before).\n"
            f"{failed} row(s) could not be parsed and were skipped.",
        )

    def open_bank_reconciliation_dialog(self):
        """Concilia o extrato bancário (importado em CSV) com o que já foi
        lançado no sistema: pagamentos recebidos (payments, de Company/
        Client) e pagamentos feitos (payments de Contractor + expenses).
        Sugere candidatos por valor + data próxima; você confirma o match,
        marca como 'Ignored' (transferência interna, tarifa de banco, etc.)
        ou deixa pendente."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Bank Reconciliation")
        dialog.resize(920, 660)
        dialog.setStyleSheet("""
            QTableWidget { background-color: #FFFFFF; color: #1C2B3A; gridline-color: #E3E8EE; }
            QHeaderView::section { background-color: #F0F4F8; color: #1C2B3A; padding: 6px; border: none; font-weight: 600; }
        """)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(
            "<b>Bank Reconciliation</b> — import your bank statement (CSV) and match each transaction "
            "against payments received or payments/expenses already recorded in the system."
        ))

        top_row = QHBoxLayout()
        btn_import = QPushButton("⤒  Import Statement (CSV)")
        btn_import.setStyleSheet(
            "QPushButton { background-color: #1565C0; color: #FFFFFF; border: none; "
            "border-radius: 6px; padding: 8px 14px; font-weight: 600; } "
            "QPushButton:hover { background-color: #1E88E5; }"
        )
        top_row.addWidget(btn_import)
        top_row.addStretch()
        top_row.addWidget(QLabel("Show:"))
        cmb_filter_status = QComboBox()
        cmb_filter_status.addItem("Unmatched", "UNMATCHED")
        cmb_filter_status.addItem("All", None)
        cmb_filter_status.addItem("Matched", "MATCHED")
        cmb_filter_status.addItem("Ignored", "IGNORED")
        top_row.addWidget(cmb_filter_status)
        layout.addLayout(top_row)

        lbl_summary = QLabel("")
        lbl_summary.setStyleSheet("font-weight:600;")
        layout.addWidget(lbl_summary)

        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Date", "Description", "Amount", "Status"])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.setMinimumHeight(240)
        layout.addWidget(table, 1)

        row_data = {}

        def reload_table():
            table.setRowCount(0)
            row_data.clear()
            status_filter = cmb_filter_status.currentData()
            query = "SELECT ID, TXN_DATE, DESCRIPTION, AMOUNT, STATUS FROM bank_transactions"
            params = []
            if status_filter:
                query += " WHERE STATUS = %s"
                params.append(status_filter)
            query += " ORDER BY TXN_DATE DESC, ID DESC"
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
                cursor.execute("SELECT STATUS, COUNT(*) FROM bank_transactions GROUP BY STATUS")
                counts = dict(cursor.fetchall())
                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(
                    dialog, "Database Error",
                    f"Could not load bank transactions:\n{e}\n\n"
                    f"(Did you run migration_fase6_bank_reconciliation.sql on the real database yet?)",
                )
                return

            table.setRowCount(len(rows))
            status_colors = {"MATCHED": "#2E7D32", "IGNORED": "#6B7C93", "UNMATCHED": "#B26A00"}
            for r, (tid, txn_date, desc, amount, status) in enumerate(rows):
                amount = float(amount or 0)
                date_str = txn_date.strftime("%m/%d/%Y") if isinstance(txn_date, date) else str(txn_date)
                values = [date_str, desc or "", f"${amount:,.2f}", status.title()]
                for c, text in enumerate(values):
                    item = QTableWidgetItem(text)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    if c == 3:
                        item.setForeground(QColor(status_colors.get(status, "#1C2B3A")))
                    table.setItem(r, c, item)
                row_data[r] = {"ID": tid, "TXN_DATE": txn_date, "DESCRIPTION": desc,
                                "AMOUNT": amount, "STATUS": status}

            lbl_summary.setText(
                f"Unmatched: {counts.get('UNMATCHED', 0)}   |   Matched: {counts.get('MATCHED', 0)}   |   "
                f"Ignored: {counts.get('IGNORED', 0)}"
            )

        cmb_filter_status.currentIndexChanged.connect(reload_table)

        layout.addWidget(QLabel("<b>Suggested Matches for Selected Transaction</b> (pick one, then click Match)"))
        table_candidates = QTableWidget()
        table_candidates.setColumnCount(4)
        table_candidates.setHorizontalHeaderLabels(["Type", "Date", "Amount", "Description"])
        table_candidates.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table_candidates.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table_candidates.setMaximumHeight(140)
        layout.addWidget(table_candidates)

        candidate_data = {}

        def load_candidates():
            table_candidates.setRowCount(0)
            candidate_data.clear()
            r = table.currentRow()
            if r < 0 or r not in row_data:
                return
            txn = row_data[r]
            if txn["STATUS"] != "UNMATCHED":
                return

            candidates = []
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                if txn["AMOUNT"] > 0:
                    cursor.execute(
                        "SELECT ID, PAID_DATE, AMOUNT, NOTE FROM payments "
                        "WHERE INVOICE_TYPE IN ('Company','Client') AND ABS(AMOUNT - %s) < 0.01 "
                        "AND ABS(DATEDIFF(PAID_DATE, %s)) <= 7 "
                        "AND ID NOT IN (SELECT COALESCE(MATCHED_ID,0) FROM bank_transactions "
                        "WHERE MATCHED_TYPE='PAYMENT')",
                        (txn["AMOUNT"], txn["TXN_DATE"]),
                    )
                    for pid, pdate, pamt, note in cursor.fetchall():
                        candidates.append(("PAYMENT", pid, pdate, float(pamt), note or "Payment received"))
                else:
                    cursor.execute(
                        "SELECT ID, PAID_DATE, AMOUNT, NOTE FROM payments "
                        "WHERE INVOICE_TYPE = 'Contractor' AND ABS(AMOUNT - %s) < 0.01 "
                        "AND ABS(DATEDIFF(PAID_DATE, %s)) <= 7 "
                        "AND ID NOT IN (SELECT COALESCE(MATCHED_ID,0) FROM bank_transactions "
                        "WHERE MATCHED_TYPE='PAYMENT')",
                        (abs(txn["AMOUNT"]), txn["TXN_DATE"]),
                    )
                    for pid, pdate, pamt, note in cursor.fetchall():
                        candidates.append(("PAYMENT", pid, pdate, -float(pamt), note or "Contractor payment"))
                    cursor.execute(
                        "SELECT ID, EXPENSE_DATE, AMOUNT, DESCRIPTION FROM expenses "
                        "WHERE ABS(AMOUNT - %s) < 0.01 AND ABS(DATEDIFF(EXPENSE_DATE, %s)) <= 7 "
                        "AND ID NOT IN (SELECT COALESCE(MATCHED_ID,0) FROM bank_transactions "
                        "WHERE MATCHED_TYPE='EXPENSE')",
                        (abs(txn["AMOUNT"]), txn["TXN_DATE"]),
                    )
                    for eid, edate, eamt, desc in cursor.fetchall():
                        candidates.append(("EXPENSE", eid, edate, -float(eamt), desc or "Expense"))
                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.warning(dialog, "Database Error", f"Could not load candidates:\n{e}")
                return

            table_candidates.setRowCount(len(candidates))
            for i, (ctype, cid, cdate, camt, cdesc) in enumerate(candidates):
                date_str = cdate.strftime("%m/%d/%Y") if isinstance(cdate, date) else str(cdate)
                values = [ctype.title(), date_str, f"${camt:,.2f}", cdesc]
                for c, text in enumerate(values):
                    table_candidates.setItem(i, c, QTableWidgetItem(text))
                candidate_data[i] = {"TYPE": ctype, "ID": cid}

        table.itemSelectionChanged.connect(load_candidates)

        def match_selected():
            r = table.currentRow()
            cr = table_candidates.currentRow()
            if r < 0 or r not in row_data:
                QMessageBox.information(dialog, "No selection", "Select a bank transaction first.")
                return
            if cr < 0 or cr not in candidate_data:
                QMessageBox.information(dialog, "No candidate selected", "Select a suggested match first.")
                return
            txn = row_data[r]
            cand = candidate_data[cr]
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE bank_transactions SET STATUS='MATCHED', MATCHED_TYPE=%s, MATCHED_ID=%s WHERE ID=%s",
                    (cand["TYPE"], cand["ID"], txn["ID"]),
                )
                conn.commit()
                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not save match:\n{e}")
                return
            reload_table()

        def ignore_selected():
            r = table.currentRow()
            if r < 0 or r not in row_data:
                QMessageBox.information(dialog, "No selection", "Select a bank transaction first.")
                return
            txn = row_data[r]
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE bank_transactions SET STATUS='IGNORED', MATCHED_TYPE=NULL, MATCHED_ID=NULL WHERE ID=%s",
                    (txn["ID"],),
                )
                conn.commit()
                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not update transaction:\n{e}")
                return
            reload_table()

        def unmatch_selected():
            r = table.currentRow()
            if r < 0 or r not in row_data:
                QMessageBox.information(dialog, "No selection", "Select a bank transaction first.")
                return
            txn = row_data[r]
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE bank_transactions SET STATUS='UNMATCHED', MATCHED_TYPE=NULL, MATCHED_ID=NULL "
                    "WHERE ID=%s",
                    (txn["ID"],),
                )
                conn.commit()
                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not update transaction:\n{e}")
                return
            reload_table()

        def delete_selected_txn():
            r = table.currentRow()
            if r < 0 or r not in row_data:
                QMessageBox.information(dialog, "No selection", "Select a bank transaction first.")
                return
            txn = row_data[r]
            confirm = QMessageBox.question(
                dialog, "Confirm delete",
                f"Delete this imported transaction?\n\n{txn['DESCRIPTION']}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM bank_transactions WHERE ID=%s", (txn["ID"],))
                conn.commit()
                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not delete transaction:\n{e}")
                return
            reload_table()

        def do_import():
            self._import_bank_statement_csv(dialog)
            reload_table()

        btn_import.clicked.connect(do_import)

        btn_row = QHBoxLayout()
        btn_match = QPushButton("✔  Match")
        btn_match.setStyleSheet(
            "QPushButton { background-color: #2E7D32; color: #FFFFFF; border: none; "
            "border-radius: 6px; padding: 8px 14px; font-weight: 600; } "
            "QPushButton:hover { background-color: #388E3C; }"
        )
        btn_match.clicked.connect(match_selected)
        btn_ignore = QPushButton("Ignore")
        btn_ignore.clicked.connect(ignore_selected)
        btn_unmatch = QPushButton("Unmatch")
        btn_unmatch.clicked.connect(unmatch_selected)
        btn_delete = QPushButton("Delete")
        btn_delete.setStyleSheet(
            "QPushButton { background-color: #C62828; color: #FFFFFF; border: none; "
            "border-radius: 6px; padding: 8px 14px; font-weight: 600; } "
            "QPushButton:hover { background-color: #E53935; }"
        )
        btn_delete.clicked.connect(delete_selected_txn)
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(dialog.accept)

        btn_row.addWidget(btn_match)
        btn_row.addWidget(btn_ignore)
        btn_row.addWidget(btn_unmatch)
        btn_row.addWidget(btn_delete)
        btn_row.addStretch()
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

        reload_table()
        dialog.exec()
