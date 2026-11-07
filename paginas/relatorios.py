# -*- coding: utf-8 -*-
"""
Relatórios: P&L, 1099 e Sales Summary (tela e exportação).

Métodos da MainWindow (mixin) — veja main_.py.
"""

from app_common import *  # noqa: F401,F403


class ReportsMixin:
    def _setup_pnl_period_filter(self):
        """Popula os combos de Mês/Ano do P&L (dinâmico, não dá pra fazer isso direto no Designer)."""
        self.ui.cmb_pnl_month.blockSignals(True)
        self.ui.cmb_pnl_month.addItem("All Months", 0)
        month_names = ["January", "February", "March", "April", "May", "June",
                       "July", "August", "September", "October", "November", "December"]
        for i, name in enumerate(month_names, start=1):
            self.ui.cmb_pnl_month.addItem(name, i)
        self.ui.cmb_pnl_month.setCurrentIndex(date.today().month)
        self.ui.cmb_pnl_month.blockSignals(False)

        self.ui.cmb_pnl_year.blockSignals(True)
        self.ui.cmb_pnl_year.addItem("All Years", 0)
        current_year = date.today().year
        for y in range(current_year - 4, current_year + 1):
            self.ui.cmb_pnl_year.addItem(str(y), y)
        self.ui.cmb_pnl_year.setCurrentIndex(self.ui.cmb_pnl_year.count() - 1)
        self.ui.cmb_pnl_year.blockSignals(False)

    def load_pnl_report(self):
        """Calcula o P&L simples do período: Receita (recebido, via payments)
        menos Despesas (por categoria, via expenses) = Lucro Líquido."""
        month = self.ui.cmb_pnl_month.currentData() or 0
        year = self.ui.cmb_pnl_year.currentData() or 0

        date_clause = ""
        params_rev = []
        params_exp = []
        if month:
            date_clause += " AND MONTH({col}) = %s"
        if year:
            date_clause += " AND YEAR({col}) = %s"

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            rev_clause = date_clause.format(col="PAID_DATE")
            if month:
                params_rev.append(month)
            if year:
                params_rev.append(year)
            cursor.execute(f"SELECT COALESCE(SUM(AMOUNT), 0) FROM payments WHERE 1=1 {rev_clause}", params_rev)
            revenue = float(cursor.fetchone()[0] or 0)

            exp_clause = date_clause.format(col="EXPENSE_DATE")
            if month:
                params_exp.append(month)
            if year:
                params_exp.append(year)
            cursor.execute(
                f"SELECT CATEGORY, COALESCE(SUM(AMOUNT), 0) FROM expenses WHERE 1=1 {exp_clause} "
                f"GROUP BY CATEGORY ORDER BY SUM(AMOUNT) DESC",
                params_exp,
            )
            expense_rows = cursor.fetchall()

            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.warning(self, "Database Error", f"Could not load the P&L report:\n{e}")
            return

        total_expenses = sum(float(amount or 0) for _, amount in expense_rows)
        net_profit = revenue - total_expenses

        self.ui.lbl_pnl_revenue_value.setText(f"${revenue:,.2f}")

        table = self.ui.table_pnl_expenses
        table.setRowCount(len(expense_rows))
        for r, (category, amount) in enumerate(expense_rows):
            for c, text in enumerate([str(category or "—"), f"${float(amount or 0):,.2f}"]):
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(r, c, item)

        self.ui.lbl_pnl_total_expenses_value.setText(f"Total Expenses: ${total_expenses:,.2f}")
        profit_color = "#2E7D32" if net_profit >= 0 else "#C62828"
        self.ui.lbl_pnl_net_profit_value.setStyleSheet(
            f"font-size:22px; font-weight:800; color:{profit_color}; background:transparent;"
        )
        self.ui.lbl_pnl_net_profit_value.setText(f"Net Profit: ${net_profit:,.2f}")

    def _setup_sales_summary_period_filter(self):
        """Popula os combos de Mês/Ano do Sales Summary."""
        self.ui.cmb_sales_summary_month.blockSignals(True)
        self.ui.cmb_sales_summary_month.addItem("All Months", 0)
        month_names = ["January", "February", "March", "April", "May", "June",
                       "July", "August", "September", "October", "November", "December"]
        for i, name in enumerate(month_names, start=1):
            self.ui.cmb_sales_summary_month.addItem(name, i)
        self.ui.cmb_sales_summary_month.setCurrentIndex(date.today().month)
        self.ui.cmb_sales_summary_month.blockSignals(False)

        self.ui.cmb_sales_summary_year.blockSignals(True)
        self.ui.cmb_sales_summary_year.addItem("All Years", 0)
        current_year = date.today().year
        for y in range(current_year - 4, current_year + 1):
            self.ui.cmb_sales_summary_year.addItem(str(y), y)
        self.ui.cmb_sales_summary_year.setCurrentIndex(self.ui.cmb_sales_summary_year.count() - 1)
        self.ui.cmb_sales_summary_year.blockSignals(False)

    def _setup_1099_year_filter(self):
        """Popula o combo de Tax Year do relatório 1099."""
        self.ui.cmb_1099_year.blockSignals(True)
        current_year = date.today().year
        for y in range(current_year - 4, current_year + 1):
            self.ui.cmb_1099_year.addItem(str(y), y)
        self.ui.cmb_1099_year.setCurrentIndex(self.ui.cmb_1099_year.count() - 1)
        self.ui.cmb_1099_year.blockSignals(False)

    def load_1099_report(self):
        """Soma quanto foi pago pra cada Contractor no ano fiscal escolhido,
        sinaliza quem passou de $600 (limite do IRS pra exigir 1099-NEC), e
        mostra se o W-9 daquele contratado já está no seu arquivo — clicar
        2x numa linha alterna esse status (ver _toggle_contractor_w9)."""
        year = self.ui.cmb_1099_year.currentData() or date.today().year

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT c.ID, COALESCE(c.COMPANY_NAME, c.FULL_NAME), c.ADDRESS,
                       COALESCE(city.CITY, '—'), COALESCE(st.STATE_NAME, '—'),
                       COALESCE(SUM(p.AMOUNT), 0) AS total_paid,
                       COALESCE(w9.RECEIVED, 0) AS w9_received
                FROM contractors c
                LEFT JOIN cities city ON city.ID = c.CITY_ID
                LEFT JOIN states st ON st.ID = c.STATE_ID
                LEFT JOIN contractor_invoices ci ON ci.CONTRACTOR_ID = c.ID
                LEFT JOIN payments p ON p.INVOICE_TYPE = 'Contractor' AND p.INVOICE_ID = ci.ID
                                      AND YEAR(p.PAID_DATE) = %s
                LEFT JOIN contractor_w9 w9 ON w9.CONTRACTOR_ID = c.ID
                GROUP BY c.ID, c.COMPANY_NAME, c.FULL_NAME, c.ADDRESS, city.CITY, st.STATE_NAME, w9.RECEIVED
                HAVING total_paid > 0
                ORDER BY total_paid DESC
                """,
                (year,),
            )
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            # Se a tabela contractor_w9 ainda não existir (migração não rodada),
            # cai pra versão sem a coluna de W-9 em vez de travar o relatório.
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT c.ID, COALESCE(c.COMPANY_NAME, c.FULL_NAME), c.ADDRESS,
                           COALESCE(city.CITY, '—'), COALESCE(st.STATE_NAME, '—'),
                           COALESCE(SUM(p.AMOUNT), 0) AS total_paid, 0 AS w9_received
                    FROM contractors c
                    LEFT JOIN cities city ON city.ID = c.CITY_ID
                    LEFT JOIN states st ON st.ID = c.STATE_ID
                    LEFT JOIN contractor_invoices ci ON ci.CONTRACTOR_ID = c.ID
                    LEFT JOIN payments p ON p.INVOICE_TYPE = 'Contractor' AND p.INVOICE_ID = ci.ID
                                          AND YEAR(p.PAID_DATE) = %s
                    GROUP BY c.ID, c.COMPANY_NAME, c.FULL_NAME, c.ADDRESS, city.CITY, st.STATE_NAME
                    HAVING total_paid > 0
                    ORDER BY total_paid DESC
                    """,
                    (year,),
                )
                rows = cursor.fetchall()
                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError) as e2:
                QMessageBox.warning(self, "Database Error", f"Could not load the 1099 report:\n{e2}")
                return

        table = self.ui.table_1099
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(
            ["Contractor", "Address", "City / State", "Total Paid", "1099 Required?", "W-9 On File?"]
        )
        table.setRowCount(len(rows))
        self._table_1099_row_contractor_ids = {}
        needs_1099_count = 0
        missing_w9_count = 0
        for r, (contractor_id, name, address, city_name, state_name, total_paid, w9_received) in enumerate(rows):
            total_paid = float(total_paid or 0)
            needs_1099 = total_paid >= 600
            has_w9 = bool(w9_received)
            if needs_1099:
                needs_1099_count += 1
                if not has_w9:
                    missing_w9_count += 1

            values = [
                str(name or ""), str(address or "—"), f"{city_name}, {state_name}",
                f"${total_paid:,.2f}", "✅ Yes" if needs_1099 else "No",
                "✅ Yes" if has_w9 else "❌ No",
            ]
            for c, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if c == 4 and needs_1099:
                    item.setForeground(QColor("#2E7D32"))
                if c == 5:
                    item.setForeground(QColor("#2E7D32") if has_w9 else QColor("#C62828"))
                    item.setToolTip("Double-click this row to change W-9 status")
                table.setItem(r, c, item)
            self._table_1099_row_contractor_ids[r] = contractor_id

        summary = f"{needs_1099_count} contractor(s) require a 1099 this year."
        if missing_w9_count:
            summary += f"  ⚠️ {missing_w9_count} of them still need a W-9 collected."
        summary += "  (Double-click a row to mark W-9 received/not received.)"
        self.ui.lbl_1099_summary.setText(summary)

    def _toggle_contractor_w9(self, row, _col=None):
        """Chamado ao dar duplo-clique numa linha do relatório 1099: alterna
        se o W-9 daquele contratado já foi recebido, com a data de hoje."""
        contractor_id = getattr(self, "_table_1099_row_contractor_ids", {}).get(row)
        if not contractor_id:
            return

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT RECEIVED FROM contractor_w9 WHERE CONTRACTOR_ID = %s", (contractor_id,))
            existing = cursor.fetchone()
            currently_received = bool(existing[0]) if existing else False
            new_value = not currently_received

            confirm = QMessageBox.question(
                self, "W-9 Status",
                ("Mark W-9 as RECEIVED for this contractor?" if new_value
                 else "Mark W-9 as NOT received for this contractor?"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if confirm != QMessageBox.StandardButton.Yes:
                cursor.close()
                conn.close()
                return

            cursor.execute(
                "INSERT INTO contractor_w9 (CONTRACTOR_ID, RECEIVED, RECEIVED_DATE) VALUES (%s, %s, %s) "
                "ON DUPLICATE KEY UPDATE RECEIVED = VALUES(RECEIVED), RECEIVED_DATE = VALUES(RECEIVED_DATE)",
                (contractor_id, 1 if new_value else 0, date.today() if new_value else None),
            )
            conn.commit()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(
                self, "Database Error",
                f"Could not update W-9 status:\n{e}\n\n(Did you run migration_contractor_w9.sql yet?)",
            )
            return

        self.load_1099_report()

    def export_1099_pdf(self):
        """Exporta o relatório 1099 do ano escolhido pra um PDF."""
        if not REPORTLAB_AVAILABLE:
            QMessageBox.critical(self, "Missing Dependency",
                                  "The 'reportlab' package is not installed.\n\nRun:\npip install reportlab")
            return

        year_name = self.ui.cmb_1099_year.currentText()
        path, _ = QFileDialog.getSaveFileName(
            self, "Export 1099 Report to PDF", f"1099_Report_{year_name}.pdf", "PDF Files (*.pdf)"
        )
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"

        try:
            styles = getSampleStyleSheet()
            doc = SimpleDocTemplate(path, pagesize=letter, topMargin=0.6 * inch, bottomMargin=0.6 * inch,
                                     leftMargin=0.6 * inch, rightMargin=0.6 * inch)
            story = [
                Paragraph(f"<b>{company_settings.COMPANY_NAME}</b>", styles["Title"]),
                Paragraph(f"<b>1099-NEC Report</b> — Tax Year {year_name}", styles["Heading2"]),
                Spacer(1, 6),
                Paragraph(
                    "Contractors paid $600 or more require a 1099-NEC (IRS threshold). "
                    "This report is for your records — it does not file the form for you.",
                    styles["Normal"],
                ),
                Spacer(1, 14),
            ]

            table = self.ui.table_1099
            data = [["Contractor", "Address", "City / State", "Total Paid", "1099 Required?", "W-9 On File?"]]
            for r in range(table.rowCount()):
                data.append([table.item(r, c).text() for c in range(6)])
            pdf_table = Table(
                data,
                colWidths=[1.25 * inch, 1.35 * inch, 1.1 * inch, 0.9 * inch, 1.0 * inch, 1.0 * inch],
                repeatRows=1,
            )
            pdf_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(BRAND_NAVY)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DDDDDD")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F9FC")]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(pdf_table)
            story.append(Spacer(1, 14))
            story.append(Paragraph(f"<b>{self.ui.lbl_1099_summary.text()}</b>", styles["Normal"]))

            doc.build(story)
            QMessageBox.information(self, "Export Complete", f"Saved to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Could not export the 1099 report:\n{e}")

    def load_sales_summary(self):
        """Monta o ranking de quem mais gera receita (Contractor/Company/
        Client), no período escolhido, ordenado do maior pro menor recebido."""
        month = self.ui.cmb_sales_summary_month.currentData() or 0
        year = self.ui.cmb_sales_summary_year.currentData() or 0
        type_filter = self.ui.cmb_sales_summary_type.currentText()

        period_clause = ""
        params_base = []
        if month:
            period_clause += " AND MONTH(ci.PERIOD_FROM) = %s"
            params_base.append(month)
        if year:
            period_clause += " AND YEAR(ci.PERIOD_FROM) = %s"
            params_base.append(year)

        entity_tables = [
            ("Contractor", "contractor_invoices", "contractors", "CONTRACTOR_ID", "COALESCE(r.COMPANY_NAME, r.FULL_NAME)"),
            ("Company", "company_invoices", "companies", "COMPANY_ID", "r.COMPANY_NAME"),
            ("Client", "client_invoices", "clients", "CLIENT_ID", "r.FULL_NAME"),
        ]
        if type_filter != "All":
            entity_tables = [e for e in entity_tables if e[0] == type_filter]

        all_rows = []
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            for label, table, ref_table, fk_col, name_col in entity_tables:
                cursor.execute(
                    f"""
                    SELECT {name_col}, COALESCE(SUM(ci.TOTAL_AMOUNT), 0), COALESCE(SUM(ci.AMOUNT_PAID), 0)
                    FROM {table} ci
                    LEFT JOIN {ref_table} r ON r.ID = ci.{fk_col}
                    WHERE 1=1 {period_clause}
                    GROUP BY {name_col}
                    """,
                    params_base,
                )
                for name, total_billed, total_received in cursor.fetchall():
                    total_billed = float(total_billed or 0)
                    total_received = float(total_received or 0)
                    if total_billed or total_received:
                        all_rows.append((label, name or "—", total_billed, total_received))
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.warning(self, "Database Error", f"Could not load the Sales Summary:\n{e}")
            return

        all_rows.sort(key=lambda row: row[3], reverse=True)

        table = self.ui.table_sales_summary
        table.setSortingEnabled(False)
        table.setRowCount(len(all_rows))
        total_received_sum = 0.0
        for r, (label, name, total_billed, total_received) in enumerate(all_rows):
            total_received_sum += total_received
            open_balance = total_billed - total_received
            values = [
                str(r + 1), label, name, f"${total_billed:,.2f}",
                f"${total_received:,.2f}", f"${open_balance:,.2f}",
            ]
            for c, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(r, c, item)
        table.setSortingEnabled(True)

        self.ui.lbl_sales_summary_total.setText(f"Total Received: ${total_received_sum:,.2f}")

    def export_sales_summary_pdf(self):
        """Exporta o Sales Summary do período/tipo atual pra um PDF."""
        if not REPORTLAB_AVAILABLE:
            QMessageBox.critical(self, "Missing Dependency",
                                  "The 'reportlab' package is not installed.\n\nRun:\npip install reportlab")
            return

        month_name = self.ui.cmb_sales_summary_month.currentText()
        year_name = self.ui.cmb_sales_summary_year.currentText()
        default_name = f"Sales_Summary_{month_name}_{year_name}.pdf".replace(" ", "_")
        path, _ = QFileDialog.getSaveFileName(self, "Export Sales Summary to PDF", default_name, "PDF Files (*.pdf)")
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"

        try:
            styles = getSampleStyleSheet()
            doc = SimpleDocTemplate(path, pagesize=letter, topMargin=0.6 * inch, bottomMargin=0.6 * inch,
                                     leftMargin=0.6 * inch, rightMargin=0.6 * inch)
            story = [
                Paragraph(f"<b>{company_settings.COMPANY_NAME}</b>", styles["Title"]),
                Paragraph(f"<b>Sales Summary</b> — {month_name} {year_name}", styles["Heading2"]),
                Spacer(1, 14),
            ]

            table = self.ui.table_sales_summary
            data = [["Rank", "Type", "Name", "Total Billed", "Total Received", "Open Balance"]]
            for r in range(table.rowCount()):
                data.append([table.item(r, c).text() for c in range(6)])
            pdf_table = Table(data, colWidths=[0.5 * inch, 0.9 * inch, 1.6 * inch, 1.1 * inch, 1.2 * inch, 1.1 * inch],
                               repeatRows=1)
            pdf_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(BRAND_NAVY)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DDDDDD")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F9FC")]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(pdf_table)
            story.append(Spacer(1, 14))
            story.append(Paragraph(f"<b>{self.ui.lbl_sales_summary_total.text()}</b>", styles["Normal"]))

            doc.build(story)
            QMessageBox.information(self, "Export Complete", f"Saved to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Could not export the Sales Summary:\n{e}")

    def export_1099_excel(self):
        """Exporta o relatório 1099 do ano escolhido pra uma planilha Excel."""
        year_name = self.ui.cmb_1099_year.currentText()
        path, _ = QFileDialog.getSaveFileName(
            self, "Export 1099 Report to Excel", f"1099_Report_{year_name}.xlsx", "Excel Files (*.xlsx)"
        )
        if not path:
            return
        if not path.lower().endswith(".xlsx"):
            path += ".xlsx"

        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment
        except ImportError:
            QMessageBox.critical(self, "Missing Dependency",
                                  "The 'openpyxl' package is not installed.\n\nRun:\npip install openpyxl")
            return

        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "1099 Report"
            ws.append([f"1099-NEC Report — Tax Year {year_name}"])
            ws["A1"].font = Font(bold=True, size=14)
            ws.append([])

            headers = ["Contractor", "Address", "City / State", "Total Paid", "1099 Required?", "W-9 On File?"]
            ws.append(headers)
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="1C2B3A", end_color="1C2B3A", fill_type="solid")
            for c in range(1, len(headers) + 1):
                cell = ws.cell(row=3, column=c)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal="center")

            table = self.ui.table_1099
            for r in range(table.rowCount()):
                ws.append([table.item(r, c).text() for c in range(6)])

            for col, width in zip("ABCDEF", [22, 28, 18, 14, 16, 16]):
                ws.column_dimensions[col].width = width

            wb.save(path)
            QMessageBox.information(self, "Export Complete", f"Saved to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Could not export to Excel:\n{e}")

    def export_pnl_pdf(self):
        """Exporta o P&L do período atual pra um PDF simples."""
        if not REPORTLAB_AVAILABLE:
            QMessageBox.critical(self, "Missing Dependency",
                                  "The 'reportlab' package is not installed.\n\nRun:\npip install reportlab")
            return

        month_name = self.ui.cmb_pnl_month.currentText()
        year_name = self.ui.cmb_pnl_year.currentText()
        default_name = f"PnL_{month_name}_{year_name}.pdf".replace(" ", "_")
        path, _ = QFileDialog.getSaveFileName(self, "Export P&L to PDF", default_name, "PDF Files (*.pdf)")
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"

        try:
            styles = getSampleStyleSheet()
            doc = SimpleDocTemplate(path, pagesize=letter, topMargin=0.6 * inch, bottomMargin=0.6 * inch,
                                     leftMargin=0.7 * inch, rightMargin=0.7 * inch)
            story = [
                Paragraph(f"<b>{company_settings.COMPANY_NAME}</b>", styles["Title"]),
                Paragraph(f"<b>Profit &amp; Loss Statement</b> — {month_name} {year_name}", styles["Heading2"]),
                Spacer(1, 14),
                Paragraph(
                    f"<b>Revenue (received in period):</b> {self.ui.lbl_pnl_revenue_value.text()}",
                    styles["Normal"],
                ),
                Spacer(1, 10),
                Paragraph("<b>Expenses by Category</b>", styles["Heading3"]),
            ]

            table = self.ui.table_pnl_expenses
            exp_data = [["Category", "Amount"]]
            for r in range(table.rowCount()):
                exp_data.append([table.item(r, 0).text(), table.item(r, 1).text()])
            exp_table = Table(exp_data, colWidths=[3.5 * inch, 2.0 * inch], repeatRows=1)
            exp_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(BRAND_NAVY)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DDDDDD")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F9FC")]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(exp_table)
            story.append(Spacer(1, 14))
            story.append(Paragraph(f"<b>{self.ui.lbl_pnl_total_expenses_value.text()}</b>", styles["Normal"]))
            story.append(Paragraph(f"<b>{self.ui.lbl_pnl_net_profit_value.text()}</b>", styles["Heading2"]))

            doc.build(story)
            QMessageBox.information(self, "Export Complete", f"Saved to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Could not export the P&L report:\n{e}")
