# -*- coding: utf-8 -*-
"""
Job Records: lista de Work Days, formulário do Job, Job Code, materiais usados,
agenda (Schedule) e Split Daily Total.

Métodos da MainWindow (mixin) — veja main_.py.
"""

from app_common import *  # noqa: F401,F403


class JobsMixin:
    def _refresh_client_name_completer(self):
        """Recarrega a lista de nomes de clientes usada no autocomplete do
        campo Client Name, e o mapa nome->ID usado pra resolver o cliente ao salvar."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT ID, FULL_NAME FROM clients ORDER BY FULL_NAME")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError):
            rows = []
        self._client_name_to_id = {name.strip().lower(): cid for cid, name in rows if name}
        self._client_name_completer.setModel(QStringListModel([name for _, name in rows]))

    def _go_to_new_expense_from_job(self):
        """Atalho no formulário de Job: leva direto pra tela New/Edit Expense
        (dentro de Receivables), já pronta pra um novo lançamento."""
        # Guarda o Job Code e a data ANTES de trocar de página: a despesa já
        # nasce ligada a este job (antes vinha sem Job Code, e o Job Profit /
        # View Project nunca descontavam despesas lançadas por aqui).
        typed_code = self.ui.cmb_job_code.currentText().strip().upper()
        project_id = self._job_code_to_id.get(typed_code)
        work_date = self.ui.date_work_date.date()
        self.new_expense_record()
        self._go_to_page(5, self.ui.btn_nav_receivables)
        self.ui.tabWidget_receivables.setCurrentWidget(self.ui.tab_expenses_master)
        if project_id:
            self._refresh_expense_job_code_combo()
            self._set_combo_by_data(self.ui.cmb_expense_job_code, project_id)
            self.ui.date_expense.setDate(work_date)
            from paginas.moderno import show_toast
            show_toast(f"New expense linked to {typed_code}.", "info", self)

    def _setup_job_form_dirty_tracking(self):
        """Conecta todos os campos do formulário New/Edit Job (incluindo a
        gaveta de Client Info) a um sinal genérico que marca o formulário como
        'com alterações não salvas', pra poder avisar antes de trocar de
        página sem salvar. Os campos de 'adicionar material' ficam de fora,
        porque eles já salvam na hora (botão Add), não fazem parte do Save
        principal do Job."""
        excluded = (self.ui.cmb_material_product, self.ui.dspn_material_qty)
        watched_containers = (self.ui.frame_job_card, self.ui.frame_client_drawer)
        for container in watched_containers:
            for child in container.findChildren(QLineEdit):
                if child in excluded:
                    continue
                child.textChanged.connect(self._mark_job_form_dirty)
            for child in container.findChildren(QComboBox):
                if child in excluded:
                    continue
                child.currentIndexChanged.connect(self._mark_job_form_dirty)
            for child in container.findChildren(QDoubleSpinBox):
                if child in excluded:
                    continue
                child.valueChanged.connect(self._mark_job_form_dirty)
            for child in container.findChildren(QDateEdit):
                if child in excluded:
                    continue
                child.dateChanged.connect(self._mark_job_form_dirty)
            for child in container.findChildren(QTextEdit):
                if child in excluded:
                    continue
                child.textChanged.connect(self._mark_job_form_dirty)

    def _mark_job_form_dirty(self, *_args):
        """Slot genérico chamado quando qualquer campo do Job form muda —
        ignora mudanças feitas programaticamente durante o carregamento."""
        if not self._loading_job_form:
            self._job_form_dirty = True

    def _on_job_tab_changed(self, index):
        """Garante que a data sempre mostre 'hoje' ao entrar na aba de novo registro
        (só corrige quando não há nenhum job carregado pra edição). Também avisa
        se está saindo do formulário New/Edit Job com alterações não salvas."""
        previous_index = getattr(self, "_previous_job_tab_index", 0)
        previous_widget = self.ui.tabWidget_jobs.widget(previous_index)

        if (previous_widget is self.ui.tab_jobs_master and index != previous_index
                and getattr(self, "_job_form_dirty", False)):
            confirm = QMessageBox.question(
                self, "Unsaved changes",
                "You have unsaved changes in this Job. Leave without saving?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if confirm != QMessageBox.StandardButton.Yes:
                self.ui.tabWidget_jobs.setCurrentIndex(previous_index)
                return
            self._job_form_dirty = False  # usuário confirmou que quer descartar

        self._previous_job_tab_index = index

        if self.ui.tabWidget_jobs.widget(index) is self.ui.tab_jobs_master and not self._current_job_id:
            self.ui.date_work_date.setDate(date.today())

    def _setup_work_type_unit_display(self):
        """Conecta cada combo de tipo de trabalho ao seu label de unidade (PCS/SQFT/LFT),
        atualizando automaticamente quando o usuário troca a seleção."""
        self._work_type_units = getattr(self, "_work_type_units", {})

        pairs = [
            (self.ui.cmb_demolition, self.ui.lbl_unit_demolition),
            (self.ui.cmb_demolition_2, self.ui.lbl_unit_demolition_2),
            (self.ui.cmb_demolition_3, self.ui.lbl_unit_demolition_3),
            (self.ui.cmb_demolition_4, self.ui.lbl_unit_demolition_4),
            (self.ui.cmb_preparation, self.ui.lbl_unit_preparation),
            (self.ui.cmb_preparation_2, self.ui.lbl_unit_preparation_2),
            (self.ui.cmb_preparation_3, self.ui.lbl_unit_preparation_3),
            (self.ui.cmb_preparation_4, self.ui.lbl_unit_preparation_4),
            (self.ui.cmb_installation, self.ui.lbl_unit_installation),
            (self.ui.cmb_installation_2, self.ui.lbl_unit_installation_2),
            (self.ui.cmb_installation_3, self.ui.lbl_unit_installation_3),
            (self.ui.cmb_installation_4, self.ui.lbl_unit_installation_4),
            (self.ui.cmb_others, self.ui.lbl_unit_others),
            (self.ui.cmb_others_2, self.ui.lbl_unit_others_2),
            (self.ui.cmb_reparo, self.ui.lbl_unit_reparo),
            (self.ui.cmb_reparo_2, self.ui.lbl_unit_reparo_2),
        ]

        def make_handler(combo, label):
            """Cria (via closure) o handler que atualiza o label de unidade sempre que o combo de tipo de trabalho mudar de selecao."""
            def handler():
                """Le o tipo de trabalho selecionado no combo e mostra a unidade correspondente no label ao lado (ou '-' se nada selecionado)."""
                type_id = combo.currentData()
                unit = self._work_type_units.get(type_id)
                label.setText(unit if unit else "—")
            return handler

        self._unit_handlers = []  # mantém referência viva (evita garbage collection)
        for combo, label in pairs:
            handler = make_handler(combo, label)
            combo.currentIndexChanged.connect(handler)
            self._unit_handlers.append(handler)

    def _setup_work_type_category_locks(self):
        """Cada checkbox de categoria (Demolition/Preparation/Installation/Others/Reparo)
        controla se os combos/quantidades daquela categoria podem ser editados.
        Começam desmarcados = campos bloqueados (esmaecidos) até o usuário marcar."""
        groups = {
            self.ui.chk_demolition: [
                self.ui.cmb_demolition, self.ui.cmb_demolition_2,
                self.ui.cmb_demolition_3, self.ui.cmb_demolition_4,
                self.ui.dspn_demolition, self.ui.dspn_demolition_2,
                self.ui.dspn_demolition_3, self.ui.dspn_demolition_4,
                self.ui.lbl_unit_demolition, self.ui.lbl_unit_demolition_2,
                self.ui.lbl_unit_demolition_3, self.ui.lbl_unit_demolition_4,
            ],
            self.ui.chk_preparation: [
                self.ui.cmb_preparation, self.ui.cmb_preparation_2,
                self.ui.cmb_preparation_3, self.ui.cmb_preparation_4,
                self.ui.dspn_preparation, self.ui.dspn_preparation_2,
                self.ui.dspn_preparation_3, self.ui.dspn_preparation_4,
                self.ui.lbl_unit_preparation, self.ui.lbl_unit_preparation_2,
                self.ui.lbl_unit_preparation_3, self.ui.lbl_unit_preparation_4,
            ],
            self.ui.chk_installation: [
                self.ui.cmb_installation, self.ui.cmb_installation_2,
                self.ui.cmb_installation_3, self.ui.cmb_installation_4,
                self.ui.dspn_installation, self.ui.dspn_installation_2,
                self.ui.dspn_installation_3, self.ui.dspn_installation_4,
                self.ui.lbl_unit_installation, self.ui.lbl_unit_installation_2,
                self.ui.lbl_unit_installation_3, self.ui.lbl_unit_installation_4,
            ],
            self.ui.chk_others: [
                self.ui.cmb_others, self.ui.cmb_others_2,
                self.ui.dspn_others, self.ui.dspn_others_2,
                self.ui.lbl_unit_others, self.ui.lbl_unit_others_2,
            ],
            self.ui.chk_reparo: [
                self.ui.cmb_reparo, self.ui.cmb_reparo_2,
                self.ui.dspn_reparo, self.ui.dspn_reparo_2,
                self.ui.lbl_unit_reparo, self.ui.lbl_unit_reparo_2,
            ],
        }

        def make_toggle_handler(widgets):
            """Cria (via closure) o handler que habilita/desabilita um grupo de campos conforme o checkbox da categoria for marcado/desmarcado."""
            def handler(checked):
                """Habilita ou desabilita todos os widgets do grupo de acordo com o estado do checkbox."""
                for w in widgets:
                    w.setEnabled(checked)
            return handler

        def make_clear_handler(widgets):
            """Quando o USUÁRIO desmarca a categoria (clicked, não toggled —
            carregar um job não apaga nada), limpa o que estava escolhido nela."""
            def handler(checked):
                if checked:
                    return
                for w in widgets:
                    if isinstance(w, QComboBox):
                        w.setCurrentIndex(0)
                    elif isinstance(w, QDoubleSpinBox):
                        w.setValue(1)
            return handler

        self._category_lock_handlers = []  # mantém referência viva
        for checkbox, widgets in groups.items():
            handler = make_toggle_handler(widgets)
            checkbox.toggled.connect(handler)
            self._category_lock_handlers.append(handler)
            clear_handler = make_clear_handler(widgets)
            checkbox.clicked.connect(clear_handler)
            self._category_lock_handlers.append(clear_handler)
            # Aplica o estado inicial (desmarcado = bloqueado)
            handler(checkbox.isChecked())

    def load_schedule_month(self):
        """Destaca no calendário os dias do mês visível que já têm Job(s)
        agendado(s), e recarrega a lista de jobs do dia selecionado."""
        calendar = self.ui.calendar_schedule
        year = calendar.yearShown()
        month = calendar.monthShown()

        # Limpa formatação antiga do mês inteiro antes de reaplicar
        default_format = QTextCharFormat()
        first_day = QDate(year, month, 1)
        for day in range(1, first_day.daysInMonth() + 1):
            calendar.setDateTextFormat(QDate(year, month, day), default_format)

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT DAY(WORK_DATE), COUNT(*) FROM work_days
                WHERE YEAR(WORK_DATE) = %s AND MONTH(WORK_DATE) = %s
                GROUP BY DAY(WORK_DATE)
                """,
                (year, month),
            )
            day_counts = dict(cursor.fetchall())
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.warning(self, "Database Error", f"Could not load schedule:\n{e}")
            return

        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor(BRAND_ORANGE))
        highlight_format.setForeground(QColor("#FFFFFF"))
        highlight_format.setFontWeight(700)

        for day, count in day_counts.items():
            fmt = QTextCharFormat(highlight_format)
            fmt.setToolTip(f"{count} job(s) scheduled")
            calendar.setDateTextFormat(QDate(year, month, day), fmt)

        self.load_schedule_day_jobs()

    def load_schedule_day_jobs(self):
        """Carrega a lista de jobs do dia selecionado no calendário do Schedule."""
        selected_qdate = self.ui.calendar_schedule.selectedDate()
        selected_date_str = selected_qdate.toString("yyyy-MM-dd")
        self.ui.lbl_schedule_selected_date.setText(f"Jobs on {selected_qdate.toString('MM/dd/yyyy')}")

        list_widget = self.ui.list_schedule_jobs
        list_widget.clear()

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT COALESCE(c.COMPANY_NAME, c.FULL_NAME, '—'), wd.JOB_ADDRESS, COALESCE(city.CITY, ''),
                       wd.VALUE, wd.STATUS
                FROM work_days wd
                LEFT JOIN contractors c ON c.ID = wd.CONTRACTOR_ID
                LEFT JOIN cities city ON city.ID = wd.CITY_ID
                WHERE wd.WORK_DATE = %s
                ORDER BY wd.ID
                """,
                (selected_date_str,),
            )
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.warning(self, "Database Error", f"Could not load jobs for this day:\n{e}")
            return

        if not rows:
            list_widget.addItem("No jobs scheduled for this day.")
            return

        for contractor, address, city, value, status in rows:
            status_label = JOB_STATUS_LABELS.get(status, status)
            text = f"{contractor} — {address or ''}{', ' + city if city else ''} — ${float(value or 0):,.2f} — {status_label or status}"
            list_widget.addItem(text)

    def _setup_job_date_filter_defaults(self):
        """Define os valores padrão do filtro de data da lista de Work Days:
        início = data mais antiga já registrada, fim = hoje."""
        self.ui.date_filter_from.blockSignals(True)
        self.ui.date_filter_to.blockSignals(True)
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT MIN(WORK_DATE) FROM work_days")
            earliest = cursor.fetchone()[0]
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError):
            earliest = None

        if earliest:
            self.ui.date_filter_from.setDate(QDate(earliest.year, earliest.month, earliest.day))
        else:
            self.ui.date_filter_from.setDate(QDate.currentDate())
        self.ui.date_filter_to.setDate(QDate.currentDate())
        self.ui.date_filter_from.blockSignals(False)
        self.ui.date_filter_to.blockSignals(False)

    def new_job_on_schedule_date(self):
        """Cria um novo Job já com a data do dia selecionado no calendário do
        Schedule, e leva o usuário direto pro formulário New/Edit Job."""
        selected_qdate = self.ui.calendar_schedule.selectedDate()
        self.new_job_record()
        self.ui.date_work_date.setDate(selected_qdate)
        self.ui.tabWidget_jobs.setCurrentWidget(self.ui.tab_jobs_master)

    def load_work_days(self):
        """Carrega os registros de work_days na tabela, aplicando filtros de busca e status."""
        search_text = self.ui.txt_search_jobs.text().strip()
        status_filter = self.ui.cmb_filter_status.currentText()

        query = """
            SELECT
                wd.ID, wd.WORK_DATE,
                COALESCE(c.COMPANY_NAME, c.FULL_NAME, wd.CONTRACTOR_ID) AS CONTRACTOR_NAME,
                COALESCE(co.COMPANY_NAME, wd.COMPANY_ID) AS COMPANY_NAME,
                COALESCE(cl.FULL_NAME, wd.CLIENT_ID) AS CLIENT_NAME,
                wd.JOB_ADDRESS,
                COALESCE(city.CITY, wd.CITY_ID) AS CITY_NAME,
                COALESCE(st.STATE_NAME, wd.STATE_ID) AS STATE_NAME,
                wd.DEMOLITION_1_ID, wd.DEMOLITION_2_ID, wd.DEMOLITION_3_ID, wd.DEMOLITION_4_ID,
                wd.INSTALLATION_1_ID, wd.INSTALLATION_2_ID, wd.INSTALLATION_3_ID, wd.INSTALLATION_4_ID,
                wd.PREPARATION_1_ID, wd.PREPARATION_2_ID, wd.PREPARATION_3_ID, wd.PREPARATION_4_ID,
                wd.OTHERS_1_ID, wd.OTHERS_2_ID,
                wd.REPARO_1_ID, wd.REPARO_2_ID,
                wd.VALUE, wd.STATUS,
                COALESCE(jp.CODE, '') AS JOB_CODE
            FROM work_days wd
            LEFT JOIN contractors c ON c.ID = wd.CONTRACTOR_ID
            LEFT JOIN companies co ON co.ID = wd.COMPANY_ID
            LEFT JOIN clients cl ON cl.ID = wd.CLIENT_ID
            LEFT JOIN cities city ON city.ID = wd.CITY_ID
            LEFT JOIN states st ON st.ID = wd.STATE_ID
            LEFT JOIN job_projects jp ON jp.ID = wd.JOB_PROJECT_ID
            WHERE 1=1
        """
        params = []

        if search_text:
            query += """
                AND (wd.JOB_ADDRESS LIKE %s
                     OR COALESCE(c.COMPANY_NAME, c.FULL_NAME, '') LIKE %s
                     OR COALESCE(city.CITY, '') LIKE %s
                     OR COALESCE(jp.CODE, '') LIKE %s)
            """
            like = f"%{search_text}%"
            params.extend([like, like, like, like])

        if status_filter and status_filter != "All Status":
            query += " AND wd.STATUS = %s"
            params.append(status_filter)

        date_from = self.ui.date_filter_from.date().toString("yyyy-MM-dd")
        date_to = self.ui.date_filter_to.date().toString("yyyy-MM-dd")
        query += " AND wd.WORK_DATE BETWEEN %s AND %s"
        params.extend([date_from, date_to])

        query += " ORDER BY wd.WORK_DATE DESC, wd.ID DESC"

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except MySQLError as e:
            QMessageBox.critical(self, "Database Error", f"Could not load work days:\n{e}")
            return
        except RuntimeError as e:
            QMessageBox.warning(self, "Driver Missing", str(e))
            return

        self._populate_table(rows)

    def _populate_table(self, rows):
        """Preenche a tabela de Work Days linha a linha, colorindo a coluna Status conforme o valor.

        As colunas Demolition/Installation/Preparation/Others/Repair mostram
        'Yes' quando pelo menos um Work Type daquela categoria foi selecionado
        no job, e 'Not' quando nenhum foi selecionado.
        """
        table = self.ui.table_work_days
        table.setSortingEnabled(False)
        table.setRowCount(0)
        table.setRowCount(len(rows))

        def yes_not(*ids):
            return "Yes" if any(i is not None for i in ids) else "No"

        for row_idx, row_data in enumerate(rows):
            (job_id, work_date, contractor, company, client, address,
             city, state,
             dem1, dem2, dem3, dem4,
             ins1, ins2, ins3, ins4,
             prep1, prep2, prep3, prep4,
             oth1, oth2,
             rep1, rep2,
             value, status, job_code) = row_data

            values = [
                str(job_id),
                work_date.strftime("%m/%d/%Y") if isinstance(work_date, date) else str(work_date or ""),
                str(contractor or "—"),
                str(company or "—"),
                str(client or "—"),
                str(address or ""),
                str(city or "—"),
                str(state or "—"),
                yes_not(dem1, dem2, dem3, dem4),
                yes_not(ins1, ins2, ins3, ins4),
                yes_not(prep1, prep2, prep3, prep4),
                yes_not(oth1, oth2),
                yes_not(rep1, rep2),
                f"${value:,.2f}" if value is not None else "$0.00",
                str(status or ""),
                str(job_code or "—"),
            ]

            for col_idx, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if col_idx == 14:  # coluna STATUS (deslocou 1 posição com a nova coluna Repair)
                    bg = STATUS_COLORS.get(status)
                    fg = STATUS_TEXT_COLORS.get(status)
                    if bg:
                        item.setBackground(bg)
                    if fg:
                        item.setForeground(fg)
                table.setItem(row_idx, col_idx, item)

        table.setSortingEnabled(True)

    def load_combo_data(self):
        """Popula os comboboxes de Contractor, Company, City, State a partir do banco."""
        was_loading = self._loading_job_form
        self._loading_job_form = True  # popular combos não conta como "edição do usuário"
        combo_map = {
            "contractor": (self.ui.cmb_contractor, "SELECT ID, COALESCE(COMPANY_NAME, FULL_NAME) FROM contractors ORDER BY COALESCE(COMPANY_NAME, FULL_NAME)"),
            "helper": (self.ui.cmb_helper, "SELECT ID, COALESCE(COMPANY_NAME, FULL_NAME) FROM helpers ORDER BY COALESCE(COMPANY_NAME, FULL_NAME)"),
            "company": (self.ui.cmb_company_form, "SELECT ID, COMPANY_NAME FROM companies ORDER BY COMPANY_NAME"),
            "state": (self.ui.cmb_client_state, "SELECT ID, STATE_NAME FROM states ORDER BY STATE_NAME"),
            "company_state": (self.ui.cmb_company_state, "SELECT ID, STATE_NAME FROM states ORDER BY STATE_NAME"),
            "contractor_state": (self.ui.cmb_contractor_state, "SELECT ID, STATE_NAME FROM states ORDER BY STATE_NAME"),
            "customer_state": (self.ui.cmb_customer_state, "SELECT ID, STATE_NAME FROM states ORDER BY STATE_NAME"),
            "client_address": (self.ui.cmb_client_address,
                                "SELECT DISTINCT JOB_ADDRESS, JOB_ADDRESS FROM work_days "
                                "WHERE JOB_ADDRESS IS NOT NULL AND JOB_ADDRESS <> '' ORDER BY JOB_ADDRESS"),
            "demolition_1": (self.ui.cmb_demolition, "SELECT ID, NAME FROM work_types WHERE CATEGORY='DEMOLITION' ORDER BY NAME"),
            "demolition_2": (self.ui.cmb_demolition_2, "SELECT ID, NAME FROM work_types WHERE CATEGORY='DEMOLITION' ORDER BY NAME"),
            "demolition_3": (self.ui.cmb_demolition_3, "SELECT ID, NAME FROM work_types WHERE CATEGORY='DEMOLITION' ORDER BY NAME"),
            "demolition_4": (self.ui.cmb_demolition_4, "SELECT ID, NAME FROM work_types WHERE CATEGORY='DEMOLITION' ORDER BY NAME"),
            "installation_1": (self.ui.cmb_installation, "SELECT ID, NAME FROM work_types WHERE CATEGORY='INSTALLATION' ORDER BY NAME"),
            "installation_2": (self.ui.cmb_installation_2, "SELECT ID, NAME FROM work_types WHERE CATEGORY='INSTALLATION' ORDER BY NAME"),
            "installation_3": (self.ui.cmb_installation_3, "SELECT ID, NAME FROM work_types WHERE CATEGORY='INSTALLATION' ORDER BY NAME"),
            "installation_4": (self.ui.cmb_installation_4, "SELECT ID, NAME FROM work_types WHERE CATEGORY='INSTALLATION' ORDER BY NAME"),
            "preparation_1": (self.ui.cmb_preparation, "SELECT ID, NAME FROM work_types WHERE CATEGORY='PREPARATION' ORDER BY NAME"),
            "preparation_2": (self.ui.cmb_preparation_2, "SELECT ID, NAME FROM work_types WHERE CATEGORY='PREPARATION' ORDER BY NAME"),
            "preparation_3": (self.ui.cmb_preparation_3, "SELECT ID, NAME FROM work_types WHERE CATEGORY='PREPARATION' ORDER BY NAME"),
            "preparation_4": (self.ui.cmb_preparation_4, "SELECT ID, NAME FROM work_types WHERE CATEGORY='PREPARATION' ORDER BY NAME"),
            "others_1": (self.ui.cmb_others, "SELECT ID, NAME FROM work_types WHERE CATEGORY='OTHERS' ORDER BY NAME"),
            "others_2": (self.ui.cmb_others_2, "SELECT ID, NAME FROM work_types WHERE CATEGORY='OTHERS' ORDER BY NAME"),
            "reparo_1": (self.ui.cmb_reparo, "SELECT ID, NAME FROM work_types WHERE CATEGORY='REPARO' ORDER BY NAME"),
            "reparo_2": (self.ui.cmb_reparo_2, "SELECT ID, NAME FROM work_types WHERE CATEGORY='REPARO' ORDER BY NAME"),
            "expense_contractor": (self.ui.cmb_expense_contractor, "SELECT ID, FULL_NAME FROM contractors ORDER BY FULL_NAME"),
            "expense_filter_contractor": (self.ui.cmb_filter_expense_contractor, "SELECT ID, FULL_NAME FROM contractors ORDER BY FULL_NAME"),
            # TODO: "payment" — cmb_payment depende do nome da tabela de formas de pagamento
        }

        # Guarda a seleção atual de cada combo pra restaurar depois de recarregar
        # (recarregar não pode apagar o que o usuário já tinha escolhido num formulário aberto)
        previous_selection = {key: combo.currentData() for key, (combo, _q) in combo_map.items()}
        city_combos = (self.ui.cmb_client_city, self.ui.cmb_company_city, self.ui.cmb_contractor_city,
                       self.ui.cmb_customer_city)
        previous_city_selection = {combo: combo.currentData() for combo in city_combos}

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            for key, (combo, query) in combo_map.items():
                combo.clear()
                placeholder = "All Contractors" if key == "expense_filter_contractor" else "— Select —"
                combo.addItem(placeholder, None)
                try:
                    cursor.execute(query)
                    rows = cursor.fetchall()
                except MySQLError:
                    # Uma tabela nova (ex: "helpers") que ainda não teve a
                    # migração rodada não pode travar os combos seguintes —
                    # esse combo fica só com o placeholder até a tabela existir.
                    rows = []
                for row_id, name in rows:
                    combo.addItem(name, row_id)
                saved = previous_selection.get(key)
                if saved is not None:
                    idx = combo.findData(saved)
                    if idx >= 0:
                        combo.setCurrentIndex(idx)

            # Cache de unidades (work_type_id -> "PCS"/"SQFT"/"LFT") pra mostrar
            # automaticamente ao lado do spinbox de quantidade
            self._work_type_units = {}
            try:
                cursor.execute("SELECT ID, UNIT FROM work_types")
                for wt_id, unit in cursor.fetchall():
                    self._work_type_units[wt_id] = unit
            except MySQLError:
                pass  # coluna UNIT ainda não existe — só não mostra a unidade

            cursor.close()
            conn.close()

            self._refresh_client_name_completer()
            self._refresh_job_code_completer()
            self._refresh_material_product_combo()

            # Cidades dependem do State — recarrega respeitando o State atual de
            # cada formulário, preservando a cidade escolhida se ainda existir nesse State
            self._reload_city_combo_for_state(
                self.ui.cmb_client_city, self.ui.cmb_client_state.currentData(),
                keep_city_id=previous_city_selection[self.ui.cmb_client_city])
            self._reload_city_combo_for_state(
                self.ui.cmb_company_city, self.ui.cmb_company_state.currentData(),
                keep_city_id=previous_city_selection[self.ui.cmb_company_city])
            self._reload_city_combo_for_state(
                self.ui.cmb_contractor_city, self.ui.cmb_contractor_state.currentData(),
                keep_city_id=previous_city_selection[self.ui.cmb_contractor_city])
            self._reload_city_combo_for_state(
                self.ui.cmb_customer_city, self.ui.cmb_customer_state.currentData(),
                keep_city_id=previous_city_selection[self.ui.cmb_customer_city])
        except (MySQLError, RuntimeError) as e:
            # Não bloqueia a tela inicial se as tabelas de apoio ainda não existirem
            print(f"[Aviso] Não foi possível carregar combos: {e}")
        finally:
            self._loading_job_form = was_loading

    def _on_new_job_button_clicked(self):
        """Chamado pelo botão '+ New Job': confirma antes de limpar o
        formulário se houver alterações não salvas."""
        if (self._job_form_dirty
                and self.ui.tabWidget_jobs.currentWidget() is self.ui.tab_jobs_master):
            confirm = QMessageBox.question(
                self, "Unsaved changes",
                "You have unsaved changes in the current Job. Discard them and start a new one?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return
        self.new_job_record()

    def _setup_job_code_completer(self):
        """Configura o autocomplete do campo Job Code."""
        self._job_code_to_id = {}
        self._job_code_completer = QCompleter([], self)
        self._job_code_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._job_code_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._job_code_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.ui.cmb_job_code.setCompleter(self._job_code_completer)

        # Clicar numa sugestão não dispara editingFinished (só Enter ou sair do
        # campo), então o preenchimento automático só acontecia depois. Agora
        # dispara na hora da escolha; o guard evita perguntar de novo quando o
        # usuário sair do campo em seguida com o mesmo código.
        self._job_code_autofill_handled = None
        self._job_code_completer.activated[str].connect(
            lambda _text: QTimer.singleShot(0, self._on_job_code_editing_finished))
        self.ui.cmb_job_code.lineEdit().textChanged.connect(self._reset_job_code_autofill_guard)

    def _reset_job_code_autofill_guard(self, _text=None):
        self._job_code_autofill_handled = None

    def _resolve_partial_job_code(self, typed):
        """Devolve o código completo se o texto digitado identifica um único
        código existente: só o número ("32" -> JB-0032) ou um pedaço do código."""
        if not typed:
            return None
        if typed.isdigit():
            matches = [code for code in self._job_code_to_id
                       if code.rsplit("-", 1)[-1].isdigit() and int(code.rsplit("-", 1)[-1]) == int(typed)]
        else:
            matches = [code for code in self._job_code_to_id if typed in code]
        return matches[0] if len(matches) == 1 else None

    def _refresh_job_code_completer(self):
        """Recarrega a lista de códigos de projeto existentes (autocomplete)."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT ID, CODE FROM job_projects ORDER BY CODE")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError):
            rows = []
        self._job_code_to_id = {code.strip().upper(): jid for jid, code in rows if code}
        self._job_code_completer.setModel(QStringListModel([code for _, code in rows]))

    def _generate_job_code(self):
        """Sugere o próximo código sequencial (o projeto em job_projects só é
        criado ao salvar o job — ver save_job_record)
        (prefixo JB- para trabalhos por dia; PJ- fica reservado pra quando a
        área de trabalhos particulares existir), e já seleciona esse código
        no formulário. Só gera se pelo menos um de Contractor/Company/Client
        estiver selecionado — evita criar códigos "fantasma" pra trabalhos
        que ainda não existem de verdade."""
        has_contractor = self.ui.cmb_contractor.currentData() is not None
        has_company = self.ui.cmb_company_form.currentData() is not None
        has_client = bool(self.ui.txt_client_name.text().strip())

        if not (has_contractor or has_company or has_client):
            QMessageBox.warning(
                self, "Missing information",
                "Before generating a Job Code, select at least one of Contractor, "
                "Company, or Client.",
            )
            return

        prefix = "JB"
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT CODE FROM job_projects WHERE PROJECT_TYPE = 'DAY_WORK' AND CODE LIKE %s",
                (f"{prefix}-%",),
            )
            existing = [row[0] for row in cursor.fetchall()]
            next_n = 1
            for code in existing:
                try:
                    n = int(code.split("-")[1])
                    next_n = max(next_n, n + 1)
                except (IndexError, ValueError):
                    continue
            new_code = f"{prefix}-{next_n:04d}"
            # O código NÃO é gravado aqui: save_job_record cria o projeto
            # quando o job for salvo. Assim, clicar em Generate Code e
            # desistir não deixa códigos vazios no banco.
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not generate a job code:\n{e}")
            return

        self._refresh_job_code_completer()
        self.ui.cmb_job_code.setEditText(new_code)
        self._update_days_worked_label()

    # Colunas de Work Type (ID + QTY) em work_days, na mesma ordem dos
    # combos/spinboxes do formulário — reaproveitada tanto por
    # load_job_into_form (clique numa linha) quanto por
    # _on_job_code_editing_finished (copiar do último job do código).
    _WORK_TYPE_FIELD_PREFIXES = [
        "DEMOLITION_1", "DEMOLITION_2", "DEMOLITION_3", "DEMOLITION_4",
        "INSTALLATION_1", "INSTALLATION_2", "INSTALLATION_3", "INSTALLATION_4",
        "PREPARATION_1", "PREPARATION_2", "PREPARATION_3", "PREPARATION_4",
        "OTHERS_1", "OTHERS_2", "REPARO_1", "REPARO_2",
    ]

    def _work_type_field_widgets(self):
        """Lista (prefixo, combo, spinbox) dos 16 campos de Work Type,
        na mesma ordem de _WORK_TYPE_FIELD_PREFIXES."""
        return [
            ("DEMOLITION_1", self.ui.cmb_demolition, self.ui.dspn_demolition),
            ("DEMOLITION_2", self.ui.cmb_demolition_2, self.ui.dspn_demolition_2),
            ("DEMOLITION_3", self.ui.cmb_demolition_3, self.ui.dspn_demolition_3),
            ("DEMOLITION_4", self.ui.cmb_demolition_4, self.ui.dspn_demolition_4),
            ("INSTALLATION_1", self.ui.cmb_installation, self.ui.dspn_installation),
            ("INSTALLATION_2", self.ui.cmb_installation_2, self.ui.dspn_installation_2),
            ("INSTALLATION_3", self.ui.cmb_installation_3, self.ui.dspn_installation_3),
            ("INSTALLATION_4", self.ui.cmb_installation_4, self.ui.dspn_installation_4),
            ("PREPARATION_1", self.ui.cmb_preparation, self.ui.dspn_preparation),
            ("PREPARATION_2", self.ui.cmb_preparation_2, self.ui.dspn_preparation_2),
            ("PREPARATION_3", self.ui.cmb_preparation_3, self.ui.dspn_preparation_3),
            ("PREPARATION_4", self.ui.cmb_preparation_4, self.ui.dspn_preparation_4),
            ("OTHERS_1", self.ui.cmb_others, self.ui.dspn_others),
            ("OTHERS_2", self.ui.cmb_others_2, self.ui.dspn_others_2),
            ("REPARO_1", self.ui.cmb_reparo, self.ui.dspn_reparo),
            ("REPARO_2", self.ui.cmb_reparo_2, self.ui.dspn_reparo_2),
        ]

    def _on_job_code_editing_finished(self):
        """Quando o usuário digita/confirma um código que já existe, pergunta
        se quer puxar TODOS os dados do último job daquele projeto: Client
        Info completo (nome/e-mail/telefone/endereço/cidade/estado/zip),
        Company, Contractor, Payment Method e os Work Types (com
        quantidade) — só Work Date, Status e Value ficam de fora, porque
        normalmente mudam a cada dia.

        Lê o job (work_days) MAIS RECENTE já salvo sob esse Job Code, em vez
        do "snapshot" congelado em job_projects — porque esse snapshot só era
        gravado uma vez (no primeiro Save daquele código) e, se o cliente
        fosse novo naquele momento, ficava com CLIENT_ID em branco pra
        sempre (o cliente só era criado DEPOIS, mais adiante em
        save_job_record). Já foi corrigida a ordem em save_job_record pra
        gravações novas, mas ler do work_days mais recente também conserta
        projetos antigos que já ficaram com esse campo faltando, sem
        precisar salvar de novo antes."""
        if self._loading_job_form:
            return
        typed = self.ui.cmb_job_code.currentText().strip().upper()
        job_id = self._job_code_to_id.get(typed)
        if not job_id:
            # Aceita o código abreviado ("32" ou "0032" -> "JB-0032") quando
            # só um código existente combina
            full_code = self._resolve_partial_job_code(typed)
            if full_code:
                self.ui.cmb_job_code.setEditText(full_code)
                typed, job_id = full_code, self._job_code_to_id[full_code]
        if not job_id:
            self._update_days_worked_label()
            return
        if typed == self._job_code_autofill_handled:
            return  # já tratado ao escolher a sugestão
        self._job_code_autofill_handled = typed

        work_type_id_cols = ", ".join(f"{p}_ID" for p in self._WORK_TYPE_FIELD_PREFIXES)
        work_type_qty_cols = ", ".join(f"{p}_QTY" for p in self._WORK_TYPE_FIELD_PREFIXES)
        # HELPER_ID só entra na consulta se a coluna já existir (migração do
        # Helpers) — do contrário, "Fill this form" continua funcionando
        # normalmente pra todo o resto, só sem preencher o Helper ainda.
        has_helper_col = self._table_column_exists("work_days", "HELPER_ID")
        helper_col_sql = ", HELPER_ID" if has_helper_col else ""

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT CLIENT_ID, COMPANY_ID, CONTRACTOR_ID, JOB_ADDRESS, JOB_ADDRESS2, "
                f"CITY_ID, STATE_ID, ZIP_CODE, PAYMENT_METHOD{helper_col_sql}, {work_type_id_cols}, {work_type_qty_cols} "
                "FROM work_days WHERE JOB_PROJECT_ID = %s ORDER BY ID DESC",
                (job_id,),
            )
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError):
            rows = []

        # Cada campo de cliente/endereço/company vem do job mais recente que o
        # tem preenchido (ex.: o último dia salvo sem ZIP, mas um anterior com).
        # Work Types ficam só do job mais recente, pra não misturar dias.
        n_head = 10 if has_helper_col else 9
        row = None
        if rows:
            head = [next((r[i] for r in rows if r[i] not in (None, "")), None) for i in range(n_head)]
            row = tuple(head) + tuple(rows[0][n_head:])

        self._update_days_worked_label()

        if not row or not any(row):
            return  # projeto ainda não tem nenhum job salvo sob esse código

        confirm = QMessageBox.question(
            self, "Existing Job Code",
            f"'{typed}' already has data saved (client, address, work types, etc). "
            f"Fill this form with that info?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        n_types = len(self._WORK_TYPE_FIELD_PREFIXES)
        if has_helper_col:
            (client_id, company_id, contractor_id, job_address, job_address2, city_id, state_id,
             zip_code, payment_method, helper_id, *rest) = row
        else:
            (client_id, company_id, contractor_id, job_address, job_address2, city_id, state_id,
             zip_code, payment_method, *rest) = row
            helper_id = None
        work_type_ids = rest[:n_types]
        work_type_qtys = rest[n_types:n_types * 2]

        if client_id:
            try:
                conn2 = self._get_connection()
                cur2 = conn2.cursor()
                cur2.execute("SELECT FULL_NAME, EMAIL, PHONE_NUMBER, PHONE_NUMBER2 FROM clients WHERE ID = %s",
                             (client_id,))
                client_row = cur2.fetchone()
                cur2.close()
                conn2.close()
                if client_row:
                    self.ui.txt_client_name.setText(client_row[0] or "")
                    self.ui.txt_client_email.setText(client_row[1] or "")
                    self.ui.txt_client_phone.setText(self._format_phone(client_row[2]) or "")
                    self.ui.txt_client_phone_2.setText(self._format_phone(client_row[3]) or "")
            except (MySQLError, RuntimeError) as e:
                QMessageBox.warning(
                    self, "Couldn't load client",
                    f"This project has a client linked, but its details couldn't be loaded:\n{e}",
                )
        if company_id:
            self._set_combo_by_data(self.ui.cmb_company_form, company_id)
        if contractor_id:
            self._set_combo_by_data(self.ui.cmb_contractor, contractor_id)
        if helper_id:
            self._set_combo_by_data(self.ui.cmb_helper, helper_id)
        # mesma equipe do último dia desse Job Code (dá pra mudar no botão Helpers)
        self._load_crew_from_latest_day(job_id)
        self._load_work_types_from_latest_day(job_id)
        if state_id:
            self._set_combo_by_data(self.ui.cmb_client_state, state_id)
            self._reload_city_combo_for_state(self.ui.cmb_client_city, state_id, keep_city_id=city_id)
        if job_address:
            self.ui.cmb_client_address.setCurrentText(job_address)
        if job_address2:
            self.ui.txt_client_address2.setText(job_address2)
        if zip_code:
            self.ui.txt_client_zip.setText(self._format_zip(zip_code) or "")
        if payment_method:
            self._set_combo_by_data(self.ui.cmb_payment, payment_method, by_text=True)

        # Work Types + quantidades, e os checkboxes de categoria (senão os
        # campos ficam bloqueados escondendo o que acabou de ser preenchido)
        # — mesmo padrão já usado em load_job_into_form.
        widgets = self._work_type_field_widgets()
        type_data = dict(zip(self._WORK_TYPE_FIELD_PREFIXES, work_type_ids))
        qty_data = dict(zip(self._WORK_TYPE_FIELD_PREFIXES, work_type_qtys))
        for prefix, combo, spin in widgets:
            type_id = type_data.get(prefix)
            if type_id:
                self._set_combo_by_data(combo, type_id)
                qty = qty_data.get(prefix)
                spin.setValue(float(qty) if qty is not None else 1)

        category_prefixes = {
            self.ui.chk_demolition: ["DEMOLITION_1", "DEMOLITION_2", "DEMOLITION_3", "DEMOLITION_4"],
            self.ui.chk_preparation: ["PREPARATION_1", "PREPARATION_2", "PREPARATION_3", "PREPARATION_4"],
            self.ui.chk_installation: ["INSTALLATION_1", "INSTALLATION_2", "INSTALLATION_3", "INSTALLATION_4"],
            self.ui.chk_others: ["OTHERS_1", "OTHERS_2"],
            self.ui.chk_reparo: ["REPARO_1", "REPARO_2"],
        }
        for checkbox, prefixes in category_prefixes.items():
            if any(type_data.get(p) for p in prefixes):
                checkbox.setChecked(True)

    def _update_days_worked_label(self):
        """Mostra, em destaque, quantos dias de trabalho já foram registrados
        sob o código de projeto atual. Parar o mouse em cima mostra a lista
        dos dias (data e status) — inclusive os que estão fora do filtro de
        datas da lista."""
        typed = self.ui.cmb_job_code.currentText().strip().upper()
        job_id = self._job_code_to_id.get(typed)
        btn_complete = getattr(self, "_btn_complete_job", None)

        if not job_id:
            self.ui.lbl_days_worked_value.setText("—")
            self.ui.lbl_days_worked_value.setToolTip("")
            if btn_complete is not None:
                btn_complete.setVisible(False)
            return

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT ID, WORK_DATE, STATUS FROM work_days WHERE JOB_PROJECT_ID = %s ORDER BY WORK_DATE, ID",
                (job_id,),
            )
            day_rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError):
            self.ui.lbl_days_worked_value.setText("—")
            return

        days_count = len({d for _i, d, _s in day_rows})
        self.ui.lbl_days_worked_value.setText(f"🗓 {days_count} day{'s' if days_count != 1 else ''}")
        lines = [f"#{i}  {d.strftime('%m/%d/%Y') if d else '?'}  —  {JOB_STATUS_LABELS.get(st, st or '')}"
                 for i, d, st in day_rows]
        self.ui.lbl_days_worked_value.setToolTip(f"Days of {typed}:\n" + "\n".join(lines))
        if btn_complete is not None:
            open_days = [r for r in day_rows if r[2] not in ("COMPLETED", "CANCELLED")]
            btn_complete.setVisible(bool(open_days))
        if hasattr(self, "_refresh_photos_button"):
            self._refresh_photos_button()

    def _refresh_material_product_combo(self):
        """Popula o combo de produtos usado pra adicionar material gasto,
        AGRUPADO POR TIPO (Flooring, Adhesive, Molding…) e mostrando quanto
        cada embalagem cobre (ex.: 23 SF / BOX)."""
        from PySide6.QtGui import QFont
        combo = self.ui.cmb_material_product
        combo.clear()
        combo.addItem("— Select a product —", None)
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT ID, NAME, UNIT, PRICE, COALESCE(NULLIF(TYPE, ''), 'Others'), BRAND, "
                           "COVERAGE_QTY, COVERAGE_UNIT FROM products ORDER BY 5, NAME")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError):
            rows = []
        self._products_cache = {}
        self._products_coverage = {}
        model = combo.model()
        current_type = None
        for product_id, name, unit, price, ptype, brand, cov, cov_unit in rows:
            if ptype != current_type:
                current_type = ptype
                # Título do grupo: item do próprio combo, desativado (não dá pra
                # escolher). Criado pelo combo — um QStandardItem criado no Python
                # era apagado pelo coletor de lixo e derrubava o app no clear().
                combo.addItem(f"── {ptype.upper()} ──", None)
                header = model.item(combo.count() - 1)
                if header is not None:
                    header.setFlags(Qt.ItemFlag.NoItemFlags)
                bold = QFont(combo.font())
                bold.setBold(True)
                combo.setItemData(combo.count() - 1, bold, Qt.ItemDataRole.FontRole)
            label = f"   {name}" + (f" ({brand})" if brand else "")
            if cov and float(cov) > 0:
                label += f"  ·  {float(cov):g} {cov_unit or ''} / {unit or 'unit'}"
            combo.addItem(label, product_id)
            self._products_cache[product_id] = (name, unit or "", float(price or 0))
            self._products_coverage[product_id] = (float(cov or 0), (cov_unit or "").upper(), ptype)

    def _update_material_hint(self, *_args):
        """Mostra, ao lado do Add, o que a quantidade digitada representa
        (ex.: 41 BOX = 943 SF · $0.00)."""
        lbl = getattr(self, "_lbl_material_hint", None)
        if lbl is None:
            return
        pid = self.ui.cmb_material_product.currentData()
        if not pid:
            lbl.setText("")
            return
        _name, unit, price = self._products_cache.get(pid, ("", "", 0.0))
        cov, cov_unit, _ptype = self._products_coverage.get(pid, (0.0, "", ""))
        qty = self.ui.dspn_material_qty.value()
        parts = []
        if cov > 0:
            parts.append(f"1 {unit or 'unit'} = {cov:g} {cov_unit}")
            parts.append(f"{qty:g} {unit} = {qty * cov:,.2f} {cov_unit}".replace(".00 ", " "))
        parts.append(f"${price:,.2f} / {unit or 'unit'}" if price else "no price yet")
        lbl.setText("   ·   ".join(parts))

    def _setup_material_hint(self):
        lbl = QLabel("")
        lbl.setObjectName("lbl_material_hint")
        lbl.setStyleSheet("color:#6B7C93; font-size:12px; background:transparent;")
        self.ui.layout_materials_body.insertWidget(
            self.ui.layout_materials_body.indexOf(self.ui.btn_remove_material), lbl)
        self._lbl_material_hint = lbl
        self.ui.cmb_material_product.currentIndexChanged.connect(self._update_material_hint)
        self.ui.dspn_material_qty.valueChanged.connect(self._update_material_hint)
        table = self.ui.table_job_materials
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["Type", "Product", "Qty", "Unit", "Covers", "Cost"])
        header = table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for col in (0, 2, 3, 4, 5):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

    def _setup_work_type_decimals(self):
        """Quantidades dos Work Types com 2 casas (antes era 0: 6,5 virava 6).
        O banco já guarda DECIMAL(10,2)."""
        for _prefix, _combo, spin in self._work_type_field_widgets():
            spin.setDecimals(2)
            spin.setMaximumWidth(16777215)
            spin.setMinimumWidth(max(spin.minimumWidth(), 84))

    def _load_job_materials(self):
        """Carrega a lista de materiais gastos no projeto (Job Code) atual,
        ordenada por tipo, com a área que cobre e o custo de cada linha."""
        table = self.ui.table_job_materials
        table.setRowCount(0)

        typed = self.ui.cmb_job_code.currentText().strip().upper()
        job_id = self._job_code_to_id.get(typed)
        self.ui.lbl_materials_total_cost.setVisible(False)
        if not job_id:
            return

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT jm.ID, COALESCE(NULLIF(p.TYPE, ''), 'Others'),
                       CONCAT(COALESCE(p.NAME, '—'), IF(COALESCE(p.BRAND, '') <> '', CONCAT(' (', p.BRAND, ')'), '')),
                       jm.QUANTITY, COALESCE(p.UNIT, ''), jm.UNIT_PRICE, p.COVERAGE_QTY, COALESCE(p.COVERAGE_UNIT, '')
                FROM job_materials jm
                LEFT JOIN products p ON p.ID = jm.PRODUCT_ID
                WHERE jm.JOB_PROJECT_ID = %s
                ORDER BY 2, 3, jm.ID
                """,
                (job_id,),
            )
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.warning(self, "Database Error", f"Could not load materials:\n{e}")
            return

        table.setRowCount(len(rows))
        total_cost = 0.0
        covered = {}
        previous_type = None
        for row_idx, (material_id, ptype, name, qty, unit, unit_price, cov, cov_unit) in enumerate(rows):
            qty, unit_price = float(qty or 0), float(unit_price or 0)
            line_cost = qty * unit_price
            total_cost += line_cost
            cov = float(cov or 0)
            covers = ""
            if cov > 0 and cov_unit:
                area = qty * cov
                covered[cov_unit] = covered.get(cov_unit, 0) + area if ptype == "Flooring" else covered.get(cov_unit, 0)
                covers = f"{area:,.2f} {cov_unit}".replace(".00 ", " ")
            values = [ptype if ptype != previous_type else "", name, f"{qty:g}", unit, covers,
                      f"${line_cost:,.2f}" if unit_price else "no price"]
            previous_type = ptype
            for col, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, material_id)
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                if col == 5 and not unit_price:
                    item.setForeground(QColor("#B26A00"))
                table.setItem(row_idx, col, item)

        # Resumo embaixo da tabela: custo total e área de piso coberta
        summary = f"Total material cost: ${total_cost:,.2f}"
        if covered.get("SF"):
            summary += f"   ·   Flooring covers {covered['SF']:,.2f} SF".replace(".00 SF", " SF")
        self.ui.lbl_materials_total_cost.setText(summary)
        self.ui.lbl_materials_total_cost.setVisible(bool(rows))

    def add_job_material(self):
        """Adiciona um material gasto ao projeto (Job Code) atual."""
        typed = self.ui.cmb_job_code.currentText().strip().upper()
        job_id = self._job_code_to_id.get(typed)
        if not job_id:
            QMessageBox.information(self, "No Job Code",
                                     "Pick or generate a Job Code first before adding materials.")
            return

        product_id = self.ui.cmb_material_product.currentData()
        if not product_id:
            QMessageBox.information(self, "No product selected", "Select a product first.")
            return

        qty = self.ui.dspn_material_qty.value()
        if qty <= 0:
            QMessageBox.warning(self, "Invalid quantity", "Enter a quantity greater than zero.")
            return

        _, _, unit_price = self._products_cache.get(product_id, ("", "", 0.0))

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO job_materials (JOB_PROJECT_ID, PRODUCT_ID, QUANTITY, UNIT_PRICE) "
                "VALUES (%s, %s, %s, %s)",
                (job_id, product_id, qty, unit_price),
            )
            conn.commit()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not add material:\n{e}")
            return

        self.ui.cmb_material_product.setCurrentIndex(0)
        self.ui.dspn_material_qty.setValue(1)
        self._load_job_materials()

    def remove_job_material(self):
        """Remove o material selecionado na lista."""
        table = self.ui.table_job_materials
        selected = table.currentRow()
        if selected < 0:
            QMessageBox.information(self, "No selection", "Select a material from the list first.")
            return

        material_id = table.item(selected, 0).data(Qt.ItemDataRole.UserRole)
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM job_materials WHERE ID = %s", (material_id,))
            conn.commit()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not remove material:\n{e}")
            return

        self._load_job_materials()

    def new_job_record(self):
        """Limpa o formulário para criar um novo registro."""
        self._loading_job_form = True
        self._current_job_id = None
        self._current_job_row = None
        self.ui.table_work_days.blockSignals(True)
        self.ui.table_work_days.clearSelection()
        self.ui.table_work_days.setCurrentCell(-1, -1)
        self.ui.table_work_days.blockSignals(False)
        self.ui.txt_job_id.clear()
        self.ui.lbl_job_id_display.setText("#ID: New")
        self.ui.cmb_job_code.setCurrentText("")
        self._update_days_worked_label()
        self.ui.table_job_materials.setRowCount(0)
        self.ui.lbl_materials_total_cost.setVisible(False)
        self.ui.date_work_date.setDate(date.today())  # sempre abre com a data de hoje
        self.ui.cmb_status_form.setCurrentIndex(0)
        self.ui.cmb_payment.setCurrentIndex(0)
        self.ui.cmb_contractor.setCurrentIndex(0)
        self.ui.cmb_helper.setCurrentIndex(0)
        self._reset_job_helpers()
        self._set_work_type_list([])
        self.ui.cmb_company_form.setCurrentIndex(0)
        self.ui.cmb_client_city.setCurrentIndex(0)
        self.ui.cmb_client_state.setCurrentIndex(0)
        self._reload_city_combo_for_state(self.ui.cmb_client_city, None)
        self.ui.dspn_value.setValue(0)
        self.ui.txt_client_name.clear()
        self.ui.cmb_client_address.setCurrentText("")
        for field in (self.ui.txt_client_email, self.ui.txt_client_phone,
                      self.ui.txt_client_phone_2, self.ui.txt_client_address2,
                      self.ui.txt_client_zip):
            field.clear()
        # Tipos de trabalho: reseta os 16 combos e os spinboxes de quantidade
        work_type_combos = (
            self.ui.cmb_demolition, self.ui.cmb_demolition_2,
            self.ui.cmb_demolition_3, self.ui.cmb_demolition_4,
            self.ui.cmb_installation, self.ui.cmb_installation_2,
            self.ui.cmb_installation_3, self.ui.cmb_installation_4,
            self.ui.cmb_preparation, self.ui.cmb_preparation_2,
            self.ui.cmb_preparation_3, self.ui.cmb_preparation_4,
            self.ui.cmb_others, self.ui.cmb_others_2,
            self.ui.cmb_reparo, self.ui.cmb_reparo_2,
        )
        for combo in work_type_combos:
            combo.setCurrentIndex(0)

        qty_spinboxes = (
            self.ui.dspn_demolition, self.ui.dspn_demolition_2,
            self.ui.dspn_demolition_3, self.ui.dspn_demolition_4,
            self.ui.dspn_installation, self.ui.dspn_installation_2,
            self.ui.dspn_installation_3, self.ui.dspn_installation_4,
            self.ui.dspn_preparation, self.ui.dspn_preparation_2,
            self.ui.dspn_preparation_3, self.ui.dspn_preparation_4,
            self.ui.dspn_others, self.ui.dspn_others_2,
            self.ui.dspn_reparo, self.ui.dspn_reparo_2,
        )
        for spin in qty_spinboxes:
            spin.setValue(1)

        for chk in (self.ui.chk_demolition, self.ui.chk_preparation,
                    self.ui.chk_installation, self.ui.chk_others, self.ui.chk_reparo):
            chk.setChecked(False)

        for lbl_unit in (self.ui.lbl_unit_demolition, self.ui.lbl_unit_demolition_2,
                         self.ui.lbl_unit_demolition_3, self.ui.lbl_unit_demolition_4,
                         self.ui.lbl_unit_installation, self.ui.lbl_unit_installation_2,
                         self.ui.lbl_unit_installation_3, self.ui.lbl_unit_installation_4,
                         self.ui.lbl_unit_preparation, self.ui.lbl_unit_preparation_2,
                         self.ui.lbl_unit_preparation_3, self.ui.lbl_unit_preparation_4,
                         self.ui.lbl_unit_others, self.ui.lbl_unit_others_2,
                         self.ui.lbl_unit_reparo, self.ui.lbl_unit_reparo_2):
            lbl_unit.setText("—")

        self.ui.txt_note.clear()
        self.ui.tabWidget_jobs.setCurrentWidget(self.ui.tab_jobs_master)
        self._loading_job_form = False
        self._job_form_dirty = False

    def load_job_into_form(self):
        """Carrega o registro selecionado na tabela para edição (dispara ao
        clicar numa linha — padrão master-detail: lista à esquerda, formulário
        sempre visível à direita)."""
        table = self.ui.table_work_days
        selected = table.currentRow()
        if selected < 0:
            return

        job_id_text = table.item(selected, 0).text()
        # Clicou na mesma linha que já está carregada: não faz nada
        # (evita re-perguntar ou perder uma edição em andamento à toa)
        if self._current_job_id is not None and str(self._current_job_id) == job_id_text:
            return

        if self._job_form_dirty:
            confirm = QMessageBox.question(
                self, "Unsaved changes",
                "You have unsaved changes in the current Job. Discard them and load the selected one?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if confirm != QMessageBox.StandardButton.Yes:
                # Reverte a seleção da lista pra continuar batendo com o formulário
                table.blockSignals(True)
                previous_row = getattr(self, "_current_job_row", None)
                if previous_row is not None and previous_row < table.rowCount():
                    table.setCurrentCell(previous_row, 0)
                else:
                    table.clearSelection()
                table.blockSignals(False)
                return

        self._loading_job_form = True
        job_id = job_id_text
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM work_days WHERE ID = %s", (job_id,))
            columns = [d[0] for d in cursor.description]
            row = cursor.fetchone()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not load job:\n{e}")
            self._loading_job_form = False
            return

        if not row:
            self._loading_job_form = False
            return

        data = dict(zip(columns, row))
        self._current_job_id = data["ID"]
        self.ui.txt_job_id.setText(str(data["ID"]))
        self.ui.lbl_job_id_display.setText(f"#ID: {data['ID']}")

        if data.get("WORK_DATE"):
            wd = data["WORK_DATE"]
            self.ui.date_work_date.setDate(wd if isinstance(wd, date) else date.today())

        self._set_combo_by_data(self.ui.cmb_status_form, data.get("STATUS"), by_text=True)
        self._set_combo_by_data(self.ui.cmb_contractor, data.get("CONTRACTOR_ID"))
        self._set_combo_by_data(self.ui.cmb_helper, data.get("HELPER_ID"))
        self._load_job_helpers(data.get("ID"), data)
        self._load_work_type_list(data.get("ID"), data)
        self._set_combo_by_data(self.ui.cmb_company_form, data.get("COMPANY_ID"))
        self._set_combo_by_data(self.ui.cmb_client_state, data.get("STATE_ID"))
        self._reload_city_combo_for_state(self.ui.cmb_client_city, data.get("STATE_ID"), keep_city_id=data.get("CITY_ID"))
        self._set_combo_by_data(self.ui.cmb_payment, data.get("PAYMENT_METHOD"), by_text=True)

        self.ui.cmb_job_code.setCurrentText("")
        if data.get("JOB_PROJECT_ID"):
            try:
                conn3 = self._get_connection()
                cur3 = conn3.cursor()
                cur3.execute("SELECT CODE FROM job_projects WHERE ID = %s", (data["JOB_PROJECT_ID"],))
                code_row = cur3.fetchone()
                cur3.close()
                conn3.close()
                if code_row:
                    self.ui.cmb_job_code.setCurrentText(code_row[0])
            except (MySQLError, RuntimeError):
                pass
        self._update_days_worked_label()
        self._load_job_materials()

        work_type_fields = [
            ("DEMOLITION_1", self.ui.cmb_demolition, self.ui.dspn_demolition),
            ("DEMOLITION_2", self.ui.cmb_demolition_2, self.ui.dspn_demolition_2),
            ("DEMOLITION_3", self.ui.cmb_demolition_3, self.ui.dspn_demolition_3),
            ("DEMOLITION_4", self.ui.cmb_demolition_4, self.ui.dspn_demolition_4),
            ("INSTALLATION_1", self.ui.cmb_installation, self.ui.dspn_installation),
            ("INSTALLATION_2", self.ui.cmb_installation_2, self.ui.dspn_installation_2),
            ("INSTALLATION_3", self.ui.cmb_installation_3, self.ui.dspn_installation_3),
            ("INSTALLATION_4", self.ui.cmb_installation_4, self.ui.dspn_installation_4),
            ("PREPARATION_1", self.ui.cmb_preparation, self.ui.dspn_preparation),
            ("PREPARATION_2", self.ui.cmb_preparation_2, self.ui.dspn_preparation_2),
            ("PREPARATION_3", self.ui.cmb_preparation_3, self.ui.dspn_preparation_3),
            ("PREPARATION_4", self.ui.cmb_preparation_4, self.ui.dspn_preparation_4),
            ("OTHERS_1", self.ui.cmb_others, self.ui.dspn_others),
            ("OTHERS_2", self.ui.cmb_others_2, self.ui.dspn_others_2),
            ("REPARO_1", self.ui.cmb_reparo, self.ui.dspn_reparo),
            ("REPARO_2", self.ui.cmb_reparo_2, self.ui.dspn_reparo_2),
        ]
        for prefix, combo, spin in work_type_fields:
            self._set_combo_by_data(combo, data.get(f"{prefix}_ID"))
            qty = data.get(f"{prefix}_QTY")
            spin.setValue(float(qty) if qty is not None else 1)

        # Marca o checkbox da categoria automaticamente se algum item dela tiver dado salvo
        # (senão os campos ficariam bloqueados escondendo dados que já existem)
        category_prefixes = {
            self.ui.chk_demolition: ["DEMOLITION_1", "DEMOLITION_2", "DEMOLITION_3", "DEMOLITION_4"],
            self.ui.chk_preparation: ["PREPARATION_1", "PREPARATION_2", "PREPARATION_3", "PREPARATION_4"],
            self.ui.chk_installation: ["INSTALLATION_1", "INSTALLATION_2", "INSTALLATION_3", "INSTALLATION_4"],
            self.ui.chk_others: ["OTHERS_1", "OTHERS_2"],
            self.ui.chk_reparo: ["REPARO_1", "REPARO_2"],
        }
        for checkbox, prefixes in category_prefixes.items():
            has_data = any(data.get(f"{p}_ID") for p in prefixes)
            checkbox.setChecked(has_data)

        # Busca nome/email/telefone do cliente (não ficam salvos em work_days, vêm de clients)
        self.ui.txt_client_name.clear()
        self.ui.txt_client_email.clear()
        self.ui.txt_client_phone.clear()
        self.ui.txt_client_phone_2.clear()
        if data.get("CLIENT_ID"):
            try:
                conn2 = self._get_connection()
                cursor2 = conn2.cursor()
                cursor2.execute(
                    "SELECT FULL_NAME, EMAIL, PHONE_NUMBER, PHONE_NUMBER2 FROM clients WHERE ID = %s",
                    (data["CLIENT_ID"],),
                )
                client_row = cursor2.fetchone()
                cursor2.close()
                conn2.close()
                if client_row:
                    self.ui.txt_client_name.setText(client_row[0] or "")
                    self.ui.txt_client_email.setText(client_row[1] or "")
                    self.ui.txt_client_phone.setText(self._format_phone(client_row[2]) or "")
                    self.ui.txt_client_phone_2.setText(self._format_phone(client_row[3]) or "")
            except (MySQLError, RuntimeError):
                pass  # não bloqueia o carregamento do job se isso falhar

        try:
            self.ui.dspn_value.setValue(float(data.get("VALUE") or 0))
        except (TypeError, ValueError):
            self.ui.dspn_value.setValue(0)
        self.ui.cmb_client_address.setCurrentText(data.get("JOB_ADDRESS") or "")
        self.ui.txt_client_address2.setText(data.get("JOB_ADDRESS2") or "")
        self.ui.txt_client_zip.setText(self._format_zip(data.get("ZIP_CODE")) or "")
        self.ui.txt_note.setPlainText(data.get("NOTE") or "")

        self.ui.tabWidget_jobs.setCurrentWidget(self.ui.tab_jobs_master)
        self._current_job_row = selected
        self._loading_job_form = False
        self._job_form_dirty = False

    # Campos de Client Info / Job Info que são do projeto (iguais em todos os
    # dias do mesmo Job Code). Work Date, Status, Value, Note, Helper e Work
    # Types ficam de fora: mudam de um dia pro outro.
    _JOB_CODE_SHARED_FIELDS = ("CLIENT_ID", "COMPANY_ID", "CONTRACTOR_ID", "PAYMENT_METHOD",
                               "JOB_ADDRESS", "JOB_ADDRESS2", "CITY_ID", "STATE_ID", "ZIP_CODE")

    def _job_code_shared_changes(self, cursor, data, job_project_id):
        """Campos compartilhados que o usuário mudou neste save, comparando com
        o que este dia tinha antes (ou, num dia novo, com os dados que o Job
        Code já tinha). Só valores preenchidos são propagados; comparar com o
        próprio dia evita que salvar um dia antigo desfaça correções feitas
        nos outros dias."""
        if not job_project_id:
            return {}
        cols = ", ".join(self._JOB_CODE_SHARED_FIELDS)
        baseline = None
        if self._current_job_id:
            cursor.execute(f"SELECT JOB_PROJECT_ID, {cols} FROM work_days WHERE ID = %s", (self._current_job_id,))
            row = cursor.fetchone()
            if row and row[0] == job_project_id:
                baseline = row[1:]
        if baseline is None:
            cursor.execute(f"SELECT {cols} FROM work_days WHERE JOB_PROJECT_ID = %s ORDER BY ID DESC",
                           (job_project_id,))
            rows = cursor.fetchall()
            if not rows:
                return {}  # primeiro dia do código: não há outros pra atualizar
            baseline = [next((r[i] for r in rows if r[i] not in (None, "")), None)
                        for i in range(len(self._JOB_CODE_SHARED_FIELDS))]

        def norm(v):
            return "" if v is None else str(v).strip().upper()

        return {field: data[field] for field, old in zip(self._JOB_CODE_SHARED_FIELDS, baseline)
                if data.get(field) not in (None, "") and norm(data[field]) != norm(old)}

    def save_job_record(self):
        """Insere ou atualiza um registro em work_days."""
        # Work Date e Contractor são obrigatórios — não deixar salvar sem eles.
        if not self.ui.date_work_date.date().isValid():
            QMessageBox.warning(self, "Required field", "Work Date is required.")
            return
        if self.ui.cmb_contractor.currentData() is None:
            QMessageBox.warning(self, "Required field", "Please select a Contractor before saving.")
            return

        value = self.ui.dspn_value.value()

        # O combo de endereço também mostra "— Select —" como placeholder quando
        # nada foi digitado/escolhido — nunca deixar isso virar texto salvo.
        job_address_text = self.ui.cmb_client_address.currentText().strip()
        if job_address_text == self.ui.cmb_client_address.itemText(0).strip():
            job_address_text = ""

        # Resolve o Job Code: usa o projeto já existente com esse código, ou
        # cria um novo (caso o usuário tenha digitado um código novo direto,
        # sem clicar em "Generate Code").
        job_code_text = self.ui.cmb_job_code.currentText().strip().upper()
        job_project_id = self._job_code_to_id.get(job_code_text) if job_code_text else None
        if job_code_text and not job_project_id:
            try:
                conn_jc = self._get_connection()
                cur_jc = conn_jc.cursor()
                cur_jc.execute(
                    "INSERT INTO job_projects (CODE, PROJECT_TYPE, STATUS) VALUES (%s, 'DAY_WORK', 'ACTIVE')",
                    (job_code_text,),
                )
                conn_jc.commit()
                job_project_id = cur_jc.lastrowid
                cur_jc.close()
                conn_jc.close()
                self._job_code_to_id[job_code_text] = job_project_id
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(self, "Database Error", f"Could not save the job code:\n{e}")
                return

        data = {
            "WORK_DATE": self.ui.date_work_date.date().toString("yyyy-MM-dd"),
            "CONTRACTOR_ID": self.ui.cmb_contractor.currentData(),
            "COMPANY_ID": self.ui.cmb_company_form.currentData(),
            "NOTE": self.ui.txt_note.toPlainText(),
            "STATUS": self.ui.cmb_status_form.currentText(),
            "PAYMENT_METHOD": self.ui.cmb_payment.currentText(),
            "VALUE": value,
            "JOB_ADDRESS": job_address_text,
            "JOB_ADDRESS2": self.ui.txt_client_address2.text(),
            "CITY_ID": self.ui.cmb_client_city.currentData(),
            "STATE_ID": self.ui.cmb_client_state.currentData(),
            "ZIP_CODE": self._format_zip(self.ui.txt_client_zip.text()),
            "JOB_PROJECT_ID": job_project_id,
        }
        # HELPER_ID só entra no INSERT/UPDATE se a coluna já existir —
        # assim, se a migração do Helpers ainda não rodou, o resto do Job
        # continua salvando normalmente (só não guarda o Helper ainda).
        # Equipe do dia (botão Helpers): em work_days fica só o resumo —
        # primeiro helper e soma dos pagamentos; a lista completa vai para
        # work_day_helpers logo depois do INSERT/UPDATE (paginas/equipe.py).
        crew_first, crew_total = self._crew_summary_fields()
        if self._table_column_exists("work_days", "HELPER_ID"):
            data["HELPER_ID"] = crew_first
        if self._table_column_exists("work_days", "HELPER_PAY"):
            data["HELPER_PAY"] = crew_total

        # Tipos de trabalho: cada combo (ID) + seu spinbox de quantidade
        work_type_fields = [
            ("DEMOLITION_1", self.ui.cmb_demolition, self.ui.dspn_demolition),
            ("DEMOLITION_2", self.ui.cmb_demolition_2, self.ui.dspn_demolition_2),
            ("DEMOLITION_3", self.ui.cmb_demolition_3, self.ui.dspn_demolition_3),
            ("DEMOLITION_4", self.ui.cmb_demolition_4, self.ui.dspn_demolition_4),
            ("INSTALLATION_1", self.ui.cmb_installation, self.ui.dspn_installation),
            ("INSTALLATION_2", self.ui.cmb_installation_2, self.ui.dspn_installation_2),
            ("INSTALLATION_3", self.ui.cmb_installation_3, self.ui.dspn_installation_3),
            ("INSTALLATION_4", self.ui.cmb_installation_4, self.ui.dspn_installation_4),
            ("PREPARATION_1", self.ui.cmb_preparation, self.ui.dspn_preparation),
            ("PREPARATION_2", self.ui.cmb_preparation_2, self.ui.dspn_preparation_2),
            ("PREPARATION_3", self.ui.cmb_preparation_3, self.ui.dspn_preparation_3),
            ("PREPARATION_4", self.ui.cmb_preparation_4, self.ui.dspn_preparation_4),
            ("OTHERS_1", self.ui.cmb_others, self.ui.dspn_others),
            ("OTHERS_2", self.ui.cmb_others_2, self.ui.dspn_others_2),
            ("REPARO_1", self.ui.cmb_reparo, self.ui.dspn_reparo),
            ("REPARO_2", self.ui.cmb_reparo_2, self.ui.dspn_reparo_2),
        ]
        # A lista de Work Types (sem limite de linhas, paginas/servicos.py)
        # preenche as colunas antigas com os primeiros serviços de cada
        # categoria; a lista completa vai para work_day_work_types logo abaixo.
        from paginas.servicos import fixed_column_values
        data.update(fixed_column_values(self._get_work_type_list()))

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Resolve o cliente: acha um já cadastrado com esse nome (sem
            # diferenciar maiúsculas/minúsculas) ou cria um novo automaticamente.
            client_name = self.ui.txt_client_name.text().strip()
            client_id = self._client_name_to_id.get(client_name.lower()) if client_name else None
            is_new_client = bool(client_name) and not client_id

            is_new_address = bool(job_address_text) and not self.ui.cmb_client_address.currentData()

            if is_new_client:
                cursor.execute(
                    """
                    INSERT INTO clients (FULL_NAME, EMAIL, PHONE_NUMBER, PHONE_NUMBER2,
                                          ADDRESS, ADDRESS2, CITY_ID, STATE_ID, ZIP_CODE)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        client_name,
                        self.ui.txt_client_email.text(),
                        self._format_phone(self.ui.txt_client_phone.text()),
                        self._format_phone(self.ui.txt_client_phone_2.text()),
                        job_address_text,
                        self.ui.txt_client_address2.text(),
                        self.ui.cmb_client_city.currentData(),
                        self.ui.cmb_client_state.currentData(),
                        self._format_zip(self.ui.txt_client_zip.text()),
                    ),
                )
                client_id = cursor.lastrowid

            data["CLIENT_ID"] = client_id

            # Dados do projeto que o usuário mudou neste dia (endereço, cliente,
            # company...) valem pra todos os outros dias do mesmo Job Code.
            shared_changes = self._job_code_shared_changes(cursor, data, job_project_id)

            if self._current_job_id:
                set_clause = ", ".join(f"{k} = %s" for k in data)
                query = f"UPDATE work_days SET {set_clause} WHERE ID = %s"
                cursor.execute(query, list(data.values()) + [self._current_job_id])
            else:
                cols = ", ".join(data.keys())
                placeholders = ", ".join(["%s"] * len(data))
                query = f"INSERT INTO work_days ({cols}) VALUES ({placeholders})"
                cursor.execute(query, list(data.values()))
            saved_job_id = self._current_job_id or cursor.lastrowid
            self._save_job_helpers(cursor, saved_job_id)
            self._save_work_type_list(cursor, saved_job_id)

            other_days_updated = 0
            if shared_changes:
                set_clause = ", ".join(f"{k} = %s" for k in shared_changes)
                cursor.execute(
                    f"UPDATE work_days SET {set_clause} WHERE JOB_PROJECT_ID = %s AND ID <> %s",
                    list(shared_changes.values()) + [job_project_id, saved_job_id],
                )
                other_days_updated = cursor.rowcount
                project_cols = {k: v for k, v in shared_changes.items()
                                if k in ("CLIENT_ID", "COMPANY_ID", "CONTRACTOR_ID", "JOB_ADDRESS", "CITY_ID", "STATE_ID")}
                if project_cols:
                    cursor.execute(
                        "UPDATE job_projects SET " + ", ".join(f"{k} = %s" for k in project_cols) + " WHERE ID = %s",
                        list(project_cols.values()) + [job_project_id],
                    )

            conn.commit()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not save job:\n{e}")
            return

        # Preenche (ou completa) os dados "mestre" desse projeto em
        # job_projects — são esses dados que auto-preenchem o formulário da
        # próxima vez que esse Job Code for digitado/selecionado (ver
        # _on_job_code_editing_finished). De propósito só grava isso AQUI,
        # depois do cliente já ter sido resolvido/criado acima: antes essa
        # gravação rodava ANTES da resolução do cliente, então um cliente
        # novo (criado nesse mesmo Save) ainda não tinha ID nenhum, e o
        # projeto ficava com CLIENT_ID em branco pra sempre — por isso
        # "Fill this form" parava de preencher o nome/telefone/e-mail do
        # cliente em projetos assim, mesmo já tendo cliente salvo no dia de
        # trabalho. Usa COALESCE pra só completar o que ainda estiver vazio
        # (repara projetos antigos que ficaram faltando algum campo, sem
        # sobrescrever dado diferente que já esteja lá).
        if job_project_id:
            try:
                conn_jc2 = self._get_connection()
                cur_jc2 = conn_jc2.cursor()
                # HELPER_ID entra no COALESCE só se a coluna já existir em
                # job_projects (migração do Helpers) — do contrário, o resto
                # do snapshot continua sendo atualizado do mesmo jeito.
                set_parts = [
                    "CLIENT_ID = COALESCE(CLIENT_ID, %s)",
                    "COMPANY_ID = COALESCE(COMPANY_ID, %s)",
                    "CONTRACTOR_ID = COALESCE(CONTRACTOR_ID, %s)",
                    "JOB_ADDRESS = COALESCE(JOB_ADDRESS, %s)",
                    "CITY_ID = COALESCE(CITY_ID, %s)",
                    "STATE_ID = COALESCE(STATE_ID, %s)",
                ]
                params = [data["CLIENT_ID"], data["COMPANY_ID"], data["CONTRACTOR_ID"],
                          data["JOB_ADDRESS"], data["CITY_ID"], data["STATE_ID"]]
                if "HELPER_ID" in data and self._table_column_exists("job_projects", "HELPER_ID"):
                    set_parts.append("HELPER_ID = COALESCE(HELPER_ID, %s)")
                    params.append(data["HELPER_ID"])
                cur_jc2.execute(
                    "UPDATE job_projects SET " + ", ".join(set_parts) + " WHERE ID = %s",
                    params + [job_project_id],
                )
                conn_jc2.commit()
                cur_jc2.close()
                conn_jc2.close()
            except (MySQLError, RuntimeError):
                pass  # não bloqueia o fluxo de salvar o job por causa disso

        if other_days_updated:
            labels = {"CLIENT_ID": "Client", "COMPANY_ID": "Company", "CONTRACTOR_ID": "Contractor",
                      "PAYMENT_METHOD": "Payment Method", "JOB_ADDRESS": "Address", "JOB_ADDRESS2": "Address 2",
                      "CITY_ID": "City", "STATE_ID": "State", "ZIP_CODE": "ZIP Code"}
            QMessageBox.information(
                self, "Success",
                f"Job record saved successfully.\n\nAlso updated {other_days_updated} other day(s) of "
                f"{job_code_text}: {', '.join(labels[k] for k in shared_changes)}.")
        else:
            QMessageBox.information(self, "Success", "Job record saved successfully.")

        if is_new_client:
            QMessageBox.information(
                self, "New Client Saved",
                f"'{client_name}' wasn't in your client list, so it was created automatically."
            )
        if is_new_address:
            QMessageBox.information(
                self, "New Address Saved",
                f"'{job_address_text}' is a new address — it's been saved and will show up "
                "as a suggestion next time you type."
            )

        self.load_work_days()
        self.load_schedule_month()
        self.load_combo_data()  # atualiza a lista de clientes (autocomplete) e o combo de endereço
        self.new_job_record()
        self.ui.tabWidget_jobs.setCurrentWidget(self.ui.tab_jobs_master)

    def delete_job_record(self):
        """Exclui o registro atualmente carregado no formulário."""
        if not self._current_job_id:
            QMessageBox.information(self, "No record selected",
                                     "Select a record from the list (double-click) before deleting.")
            return

        confirm = QMessageBox.question(
            self, "Confirm delete",
            f"Are you sure you want to delete job #{self._current_job_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM work_days WHERE ID = %s", (self._current_job_id,))
            conn.commit()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not delete job:\n{e}")
            return

        QMessageBox.information(self, "Deleted", "Job record deleted.")
        self.new_job_record()
        self.load_work_days()
        self.load_schedule_month()
        self.ui.tabWidget_jobs.setCurrentWidget(self.ui.tab_jobs_master)

    def open_split_daily_total_dialog(self):
        """Abre uma janela pra escolher uma data, ver os jobs daquele dia,
        digitar o total recebido e dividir automaticamente entre eles."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Split Daily Total")
        dialog.resize(880, 520)
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
        """)

        layout = QVBoxLayout(dialog)

        # Linha: data + botão carregar
        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("Work Date:"))
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDisplayFormat("MM/dd/yyyy")
        date_edit.setDate(date.today())
        top_row.addWidget(date_edit)

        btn_load = QPushButton("Load Jobs")
        btn_load.setCursor(Qt.CursorShape.PointingHandCursor)
        top_row.addWidget(btn_load)
        top_row.addStretch()
        layout.addLayout(top_row)

        # Linha: total do dia + botão dividir
        total_row = QHBoxLayout()
        total_row.addWidget(QLabel("Total received today ($):"))
        total_spin = QDoubleSpinBox()
        total_spin.setMaximum(999999.99)
        total_spin.setDecimals(2)
        total_spin.setPrefix("$ ")
        total_row.addWidget(total_spin)

        btn_split = QPushButton("Split Evenly")
        btn_split.setCursor(Qt.CursorShape.PointingHandCursor)
        total_row.addWidget(btn_split)
        total_row.addStretch()
        layout.addLayout(total_row)

        # Tabela: jobs do dia, com valor atual e valor novo (editável)
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels(
            ["ID", "Client", "Contractor", "Current Value", "New Value", "Address", "Order"])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        table.setColumnWidth(0, 50)   # ID
        table.setColumnWidth(3, 100)  # Current Value
        table.setColumnWidth(4, 130)  # New Value (spinbox)
        table.setColumnWidth(5, 200)  # Address
        table.setColumnWidth(6, 90)   # Order (spinbox)
        layout.addWidget(table)
        layout.addWidget(QLabel(
            "Tip: set the Order to match the sequence you actually visited each job "
            "(1st, 2nd, 3rd…) — this is what shows up as 'Job 1', 'Job 2'… on invoices."))

        # Linha de status (soma atual vs total)
        lbl_sum_status = QLabel("")
        layout.addWidget(lbl_sum_status)

        # Botões finais
        bottom_row = QHBoxLayout()
        bottom_row.addStretch()
        btn_cancel = QPushButton("Cancel")
        btn_save = QPushButton("Save")
        btn_save.setObjectName("btn_save_job")  # reaproveita o estilo azul já existente
        bottom_row.addWidget(btn_cancel)
        bottom_row.addWidget(btn_save)
        layout.addLayout(bottom_row)

        job_ids = []  # guarda os IDs na mesma ordem das linhas da tabela

        def load_jobs_for_date():
            """Busca no banco os jobs da data escolhida no dialogo e preenche a tabela de divisao de valores."""
            job_ids.clear()
            work_date = date_edit.date().toString("yyyy-MM-dd")
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT wd.ID, COALESCE(cl.FULL_NAME, '—'), COALESCE(c.COMPANY_NAME, c.FULL_NAME, '—'), wd.VALUE,
                           wd.JOB_ADDRESS, wd.DAY_SEQUENCE
                    FROM work_days wd
                    LEFT JOIN clients cl ON cl.ID = wd.CLIENT_ID
                    LEFT JOIN contractors c ON c.ID = wd.CONTRACTOR_ID
                    WHERE wd.WORK_DATE = %s
                    ORDER BY COALESCE(wd.DAY_SEQUENCE, 999999), wd.ID
                    """,
                    (work_date,),
                )
                rows = cursor.fetchall()
                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not load jobs:\n{e}")
                return

            table.setRowCount(len(rows))
            table.verticalHeader().setDefaultSectionSize(44)
            for row_idx, (job_id, client, contractor, value, address, day_sequence) in enumerate(rows):
                job_ids.append(job_id)
                table.setRowHeight(row_idx, 44)
                item_id = QTableWidgetItem(str(job_id))
                item_client = QTableWidgetItem(str(client))
                item_contractor = QTableWidgetItem(str(contractor))
                item_current = QTableWidgetItem(f"${float(value or 0):,.2f}")
                item_address = QTableWidgetItem(str(address or "—"))
                for it in (item_id, item_client, item_contractor, item_current, item_address):
                    it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(row_idx, 0, item_id)
                table.setItem(row_idx, 1, item_client)
                table.setItem(row_idx, 2, item_contractor)
                table.setItem(row_idx, 3, item_current)
                table.setItem(row_idx, 5, item_address)

                new_value_spin = QDoubleSpinBox()
                new_value_spin.setMaximum(999999.99)
                new_value_spin.setDecimals(2)
                new_value_spin.setPrefix("$ ")
                new_value_spin.setValue(float(value or 0))
                new_value_spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
                new_value_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
                new_value_spin.setStyleSheet(
                    "background-color:#FFFFFF; color:#1C2B3A; border:1px solid #CBD5E1; "
                    "border-radius:6px; padding:2px 6px; font-size:13px; min-height:28px;"
                )
                new_value_spin.valueChanged.connect(update_sum_status)
                table.setCellWidget(row_idx, 4, new_value_spin)

                order_spin = QSpinBox()
                order_spin.setMinimum(1)
                order_spin.setMaximum(max(len(rows), 1))
                order_spin.setValue(day_sequence if day_sequence else row_idx + 1)
                order_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
                order_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
                order_spin.setStyleSheet(
                    "background-color:#FFFFFF; color:#1C2B3A; border:1px solid #CBD5E1; "
                    "border-radius:6px; padding:2px 6px; font-size:13px; min-height:28px;"
                )
                table.setCellWidget(row_idx, 6, order_spin)

            if not rows:
                lbl_sum_status.setText("No jobs found for this date.")
            update_sum_status()

        def split_evenly():
            """Divide o valor total digitado igualmente entre todos os jobs listados, ajustando o centavo restante no ultimo."""
            if table.rowCount() == 0:
                QMessageBox.information(dialog, "No jobs", "Load a date with jobs first.")
                return
            total = total_spin.value()
            share = round(total / table.rowCount(), 2)
            remainder = round(total - share * table.rowCount(), 2)
            for row_idx in range(table.rowCount()):
                spin = table.cellWidget(row_idx, 4)
                # ajusta o centavo restante no último, pra soma bater exatamente
                extra = remainder if row_idx == table.rowCount() - 1 else 0
                spin.setValue(share + extra)
            update_sum_status()

        def update_sum_status():
            """Compara a soma atual dos valores da tabela com o total-alvo e mostra um aviso visual se nao baterem."""
            total_target = total_spin.value()
            current_sum = sum(
                table.cellWidget(row_idx, 4).value()
                for row_idx in range(table.rowCount())
                if table.cellWidget(row_idx, 4) is not None
            )
            diff = round(total_target - current_sum, 2)
            if abs(diff) < 0.01:
                lbl_sum_status.setText(f"✅ Sum matches: ${current_sum:,.2f}")
                lbl_sum_status.setStyleSheet("color:#2E7D32; font-weight:600;")
            else:
                lbl_sum_status.setText(
                    f"⚠️ Sum is ${current_sum:,.2f} — target is ${total_target:,.2f} (difference: ${diff:,.2f})"
                )
                lbl_sum_status.setStyleSheet("color:#E65100; font-weight:600;")

        def save_new_values():
            """Grava no banco os novos valores definidos para cada job e fecha o dialogo."""
            if table.rowCount() == 0:
                dialog.reject()
                return
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                for row_idx, job_id in enumerate(job_ids):
                    new_value = table.cellWidget(row_idx, 4).value()
                    new_order = table.cellWidget(row_idx, 6).value()
                    cursor.execute(
                        "UPDATE work_days SET VALUE = %s, DAY_SEQUENCE = %s WHERE ID = %s",
                        (new_value, new_order, job_id),
                    )
                conn.commit()
                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not save values:\n{e}")
                return

            QMessageBox.information(dialog, "Success", "Job values updated successfully.")
            self.load_work_days()
            dialog.accept()

        btn_load.clicked.connect(load_jobs_for_date)
        btn_split.clicked.connect(split_evenly)
        total_spin.valueChanged.connect(update_sum_status)
        btn_cancel.clicked.connect(dialog.reject)
        btn_save.clicked.connect(save_new_values)

        load_jobs_for_date()  # já carrega os jobs de hoje ao abrir
        dialog.exec()
