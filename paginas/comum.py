# -*- coding: utf-8 -*-
"""
Funções usadas por várias telas: conexão com o banco, formatação de telefone/ZIP,
combos de cidade/estado e exportação genérica para Excel/PDF.

Métodos da MainWindow (mixin) — veja main_.py.
"""

from app_common import *  # noqa: F401,F403


class UtilsMixin:
    @staticmethod
    def _normalize_keyword_text(text):
        """Remove acentos e baixa a caixa, pra comparar palavras-chave sem
        se importar com 'endereço' vs 'endereco', maiúsculas, etc."""
        if not text:
            return ""
        no_accents = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
        return no_accents.lower()

    @staticmethod
    def _format_zip(raw):
        """Formata um Zip Code no padrão 00000-0000 (ZIP+4). Se tiver só 5
        dígitos, devolve os 5 dígitos sem traço (ZIP simples, também válido).
        Qualquer outra quantidade devolve o valor original sem mexer."""
        if not raw:
            return ""
        digits = "".join(ch for ch in str(raw) if ch.isdigit())
        if len(digits) == 9:
            return f"{digits[0:5]}-{digits[5:9]}"
        if len(digits) == 5:
            return digits
        if len(digits) == 0:
            return ""
        return raw

    def _limit_zip_digits(self, field):
        """Impede digitar mais de 9 números no campo de Zip Code (sem travar
        a formatação '00000-0000' que aparece depois)."""
        text = field.text()
        digits = "".join(ch for ch in text if ch.isdigit())
        if len(digits) > 9:
            kept_digits = 0
            new_text = []
            for ch in text:
                if ch.isdigit():
                    if kept_digits >= 9:
                        continue
                    kept_digits += 1
                new_text.append(ch)
            field.blockSignals(True)
            field.setText("".join(new_text))
            field.blockSignals(False)

    def _setup_zip_code_fields(self):
        """Configura os campos de Zip Code com placeholder cinza mostrando o
        formato ZIP+4, limita a 9 números, e formata automaticamente assim
        que o usuário sai do campo."""
        zip_fields = [
            self.ui.txt_client_zip, self.ui.txt_company_zip,
            self.ui.txt_contractor_zip, self.ui.txt_customer_zip,
        ]
        for field in zip_fields:
            field.setPlaceholderText("00000-0000")
            field.textChanged.connect(lambda _text, f=field: self._limit_zip_digits(f))
            field.editingFinished.connect(lambda f=field: f.setText(self._format_zip(f.text())))

    def _limit_phone_digits(self, field):
        """Impede digitar mais de 10 números no campo de telefone (sem
        travar a formatação '(000) 000 - 0000' que aparece depois)."""
        text = field.text()
        digits = "".join(ch for ch in text if ch.isdigit())
        if len(digits) > 10:
            # mantém só os primeiros 10 dígitos, preservando o que não é dígito
            kept_digits = 0
            new_text = []
            for ch in text:
                if ch.isdigit():
                    if kept_digits >= 10:
                        continue
                    kept_digits += 1
                new_text.append(ch)
            field.blockSignals(True)
            field.setText("".join(new_text))
            field.blockSignals(False)

    def _setup_phone_input_masks(self):
        """Configura os campos de telefone com um placeholder cinza (igual o
        do email) mostrando o formato esperado, limita a 10 números, e
        formata automaticamente assim que o usuário sai do campo (não trava
        a digitação com máscara dura, só arruma no final)."""
        phone_fields = [
            self.ui.txt_client_phone, self.ui.txt_client_phone_2,
            self.ui.txt_company_phone, self.ui.txt_company_phone2,
            self.ui.txt_contractor_company_phone, self.ui.txt_contractor_company_phone2,
            self.ui.txt_contractor_phone, self.ui.txt_contractor_phone2,
            self.ui.txt_customer_phone, self.ui.txt_customer_phone2,
            self.ui.txt_user_phone, self.ui.txt_user_phone2,
        ]
        for field in phone_fields:
            field.setPlaceholderText("(000) 000 - 0000")
            field.textChanged.connect(lambda _text, f=field: self._limit_phone_digits(f))
            field.editingFinished.connect(lambda f=field: f.setText(self._format_phone(f.text())))

    def _setup_autocomplete_combos(self):
        """Configura busca por qualquer parte do texto (não só pelo início) no
        combo editável de endereço e no campo de nome do cliente — dá a
        sensação de autopreenchimento de verdade enquanto digita."""
        completer = self.ui.cmb_client_address.completer()
        if completer:
            completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        # Client Name agora é um campo de texto simples (sem "select"), com
        # autocomplete próprio ligado à lista de clientes já cadastrados.
        self._client_name_to_id = {}
        self._client_name_completer = QCompleter([], self)
        self._client_name_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._client_name_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._client_name_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.ui.txt_client_name.setCompleter(self._client_name_completer)

    @staticmethod
    def _format_phone(raw):
        """Formata um telefone no padrão (000) 000 - 0000, a partir de
        qualquer coisa que o usuário tenha digitado (com ou sem formatação
        prévia, inclusive os campos com máscara). Se não tiver exatamente 10
        dígitos, devolve vazio (campo em branco) ou o valor original sem
        mexer, conforme o caso (evita quebrar números com extensão ou
        internacionais)."""
        if not raw:
            return ""
        digits = "".join(ch for ch in str(raw) if ch.isdigit())
        if len(digits) == 10:
            return f"({digits[0:3]}) {digits[3:6]} - {digits[6:10]}"
        if len(digits) == 0:
            return ""
        return raw

    def _get_connection(self):
        """Abre e retorna uma nova conexao com o MySQL usando self.db_config."""
        if mysql is None:
            raise RuntimeError(
                "mysql-connector-python não instalado. Rode: pip install mysql-connector-python"
            )
        conn = mysql.connector.connect(**self.db_config)
        # Perfil "Viewer": o próprio MySQL recusa qualquer gravação nesta
        # conexão (segunda barreira, além dos botões desativados).
        if getattr(self, "_db_read_only", False):
            cur = conn.cursor()
            cur.execute("SET SESSION TRANSACTION READ ONLY")
            cur.close()
            return conn
        # Depois do login, toda alteração passa a ir pro histórico (audit_log)
        username = getattr(self, "_current_username", None)
        if username:
            return historico.AuditConnection(conn, username)
        return conn

    def _reload_city_combo_for_state(self, city_combo, state_id, keep_city_id=None):
        """Recarrega um combo de City mostrando só as cidades daquele State
        (usa DISTINCT no nome pra não mostrar cidades duplicadas mesmo que
        existam linhas repetidas na tabela). Se keep_city_id for passado,
        tenta manter esse City selecionado depois de recarregar."""
        city_combo.blockSignals(True)
        city_combo.clear()

        if not state_id:
            city_combo.addItem("— Select a State first —", None)
            city_combo.blockSignals(False)
            return

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            # MIN(ID) como representante de cada nome de cidade repetido nesse State
            cursor.execute(
                """
                SELECT MIN(ID), CITY FROM cities
                WHERE ID_STATE = %s
                GROUP BY CITY
                ORDER BY CITY
                """,
                (state_id,),
            )
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            print(f"[Aviso] Não foi possível carregar cidades: {e}")
            rows = []

        city_combo.addItem("— Select —", None)
        for city_id, city_name in rows:
            city_combo.addItem(city_name, city_id)

        if keep_city_id is not None:
            idx = city_combo.findData(keep_city_id)
            if idx >= 0:
                city_combo.setCurrentIndex(idx)

        city_combo.blockSignals(False)

    def _on_client_state_changed(self):
        self._reload_city_combo_for_state(self.ui.cmb_client_city, self.ui.cmb_client_state.currentData())

    def _on_company_state_changed(self):
        self._reload_city_combo_for_state(self.ui.cmb_company_city, self.ui.cmb_company_state.currentData())

    def _on_contractor_state_changed(self):
        self._reload_city_combo_for_state(self.ui.cmb_contractor_city, self.ui.cmb_contractor_state.currentData())

    def _on_customer_state_changed(self):
        self._reload_city_combo_for_state(self.ui.cmb_customer_city, self.ui.cmb_customer_state.currentData())

    def _set_combo_by_data(self, combo, value, by_text=False):
        """Seleciona um item do combo pelo valor salvo em itemData (ou pelo texto, se by_text=True)."""
        if value is None:
            combo.setCurrentIndex(0)
            return
        if by_text:
            idx = combo.findText(str(value))
        else:
            idx = combo.findData(value)
        combo.setCurrentIndex(idx if idx >= 0 else 0)

    def _table_column_exists(self, table, column):
        """Confere (com cache em memória, uma vez por execução do app) se
        uma coluna existe numa tabela — usado pra decidir se um campo novo
        que ainda depende de uma migração pendente (ex: HELPER_ID) pode ser
        incluído com segurança num INSERT/UPDATE, sem travar o resto do
        registro (ex: o Job inteiro) se a migração ainda não rodou. `table`
        nunca vem de entrada do usuário — é sempre um nome fixo escrito no
        código, então montar a query com f-string aqui é seguro."""
        if not hasattr(self, "_column_exists_cache"):
            self._column_exists_cache = {}
        cache_key = f"{table}.{column}"
        if cache_key in self._column_exists_cache:
            return self._column_exists_cache[cache_key]
        exists = False
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(f"SHOW COLUMNS FROM {table} LIKE %s", (column,))
            exists = cursor.fetchone() is not None
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError):
            exists = False
        self._column_exists_cache[cache_key] = exists
        return exists

    def _export_table_to_excel(self, table_widget, suggested_name):
        """Exporta o conteúdo atual (o que está na tela, já filtrado/pesquisado)
        de qualquer QTableWidget do sistema para um arquivo Excel (.xlsx)."""
        path, _ = QFileDialog.getSaveFileName(self, "Export to Excel", suggested_name, "Excel Files (*.xlsx)")
        if not path:
            return
        if not path.lower().endswith(".xlsx"):
            path += ".xlsx"
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment
            from openpyxl.utils import get_column_letter
        except ImportError:
            QMessageBox.critical(self, "Missing Dependency",
                                  "The 'openpyxl' package is not installed.\n\nRun:\npip install openpyxl")
            return

        try:
            headers = [table_widget.horizontalHeaderItem(c).text() if table_widget.horizontalHeaderItem(c) else ""
                       for c in range(table_widget.columnCount())]
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.append(headers)
            header_fill = PatternFill(start_color="1C2B3A", end_color="1C2B3A", fill_type="solid")
            for c in range(1, len(headers) + 1):
                cell = ws.cell(row=1, column=c)
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal="center")

            for r in range(table_widget.rowCount()):
                row_vals = []
                for c in range(table_widget.columnCount()):
                    item = table_widget.item(r, c)
                    row_vals.append(item.text() if item else "")
                ws.append(row_vals)

            for c, header in enumerate(headers, start=1):
                ws.column_dimensions[get_column_letter(c)].width = max(12, len(header) + 4)
            ws.freeze_panes = "A2"
            if ws.max_row > 1:
                ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{ws.max_row}"

            wb.save(path)
            QMessageBox.information(self, "Export Complete", f"Saved to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Could not export to Excel:\n{e}")

    def _export_table_to_pdf(self, table_widget, suggested_name, title):
        """Exporta o conteúdo atual (o que está na tela, já filtrado/pesquisado)
        de qualquer QTableWidget do sistema para um PDF simples em paisagem."""
        if not REPORTLAB_AVAILABLE:
            QMessageBox.critical(self, "Missing Dependency",
                                  "The 'reportlab' package is not installed.\n\nRun:\npip install reportlab")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export to PDF", suggested_name, "PDF Files (*.pdf)")
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"

        try:
            from reportlab.lib.pagesizes import landscape

            headers = [table_widget.horizontalHeaderItem(c).text() if table_widget.horizontalHeaderItem(c) else ""
                       for c in range(table_widget.columnCount())]
            data = [headers]
            for r in range(table_widget.rowCount()):
                row_vals = []
                for c in range(table_widget.columnCount()):
                    item = table_widget.item(r, c)
                    row_vals.append(item.text() if item else "")
                data.append(row_vals)

            page_size = landscape(letter)
            styles = getSampleStyleSheet()
            doc = SimpleDocTemplate(path, pagesize=page_size, topMargin=0.4 * inch, bottomMargin=0.4 * inch,
                                     leftMargin=0.4 * inch, rightMargin=0.4 * inch)
            story = [Paragraph(f"<b>{title}</b>", styles["Title"]),
                     Paragraph(f"Exported {date.today().strftime('%m/%d/%Y')}", styles["Normal"]),
                     Spacer(1, 12)]

            n_cols = max(len(headers), 1)
            avail_width = page_size[0] - 0.8 * inch
            col_width = avail_width / n_cols
            pdf_table = Table(data, colWidths=[col_width] * n_cols, repeatRows=1)
            pdf_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(BRAND_NAVY)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DDDDDD")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F9FC")]),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            story.append(pdf_table)
            doc.build(story)
            QMessageBox.information(self, "Export Complete", f"Saved to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Could not export to PDF:\n{e}")
