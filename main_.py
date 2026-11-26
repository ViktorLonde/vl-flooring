# -*- coding: utf-8 -*-
"""
VL FLOORING — janela principal.

A MainWindow junta as telas que ficam em paginas/ (cada uma é um mixin com os
métodos daquela parte do sistema). Aqui fica só o que é da janela em si:
inicialização, sidebar animada, navegação entre páginas e ajustes de layout.

Imports e constantes compartilhados: app_common.py.
"""

from app_common import *  # noqa: F401,F403
from paginas.comum import UtilsMixin
from paginas.configuracoes import SettingsMixin
from paginas.compliance import ComplianceMixin
from paginas.conciliacao_bancaria import BankReconciliationMixin
from paginas.caixas_entrada import InboxMixin
from paginas.ajudantes import HelpersMixin
from paginas.jobs import JobsMixin
from paginas.projetos import ProjectsMixin
from paginas.cadastros import RegistrationsMixin
from paginas.faturas import InvoicesMixin
from paginas.faturas_pdf import InvoicePdfMixin
from paginas.recebiveis import ReceivablesMixin
from paginas.relatorios import ReportsMixin
from paginas.home import HomeMixin
from paginas.clientes import CustomersMixin
from paginas.usuarios import UsersMixin
from paginas.despesas import ExpensesMixin
from paginas.permissoes import PermissionsMixin
from paginas.visual import VisualMixin, SIDEBAR_ITEMS
from paginas.recebiveis_plus import ReceivablesPlusMixin
from paginas.controle import ControlMixin
from paginas.particulares import PrivateProjectsMixin
from paginas.ordem_tab import TabOrderMixin
from paginas.moderno import ModernMixin
from paginas.tema import ThemeMixin
from paginas.sessao import SessionMixin
from paginas.operacoes import OperationsMixin
from paginas.equipe import CrewMixin
from paginas.hub import RegistrationsHubMixin
from paginas.ferramentas import ToolsMixin
from paginas.servicos import WorkTypeListMixin
from paginas.padrao_texto import TextStandardMixin
from paginas.digitacao import InputHelpersMixin
from paginas.compras import PurchasesStockMixin
from paginas.painel import BoardSummaryCleanupMixin
from paginas.precos import ServiceRatesMixin
from paginas.fracao import DayPortionMixin
from paginas.hoje import TodayMixin
from paginas.rateio import ExpenseSplitMixin
from paginas.email_teste import EmailTestMixin
from paginas.contador import AccountantMixin
from paginas.inbox_trabalho import WorkInboxMixin
from paginas.emails_clientes import CustomerEmailsMixin
from paginas.financas import FinanceInsightsMixin
from paginas.pos_job import AfterJobMixin
from PySide6.QtCore import Signal


class MainWindow(
    TabOrderMixin,
    PrivateProjectsMixin,
    ControlMixin,
    ReceivablesPlusMixin,
    WorkInboxMixin,
    CustomerEmailsMixin,
    FinanceInsightsMixin,
    AfterJobMixin,
    EmailTestMixin,
    TodayMixin,
    ExpenseSplitMixin,
    DayPortionMixin,
    ServiceRatesMixin,
    AccountantMixin,
    PurchasesStockMixin,
    BoardSummaryCleanupMixin,
    InputHelpersMixin,
    TextStandardMixin,
    WorkTypeListMixin,
    ToolsMixin,
    RegistrationsHubMixin,
    CrewMixin,
    OperationsMixin,
    SessionMixin,
    ThemeMixin,
    ModernMixin,
    VisualMixin,
    PermissionsMixin,
    UtilsMixin,
    SettingsMixin,
    ComplianceMixin,
    BankReconciliationMixin,
    InboxMixin,
    HelpersMixin,
    JobsMixin,
    ProjectsMixin,
    RegistrationsMixin,
    InvoicesMixin,
    InvoicePdfMixin,
    ReceivablesMixin,
    ReportsMixin,
    HomeMixin,
    CustomersMixin,
    UsersMixin,
    ExpensesMixin,
    QMainWindow,
):
    # Emitido ao escolher "Switch user" no menu do nome (app.py volta pro login)
    signed_out = Signal()

    def __init__(self, db_config: dict | None = None):
        """Inicializa a janela principal: carrega a UI, guarda a config do banco, monta a sidebar animada, conecta todos os sinais e carrega os dados iniciais de cada modulo."""
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Credenciais do banco: usa as recebidas (ex: vindas do app.py com o
        # servidor real 192.168.4.34) ou cai no DB_CONFIG local deste arquivo.
        self.db_config = db_config or DB_CONFIG
        self._load_app_settings_from_db()

        self._sidebar_expanded = False
        self._current_job_id = None  # None = modo "novo registro"
        self._current_job_row = None  # linha da tabela correspondente ao job carregado
        self._job_form_dirty = False
        self._loading_job_form = False  # evita marcar como "sujo" enquanto carrega dados no formulário

        self._setup_compliance_feature()
        self._setup_sales_tax_feature()
        self._setup_project_budget_feature()
        self._setup_documents_feature()
        self._setup_bank_reconciliation_feature()
        self._setup_receipt_inbox_feature()
        self._setup_job_site_inbox_feature()
        self._setup_helpers_feature()
        self._setup_helper_field()
        self._setup_projects_dashboard_feature()
        self._setup_sidebar_animation()
        self._setup_client_drawer_animation()
        self._setup_client_drawer_scrollable()
        self._setup_pages_size_isolation()
        self._setup_combo_width_limits()
        self._set_collapsed_instant()
        self._connect_signals()
        self._setup_autocomplete_combos()
        self._setup_phone_input_masks()
        self._setup_zip_code_fields()
        self._setup_job_code_completer()
        self._setup_product_unit_completer()
        self._setup_work_type_unit_display()
        self._setup_work_type_category_locks()
        self._setup_incomplete_jobs_button()
        self._setup_change_history_button()
        self._setup_operations()
        self._setup_crew_ui()
        self._setup_helper_pay_tab()
        self._setup_products_no_price_filter()
        self._setup_tools()
        self._setup_board_summary_tools()
        self._setup_material_hint()
        self._setup_stock_button()
        self._setup_work_type_decimals()
        self._setup_rate_hint()
        self._setup_day_portion_field()
        self._setup_work_type_list()
        self._setup_rates_tools()
        self._setup_accountant_tools()
        self._setup_today_card()
        self._setup_expense_split_button()
        self._setup_email_test_button()
        self._setup_title_case_fields()
        self._setup_zip_suggestions()
        self._refresh_material_product_combo()
        self._setup_work_inboxes()
        self._setup_finance_tools()
        self._setup_receivables_plus()
        self._setup_private_projects()
        self._setup_after_job_tools()
        self._setup_registrations_hub()
        self._setup_icon_theme()
        self._setup_modern_ui()
        self._setup_theme_toggle()
        self._setup_user_menu()
        self._setup_customer_invoices_button()
        self._setup_restore_backup_button()
        self._setup_settings_tabs()
        self._check_files_folder_on_start()
        self._setup_tab_order()
        self._setup_dashboard_period_filter()
        self._setup_pnl_period_filter()
        self._setup_1099_year_filter()
        self._setup_sales_summary_period_filter()
        self._setup_job_date_filter_defaults()
        self._setup_job_form_dirty_tracking()

        # Carrega dados iniciais
        self._invoice_row_meta = {}
        self.load_work_days()
        self.load_schedule_month()
        self.load_combo_data()
        self.load_companies()
        self.load_contractors()
        self.load_users()
        self.load_work_types()
        self.load_products()
        self.load_expenses()
        self._refresh_expense_entity_combo()
        self.load_customers()
        self._refresh_compliance_alerts()
        self._go_to_page(0, self.ui.btn_home)

    def closeEvent(self, event):
        """Pede confirmação antes de fechar o sistema, pra evitar sair sem
        querer e perder o que estava sendo digitado."""
        if getattr(self, "_closing_for_sign_out", False):
            event.accept()  # "Switch user": fecha sem perguntar
            return
        confirm = QMessageBox.question(
            self,
            "Exit VL Flooring",
            "Are you sure you want to exit the system?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.save_ui_state()
            event.accept()
        else:
            event.ignore()

    def _setup_sidebar_animation(self):
        """Cria as animacoes de largura (minima/maxima) da sidebar e registra o event filter que detecta quando o mouse entra/sai dela."""
        self._anim_min = QPropertyAnimation(self.ui.Left_container, b"minimumWidth")
        self._anim_min.setDuration(ANIM_DURATION)
        self._anim_min.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self._anim_max = QPropertyAnimation(self.ui.Left_container, b"maximumWidth")
        self._anim_max.setDuration(ANIM_DURATION)
        self._anim_max.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self.installEventFilter(self)
        self.ui.Left_container.installEventFilter(self)  # detecta hover (mouse entra/sai)

    def _toggle_table_expanded(self):
        """Esconde o formulário (e fecha a gaveta de Client Info, se aberta)
        pra tabela de Work Days ocupar a largura toda, e vice-versa."""
        table_expanded = getattr(self, "_table_expanded", False)

        if not table_expanded:
            # Fecha a gaveta antes de expandir, se estiver aberta
            if self._client_drawer_expanded:
                self._toggle_client_drawer()
            self.ui.frame_jobs_right_panel.setVisible(False)
            self.ui.frame_jobs_left_panel.setMaximumWidth(16777215)
            self.ui.btn_toggle_table_expanded.setText("⛶  Collapse Table")
        else:
            self.ui.frame_jobs_right_panel.setVisible(True)
            self.ui.frame_jobs_left_panel.setMaximumWidth(460)
            self.ui.btn_toggle_table_expanded.setText("⛶  Expand Table")

        self._table_expanded = not table_expanded

    def _toggle_users_table_expanded(self):
        """Esconde o formulário de User pra tabela ocupar a largura toda, e vice-versa."""
        table_expanded = getattr(self, "_users_table_expanded", False)

        if not table_expanded:
            self.ui.frame_users_right_panel.setVisible(False)
            self.ui.frame_users_left_panel.setMaximumWidth(16777215)
            self.ui.btn_toggle_users_table_expanded.setText("⛶  Collapse Table")
        else:
            self.ui.frame_users_right_panel.setVisible(True)
            self.ui.frame_users_left_panel.setMaximumWidth(460)
            self.ui.btn_toggle_users_table_expanded.setText("⛶  Expand Table")

        self._users_table_expanded = not table_expanded

    def _toggle_companies_table_expanded(self):
        table_expanded = getattr(self, "_companies_table_expanded", False)
        if not table_expanded:
            self.ui.frame_companies_right_panel.setVisible(False)
            self.ui.frame_companies_left_panel.setMaximumWidth(16777215)
            self.ui.btn_toggle_companies_table_expanded.setText("⛶  Collapse Table")
        else:
            self.ui.frame_companies_right_panel.setVisible(True)
            self.ui.frame_companies_left_panel.setMaximumWidth(460)
            self.ui.btn_toggle_companies_table_expanded.setText("⛶  Expand Table")
        self._companies_table_expanded = not table_expanded

    def _toggle_contractors_table_expanded(self):
        table_expanded = getattr(self, "_contractors_table_expanded", False)
        if not table_expanded:
            self.ui.frame_contractors_right_panel.setVisible(False)
            self.ui.frame_contractors_left_panel.setMaximumWidth(16777215)
            self.ui.btn_toggle_contractors_table_expanded.setText("⛶  Collapse Table")
        else:
            self.ui.frame_contractors_right_panel.setVisible(True)
            self.ui.frame_contractors_left_panel.setMaximumWidth(460)
            self.ui.btn_toggle_contractors_table_expanded.setText("⛶  Expand Table")
        self._contractors_table_expanded = not table_expanded

    def _toggle_work_types_table_expanded(self):
        table_expanded = getattr(self, "_work_types_table_expanded", False)
        if not table_expanded:
            self.ui.frame_work_types_right_panel.setVisible(False)
            self.ui.frame_work_types_left_panel.setMaximumWidth(16777215)
            self.ui.btn_toggle_work_types_table_expanded.setText("⛶  Collapse Table")
        else:
            self.ui.frame_work_types_right_panel.setVisible(True)
            self.ui.frame_work_types_left_panel.setMaximumWidth(460)
            self.ui.btn_toggle_work_types_table_expanded.setText("⛶  Expand Table")
        self._work_types_table_expanded = not table_expanded

    def _toggle_expenses_table_expanded(self):
        table_expanded = getattr(self, "_expenses_table_expanded", False)
        if not table_expanded:
            self.ui.frame_expenses_right_panel.setVisible(False)
            self.ui.frame_expenses_left_panel.setMaximumWidth(16777215)
            self.ui.btn_toggle_expenses_table_expanded.setText("⛶  Collapse Table")
        else:
            self.ui.frame_expenses_right_panel.setVisible(True)
            self.ui.frame_expenses_left_panel.setMaximumWidth(460)
            self.ui.btn_toggle_expenses_table_expanded.setText("⛶  Expand Table")
        self._expenses_table_expanded = not table_expanded

    def _setup_client_drawer_animation(self):
        """Cria a animação de largura da 'gaveta' de Client Info (mesmo
        princípio da sidebar): fica fechada (0px) até o usuário clicar em
        '👤 Client Info', então desliza abrindo, sem atrapalhar o foco em
        Work Types no resto do formulário."""
        self._client_drawer_expanded = False
        self._client_drawer_anim_min = QPropertyAnimation(self.ui.frame_client_drawer, b"minimumWidth")
        self._client_drawer_anim_min.setDuration(ANIM_DURATION)
        self._client_drawer_anim_min.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self._client_drawer_anim_max = QPropertyAnimation(self.ui.frame_client_drawer, b"maximumWidth")
        self._client_drawer_anim_max.setDuration(ANIM_DURATION)
        self._client_drawer_anim_max.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._client_drawer_anim_max.finished.connect(self._on_client_drawer_anim_finished)
        self._drawer_hid_left_panel = False

    def _on_client_drawer_anim_finished(self):
        """Quando a gaveta termina de fechar, devolve a tabela de Work Days
        (se ela foi escondida pra gaveta caber na tela)."""
        if not self._client_drawer_expanded and self._drawer_hid_left_panel:
            self._drawer_hid_left_panel = False
            self.ui.frame_jobs_left_panel.setVisible(True)
        QTimer.singleShot(0, self._fit_window_to_screen)

    def _setup_pages_size_isolation(self):
        """O QStackedWidget usa o MAIOR tamanho mínimo entre TODAS as páginas.
        Se uma página cresce (ex.: texto longo carregado do banco), a janela
        inteira passa a ser mais larga que a tela e todas as páginas ficam
        cortadas à direita. Aqui só a página visível conta pro tamanho."""
        self.ui.Pages.currentChanged.connect(self._isolate_page_sizes)
        self._isolate_page_sizes(self.ui.Pages.currentIndex())

        # F12 ou Ctrl+Shift+D grava layout_debug.txt com os widgets que estão
        # forçando largura (Ctrl+Shift+D é pra notebooks onde F12 precisa de Fn)
        self._layout_debug_shortcuts = []
        for keys in ("F12", "Ctrl+Shift+D"):
            sc = QShortcut(QKeySequence(keys), self)
            sc.setContext(Qt.ShortcutContext.ApplicationShortcut)
            sc.activated.connect(self._dump_layout_debug)
            self._layout_debug_shortcuts.append(sc)

    def _isolate_page_sizes(self, current_index):
        """Páginas escondidas ficam com size policy Ignored (não forçam tamanho)."""
        for i in range(self.ui.Pages.count()):
            page = self.ui.Pages.widget(i)
            policy = QSizePolicy.Policy.Preferred if i == current_index else QSizePolicy.Policy.Ignored
            page.setSizePolicy(policy, policy)
        QTimer.singleShot(0, self._fit_window_to_screen)

    def _fit_window_to_screen(self):
        """Se a janela ficou mais larga que a tela (o Qt alarga mas nunca
        encolhe de volta sozinho), devolve ela pro tamanho da tela."""
        avail = self.screen().availableGeometry()
        if self.width() <= avail.width():
            return
        if self.isMaximized():
            self.showNormal()
            self.showMaximized()
        else:
            self.resize(avail.width(), min(self.height(), avail.height()))

    def _dump_layout_debug(self):
        """Diagnóstico: lista os widgets da página atual com largura mínima
        maior que o espaço disponível, pra achar quem desconfigura a tela."""
        page = self.ui.Pages.currentWidget()
        screen_w = self.screen().availableGeometry().width()
        lines = [
            f"Gerado em {datetime.now():%Y-%m-%d %H:%M:%S}",
            f"Tela: {screen_w}px | Janela: {self.width()}px | "
            f"Largura minima da janela: {self.minimumSizeHint().width()}px",
            f"Pagina atual: {page.objectName()} (minimo {page.minimumSizeHint().width()}px)",
            "",
            "Widgets com largura minima grande (provaveis culpados):",
        ]
        rows = []
        for wdg in page.findChildren(QWidget):
            if not wdg.isVisible():
                continue
            min_w = max(wdg.minimumSizeHint().width(), wdg.minimumWidth())
            parent = wdg.parentWidget()
            if parent is None or min_w < 300:
                continue
            text = ""
            for getter in ("text", "currentText", "placeholderText"):
                if hasattr(wdg, getter):
                    try:
                        text = str(getattr(wdg, getter)())[:120]
                        break
                    except TypeError:
                        pass
            rows.append((min_w, f"{min_w:5}px  {type(wdg).__name__:14} {wdg.objectName() or '(sem nome)':40} "
                                f"pai={parent.objectName() or type(parent).__name__}  texto='{text}'"))
        rows.sort(key=lambda r: -r[0])
        lines += [r[1] for r in rows[:60]] or ["(nenhum)"]

        path = os.path.join(PROJECT_DIR, "diagnostico_layout.txt")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
        except OSError as e:
            QMessageBox.warning(self, "Layout debug", f"Não consegui salvar o diagnóstico:\n{e}")
            return
        QMessageBox.information(self, "Layout debug", f"Diagnóstico salvo em:\n{path}")

    def _toggle_client_drawer(self):
        """Abre ou fecha a gaveta de Client Info."""
        if not self._client_drawer_expanded:
            # Tabela + formulário + gaveta lado a lado podem não caber em telas
            # menores (ex.: notebook 1536px com zoom 125%), o que empurrava a
            # janela pra fora da tela. Nesse caso escondemos a tabela enquanto
            # a gaveta estiver aberta.
            screen_w = self.screen().availableGeometry().width()
            needed = (self.minimumSizeHint().width() + CLIENT_DRAWER_WIDTH
                      + (SIDEBAR_EXPANDED - SIDEBAR_COLLAPSED))
            if needed > screen_w and self.ui.frame_jobs_left_panel.isVisible():
                self._drawer_hid_left_panel = True
                self.ui.frame_jobs_left_panel.setVisible(False)

        start = self.ui.frame_client_drawer.width()
        end = 0 if self._client_drawer_expanded else self._client_drawer_target_width()

        self._client_drawer_anim_min.stop()
        self._client_drawer_anim_max.stop()
        self._client_drawer_anim_min.setStartValue(start)
        self._client_drawer_anim_min.setEndValue(end)
        self._client_drawer_anim_max.setStartValue(start)
        self._client_drawer_anim_max.setEndValue(end)
        self._client_drawer_anim_min.start()
        self._client_drawer_anim_max.start()

        self._client_drawer_expanded = not self._client_drawer_expanded
        self.ui.btn_toggle_client_drawer.setText(
            "👤  Client Info  ✕" if self._client_drawer_expanded else "👤  Client Info"
        )

    def _client_drawer_target_width(self):
        """Largura da gaveta que cabe na tela: até CLIENT_DRAWER_WIDTH, mas
        nunca empurrando a janela além da largura disponível (mínimo 440)."""
        screen_w = self.screen().availableGeometry().width()
        drawer = self.ui.frame_client_drawer
        others = self.minimumSizeHint().width() - max(drawer.minimumWidth(), 0)
        if self._drawer_hid_left_panel:  # a tabela acabou de ser escondida — não conta
            others -= self.ui.frame_jobs_left_panel.minimumSizeHint().width() + 16
        if self._sidebar_expanded:
            others -= SIDEBAR_EXPANDED - SIDEBAR_COLLAPSED
        free = screen_w - others - 8
        return max(470, min(CLIENT_DRAWER_WIDTH, free))

    def _setup_combo_width_limits(self):
        """Combos com textos longos vindos do banco (produtos, empresas…)
        alargavam a página inteira (o Qt dimensiona o combo pelo maior item)
        — era isso que empurrava a tela pra fora com a gaveta de Client Info
        aberta. Quando o maior item passa de ~240px, o combo passa a
        dimensionar por 20 caracteres; a lista aberta continua mostrando o
        nome inteiro (o Qt alarga o popup sozinho)."""
        def limit(combo):
            import shiboken6
            if not shiboken6.isValid(combo):
                return
            if combo.sizeAdjustPolicy() == QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon:
                return
            fm = combo.fontMetrics()
            longest = max((fm.horizontalAdvance(combo.itemText(i)) for i in range(combo.count())), default=0)
            if longest > 240:
                combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
                combo.setMinimumContentsLength(20)
                combo.updateGeometry()

        for combo in self.findChildren(QComboBox):
            model = combo.model()
            model.rowsInserted.connect(lambda *_a, c=combo: limit(c))
            model.modelReset.connect(lambda *_a, c=combo: limit(c))
            limit(combo)
        # O título "Work Day Record" pode sumir quando falta espaço no cabeçalho
        title = getattr(self.ui, "lbl_form_title", None)
        if title is not None:
            title.setMinimumWidth(1)  # prefere o tamanho do texto, mas pode encolher
        # Título "Materials Used" vinha branco fixo (de quando o cabeçalho era
        # escuro) e sumia no cabeçalho claro — usa o mesmo estilo do título
        # "Client Info" (que já funciona no claro e no dark mode).
        mat_title = getattr(self.ui, "lbl_materials_title", None)
        ref_title = getattr(self.ui, "lbl_client_info_title", None)
        if mat_title is not None and ref_title is not None:
            mat_title.setStyleSheet(ref_title.styleSheet())
        # Larguras mínimas do .ui no Job Info somavam ~750px — com a gaveta
        # aberta o card ficava mais largo que o espaço (Payment cortado).
        # Os campos continuam crescendo quando há espaço; só o mínimo cai.
        for name, min_w in (("cmb_contractor", 140), ("cmb_company_form", 140), ("cmb_status_form", 140),
                            ("dspn_value", 110), ("date_work_date", 120), ("cmb_job_code", 130),
                            ("cmb_payment", 120)):
            field = getattr(self.ui, name, None)
            if field is not None:
                field.setMinimumWidth(min_w)
        scroll = getattr(self.ui, "scroll_client_drawer", None)
        if scroll is not None:
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def _setup_client_drawer_scrollable(self):
        """NÃO cria nada novo — o próprio .ui (main_window_vl_flooring_6.ui)
        já vem com um QScrollArea chamado 'scroll_client_drawer' dentro do
        frame_client_drawer, envolvendo todos os campos de Client Info (e
        já configurado com barra de rolagem vertical 'as needed'). Numa
        rodada anterior eu tentei "adicionar" rolagem criando um SEGUNDO
        QScrollArea por cima do que já existia — isso só aninhava uma área
        de rolagem dentro da outra, sem ganho nenhum, e mexeu na conta de
        tamanho mínimo do frame o suficiente pra bagunçar a largura da
        gaveta. Removido: agora essa função só confirma (com segurança,
        sem quebrar nada se algum dia o .ui mudar) que o scroll area
        original existe, e não toca em mais nada. A largura em si é
        controlada só por CLIENT_DRAWER_WIDTH, em _toggle_client_drawer."""
        if not hasattr(self.ui, "scroll_client_drawer"):
            return  # segurança: se o .ui mudar e não tiver mais esse scroll area, não faz nada
        try:
            self.ui.scroll_client_drawer.setWidgetResizable(True)
        except (AttributeError, RuntimeError):
            pass

    def _set_collapsed_instant(self):
        """Deixa a sidebar ja colapsada (60px) sem animacao -- usado uma vez, na abertura do app."""
        self.ui.Left_container.setMinimumWidth(SIDEBAR_COLLAPSED)
        self.ui.Left_container.setMaximumWidth(SIDEBAR_COLLAPSED)
        self._sidebar_expanded = False
        self._update_sidebar_labels()

    def _expand_sidebar(self):
        """Anima a sidebar de colapsada (60px) para expandida (200px)."""
        if self._sidebar_expanded:
            return
        start = self.ui.Left_container.width()
        self._anim_min.setStartValue(start)
        self._anim_min.setEndValue(SIDEBAR_EXPANDED)
        self._anim_max.setStartValue(start)
        self._anim_max.setEndValue(SIDEBAR_EXPANDED)
        self._anim_min.start()
        self._anim_max.start()
        self._sidebar_expanded = True
        self._update_sidebar_labels()

    def _collapse_sidebar(self):
        """Anima a sidebar de expandida (200px) de volta para colapsada (60px)."""
        if not self._sidebar_expanded:
            return
        start = self.ui.Left_container.width()
        self._anim_min.setStartValue(start)
        self._anim_min.setEndValue(SIDEBAR_COLLAPSED)
        self._anim_max.setStartValue(start)
        self._anim_max.setEndValue(SIDEBAR_COLLAPSED)
        self._anim_min.start()
        self._anim_max.start()
        self._sidebar_expanded = False
        self._update_sidebar_labels()

    def _toggle_sidebar(self):
        """Alterna a sidebar entre expandida e colapsada (usado pelo botao de menu)."""
        if self._sidebar_expanded:
            self._collapse_sidebar()
        else:
            self._expand_sidebar()

    def _update_sidebar_labels(self):
        """Mostra/esconde texto dos botões e logo conforme estado da sidebar
        (ícones e nomes ficam em paginas/visual.py → SIDEBAR_ITEMS)."""
        show_text = self._sidebar_expanded
        for attr in SIDEBAR_ITEMS:
            if attr != "btn_reg_compliance":
                self._sidebar_label(attr, show_text)
        self.ui.label_logo.setVisible(show_text)
        # Compliance tem texto próprio porque mostra um contador de itens
        # vencendo (contagem já em cache — não bate no banco a cada hover).
        self._apply_compliance_button_label()

    def eventFilter(self, obj, event):
        """Escuta eventos de mouse/janela: expande a sidebar ao passar o mouse em cima ou maximizar a janela, e colapsa ao sair/restaurar."""
        if obj is self and event.type() == QEvent.Type.WindowStateChange:
            if self.isMaximized():
                self._expand_sidebar()
            else:
                self._collapse_sidebar()

        elif obj is self.ui.lbl_user:
            if event.type() == QEvent.Type.MouseButtonPress:
                self._show_user_menu()
                return True

        elif obj is getattr(self, "_global_search", None):
            if self._global_search_key(event):
                return True

        elif obj is self.ui.Left_container:
            if event.type() == QEvent.Type.Enter:
                self._expand_sidebar()
            elif event.type() == QEvent.Type.Leave:
                self._collapse_sidebar()

        return super().eventFilter(obj, event)

    def _connect_signals(self):
        """Liga cada botao, tabela e campo da interface ao metodo Python que deve rodar quando o usuario interage com eles. E aqui que qualquer widget novo precisa ser conectado."""
        self.ui.btn_toggle.clicked.connect(self._toggle_sidebar)

        # Cidade filtrada por State (Job Address, Company, Contractor)
        self.ui.cmb_client_state.currentIndexChanged.connect(self._on_client_state_changed)
        self.ui.cmb_company_state.currentIndexChanged.connect(self._on_company_state_changed)
        self.ui.cmb_contractor_state.currentIndexChanged.connect(self._on_contractor_state_changed)
        self.ui.cmb_customer_state.currentIndexChanged.connect(self._on_customer_state_changed)

        self.ui.btn_home.clicked.connect(lambda: self._go_to_page(0, self.ui.btn_home))
        self.ui.btn_jobs.clicked.connect(lambda: self._go_to_page(1, self.ui.btn_jobs))
        self.ui.btn_registrations.clicked.connect(self._toggle_registrations_submenu)
        self.ui.btn_reg_companies.clicked.connect(lambda: self._go_to_page(2, self.ui.btn_reg_companies))
        self.ui.btn_reg_contractors.clicked.connect(lambda: self._go_to_page(3, self.ui.btn_reg_contractors))
        self.ui.btn_reg_helpers.clicked.connect(self.open_helpers_manager_dialog)
        self.ui.btn_reg_work_types.clicked.connect(lambda: self._go_to_page(4, self.ui.btn_reg_work_types))
        self.ui.btn_reg_products.clicked.connect(lambda: self._go_to_page(8, self.ui.btn_reg_products))
        self.ui.btn_reg_compliance.clicked.connect(self.open_compliance_manager_dialog)
        self.ui.btn_reg_documents.clicked.connect(lambda: self.open_documents_manager_dialog())
        self.ui.btn_reg_bank_reconciliation.clicked.connect(self.open_bank_reconciliation_dialog)
        self.ui.btn_reg_receipt_inbox.clicked.connect(self.open_receipt_inbox_dialog)
        self.ui.btn_reg_job_site_inbox.clicked.connect(self.open_job_site_inbox_dialog)
        self.ui.btn_reg_projects_dashboard.clicked.connect(self.open_projects_dashboard_dialog)
        self.ui.btn_nav_receivables.clicked.connect(lambda: self._go_to_page(5, self.ui.btn_nav_receivables))
        self.ui.btn_customer.clicked.connect(lambda: self._go_to_page(6, self.ui.btn_customer))
        self.ui.btn_user.clicked.connect(lambda: self._go_to_page(7, self.ui.btn_user))
        self.ui.btn_settings.clicked.connect(lambda: self._go_to_page(9, self.ui.btn_settings))
        self.ui.btn_settings_save.clicked.connect(self.save_settings_form)
        self.ui.btn_settings_change_logo.clicked.connect(self.change_company_logo)

        # Job Records
        self.ui.btn_refresh_jobs.clicked.connect(self.load_work_days)
        self.ui.btn_export_excel_jobs.clicked.connect(
            lambda: self._export_table_to_excel(self.ui.table_work_days, "work_days.xlsx"))
        self.ui.btn_export_pdf_jobs.clicked.connect(
            lambda: self._export_table_to_pdf(self.ui.table_work_days, "work_days.pdf", "Work Days"))
        self.ui.btn_split_daily_total.clicked.connect(self.open_split_daily_total_dialog)
        self.ui.btn_new_job.clicked.connect(self._on_new_job_button_clicked)
        self.ui.btn_save_job.clicked.connect(self.save_job_record)
        self.ui.btn_delete_job.clicked.connect(self.delete_job_record)
        self.ui.txt_search_jobs.textChanged.connect(self.load_work_days)
        self.ui.cmb_filter_status.currentIndexChanged.connect(self.load_work_days)
        self.ui.date_filter_from.dateChanged.connect(self.load_work_days)
        self.ui.date_filter_to.dateChanged.connect(self.load_work_days)
        self.ui.table_work_days.itemSelectionChanged.connect(self.load_job_into_form)
        self.ui.btn_job_go_to_expense.clicked.connect(self._go_to_new_expense_from_job)
        self.ui.btn_toggle_client_drawer.clicked.connect(self._toggle_client_drawer)
        self.ui.btn_toggle_table_expanded.clicked.connect(self._toggle_table_expanded)
        self.ui.btn_toggle_users_table_expanded.clicked.connect(self._toggle_users_table_expanded)
        self.ui.btn_toggle_companies_table_expanded.clicked.connect(self._toggle_companies_table_expanded)
        self.ui.btn_toggle_contractors_table_expanded.clicked.connect(self._toggle_contractors_table_expanded)
        self.ui.btn_toggle_work_types_table_expanded.clicked.connect(self._toggle_work_types_table_expanded)
        self.ui.btn_toggle_expenses_table_expanded.clicked.connect(self._toggle_expenses_table_expanded)
        self.ui.btn_toggle_customers_table_expanded.clicked.connect(self._toggle_customers_table_expanded)
        self.ui.btn_refresh_customers.clicked.connect(self.load_customers)
        self.ui.list_schedule_jobs.itemClicked.connect(self.open_schedule_job)
        self.ui.list_schedule_jobs.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ui.txt_product_type.editingFinished.connect(self._suggest_unit_for_product_type)
        self.ui.dspn_product_price.valueChanged.connect(self._update_product_unit_price_display)
        self.ui.dspn_product_coverage_qty.valueChanged.connect(self._update_product_unit_price_display)
        self.ui.txt_product_coverage_unit.textChanged.connect(self._update_product_unit_price_display)
        self.ui.btn_home_new_job.clicked.connect(self._go_home_new_job)
        self.ui.btn_home_generate_invoices.clicked.connect(self._go_home_generate_invoices)
        self.ui.btn_home_schedule.clicked.connect(self._go_home_schedule)
        self.ui.btn_home_new_customer.clicked.connect(self._go_home_new_customer)
        self.ui.txt_search_customers.textChanged.connect(self.load_customers)
        self.ui.table_customers.itemSelectionChanged.connect(self.load_customer_into_form)
        self.ui.btn_new_customer.clicked.connect(self.new_customer_record)
        self.ui.btn_save_customer.clicked.connect(self.save_customer_record)
        self.ui.btn_delete_customer.clicked.connect(self.delete_customer_record)
        self.ui.btn_export_excel_customers.clicked.connect(
            lambda: self._export_table_to_excel(self.ui.table_customers, "customers.xlsx"))
        self.ui.btn_export_pdf_customers.clicked.connect(
            lambda: self._export_table_to_pdf(self.ui.table_customers, "customers.pdf", "Customers"))
        self.ui.btn_generate_job_code.clicked.connect(self._generate_job_code)
        self.ui.btn_view_project.clicked.connect(self.open_project_view_dialog)
        self.ui.btn_clean_empty_job_codes.clicked.connect(self.open_clean_empty_job_codes_dialog)
        self.ui.cmb_job_code.lineEdit().editingFinished.connect(self._on_job_code_editing_finished)
        self.ui.btn_add_material.clicked.connect(self.add_job_material)
        self.ui.btn_remove_material.clicked.connect(self.remove_job_material)
        # Schedule é a primeira aba de Job Records (pedido do Viktor, 25/11/2026)
        bar = self.ui.tabWidget_jobs.tabBar()
        bar.moveTab(self.ui.tabWidget_jobs.indexOf(self.ui.tab_schedule), 0)
        self.ui.tabWidget_jobs.setCurrentWidget(self.ui.tab_schedule)
        self._previous_job_tab_index = self.ui.tabWidget_jobs.currentIndex()
        self.ui.tabWidget_jobs.currentChanged.connect(self._on_job_tab_changed)

        # Job Records — Schedule
        self.ui.calendar_schedule.currentPageChanged.connect(lambda y, m: self.load_schedule_month())
        self.ui.calendar_schedule.selectionChanged.connect(self.load_schedule_day_jobs)
        self.ui.btn_schedule_new_job.clicked.connect(self.new_job_on_schedule_date)

        # Companies
        self.ui.btn_refresh_companies.clicked.connect(self.load_companies)
        self.ui.btn_export_excel_companies.clicked.connect(
            lambda: self._export_table_to_excel(self.ui.table_companies, "companies.xlsx"))
        self.ui.btn_export_pdf_companies.clicked.connect(
            lambda: self._export_table_to_pdf(self.ui.table_companies, "companies.pdf", "Companies"))
        self.ui.btn_new_company.clicked.connect(self.new_company_record)
        self.ui.btn_save_company.clicked.connect(self.save_company_record)
        self.ui.btn_delete_company.clicked.connect(self.delete_company_record)
        self.ui.txt_search_companies.textChanged.connect(self.load_companies)
        self.ui.cmb_filter_company_status.currentIndexChanged.connect(self.load_companies)
        self.ui.table_companies.itemSelectionChanged.connect(self.load_company_into_form)

        # Contractors
        self.ui.btn_refresh_contractors.clicked.connect(self.load_contractors)
        self.ui.btn_export_excel_contractors.clicked.connect(
            lambda: self._export_table_to_excel(self.ui.table_contractors, "contractors.xlsx"))
        self.ui.btn_export_pdf_contractors.clicked.connect(
            lambda: self._export_table_to_pdf(self.ui.table_contractors, "contractors.pdf", "Contractors"))
        self.ui.btn_new_contractor.clicked.connect(self.new_contractor_record)
        self.ui.btn_save_contractor.clicked.connect(self.save_contractor_record)
        self.ui.btn_delete_contractor.clicked.connect(self.delete_contractor_record)
        self.ui.txt_search_contractors.textChanged.connect(self.load_contractors)
        self.ui.cmb_filter_contractor_status.currentIndexChanged.connect(self.load_contractors)
        self.ui.table_contractors.itemSelectionChanged.connect(self.load_contractor_into_form)

        # Receivables — Invoices
        self.ui.btn_generate_invoices.clicked.connect(self.open_generate_invoices_dialog)
        self.ui.btn_refresh_invoices.clicked.connect(self.load_contractor_invoices)
        self.ui.btn_export_excel_invoices.clicked.connect(
            lambda: self._export_table_to_excel(self.ui.table_contractor_invoices, "invoices.xlsx"))
        self.ui.btn_export_pdf_invoices.clicked.connect(
            lambda: self._export_table_to_pdf(self.ui.table_contractor_invoices, "invoices.pdf", "Invoices"))
        self.ui.btn_send_selected_invoices.clicked.connect(self.open_send_invoices_dialog)
        self.ui.cmb_filter_invoice_status.currentIndexChanged.connect(self.load_contractor_invoices)
        self.ui.cmb_invoice_entity_type.currentIndexChanged.connect(self.load_contractor_invoices)
        self.ui.table_contractor_invoices.itemDoubleClicked.connect(self.open_invoice_detail_dialog)

        # Receivables — Dashboard
        self.ui.cmb_dashboard_month.currentIndexChanged.connect(self.load_receivables_dashboard)
        self.ui.btn_dashboard_record_payment.clicked.connect(self.open_record_payment_dialog)
        self.ui.cmb_dashboard_year.currentIndexChanged.connect(self.load_receivables_dashboard)
        self.ui.cmb_pnl_month.currentIndexChanged.connect(self.load_pnl_report)
        self.ui.cmb_pnl_year.currentIndexChanged.connect(self.load_pnl_report)
        self.ui.btn_export_pdf_pnl.clicked.connect(self.export_pnl_pdf)
        self.ui.cmb_1099_year.currentIndexChanged.connect(self.load_1099_report)
        self.ui.table_1099.cellDoubleClicked.connect(self._toggle_contractor_w9)
        self.ui.btn_export_pdf_1099.clicked.connect(self.export_1099_pdf)
        self.ui.btn_export_excel_1099.clicked.connect(self.export_1099_excel)
        self.ui.cmb_sales_summary_month.currentIndexChanged.connect(self.load_sales_summary)
        self.ui.cmb_sales_summary_year.currentIndexChanged.connect(self.load_sales_summary)
        self.ui.cmb_sales_summary_type.currentIndexChanged.connect(self.load_sales_summary)
        self.ui.btn_export_pdf_sales_summary.clicked.connect(self.export_sales_summary_pdf)

        # Users
        self.ui.btn_refresh_users.clicked.connect(self.load_users)
        self.ui.btn_export_excel_users.clicked.connect(
            lambda: self._export_table_to_excel(self.ui.table_users, "users.xlsx"))
        self.ui.btn_export_pdf_users.clicked.connect(
            lambda: self._export_table_to_pdf(self.ui.table_users, "users.pdf", "Users"))
        self.ui.btn_new_user.clicked.connect(self.new_user_record)
        self.ui.btn_update_user.clicked.connect(self.load_user_into_form)
        self.ui.btn_save_user.clicked.connect(self.save_user_record)
        self.ui.btn_delete_user.clicked.connect(self.delete_user_record)
        self.ui.txt_search_users.textChanged.connect(self.load_users)
        self.ui.cmb_filter_user_status.currentIndexChanged.connect(self.load_users)
        self.ui.table_users.itemSelectionChanged.connect(self.load_user_into_form)

        # Work Types
        self.ui.btn_refresh_work_types.clicked.connect(self.load_work_types)
        self.ui.btn_export_excel_work_types.clicked.connect(
            lambda: self._export_table_to_excel(self.ui.table_work_types, "work_types.xlsx"))
        self.ui.btn_export_pdf_work_types.clicked.connect(
            lambda: self._export_table_to_pdf(self.ui.table_work_types, "work_types.pdf", "Work Types"))
        self.ui.btn_new_work_type.clicked.connect(self.new_work_type_record)
        self.ui.btn_save_work_type.clicked.connect(self.save_work_type_record)
        self.ui.btn_delete_work_type.clicked.connect(self.delete_work_type_record)
        self.ui.txt_search_work_types.textChanged.connect(self.load_work_types)
        self.ui.cmb_filter_work_type_category.currentIndexChanged.connect(self.load_work_types)
        self.ui.table_work_types.itemSelectionChanged.connect(self.load_work_type_into_form)

        # Products
        self.ui.btn_refresh_products.clicked.connect(self.load_products)
        self.ui.btn_export_excel_products.clicked.connect(
            lambda: self._export_table_to_excel(self.ui.table_products, "products.xlsx"))
        self.ui.btn_export_pdf_products.clicked.connect(
            lambda: self._export_table_to_pdf(self.ui.table_products, "products.pdf", "Products"))
        self.ui.btn_new_product.clicked.connect(self.new_product_record)
        self.ui.btn_save_product.clicked.connect(self.save_product_record)
        self.ui.btn_delete_product.clicked.connect(self.delete_product_record)
        self.ui.txt_search_products.textChanged.connect(self.load_products)
        self.ui.table_products.itemDoubleClicked.connect(self.load_product_into_form)

        # Expenses
        self.ui.btn_refresh_expenses.clicked.connect(self.load_expenses)
        self.ui.btn_export_excel_expenses.clicked.connect(
            lambda: self._export_table_to_excel(self.ui.table_expenses, "expenses.xlsx"))
        self.ui.btn_export_pdf_expenses.clicked.connect(
            lambda: self._export_table_to_pdf(self.ui.table_expenses, "expenses.pdf", "Expenses"))
        self.ui.btn_new_expense.clicked.connect(self.new_expense_record)
        self.ui.btn_save_expense.clicked.connect(self.save_expense_record)
        self.ui.btn_delete_expense.clicked.connect(self.delete_expense_record)
        self.ui.btn_expense_attach_receipt.clicked.connect(self.attach_expense_receipt)
        self.ui.cmb_expense_entity_type.currentIndexChanged.connect(self._refresh_expense_entity_combo)
        self.ui.txt_search_expenses.textChanged.connect(self.load_expenses)
        self.ui.cmb_filter_expense_category.currentIndexChanged.connect(self.load_expenses)
        self.ui.cmb_filter_expense_contractor.currentIndexChanged.connect(self.load_expenses)
        self.ui.table_expenses.itemSelectionChanged.connect(self.load_expense_into_form)

    def _toggle_registrations_submenu(self):
        """Mostra/esconde o submenu de Companies/Contractors/Work Types."""
        is_visible = self.ui.frame_registrations_submenu.isVisible()
        self.ui.frame_registrations_submenu.setVisible(not is_visible)
        if not is_visible:
            self._expand_sidebar()  # abre a sidebar pra dar pra ler os nomes

    def _go_to_page(self, index, active_btn):
        """Troca a pagina visivel, marca o botao correspondente como ativo na sidebar e atualiza o titulo no topo. Se for a pagina Receivables, recarrega dashboard e invoices."""
        # Users (7) e Settings (9) são só do Admin — ver paginas/permissoes.py
        if index in (7, 9) and not self._role_rule("admin_pages"):
            return
        # Se está saindo do Job Records com o formulário New/Edit Job com
        # alterações não salvas, confirma antes de trocar de página.
        currently_on_jobs = self.ui.Pages.currentIndex() == 1
        if (currently_on_jobs and index != 1 and getattr(self, "_job_form_dirty", False)
                and self.ui.tabWidget_jobs.currentWidget() is self.ui.tab_jobs_master):
            confirm = QMessageBox.question(
                self, "Unsaved changes",
                "You have unsaved changes in this Job. Leave without saving?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return
            self._job_form_dirty = False  # usuário confirmou que quer descartar

        self.ui.Pages.setCurrentIndex(index)

        top_level_buttons = (self.ui.btn_home, self.ui.btn_jobs, self.ui.btn_nav_receivables,
                              self.ui.btn_customer, self.ui.btn_user, self.ui.btn_settings)
        sub_buttons = (self.ui.btn_reg_companies, self.ui.btn_reg_contractors,
                       self.ui.btn_reg_work_types, self.ui.btn_reg_products)

        projects_btn = getattr(self.ui, "btn_projects", None)
        if projects_btn is not None:
            top_level_buttons = top_level_buttons + (projects_btn,)
        for btn in top_level_buttons:
            btn.setChecked(btn is active_btn)
        for btn in sub_buttons:
            btn.setChecked(btn is active_btn)

        # "Registrations" fica marcado na página de cartões e nas 4 páginas de cadastro
        hub_index = getattr(self, "_hub_index", -1)
        self.ui.btn_registrations.setChecked(index in (2, 3, 4, 8, hub_index))

        titles = {
            0: "Dashboard", 1: "Job Records", 2: "Companies", 3: "Contractors",
            4: "Work Types", 5: "Receivables", 6: "Customer", 7: "User", 8: "Products",
            9: "Settings", hub_index: "Registrations",
        }
        projects_index = getattr(self, "_projects_index", -2)
        titles[projects_index] = "Projects"
        self.ui.Top_label.setText(titles.get(index, ""))

        if index == hub_index:
            self.refresh_registrations_hub()

        if index == projects_index:
            self.load_projects_page()

        if index == 9:
            self.load_settings_form()

        if index == 5:
            self.load_receivables_dashboard()
            self.load_contractor_invoices()
            self.load_pnl_report()
            self.load_1099_report()
            self.load_sales_summary()

        if index == 0:
            self.load_home_dashboard()

        if index == 1:
            # Atualiza os combos (Contractor/Company/Client) toda vez que entra
            # em Job Records, pra sempre refletir cadastros recentes.
            self.load_combo_data()

    def _toggle_customers_table_expanded(self):
        table_expanded = getattr(self, "_customers_table_expanded", False)
        if not table_expanded:
            self.ui.frame_customers_right_panel.setVisible(False)
            self.ui.frame_customers_left_panel.setMaximumWidth(16777215)
            self.ui.btn_toggle_customers_table_expanded.setText("⛶  Collapse Table")
        else:
            self.ui.frame_customers_right_panel.setVisible(True)
            self.ui.frame_customers_left_panel.setMaximumWidth(460)
            self.ui.btn_toggle_customers_table_expanded.setText("⛶  Expand Table")
        self._customers_table_expanded = not table_expanded



# ── ENTRY POINT ───────────────────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())