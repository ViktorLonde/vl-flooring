# -*- coding: utf-8 -*-
"""
Montagem do PDF dos invoices (itens, decoração, layout) para contractor,
company e client.

Métodos da MainWindow (mixin) — veja main_.py.
"""

from app_common import *  # noqa: F401,F403


class InvoicePdfMixin:
    # ── Helpers compartilhados pela geração de PDF de invoice ──────
    def _get_work_type_lookup(self, cursor):
        """Retorna um dict {work_type_id: (nome, unidade)} pra montar as descrições dos jobs."""
        cursor.execute("SELECT ID, NAME, UNIT FROM work_types")
        return {wt_id: (name, unit or "") for wt_id, name, unit in cursor.fetchall()}

    def _describe_job_work_types(self, wt_fields, wt_lookup, show_qty):
        """wt_fields = as 32 colunas finais de _fetch_invoice_jobs (ID/QTY de cada
        slot de Demolition/Installation/Preparation/Others/Repair). Retorna uma
        lista de strings tipo 'Installation: Vinyl Plank (350 sqft)'."""
        slots = [
            ("DEMOLITION", wt_fields[0], wt_fields[1]), ("DEMOLITION", wt_fields[2], wt_fields[3]),
            ("DEMOLITION", wt_fields[4], wt_fields[5]), ("DEMOLITION", wt_fields[6], wt_fields[7]),
            ("INSTALLATION", wt_fields[8], wt_fields[9]), ("INSTALLATION", wt_fields[10], wt_fields[11]),
            ("INSTALLATION", wt_fields[12], wt_fields[13]), ("INSTALLATION", wt_fields[14], wt_fields[15]),
            ("PREPARATION", wt_fields[16], wt_fields[17]), ("PREPARATION", wt_fields[18], wt_fields[19]),
            ("PREPARATION", wt_fields[20], wt_fields[21]), ("PREPARATION", wt_fields[22], wt_fields[23]),
            ("OTHERS", wt_fields[24], wt_fields[25]), ("OTHERS", wt_fields[26], wt_fields[27]),
            ("REPARO", wt_fields[28], wt_fields[29]), ("REPARO", wt_fields[30], wt_fields[31]),
        ]
        lines = []
        for category, wt_id, qty in slots:
            if wt_id is None:
                continue
            name, unit = wt_lookup.get(wt_id, (f"Work Type #{wt_id}", ""))
            label = WORK_TYPE_CATEGORY_LABELS.get(category, category)
            if show_qty and qty is not None:
                lines.append(f"{label}: {name} ({float(qty):g} {unit})".strip())
            else:
                lines.append(f"{label}: {name}")
        return lines

    def _describe_work_type_list(self, items, wt_lookup, show_qty):
        """Mesmo formato de _describe_job_work_types, a partir da lista
        completa [(categoria, work_type_id, qty)]."""
        lines = []
        for category, wt_id, qty in items:
            name, unit = wt_lookup.get(wt_id, (f"Work Type #{wt_id}", ""))
            label = WORK_TYPE_CATEGORY_LABELS.get(category, category)
            if show_qty and qty is not None:
                lines.append(f"{label}: {name} ({float(qty):g} {unit})".strip())
            else:
                lines.append(f"{label}: {name}")
        return lines

    @staticmethod
    def _link_invoice_days(cursor, kind, invoice_id, jobs):
        """Grava quais dias entraram no invoice (o Projects Board usa isso
        pra mover o Job Code para Invoiced / Paid sozinho)."""
        day_ids = [r[-1] for r in jobs if r and r[-1]]
        if not day_ids:
            return
        try:
            cursor.executemany("INSERT IGNORE INTO invoice_work_days (INVOICE_TYPE, INVOICE_ID, WORK_DAY_ID) "
                               "VALUES (%s, %s, %s)", [(kind, invoice_id, d) for d in day_ids])
        except MySQLError:
            logging.getLogger("vl_flooring").exception("could not link invoice %s days", invoice_id)

    @staticmethod
    def _has_invoice_expenses_table(cursor):
        try:
            cursor.execute("SHOW TABLES LIKE 'invoice_expenses'")
            return cursor.fetchone() is not None
        except MySQLError:
            return False

    @staticmethod
    def _link_invoice_expenses(cursor, kind, invoice_id, expense_ids):
        """Grava quais despesas foram cobradas neste invoice (não entram de
        novo, por padrão, no próximo)."""
        expense_ids = [e for e in expense_ids if e]
        if not expense_ids:
            return
        try:
            cursor.executemany("INSERT IGNORE INTO invoice_expenses (INVOICE_TYPE, INVOICE_ID, EXPENSE_ID) "
                               "VALUES (%s, %s, %s)", [(kind, invoice_id, e) for e in expense_ids])
        except MySQLError:
            logging.getLogger("vl_flooring").exception("could not link invoice %s expenses", invoice_id)

    def _fetch_invoice_jobs(self, cursor, fk_col, fk_id, d_from, d_to, partner_table, partner_fk_col,
                             partner_name_col, job_ids=None):
        """Busca os jobs de uma entidade (contractor/company/client) no período,
        junto com todos os IDs/QTY de Work Type e o nome da 'contraparte'
        (ex: pro invoice de Contractor, mostra o Client de cada job).
        Se job_ids for passado, restringe só a esses IDs específicos (usado
        quando o usuário escolhe manualmente quais jobs entram no invoice)."""
        query = f"""
            SELECT wd.WORK_DATE, wd.JOB_ADDRESS, wd.JOB_ADDRESS2, COALESCE(city.CITY, '—'),
                   COALESCE(partner.{partner_name_col}, '—'), wd.VALUE, wd.DAY_SEQUENCE,
                   wd.DEMOLITION_1_ID, wd.DEMOLITION_1_QTY, wd.DEMOLITION_2_ID, wd.DEMOLITION_2_QTY,
                   wd.DEMOLITION_3_ID, wd.DEMOLITION_3_QTY, wd.DEMOLITION_4_ID, wd.DEMOLITION_4_QTY,
                   wd.INSTALLATION_1_ID, wd.INSTALLATION_1_QTY, wd.INSTALLATION_2_ID, wd.INSTALLATION_2_QTY,
                   wd.INSTALLATION_3_ID, wd.INSTALLATION_3_QTY, wd.INSTALLATION_4_ID, wd.INSTALLATION_4_QTY,
                   wd.PREPARATION_1_ID, wd.PREPARATION_1_QTY, wd.PREPARATION_2_ID, wd.PREPARATION_2_QTY,
                   wd.PREPARATION_3_ID, wd.PREPARATION_3_QTY, wd.PREPARATION_4_ID, wd.PREPARATION_4_QTY,
                   wd.OTHERS_1_ID, wd.OTHERS_1_QTY, wd.OTHERS_2_ID, wd.OTHERS_2_QTY,
                   wd.REPARO_1_ID, wd.REPARO_1_QTY, wd.REPARO_2_ID, wd.REPARO_2_QTY,
                   wd.ID
            FROM work_days wd
            LEFT JOIN cities city ON city.ID = wd.CITY_ID
            LEFT JOIN {partner_table} partner ON partner.ID = wd.{partner_fk_col}
            WHERE wd.{fk_col} = %s AND wd.WORK_DATE BETWEEN %s AND %s
        """
        params = [fk_id, d_from, d_to]
        if job_ids is not None and not job_ids:
            return []  # job_ids=[] explicitamente = nenhum job deve entrar (ex: invoice só com despesas)
        if job_ids:
            placeholders = ", ".join(["%s"] * len(job_ids))
            query += f" AND wd.ID IN ({placeholders})"
            params.extend(job_ids)
        query += " ORDER BY wd.WORK_DATE, COALESCE(wd.DAY_SEQUENCE, 999999), wd.ID"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        # lista completa de Work Types de cada dia (inclui os que não cabem
        # nas colunas antigas) — usada por _prepare_invoice_item_rows
        self._invoice_work_type_lists = self._work_types_by_day(cursor, [r[-1] for r in rows])
        return rows

    def _prepare_invoice_item_rows(self, jobs, wt_lookup, options, cell_style):
        """Monta as linhas prontas pra tabela de itens do PDF (Date | Address |
        Work Done | Value), respeitando as opções de agrupar por data e
        mostrar quantidade. Retorna (item_rows, jobs_total)."""
        show_qty = options["show_qty"]
        group = options["group_same_date"]

        parsed = []
        jobs_total = 0.0
        for row in jobs:
            work_date, address, address2, city, partner, value, day_sequence, *wt_fields = row
            day_id = wt_fields[32] if len(wt_fields) > 32 else None
            full_list = getattr(self, "_invoice_work_type_lists", {}).get(day_id)
            value = float(value or 0)
            jobs_total += value
            full_address = address or ""
            if address2:
                full_address += f", {address2}"
            if full_list:
                desc_lines = self._describe_work_type_list(full_list, wt_lookup, show_qty)
            else:
                desc_lines = self._describe_job_work_types(wt_fields, wt_lookup, show_qty)
            parsed.append({
                "date": work_date, "address": full_address, "city": city,
                "value": value, "desc_lines": desc_lines or ["—"],
            })

        def date_str(d):
            return d.strftime("%m/%d/%Y") if isinstance(d, date) else str(d)

        item_rows = []
        if not group:
            for j in parsed:
                addr_html = f"{j['address']}<br/>{j['city']}"
                desc_html = "<br/>".join(j["desc_lines"])
                item_rows.append([
                    date_str(j["date"]),
                    Paragraph(addr_html, cell_style),
                    Paragraph(desc_html, cell_style),
                    f"${j['value']:,.2f}",
                ])
            return item_rows, jobs_total

        grouped = {}
        order = []
        for j in parsed:
            if j["date"] not in grouped:
                grouped[j["date"]] = []
                order.append(j["date"])
            grouped[j["date"]].append(j)

        for work_date in order:
            entries = grouped[work_date]
            if len(entries) == 1:
                j = entries[0]
                addr_html = f"{j['address']}<br/>{j['city']}"
                desc_html = "<br/>".join(j["desc_lines"])
                total_value = j["value"]
            else:
                addr_html = "<br/>".join(
                    f"<b>Job {i+1}</b> — {e['address']} ({e['city']})" for i, e in enumerate(entries)
                )
                desc_html = "<br/>".join(
                    f"<b>Job {i+1}</b> — {'; '.join(e['desc_lines'])}" for i, e in enumerate(entries)
                )
                total_value = sum(e["value"] for e in entries)
            item_rows.append([
                date_str(work_date),
                Paragraph(addr_html, cell_style),
                Paragraph(desc_html, cell_style),
                f"${total_value:,.2f}",
            ])
        return item_rows, jobs_total

    def _draw_invoice_side_decorations(self, canvas, doc):
        """Desenha o fundo decorativo da página do invoice.

        Se existir um arquivo em INVOICE_BACKGROUND_PATH (assets/invoice_background.png),
        usa essa imagem como fundo — assim dá pra desenhar as margens/efeitos
        num programa de design e só substituir o arquivo, sem mexer em código.
        Caso contrário, cai no desenho padrão (faixas onduladas + círculos)."""
        page_w, page_h = letter

        if os.path.exists(INVOICE_BACKGROUND_PATH):
            canvas.saveState()
            canvas.drawImage(INVOICE_BACKGROUND_PATH, 0, 0, width=page_w, height=page_h,
                              mask='auto', preserveAspectRatio=False)
            canvas.restoreState()
            return

        canvas.saveState()
        navy = colors.HexColor(BRAND_NAVY)
        orange = colors.HexColor(BRAND_ORANGE)
        strip_w = 0.55 * inch

        # Círculo laranja à esquerda (fica atrás da faixa navy, só a "sobra" aparece)
        canvas.setFillColor(orange)
        canvas.circle(strip_w * 0.25, page_h * 0.74, 0.40 * inch, fill=1, stroke=0)
        # Círculo laranja à direita
        canvas.circle(page_w - strip_w * 0.25, page_h * 0.20, 0.36 * inch, fill=1, stroke=0)

        # Faixa ondulada azul-marinho à esquerda
        canvas.setFillColor(navy)
        left_path = canvas.beginPath()
        left_path.moveTo(0, 0)
        left_path.lineTo(0, page_h)
        left_path.curveTo(strip_w * 1.35, page_h * 0.88, strip_w * 0.25, page_h * 0.70, strip_w * 1.15, page_h * 0.55)
        left_path.curveTo(strip_w * 1.65, page_h * 0.44, strip_w * 0.15, page_h * 0.34, strip_w * 0.95, page_h * 0.20)
        left_path.curveTo(strip_w * 1.35, page_h * 0.10, strip_w * 0.35, page_h * 0.04, strip_w * 0.55, 0)
        left_path.close()
        canvas.drawPath(left_path, fill=1, stroke=0)

        # Faixa ondulada azul-marinho à direita (espelhada)
        right_path = canvas.beginPath()
        right_path.moveTo(page_w, 0)
        right_path.lineTo(page_w, page_h)
        right_path.curveTo(page_w - strip_w * 1.35, page_h * 0.82, page_w - strip_w * 0.25, page_h * 0.64,
                            page_w - strip_w * 1.15, page_h * 0.50)
        right_path.curveTo(page_w - strip_w * 1.65, page_h * 0.40, page_w - strip_w * 0.15, page_h * 0.30,
                            page_w - strip_w * 0.95, page_h * 0.15)
        right_path.curveTo(page_w - strip_w * 1.35, page_h * 0.07, page_w - strip_w * 0.35, page_h * 0.02,
                            page_w - strip_w * 0.55, 0)
        right_path.close()
        canvas.drawPath(right_path, fill=1, stroke=0)

        canvas.restoreState()

    # Valores de exemplo que vêm de fábrica em company_settings.py
    _PLACEHOLDER_BANK_MARKERS = ("123456789", "your bank name", "000000000")

    def _bank_info_is_placeholder(self, info=None):
        info = company_settings.COMPANY_BANK_INFO if info is None else info
        text = " ".join(str(info.get(k) or "") for k in ("account_no", "bank_details")).lower()
        return (not str(info.get("account_no") or "").strip()
                or any(marker in text for marker in self._PLACEHOLDER_BANK_MARKERS))

    def _confirm_bank_info_ready(self, parent=None):
        """Antes avisava que a invoice sairia com os dados bancários de
        exemplo. Agora, enquanto forem os de exemplo, a invoice simplesmente
        não mostra o bloco de conta (ver _invoice_payment_info_lines), então
        não há mais o que avisar. Mantido pra não mexer nos chamadores."""
        return True

    def _invoice_payment_info_lines(self, info=None, methods=None, details=None):
        """Linhas do bloco 'Payment Info' da invoice. Com os dados bancários
        de exemplo, esconde conta/routing e tira 'Bank Transfer' dos métodos
        aceitos; quando os dados reais forem salvos em Settings → Invoices,
        o bloco volta sozinho. Sem argumentos usa o que está salvo; o preview
        de Settings passa os valores digitados (ainda não salvos)."""
        from xml.sax.saxutils import escape
        info = company_settings.COMPANY_BANK_INFO if info is None else info
        methods = list(company_settings.COMPANY_PAYMENT_METHODS if methods is None else methods)
        if details is None:
            details = getattr(company_settings, "COMPANY_PAYMENT_DETAILS", {}) or {}
        lines = []
        if self._bank_info_is_placeholder(info):
            methods = [m for m in methods if m != "Bank Transfer"]
        else:
            lines += ["<b>Payment Info:</b>",
                      f"Account No: {escape(str(info.get('account_no') or ''))}",
                      f"A/C Name: {escape(str(info.get('account_name') or ''))}",
                      f"Bank Details: {escape(str(info.get('bank_details') or ''))}",
                      ""]
        # Cada forma com o seu detalhe (Settings → Invoices), ex. "Zelle: 941-382-7383".
        # Sem nenhum detalhe preenchido, continua numa linha só como antes.
        lines.append("<b>Accepted Methods:</b>")
        if any(details.get(m) for m in methods):
            for m in methods:
                d = (details.get(m) or "").strip()
                lines.append(f"{escape(m)}: {escape(d)}" if d else escape(m))
        else:
            lines.append(escape(", ".join(methods)))
        return lines

    def _build_invoice_pdf(self, filepath, invoice_number, entity_label, entity_name, entity_contact_lines,
                            d_from_qdate, d_to_qdate, item_rows, jobs_total, has_expenses, expenses_rows,
                            expenses_total, discount, addition, tax_percent, status,
                            payments=None, invoice_date=None):
        """Monta visualmente o PDF do invoice (logo + cores da marca Vertex Londe),
        com tabela de itens, ajustes de desconto/acréscimo/taxa, informações de
        pagamento e status. Usado por Contractor, Company e Client.
        payments=[(data, valor, forma)] → versão PAGA: selo PAID IN FULL e a
        lista de pagamentos recebidos (para mandar ao cliente depois de pago)."""
        styles = getSampleStyleSheet()
        cell_style = ParagraphStyle("cell", parent=styles["Normal"], fontSize=8.5, leading=11)
        right_style = ParagraphStyle("right", parent=styles["Normal"], alignment=TA_RIGHT)

        page_w, page_h = letter
        left_margin = 0.85 * inch
        right_margin = 0.85 * inch
        bottom_margin = 0.5 * inch
        top_margin_first = 0.5 * inch
        top_margin_later = 1.3 * inch  # espaço extra pra não bater na logo do fundo nas páginas seguintes

        frame_width = page_w - left_margin - right_margin
        frame_first = Frame(left_margin, bottom_margin, frame_width,
                             page_h - top_margin_first - bottom_margin, id="first")
        frame_later = Frame(left_margin, bottom_margin, frame_width,
                             page_h - top_margin_later - bottom_margin, id="later")

        doc = BaseDocTemplate(filepath, pagesize=letter,
                               leftMargin=left_margin, rightMargin=right_margin,
                               topMargin=top_margin_first, bottomMargin=bottom_margin)
        doc.addPageTemplates([
            PageTemplate(id="First", frames=[frame_first], onPage=self._draw_invoice_side_decorations),
            PageTemplate(id="Later", frames=[frame_later], onPage=self._draw_invoice_side_decorations),
        ])
        story = [NextPageTemplate("Later")]

        navy = colors.HexColor(BRAND_NAVY)
        has_custom_background = os.path.exists(INVOICE_BACKGROUND_PATH)

        # ── Cabeçalho: logo + nome à esquerda, "INVOICE" à direita ──
        # Se já existe uma imagem de fundo personalizada (assets/invoice_background.png),
        # assume-se que a marca/logo já está desenhada nela, então não desenha de novo aqui
        # (evita logo duplicado) — só reserva o espaço pra manter o alinhamento do título.
        if has_custom_background:
            company_block = Paragraph("", styles["Normal"])
        else:
            if os.path.exists(COMPANY_LOGO_PATH):
                logo_cell = Image(COMPANY_LOGO_PATH, width=0.55 * inch, height=0.55 * inch)
            else:
                logo_cell = Paragraph("", styles["Normal"])

            company_html = f"<b>{company_settings.COMPANY_NAME}</b><br/><font size=7 color='{BRAND_ORANGE}'>{company_settings.COMPANY_TAGLINE}</font>"
            company_block = Table([[logo_cell, Paragraph(company_html, styles["Normal"])]],
                                   colWidths=[0.65 * inch, 2.8 * inch])
            company_block.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (0, 0), 0),
            ]))

        header_table = Table(
            [[company_block, Paragraph(f"<font size=26 color='{BRAND_NAVY}'><b>INVOICE</b></font>", right_style)]],
            colWidths=[3.6 * inch, 2.8 * inch],
        )
        header_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        story.append(header_table)
        story.append(Spacer(1, 12))
        if not has_custom_background:
            story.append(HRFlowable(width="100%", thickness=1.2, color=colors.HexColor(BRAND_ORANGE)))
        story.append(Spacer(1, 10))

        # ── Invoice to / dados do invoice ──
        status_label = PAYMENT_STATUS_LABELS.get(status, status)
        invoice_to_html = "<br/>".join([f"<b>Invoice To ({entity_label}):</b>", f"<b>{entity_name}</b>"] + entity_contact_lines)
        info_html = "<br/>".join([
            f"<b>Invoice #:</b> {invoice_number}",
            f"<b>Invoice Date:</b> {(invoice_date or date.today()).strftime('%m/%d/%Y')}",
            f"<b>Period:</b> {d_from_qdate.toString('MM/dd/yyyy')} – {d_to_qdate.toString('MM/dd/yyyy')}",
            f"<b>Payment Status:</b> {status_label}",
        ])
        info_table = Table(
            [[Paragraph(invoice_to_html, styles["Normal"]), Paragraph(info_html, right_style)]],
            colWidths=[3.6 * inch, 2.8 * inch],
        )
        info_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        story.append(info_table)
        story.append(Spacer(1, 18))
        if payments:
            last_paid = max(d for d, _a, _m in payments)
            stamp = Table([[Paragraph(
                f"<para alignment='center'><font size=20 color='#2E7D32'><b>PAID IN FULL</b></font><br/>"
                f"<font size=9 color='#2E7D32'>on {last_paid.strftime('%m/%d/%Y')} — thank you!</font></para>",
                ParagraphStyle("paid_stamp", parent=styles["Normal"], leading=26))]], colWidths=[3.2 * inch])
            stamp.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 2, colors.HexColor("#2E7D32")),
                                       ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
            stamp.hAlign = "CENTER"
            story.append(stamp)
            story.append(Spacer(1, 16))

        # ── Tabela de itens (jobs) ──
        table_data = [["Date", "Address", "Work Done", "Value"]] + item_rows
        items_table = Table(table_data, colWidths=[0.9 * inch, 2.1 * inch, 2.6 * inch, 0.9 * inch], repeatRows=1)
        items_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), navy),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
            ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F9FC")]),
        ]))
        story.append(items_table)

        if not item_rows:
            story.append(Spacer(1, 8))
            story.append(Paragraph(f"No jobs found for this {entity_label.lower()} in the selected period.",
                                    styles["Normal"]))

        # ── Despesas (só aparece em invoice de Contractor) ──
        if has_expenses:
            story.append(Spacer(1, 16))
            story.append(Paragraph("<b>Expenses to Reimburse</b>", styles["Heading4"]))
            exp_table_data = [["Date", "Category", "Description", "Amount"]] + expenses_rows
            exp_table = Table(exp_table_data, colWidths=[0.9 * inch, 1.3 * inch, 3.3 * inch, 1.0 * inch])
            exp_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#37474F")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
                ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(exp_table)
            if not expenses_rows:
                story.append(Spacer(1, 6))
                story.append(Paragraph("No expenses linked to this contractor in the selected period.",
                                        styles["Normal"]))

        # ── Totais (com Discount / Additional Fee / Tax) ──
        tax_amount = (jobs_total + expenses_total - discount + addition) * (tax_percent / 100.0)
        grand_total = jobs_total + expenses_total - discount + addition + tax_amount

        totals_rows = [["Jobs Subtotal", f"${jobs_total:,.2f}"]]
        if has_expenses:
            totals_rows.append(["Expenses Subtotal", f"${expenses_total:,.2f}"])
        if discount:
            totals_rows.append(["Discount", f"-${discount:,.2f}"])
        if addition:
            totals_rows.append(["Additional Fee", f"${addition:,.2f}"])
        if tax_percent:
            totals_rows.append([f"Tax ({tax_percent:g}%)", f"${tax_amount:,.2f}"])
        totals_rows.append(["GRAND TOTAL", f"${grand_total:,.2f}"])

        totals_table = Table(totals_rows, colWidths=[1.8 * inch, 1.2 * inch])
        totals_table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 9.5),
            ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LINEABOVE", (0, -1), (-1, -1), 1, navy),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, -1), (-1, -1), 12),
            ("TEXTCOLOR", (0, -1), (-1, -1), navy),
        ]))
        story.append(Spacer(1, 16))
        wrapper = Table([["", totals_table]], colWidths=[3.5 * inch, 3.0 * inch])
        wrapper.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        story.append(wrapper)
        story.append(Spacer(1, 22))

        if payments:
            story.append(Paragraph("<b>Payments Received</b>", styles["Heading4"]))
            pay_rows = [["Date", "Method", "Amount"]] + [
                [d.strftime("%m/%d/%Y"), m or "", f"${float(a):,.2f}"] for d, a, m in payments]
            paid_total = sum(float(a) for _d, a, _m in payments)
            pay_rows.append(["", "Total paid", f"${paid_total:,.2f}"])
            pay_rows.append(["", "Balance due", f"${max(grand_total - paid_total, 0):,.2f}"])
            pay_table = Table(pay_rows, colWidths=[1.2 * inch, 3.3 * inch, 1.5 * inch])
            pay_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E7D32")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("GRID", (0, 0), (-1, -3), 0.5, colors.HexColor("#DDDDDD")),
                ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),
                ("ALIGN", (1, -2), (1, -1), "RIGHT"),
                ("FONTNAME", (0, -2), (-1, -1), "Helvetica-Bold"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(pay_table)
            story.append(Spacer(1, 22))

        # ── Payment Info + status ──
        bank_html = "<br/>".join(self._invoice_payment_info_lines())
        status_color_map = {"PENDING": "#E65100", "PARTIAL": "#1565C0", "RECEIVED": "#2E7D32"}
        status_color = status_color_map.get(status, BRAND_NAVY)
        status_html = (
            f"<para alignment='right'><b>Payment Status</b><br/>"
            f"<font size=13 color='{status_color}'><b>{status_label}</b></font></para>"
        )
        footer_info_table = Table(
            [[Paragraph(bank_html, styles["Normal"]), Paragraph(status_html, styles["Normal"])]],
            colWidths=[3.8 * inch, 2.6 * inch],
        )
        footer_info_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        story.append(footer_info_table)

        story.append(Spacer(1, 26))
        story.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor("#DDDDDD")))
        story.append(Spacer(1, 8))
        story.append(Paragraph(
            f"<font size=8 color='#6B7C93'>{company_settings.COMPANY_PHONE} &nbsp;|&nbsp; {company_settings.COMPANY_EMAIL} &nbsp;|&nbsp; {company_settings.COMPANY_WEBSITE}</font>",
            styles["Normal"],
        ))
        story.append(Paragraph("<font size=8 color='#6B7C93'>Thank you for your business with us.</font>",
                                styles["Normal"]))

        doc.build(story, canvasmaker=_InvoiceNumberedCanvas)
        return grand_total

    # tipo → (tabela, tabela do pagador, coluna do pagador, nome do pagador, contraparte: tabela/coluna/nome)
    _PAID_KIND = {
        "Contractor": ("contractor_invoices", "contractors", "CONTRACTOR_ID",
                       "COALESCE(NULLIF(r.COMPANY_NAME, ''), r.FULL_NAME)", "clients", "CLIENT_ID", "FULL_NAME"),
        "Company": ("company_invoices", "companies", "COMPANY_ID", "r.COMPANY_NAME", "clients", "CLIENT_ID", "FULL_NAME"),
        "Client": ("client_invoices", "clients", "CLIENT_ID", "r.FULL_NAME", "companies", "COMPANY_ID", "COMPANY_NAME"),
    }

    def _build_paid_invoice_pdf(self, kind, invoice_id):
        """Gera a versão PAGA de uma invoice (mesmos dias e despesas, selo PAID IN
        FULL e os pagamentos recebidos) na pasta de arquivos, em Invoices/<ano>.
        Devolve o caminho do PDF."""
        import arquivos
        if hasattr(self, "_paid_project_invoice_pdf"):
            project_pdf = self._paid_project_invoice_pdf(kind, invoice_id)
            if project_pdf:
                return project_pdf
        table, ref, fk, name_sql, ptable, pfk, pname = self._PAID_KIND[kind]
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            exp_col = "t.EXPENSES_TOTAL" if kind == "Contractor" else "0"
            cursor.execute(f"""
                SELECT t.{fk}, COALESCE({name_sql}, '—'), t.PERIOD_FROM, t.PERIOD_TO, {exp_col}, t.TOTAL_AMOUNT,
                       t.GENERATED_AT
                FROM {table} t LEFT JOIN {ref} r ON r.ID = t.{fk} WHERE t.ID = %s""", (invoice_id,))
            row = cursor.fetchone()
            if not row:
                raise RuntimeError(f"Invoice #{invoice_id} not found.")
            entity_id, entity_name, d_from, d_to, exp_total_saved, total, generated = row
            cursor.execute(f"SELECT EMAIL, PHONE_NUMBER FROM {ref} WHERE ID = %s", (entity_id,))
            contact = cursor.fetchone() or (None, None)
            contact_lines = [x for x in (contact[0], self._format_phone(contact[1]) if contact[1] else None) if x]
            cursor.execute("SELECT WORK_DAY_ID FROM invoice_work_days WHERE INVOICE_TYPE=%s AND INVOICE_ID=%s",
                           (kind, invoice_id))
            day_ids = [r[0] for r in cursor.fetchall()]
            wt_lookup = self._get_work_type_lookup(cursor)
            jobs = self._fetch_invoice_jobs(cursor, fk, entity_id, d_from, d_to, ptable, pfk, pname,
                                            job_ids=day_ids or None)
            expenses = []
            if kind == "Contractor" and float(exp_total_saved or 0) > 0:
                linked = []
                if self._has_invoice_expenses_table(cursor):
                    cursor.execute("SELECT EXPENSE_ID FROM invoice_expenses WHERE INVOICE_TYPE=%s AND INVOICE_ID=%s",
                                   (kind, invoice_id))
                    linked = [r[0] for r in cursor.fetchall()]
                if linked:
                    cursor.execute("SELECT EXPENSE_DATE, CATEGORY, DESCRIPTION, AMOUNT FROM expenses WHERE ID IN ("
                                   + ",".join(["%s"] * len(linked)) + ") ORDER BY EXPENSE_DATE", linked)
                else:
                    cursor.execute("SELECT EXPENSE_DATE, CATEGORY, DESCRIPTION, AMOUNT FROM expenses "
                                   "WHERE CONTRACTOR_ID=%s AND EXPENSE_DATE BETWEEN %s AND %s ORDER BY EXPENSE_DATE",
                                   (entity_id, d_from, d_to))
                expenses = cursor.fetchall()
            cursor.execute("SELECT PAID_DATE, AMOUNT, PAYMENT_METHOD FROM payments WHERE INVOICE_TYPE=%s "
                           "AND INVOICE_ID=%s ORDER BY PAID_DATE, ID", (kind, invoice_id))
            payments = cursor.fetchall()
        finally:
            cursor.close()
            conn.close()
        if not payments:
            raise RuntimeError(f"Invoice #{invoice_id} has no payments yet.")

        styles = getSampleStyleSheet()
        cell_style = ParagraphStyle("cell_p", parent=styles["Normal"], fontSize=8.5, leading=11)
        options = {"group_same_date": True, "show_qty": True}
        item_rows, jobs_total = self._prepare_invoice_item_rows(jobs, wt_lookup, options, cell_style)
        expenses_rows, expenses_total = [], 0.0
        for exp_date, category, description, amount in expenses:
            expenses_total += float(amount or 0)
            expenses_rows.append([exp_date.strftime("%m/%d/%Y"), category, description or "",
                                  f"${float(amount or 0):,.2f}"])
        # o total tem que ser o mesmo da invoice original (desconto/acréscimo/taxa viram um ajuste)
        diff = round(float(total or 0) - (jobs_total + expenses_total), 2)
        discount, addition = (-diff, 0.0) if diff < 0 else (0.0, diff)
        safe = "".join(c if c.isalnum() or c in " _-" else "" for c in entity_name).strip().replace(" ", "_")
        path = os.path.join(arquivos.folder("invoices", str(d_to.year)),
                            f"Invoice_{invoice_id}_{safe}_{d_from}_to_{d_to}_PAID.pdf")
        gen = generated.date() if hasattr(generated, "date") else generated
        self._build_invoice_pdf(
            path, invoice_id, kind, entity_name, contact_lines,
            QDate(d_from.year, d_from.month, d_from.day), QDate(d_to.year, d_to.month, d_to.day),
            item_rows, jobs_total, kind == "Contractor" and bool(expenses_rows), expenses_rows, expenses_total,
            discount, addition, 0.0, "RECEIVED", payments=payments, invoice_date=gen)
        return path

    def _generate_single_contractor_invoice(self, contractor_id, contractor_name,
                                             d_from, d_to, d_from_qdate, d_to_qdate, out_dir, options,
                                             job_ids=None, expense_ids=None):
        """Monta o PDF de invoice de um único contractor (jobs + despesas do
        período) e salva um registro no histórico (contractor_invoices).
        Se job_ids/expense_ids forem passados, inclui só esses itens
        específicos (selecionados manualmente pelo usuário)."""
        conn = self._get_connection()
        cursor = conn.cursor()

        wt_lookup = self._get_work_type_lookup(cursor)
        jobs = self._fetch_invoice_jobs(cursor, "CONTRACTOR_ID", contractor_id, d_from, d_to,
                                         "clients", "CLIENT_ID", "FULL_NAME", job_ids=job_ids)

        if expense_ids is not None and not expense_ids:
            expenses = []  # usuário desmarcou todas as despesas — nenhuma entra no invoice
        else:
            expense_query = (
                "SELECT EXPENSE_DATE, CATEGORY, DESCRIPTION, AMOUNT, ID FROM expenses "
                "WHERE CONTRACTOR_ID = %s AND EXPENSE_DATE BETWEEN %s AND %s"
            )
            expense_params = [contractor_id, d_from, d_to]
            if expense_ids:
                placeholders = ", ".join(["%s"] * len(expense_ids))
                expense_query += f" AND ID IN ({placeholders})"
                expense_params.extend(expense_ids)
            elif self._has_invoice_expenses_table(cursor):
                # sem seleção manual: só as despesas que ainda não foram cobradas
                expense_query += " AND ID NOT IN (SELECT EXPENSE_ID FROM invoice_expenses)"
            expense_query += " ORDER BY EXPENSE_DATE"
            cursor.execute(expense_query, expense_params)
            expenses = cursor.fetchall()

        cursor.execute("SELECT EMAIL, PHONE_NUMBER, CITY_ID, STATE_ID FROM contractors WHERE ID = %s", (contractor_id,))
        contact_row = cursor.fetchone()
        contact_lines = []
        if contact_row:
            email, phone, _, _ = contact_row
            if email:
                contact_lines.append(email)
            if phone:
                contact_lines.append(self._format_phone(phone))

        safe_name = "".join(c if c.isalnum() or c in " _-" else "" for c in contractor_name).strip()
        filename = f"Invoice_{safe_name}_{d_from}_to_{d_to}.pdf".replace(" ", "_")
        filepath = f"{out_dir}/{filename}"

        styles = getSampleStyleSheet()
        cell_style = ParagraphStyle("cell_c", parent=styles["Normal"], fontSize=8.5, leading=11)
        item_rows, jobs_total = self._prepare_invoice_item_rows(jobs, wt_lookup, options, cell_style)

        expenses_rows = []
        expenses_total = 0.0
        for exp_date, category, description, amount, *_rest in expenses:
            amount = float(amount or 0)
            expenses_total += amount
            exp_date_str = exp_date.strftime("%m/%d/%Y") if isinstance(exp_date, date) else str(exp_date)
            expenses_rows.append([exp_date_str, category, description or "", f"${amount:,.2f}"])

        # Insere primeiro (status inicial PENDING) pra ter o número do invoice
        cursor.execute(
            """
            INSERT INTO contractor_invoices
                (CONTRACTOR_ID, PERIOD_FROM, PERIOD_TO, JOBS_TOTAL, EXPENSES_TOTAL,
                 TOTAL_AMOUNT, STATUS, PDF_PATH)
            VALUES (%s, %s, %s, %s, %s, %s, 'PENDING', '')
            """,
            (contractor_id, d_from, d_to, jobs_total, expenses_total, jobs_total + expenses_total),
        )
        invoice_id = cursor.lastrowid
        self._link_invoice_days(cursor, "Contractor", invoice_id, jobs)
        self._link_invoice_expenses(cursor, "Contractor", invoice_id, [r[4] for r in expenses])

        # Só mostra a seção de despesas se sobrou pelo menos alguma despesa a
        # incluir (respeita o checkbox "Include Expenses" e a seleção manual).
        has_expenses = bool(expenses) or expense_ids is None

        grand_total = self._build_invoice_pdf(
            filepath, invoice_id, "Contractor", contractor_name, contact_lines,
            d_from_qdate, d_to_qdate, item_rows, jobs_total, has_expenses, expenses_rows, expenses_total,
            options["discount"], options["addition"], options["tax_percent"], "PENDING",
        )

        cursor.execute(
            "UPDATE contractor_invoices SET TOTAL_AMOUNT = %s, PDF_PATH = %s WHERE ID = %s",
            (grand_total, filepath, invoice_id),
        )
        conn.commit()
        cursor.close()
        conn.close()

    def _generate_single_company_invoice(self, company_id, company_name,
                                          d_from, d_to, d_from_qdate, d_to_qdate, out_dir, options,
                                          job_ids=None, expense_ids=None):
        """Monta o PDF de invoice de uma Company (soma dos Jobs feitos para ela
        no período) e salva um registro no histórico (company_invoices).
        Diferente do invoice de Contractor, aqui não há reembolso de despesas."""
        conn = self._get_connection()
        cursor = conn.cursor()

        wt_lookup = self._get_work_type_lookup(cursor)
        jobs = self._fetch_invoice_jobs(cursor, "COMPANY_ID", company_id, d_from, d_to,
                                         "clients", "CLIENT_ID", "FULL_NAME", job_ids=job_ids)

        cursor.execute("SELECT EMAIL, PHONE_NUMBER FROM companies WHERE ID = %s", (company_id,))
        contact_row = cursor.fetchone()
        contact_lines = []
        if contact_row:
            email, phone = contact_row
            if email:
                contact_lines.append(email)
            if phone:
                contact_lines.append(self._format_phone(phone))

        safe_name = "".join(c if c.isalnum() or c in " _-" else "" for c in company_name).strip()
        filename = f"Invoice_{safe_name}_{d_from}_to_{d_to}.pdf".replace(" ", "_")
        filepath = f"{out_dir}/{filename}"

        styles = getSampleStyleSheet()
        cell_style = ParagraphStyle("cell_co", parent=styles["Normal"], fontSize=8.5, leading=11)
        item_rows, jobs_total = self._prepare_invoice_item_rows(jobs, wt_lookup, options, cell_style)

        cursor.execute(
            """
            INSERT INTO company_invoices
                (COMPANY_ID, PERIOD_FROM, PERIOD_TO, JOBS_TOTAL, TOTAL_AMOUNT, STATUS, PDF_PATH)
            VALUES (%s, %s, %s, %s, %s, 'PENDING', '')
            """,
            (company_id, d_from, d_to, jobs_total, jobs_total),
        )
        invoice_id = cursor.lastrowid
        self._link_invoice_days(cursor, "Company", invoice_id, jobs)

        grand_total = self._build_invoice_pdf(
            filepath, invoice_id, "Company", company_name, contact_lines,
            d_from_qdate, d_to_qdate, item_rows, jobs_total, False, [], 0.0,
            options["discount"], options["addition"], options["tax_percent"], "PENDING",
        )

        cursor.execute(
            "UPDATE company_invoices SET TOTAL_AMOUNT = %s, PDF_PATH = %s WHERE ID = %s",
            (grand_total, filepath, invoice_id),
        )
        conn.commit()
        cursor.close()
        conn.close()

    def _generate_single_client_invoice(self, client_id, client_name,
                                         d_from, d_to, d_from_qdate, d_to_qdate, out_dir, options,
                                         job_ids=None, expense_ids=None):
        """Monta o PDF de invoice de um Client (soma dos Jobs feitos para ele
        no período) e salva um registro no histórico (client_invoices)."""
        conn = self._get_connection()
        cursor = conn.cursor()

        wt_lookup = self._get_work_type_lookup(cursor)
        jobs = self._fetch_invoice_jobs(cursor, "CLIENT_ID", client_id, d_from, d_to,
                                         "companies", "COMPANY_ID", "COMPANY_NAME", job_ids=job_ids)

        cursor.execute("SELECT EMAIL, PHONE_NUMBER FROM clients WHERE ID = %s", (client_id,))
        contact_row = cursor.fetchone()
        contact_lines = []
        if contact_row:
            email, phone = contact_row
            if email:
                contact_lines.append(email)
            if phone:
                contact_lines.append(self._format_phone(phone))

        safe_name = "".join(c if c.isalnum() or c in " _-" else "" for c in client_name).strip()
        filename = f"Invoice_{safe_name}_{d_from}_to_{d_to}.pdf".replace(" ", "_")
        filepath = f"{out_dir}/{filename}"

        styles = getSampleStyleSheet()
        cell_style = ParagraphStyle("cell_cl", parent=styles["Normal"], fontSize=8.5, leading=11)
        item_rows, jobs_total = self._prepare_invoice_item_rows(jobs, wt_lookup, options, cell_style)

        cursor.execute(
            """
            INSERT INTO client_invoices
                (CLIENT_ID, PERIOD_FROM, PERIOD_TO, JOBS_TOTAL, TOTAL_AMOUNT, STATUS, PDF_PATH)
            VALUES (%s, %s, %s, %s, %s, 'PENDING', '')
            """,
            (client_id, d_from, d_to, jobs_total, jobs_total),
        )
        invoice_id = cursor.lastrowid
        self._link_invoice_days(cursor, "Client", invoice_id, jobs)

        grand_total = self._build_invoice_pdf(
            filepath, invoice_id, "Client", client_name, contact_lines,
            d_from_qdate, d_to_qdate, item_rows, jobs_total, False, [], 0.0,
            options["discount"], options["addition"], options["tax_percent"], "PENDING",
        )

        cursor.execute(
            "UPDATE client_invoices SET TOTAL_AMOUNT = %s, PDF_PATH = %s WHERE ID = %s",
            (grand_total, filepath, invoice_id),
        )
        conn.commit()
        cursor.close()
        conn.close()
