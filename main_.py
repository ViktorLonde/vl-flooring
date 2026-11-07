# -*- coding: utf-8 -*-
"""
VL FLOORING — Main Application
Sidebar animada (colapsa/expande) + integração com MySQL (vl_bd_flooring.work_days)

Requisitos:
    pip install PySide6 mysql-connector-python
"""

import sys
import os
import tempfile
import hashlib
import shutil
import re
import smtplib
import unicodedata
from email.message import EmailMessage
from datetime import date, datetime, timedelta

from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QSize, Qt, QEvent, QUrl, QDate, QStringListModel, QRectF, QTimer
from PySide6.QtWidgets import (
    QMainWindow, QApplication, QTableWidgetItem, QMessageBox, QCompleter,
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QDateEdit, QDoubleSpinBox,
    QPushButton, QTableWidget, QHeaderView, QAbstractItemView,
    QFileDialog, QCheckBox, QScrollArea, QWidget, QComboBox, QLineEdit,
    QRadioButton, QButtonGroup, QGroupBox, QListWidget, QTextEdit, QFrame, QSpinBox, QTabWidget,
    QProgressBar, QGridLayout, QSizePolicy,
)

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import (SimpleDocTemplate, BaseDocTemplate, PageTemplate, Frame,
                                     NextPageTemplate, Table, TableStyle, Paragraph, Spacer, Image, HRFlowable)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_RIGHT
    from reportlab.pdfgen import canvas as _pdfcanvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
from PySide6.QtGui import QColor, QDesktopServices, QTextCharFormat, QPixmap, QPainter, QBrush, QShortcut, QKeySequence

from ui_main_window_vl_flooring import Ui_MainWindow
from passwords import hash_password

# Driver MySQL — troque por mysql.connector, pymysql ou PyQt sql conforme seu projeto
try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
except ImportError:
    mysql = None
    MySQLError = Exception


# ── CONFIGURAÇÃO DO BANCO ────────────────────────────────────────────
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "vl_bd_flooring",
}

# ── MARCA / INVOICE ───────────────────────────────────────────────────
# Ajuste esses dados livremente — são usados só na geração dos PDFs de invoice.
COMPANY_NAME = "Vertex Londe Construction"
COMPANY_TAGLINE = "CONSTRUCTION"
COMPANY_PHONE = "+00 1234 5678 013"
COMPANY_EMAIL = "info@vertexlonde.com"
COMPANY_WEBSITE = "www.vertexlonde.com"
COMPANY_LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo_icon_only.png")
# Se você desenhar seus próprios efeitos de margem (num Canva/Photoshop/Figma,
# por exemplo), salve como PNG do tamanho de uma página Letter (612x792 pt,
# ou um múltiplo proporcional, ex: 1836x2376 px) com o MEIO da página
# transparente (é onde o conteúdo do invoice entra) e coloque em
# assets/invoice_background.png — o código detecta e usa automaticamente,
# sem precisar mexer em mais nada.
INVOICE_BACKGROUND_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "invoice_background.png")

# Cores extraídas do logo da empresa
BRAND_NAVY = "#16222D"
BRAND_ORANGE = "#E8590C"

# Informações bancárias mostradas na área "Payment Info" do invoice.
COMPANY_BANK_INFO = {
    "account_no": "123456789",
    "account_name": "Vertex Londe Construction",
    "bank_details": "Your Bank Name — Routing 000000000",
}
# Formas de pagamento aceitas, mostradas no invoice.
COMPANY_PAYMENT_METHODS = ["Zelle", "Check", "Cash", "Bank Transfer"]

# ── ENVIO DE INVOICES POR E-MAIL ──────────────────────────────────────
# Preencha com os dados do seu provedor de e-mail (Gmail, Outlook, etc.)
# Para Gmail, use uma "App Password" (não a senha normal da conta) —
# gere em https://myaccount.google.com/apppasswords
EMAIL_SMTP_HOST = "smtp.gmail.com"
EMAIL_SMTP_PORT = 587
EMAIL_SMTP_USER = "your-email@gmail.com"
EMAIL_SMTP_PASSWORD = "your-app-password"
EMAIL_FROM_NAME = COMPANY_NAME

# Rótulos amigáveis de status de pagamento mostrados no PDF (o valor salvo no
# banco continua sendo PENDING/PARTIAL/RECEIVED; isso é só o texto exibido).
PAYMENT_STATUS_LABELS = {
    "PENDING": "Payment Due",
    "PARTIAL": "Partially Paid",
    "RECEIVED": "Paid in Full",
}

JOB_STATUS_LABELS = {
    "PENDING": "Pending",
    "STARTED": "Started",
    "IN_PROGRESS": "In Progress",
    "COMPLETED": "Completed",
    "CANCELLED": "Cancelled",
}

# Status "derivado" de um projeto (Job Code) — job_projects.STATUS sempre
# fica 'ACTIVE' desde a criação (nunca é atualizado em nenhum lugar do
# código), então o Projects Dashboard e o painel da Home calculam o status
# de verdade a partir dos jobs (work_days) ligados àquele Job Code.
PROJECT_STATUS_LABELS = {
    "ACTIVE": "Active",
    "COMPLETED": "Completed",
    "CANCELLED": "Cancelled",
    "NO_JOBS": "No Jobs Yet",
}
PROJECT_STATUS_COLORS = {
    "ACTIVE": QColor("#1565C0"),
    "COMPLETED": QColor("#2E7D32"),
    "CANCELLED": QColor("#C62828"),
    "NO_JOBS": QColor("#9AA5B1"),
}


class _DonutChartWidget(QWidget):
    """Gráfico de rosca (donut) bem simples, desenhado à mão com QPainter —
    de propósito sem depender do módulo QtCharts (que pode nem estar
    instalado), seguindo o mesmo espírito dos gráficos de barra já
    existentes na Home (_draw_home_revenue_chart / _draw_home_work_types_chart),
    que também são desenhados com QFrame/QPainter puro."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._segments = []  # lista de (label, count, QColor)

    def set_data(self, segments):
        self._segments = segments or []
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        side = min(self.width(), self.height()) - 10
        if side <= 0:
            painter.end()
            return
        rect = QRectF((self.width() - side) / 2.0, (self.height() - side) / 2.0, side, side)

        total = sum(count for _, count, _ in self._segments)
        if not total:
            painter.setPen(QColor("#9AA5B1"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No projects yet")
            painter.end()
            return

        start_angle = 90 * 16  # começa no topo (12h) e vai no sentido horário
        for _, count, color in self._segments:
            if not count:
                continue
            span = int(round((count / total) * 360 * 16))
            if span == 0:
                continue
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPie(rect, start_angle, -span)
            start_angle -= span

        # "Buraco" no meio, pra virar rosca em vez de pizza cheia
        hole_ratio = 0.55
        hole_side = side * hole_ratio
        hole_rect = QRectF(
            rect.x() + (side - hole_side) / 2.0,
            rect.y() + (side - hole_side) / 2.0,
            hole_side, hole_side,
        )
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(hole_rect)

        painter.setPen(QColor("#1C2B3A"))
        font = painter.font()
        font.setBold(True)
        font.setPointSize(13)
        painter.setFont(font)
        painter.drawText(hole_rect, Qt.AlignmentFlag.AlignCenter, str(total))
        painter.end()


# ── CONFIGURAÇÃO DA SIDEBAR ──────────────────────────────────────────
SIDEBAR_COLLAPSED = 60
SIDEBAR_EXPANDED = 200
ANIM_DURATION = 250
# Largura da gaveta de Client Info quando expandida — 501px era o valor
# original; +20% a pedido do Viktor (501 * 1.2 ≈ 601).
CLIENT_DRAWER_WIDTH = 601

# Cores de status para a tabela
STATUS_COLORS = {
    "PENDING": QColor("#FFF3E0"),
    "STARTED": QColor("#EDE7F6"),
    "IN_PROGRESS": QColor("#E3F2FD"),
    "COMPLETED": QColor("#E8F5E9"),
    "CANCELLED": QColor("#FFEBEE"),
}
STATUS_TEXT_COLORS = {
    "PENDING": QColor("#E65100"),
    "STARTED": QColor("#5E35B1"),
    "IN_PROGRESS": QColor("#1565C0"),
    "COMPLETED": QColor("#2E7D32"),
    "CANCELLED": QColor("#C62828"),
}

# Rótulos amigáveis das categorias de Work Type usados na descrição do invoice
WORK_TYPE_CATEGORY_LABELS = {
    "DEMOLITION": "Demolition",
    "INSTALLATION": "Installation",
    "PREPARATION": "Preparation",
    "OTHERS": "Others",
    "REPARO": "Repair",
}

if REPORTLAB_AVAILABLE:
    class _InvoiceNumberedCanvas(_pdfcanvas.Canvas):
        """Canvas customizado só pra poder escrever 'Page X of Y' no rodapé —
        o total de páginas (Y) só é conhecido depois que todas as páginas já
        foram desenhadas, então isso é feito num segundo passe, no save()."""

        def __init__(self, *args, **kwargs):
            _pdfcanvas.Canvas.__init__(self, *args, **kwargs)
            self._saved_page_states = []

        def showPage(self):
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total_pages = len(self._saved_page_states)
            for state in self._saved_page_states:
                self.__dict__.update(state)
                self._draw_page_counter(total_pages)
                _pdfcanvas.Canvas.showPage(self)
            _pdfcanvas.Canvas.save(self)

        def _draw_page_counter(self, total_pages):
            """Escreve 'Page X of Y' no centro do rodapé da página."""
            self.saveState()
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#6B7C93"))
            page_w, _ = letter
            self.drawCentredString(page_w / 2.0, 0.30 * inch, f"Page {self._pageNumber} of {total_pages}")
            self.restoreState()


class MainWindow(QMainWindow):
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
        self._set_collapsed_instant()
        self._connect_signals()
        self._setup_autocomplete_combos()
        self._setup_phone_input_masks()
        self._setup_zip_code_fields()
        self._setup_job_code_completer()
        self._setup_product_unit_completer()
        self._setup_work_type_unit_display()
        self._setup_work_type_category_locks()
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
        confirm = QMessageBox.question(
            self,
            "Exit VL Flooring",
            "Are you sure you want to exit the system?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()

    # ══════════════════════════════════════════════════════════════
    # SIDEBAR ANIMADA
    # ══════════════════════════════════════════════════════════════

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

        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diagnostico_layout.txt")
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
        end = 0 if self._client_drawer_expanded else CLIENT_DRAWER_WIDTH

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
        """Mostra/esconde texto dos botões e logo conforme estado da sidebar."""
        show_text = self._sidebar_expanded

        btn_texts = {
            self.ui.btn_home: "  Home",
            self.ui.btn_jobs: "  Job Records",
            self.ui.btn_registrations: "  Registrations",
            self.ui.btn_customer: "  Customer",
            self.ui.btn_user: "  User",
        }
        for btn, text in btn_texts.items():
            btn.setText(text if show_text else "")
            btn.setToolTip("" if show_text else text.strip())

        sub_btn_texts = {
            self.ui.btn_reg_companies: ("  🏢 Companies", "🏢"),
            self.ui.btn_reg_contractors: ("  👷 Contractors", "👷"),
            self.ui.btn_reg_helpers: ("  🦺 Helpers", "🦺"),
            self.ui.btn_reg_work_types: ("  🧱 Work Types", "🧱"),
            self.ui.btn_reg_products: ("  📦 Products", "📦"),
            self.ui.btn_reg_documents: ("  📁 Documents", "📁"),
            self.ui.btn_reg_bank_reconciliation: ("  🏦 Bank Reconciliation", "🏦"),
            self.ui.btn_reg_receipt_inbox: ("  📥 Receipt Inbox", "📥"),
            self.ui.btn_reg_job_site_inbox: ("  📍 Job Site Inbox", "📍"),
            self.ui.btn_reg_projects_dashboard: ("  📊 Projects Dashboard", "📊"),
            self.ui.btn_nav_receivables: ("  💰 Receivables", "💰"),
        }
        for btn, (full_text, icon_only) in sub_btn_texts.items():
            btn.setText(full_text if show_text else icon_only)
            btn.setToolTip("" if show_text else full_text.strip())

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

        elif obj is self.ui.Left_container:
            if event.type() == QEvent.Type.Enter:
                self._expand_sidebar()
            elif event.type() == QEvent.Type.Leave:
                self._collapse_sidebar()

        return super().eventFilter(obj, event)

    # ══════════════════════════════════════════════════════════════
    # SINAIS / NAVEGAÇÃO
    # ══════════════════════════════════════════════════════════════

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

    # ══════════════════════════════════════════════════════════════
    # COMPLIANCE — LLC Annual Report, Business Tax Receipt, seguro/licença
    # (guardado em compliance_items — ver migration_compliance_items.sql)
    # ══════════════════════════════════════════════════════════════

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

    # ══════════════════════════════════════════════════════════════
    # SALES TAX — marcação de "imposto já pago na compra" por produto
    # (coluna products.SALES_TAX_PAID_AT_PURCHASE — ver migration_fase4_w9_salestax.sql)
    # ══════════════════════════════════════════════════════════════

    def _setup_sales_tax_feature(self):
        """Adiciona, em tempo de execução (sem editar o .ui), uma checkbox no
        formulário de Products: 'Sales tax already paid when I buy this
        material'. Na Flórida, contratado que compra material no varejo já
        paga sales tax na hora da compra — então, ao revender/cobrar isso do
        cliente num contrato fechado (lump-sum), normalmente NÃO se cobra
        sales tax de novo. Isso só marca a situação de cada produto pra você
        ter esse controle; não mexe em cálculo de fatura."""
        self.ui.chk_product_tax_paid_at_purchase = QCheckBox(
            "Sales tax already paid when I buy this material (most retail purchases)",
            self.ui.tab_product_form,
        )
        self.ui.chk_product_tax_paid_at_purchase.setObjectName(u"chk_product_tax_paid_at_purchase")
        self.ui.chk_product_tax_paid_at_purchase.setChecked(True)
        insert_at = max(0, self.ui.layout_tab_product_form.count() - 1)
        self.ui.layout_tab_product_form.insertWidget(insert_at, self.ui.chk_product_tax_paid_at_purchase)

    # ══════════════════════════════════════════════════════════════
    # JOB COSTING — vincular expenses a um Job Code + orçamento do projeto
    # (colunas expenses.JOB_PROJECT_ID e job_projects.BUDGET_AMOUNT —
    # ver migration_fase3_budget_expenses.sql)
    # ══════════════════════════════════════════════════════════════

    def _setup_project_budget_feature(self):
        """Injeta, em tempo de execução (sem editar o .ui), o combo 'Job
        Code (optional)' no formulário de Expenses — é o que permite marcar
        que uma despesa pertence a um projeto específico, pra depois
        aparecer somada em 'Budget x Actual' na tela de Project View."""
        row = QWidget(self.ui.frame_expense_card)
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 6, 0, 6)
        row_layout.addWidget(QLabel("Job Code (optional):"))
        self.ui.cmb_expense_job_code = QComboBox()
        self.ui.cmb_expense_job_code.setObjectName(u"cmb_expense_job_code")
        row_layout.addWidget(self.ui.cmb_expense_job_code, 1)
        self.ui.layout_expense_card.insertWidget(2, row)
        self._refresh_expense_job_code_combo()

    def _refresh_expense_job_code_combo(self):
        """Recarrega a lista de Job Codes disponíveis no combo da despesa,
        preservando a seleção atual quando possível."""
        combo = self.ui.cmb_expense_job_code
        current = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("— None —", None)
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT ID, CODE FROM job_projects ORDER BY CODE DESC")
            for jp_id, code in cursor.fetchall():
                combo.addItem(code, jp_id)
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError):
            pass
        if current:
            pos = combo.findData(current)
            if pos >= 0:
                combo.setCurrentIndex(pos)
        combo.blockSignals(False)

    # ══════════════════════════════════════════════════════════════
    # DOCUMENTS — repositório central (contratos, propostas, apólices,
    # lien waivers) — tabela documents, ver migration_fase5_documents.sql
    # ══════════════════════════════════════════════════════════════

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

    # ══════════════════════════════════════════════════════════════
    # BANK RECONCILIATION — importa extrato CSV e compara com payments/
    # expenses já lançados (tabela bank_transactions — ver
    # migration_fase6_bank_reconciliation.sql)
    # ══════════════════════════════════════════════════════════════

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

    # ══════════════════════════════════════════════════════════════
    # RECEIPT INBOX — "Email to Expense" (captura de recibo via celular)
    # Reaproveita a MESMA conta de e-mail já configurada em Settings (SMTP,
    # usada pra mandar fatura) via IMAP — nenhuma tabela nova no banco, só
    # baixa o anexo do e-mail e abre o formulário de Expense preenchido.
    # ══════════════════════════════════════════════════════════════

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

    def _setup_helpers_feature(self):
        """Cria, em tempo de execução, o botão 'Helpers' no submenu de
        Registrations — mesmo padrão dos outros botões novos (nenhum
        widget novo no .ui)."""
        self.ui.btn_reg_helpers = QPushButton(self.ui.frame_registrations_submenu)
        self.ui.btn_reg_helpers.setObjectName(u"btn_reg_helpers")
        self.ui.btn_reg_helpers.setCheckable(False)
        self.ui.btn_reg_helpers.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ui.layout_registrations_submenu.addWidget(self.ui.btn_reg_helpers)

    def _setup_helper_field(self):
        """Adiciona o campo 'Helper' ao formulário de New/Edit Job, em tempo
        de execução, reaproveitando a grade (`grid_job_info`) que já existia
        no .ui — as linhas 0 a 3 dessa grade já estavam todas ocupadas
        (Work Date/Job Code/Payment na linha 0-1, Contractor/Company/
        Status/Value na linha 2-3), então o campo novo entra nas linhas 4-5,
        mesmo estilo do Contractor. Como todo o formulário de Job já fica
        dentro de um QScrollArea (`scroll_job_form`), a grade ficando um
        pouco mais alta não corta nem sobrepõe nada — só rola um pouco mais.
        O Helper é opcional (ao contrário do Contractor, que é obrigatório)."""
        self.ui.lbl_helper = QLabel(self.ui.frame_job_info_body)
        self.ui.lbl_helper.setObjectName(u"lbl_helper")
        self.ui.lbl_helper.setText("Helper")
        self.ui.grid_job_info.addWidget(self.ui.lbl_helper, 4, 0, 1, 1)

        self.ui.cmb_helper = QComboBox(self.ui.frame_job_info_body)
        self.ui.cmb_helper.setObjectName(u"cmb_helper")
        self.ui.cmb_helper.setMinimumSize(QSize(190, 46))
        self.ui.cmb_helper.setMaximumSize(QSize(190, 36))
        self.ui.cmb_helper.setStyleSheet(u"font: 9pt \"MS Shell Dlg 2\";")
        self.ui.grid_job_info.addWidget(self.ui.cmb_helper, 5, 0, 1, 1)

    # ══════════════════════════════════════════════════════════════
    # HELPERS — cadastro dos ajudantes de obra (nome, empresa, contato e
    # endereço, mesmo nível de detalhe do Contractor). Tela nova, criada em
    # tempo de execução (nenhum widget novo no .ui) — mesmo padrão do
    # Documents/Bank Reconciliation: lista + formulário dentro de uma só
    # janela. Precisa da tabela nova `helpers` (ver
    # migration-helpers.sql) — se ela ainda não existir, a tela avisa e não
    # trava o resto do app; o combo Helper no formulário de Job também
    # degrada graciosamente (fica só com o placeholder) até a migração
    # rodar.
    # ══════════════════════════════════════════════════════════════

    def open_helpers_manager_dialog(self):
        """Cadastro de Helpers: lista à esquerda/tabela em cima, formulário
        embaixo. Clica numa linha da tabela pra editar, ou preenche o
        formulário do zero (depois de '+ New') pra cadastrar um novo."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Helpers")
        dialog.resize(760, 640)
        dialog.setStyleSheet("""
            QTableWidget { background-color: #FFFFFF; color: #1C2B3A; gridline-color: #E3E8EE; }
            QHeaderView::section { background-color: #F0F4F8; color: #1C2B3A; padding: 6px; border: none; font-weight: 600; }
        """)
        layout = QVBoxLayout(dialog)
        lbl_intro = QLabel(
            "<b>Helpers</b> — helpers who assist on jobs (name, company, contact and address, "
            "same level of detail as Contractor). Click a row below to edit it, or click "
            "'+ New' and fill the form to add one."
        )
        lbl_intro.setWordWrap(True)
        layout.addWidget(lbl_intro)

        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Name", "Company", "Phone", "Email"])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        table.setMinimumHeight(120)
        table.setMaximumHeight(180)
        layout.addWidget(table)

        form_frame = QFrame()
        form_layout = QGridLayout(form_frame)

        txt_full_name = QLineEdit()
        txt_company_name = QLineEdit()
        txt_email = QLineEdit()
        txt_phone = QLineEdit()
        txt_phone.setPlaceholderText("(000) 000 - 0000")
        txt_phone2 = QLineEdit()
        txt_phone2.setPlaceholderText("(000) 000 - 0000")
        txt_address = QLineEdit()
        txt_address2 = QLineEdit()
        cmb_state = QComboBox()
        cmb_city = QComboBox()
        txt_zip = QLineEdit()
        txt_zip.setPlaceholderText("00000-0000")

        # Formas de pagamento — todas opcionais, e um Helper pode ter mais de
        # uma preenchida ao mesmo tempo (ex: Zelle E Cash App). Cada uma tem
        # seu próprio campo específico (mais organizado do que um campo
        # único de texto livre pra tudo).
        txt_zelle = QLineEdit()
        txt_zelle.setPlaceholderText("Phone or email used on Zelle")
        txt_cashapp = QLineEdit()
        txt_cashapp.setPlaceholderText("$cashtag")
        txt_venmo = QLineEdit()
        txt_venmo.setPlaceholderText("@username")
        txt_check_name = QLineEdit()
        txt_check_name.setPlaceholderText("Pay to the order of...")
        txt_bank_routing = QLineEdit()
        txt_bank_routing.setPlaceholderText("Routing number")
        txt_bank_account = QLineEdit()
        txt_bank_account.setPlaceholderText("Account number")
        # Mapa coluna do banco -> campo, reaproveitado por load/save — assim
        # cada forma nova entra num só lugar sem duplicar lista em vários
        # pontos da função.
        payment_fields = {
            "PAYMENT_ZELLE": txt_zelle,
            "PAYMENT_CASHAPP": txt_cashapp,
            "PAYMENT_VENMO": txt_venmo,
            "PAYMENT_CHECK_NAME": txt_check_name,
            "PAYMENT_BANK_ROUTING": txt_bank_routing,
            "PAYMENT_BANK_ACCOUNT": txt_bank_account,
        }

        field_rows = [
            ("Full Name*:", txt_full_name), ("Company:", txt_company_name),
            ("Email:", txt_email), ("Phone:", txt_phone), ("Phone 2:", txt_phone2),
            ("Address:", txt_address), ("Address Line 2:", txt_address2),
        ]
        for i, (label_text, widget) in enumerate(field_rows):
            form_layout.addWidget(QLabel(label_text), i, 0)
            form_layout.addWidget(widget, i, 1)
        next_row = len(field_rows)
        form_layout.addWidget(QLabel("State:"), next_row, 0)
        form_layout.addWidget(cmb_state, next_row, 1)
        form_layout.addWidget(QLabel("City:"), next_row + 1, 0)
        form_layout.addWidget(cmb_city, next_row + 1, 1)
        form_layout.addWidget(QLabel("Zip Code:"), next_row + 2, 0)
        form_layout.addWidget(txt_zip, next_row + 2, 1)

        lbl_payment_section = QLabel(
            "Payment Methods (optional — fill in whichever this helper uses; you can fill more than one)"
        )
        lbl_payment_section.setWordWrap(True)
        payment_section_row = next_row + 3
        form_layout.addWidget(lbl_payment_section, payment_section_row, 0, 1, 2)
        payment_rows = [
            ("Zelle:", txt_zelle),
            ("Cash App:", txt_cashapp),
            ("Venmo:", txt_venmo),
            ("Check — Pay to the order of:", txt_check_name),
            ("Bank Transfer — Routing #:", txt_bank_routing),
            ("Bank Transfer — Account #:", txt_bank_account),
        ]
        for offset, (label_text, widget) in enumerate(payment_rows, start=1):
            form_layout.addWidget(QLabel(label_text), payment_section_row + offset, 0)
            form_layout.addWidget(widget, payment_section_row + offset, 1)

        # Formulário agora tem mais campos (com as formas de pagamento) do
        # que cabe numa tela só — envolve num QScrollArea pra dar rolagem
        # vertical em vez de estourar o tamanho da janela.
        form_scroll = QScrollArea()
        form_scroll.setWidgetResizable(True)
        form_scroll.setFrameShape(QFrame.Shape.NoFrame)
        form_scroll.setWidget(form_frame)
        layout.addWidget(form_scroll, 1)

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
        for phone_field in (txt_phone, txt_phone2):
            phone_field.editingFinished.connect(lambda f=phone_field: f.setText(self._format_phone(f.text())))
        txt_zip.editingFinished.connect(lambda: txt_zip.setText(self._format_zip(txt_zip.text())))

        current_helper_id = {"value": None}  # None = formulário em modo "novo"

        def clear_form():
            current_helper_id["value"] = None
            for w in (txt_full_name, txt_company_name, txt_email, txt_phone, txt_phone2,
                      txt_address, txt_address2, txt_zip):
                w.clear()
            for w in payment_fields.values():
                w.clear()
            cmb_state.setCurrentIndex(0)
            self._reload_city_combo_for_state(cmb_city, None)
            table.clearSelection()

        def load_helpers():
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT ID, FULL_NAME, COMPANY_NAME, PHONE_NUMBER, EMAIL FROM helpers ORDER BY FULL_NAME"
                )
                rows = cursor.fetchall()
                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.information(
                    dialog, "Helpers not available yet",
                    "This list isn't available yet — the 'helpers' table hasn't been created in "
                    f"the database.\n\n({e})",
                )
                rows = []
            table.setRowCount(len(rows))
            for i, (hid, name, company, phone, email) in enumerate(rows):
                values = [name or "", company or "", self._format_phone(phone) or "", email or ""]
                for col, text in enumerate(values):
                    item = QTableWidgetItem(text)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    if col == 0:
                        item.setData(Qt.ItemDataRole.UserRole, hid)
                    table.setItem(i, col, item)

        def load_selected_into_form():
            r = table.currentRow()
            if r < 0:
                return
            helper_id = table.item(r, 0).data(Qt.ItemDataRole.UserRole)
            base_cols = ["FULL_NAME", "COMPANY_NAME", "EMAIL", "PHONE_NUMBER", "PHONE_NUMBER2",
                         "ADDRESS", "ADDRESS2", "CITY_ID", "STATE_ID", "ZIP_CODE"]
            # As colunas de pagamento só entram na consulta se a migração
            # correspondente já tiver rodado — assim, carregar um Helper
            # continua funcionando mesmo antes de você rodar a migração nova.
            payment_cols = [col for col in payment_fields if self._table_column_exists("helpers", col)]
            all_cols = base_cols + payment_cols
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(f"SELECT {', '.join(all_cols)} FROM helpers WHERE ID = %s", (helper_id,))
                row = cursor.fetchone()
                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.warning(dialog, "Database Error", f"Could not load this helper:\n{e}")
                return
            if not row:
                return
            values = dict(zip(all_cols, row))
            current_helper_id["value"] = helper_id
            txt_full_name.setText(values.get("FULL_NAME") or "")
            txt_company_name.setText(values.get("COMPANY_NAME") or "")
            txt_email.setText(values.get("EMAIL") or "")
            txt_phone.setText(self._format_phone(values.get("PHONE_NUMBER")) or "")
            txt_phone2.setText(self._format_phone(values.get("PHONE_NUMBER2")) or "")
            txt_address.setText(values.get("ADDRESS") or "")
            txt_address2.setText(values.get("ADDRESS2") or "")
            txt_zip.setText(self._format_zip(values.get("ZIP_CODE")) or "")
            self._set_combo_by_data(cmb_state, values.get("STATE_ID"))
            self._reload_city_combo_for_state(cmb_city, values.get("STATE_ID"), keep_city_id=values.get("CITY_ID"))
            for col, widget in payment_fields.items():
                widget.setText(values.get(col) or "")

        table.itemSelectionChanged.connect(load_selected_into_form)

        def save_helper():
            full_name = txt_full_name.text().strip()
            if not full_name:
                QMessageBox.warning(dialog, "Required field", "Full Name is required.")
                return
            data = {
                "FULL_NAME": full_name,
                "COMPANY_NAME": txt_company_name.text().strip(),
                "EMAIL": txt_email.text().strip(),
                "PHONE_NUMBER": self._format_phone(txt_phone.text()),
                "PHONE_NUMBER2": self._format_phone(txt_phone2.text()),
                "ADDRESS": txt_address.text().strip(),
                "ADDRESS2": txt_address2.text().strip(),
                "CITY_ID": cmb_city.currentData(),
                "STATE_ID": cmb_state.currentData(),
                "ZIP_CODE": self._format_zip(txt_zip.text()),
            }
            # Cada campo de pagamento só entra no INSERT/UPDATE se a coluna
            # já existir — se a migração nova ainda não rodou, o resto do
            # Helper continua salvando normal, só sem os dados de pagamento.
            for col, widget in payment_fields.items():
                if self._table_column_exists("helpers", col):
                    data[col] = widget.text().strip()
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                if current_helper_id["value"]:
                    set_clause = ", ".join(f"{k} = %s" for k in data)
                    cursor.execute(
                        f"UPDATE helpers SET {set_clause} WHERE ID = %s",
                        list(data.values()) + [current_helper_id["value"]],
                    )
                else:
                    cols = ", ".join(data.keys())
                    placeholders = ", ".join(["%s"] * len(data))
                    cursor.execute(f"INSERT INTO helpers ({cols}) VALUES ({placeholders})", list(data.values()))
                conn.commit()
                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not save this helper:\n{e}")
                return
            QMessageBox.information(dialog, "Saved", "Helper saved successfully.")
            clear_form()
            load_helpers()
            self.load_combo_data()  # atualiza o combo Helper no formulário de Job na hora

        def delete_helper():
            if not current_helper_id["value"]:
                QMessageBox.information(dialog, "No selection", "Select a helper from the list first.")
                return
            confirm = QMessageBox.question(
                dialog, "Confirm delete",
                "Are you sure you want to delete this helper?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM helpers WHERE ID = %s", (current_helper_id["value"],))
                conn.commit()
                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not delete this helper:\n{e}")
                return
            clear_form()
            load_helpers()
            self.load_combo_data()

        btn_row = QHBoxLayout()
        btn_new = QPushButton("+ New")
        btn_new.clicked.connect(clear_form)
        btn_save = QPushButton("✔  Save")
        btn_save.setStyleSheet(
            "QPushButton { background-color: #2E7D32; color: #FFFFFF; border: none; "
            "border-radius: 6px; padding: 8px 14px; font-weight: 600; } "
            "QPushButton:hover { background-color: #388E3C; }"
        )
        btn_save.clicked.connect(save_helper)
        btn_delete = QPushButton("Delete")
        btn_delete.clicked.connect(delete_helper)
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(dialog.accept)
        btn_row.addWidget(btn_new)
        btn_row.addWidget(btn_save)
        btn_row.addWidget(btn_delete)
        btn_row.addStretch()
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

        load_helpers()
        dialog.exec()

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
            f"<b>{EMAIL_SMTP_USER}</b> (same account configured in Settings) with the word "
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
            imap.login(EMAIL_SMTP_USER, EMAIL_SMTP_PASSWORD)
            imap.select("INBOX")
            return imap

        def check_inbox():
            if not EMAIL_SMTP_USER or EMAIL_SMTP_USER == "your-email@gmail.com":
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

            receipts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "receipts_received")
            try:
                os.makedirs(receipts_dir, exist_ok=True)
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

    # ══════════════════════════════════════════════════════════════
    # JOB SITE INBOX — "Email to Job Address" (captura de endereço via
    # celular, mesmo padrão do Receipt Inbox: reaproveita a MESMA conta de
    # e-mail já configurada em Settings, via IMAP). O e-mail nunca aplica
    # nada sozinho — só fica esperando na caixa de entrada até você revisar
    # e confirmar aqui dentro. Ao confirmar: atualiza o endereço salvo do
    # Job (job_projects) e grava uma linha no histórico por data
    # (job_site_visits — tabela nova, ver migration-jobsite-visits.sql). Se
    # essa tabela ainda não existir, o endereço do Job é atualizado do
    # mesmo jeito — só o histórico não é gravado, sem travar o resto.
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def _normalize_keyword_text(text):
        """Remove acentos e baixa a caixa, pra comparar palavras-chave sem
        se importar com 'endereço' vs 'endereco', maiúsculas, etc."""
        if not text:
            return ""
        no_accents = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
        return no_accents.lower()

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
            f"<b>{EMAIL_SMTP_USER}</b> (same account configured in Settings) with "
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
            imap.login(EMAIL_SMTP_USER, EMAIL_SMTP_PASSWORD)
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
            if not EMAIL_SMTP_USER or EMAIL_SMTP_USER == "your-email@gmail.com":
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
        self.new_expense_record()
        self._go_to_page(5, self.ui.btn_nav_receivables)
        self.ui.tabWidget_receivables.setCurrentWidget(self.ui.tab_expenses_master)

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

        self._category_lock_handlers = []  # mantém referência viva
        for checkbox, widgets in groups.items():
            handler = make_toggle_handler(widgets)
            checkbox.toggled.connect(handler)
            self._category_lock_handlers.append(handler)
            # Aplica o estado inicial (desmarcado = bloqueado)
            handler(checkbox.isChecked())

    def _go_to_page(self, index, active_btn):
        """Troca a pagina visivel, marca o botao correspondente como ativo na sidebar e atualiza o titulo no topo. Se for a pagina Receivables, recarrega dashboard e invoices."""
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

        for btn in top_level_buttons:
            btn.setChecked(btn is active_btn)
        for btn in sub_buttons:
            btn.setChecked(btn is active_btn)

        # "Registrations" fica marcado quando qualquer uma das 4 sub-páginas está ativa
        self.ui.btn_registrations.setChecked(index in (2, 3, 4, 8))

        titles = {
            0: "Dashboard", 1: "Job Records", 2: "Companies", 3: "Contractors",
            4: "Work Types", 5: "Receivables", 6: "Customer", 7: "User", 8: "Products",
            9: "Settings",
        }
        self.ui.Top_label.setText(titles.get(index, ""))

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

    # ══════════════════════════════════════════════════════════════
    # BANCO DE DADOS — CONEXÃO
    # ══════════════════════════════════════════════════════════════

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

    def _load_app_settings_from_db(self):
        """Carrega as configurações salvas em app_settings e sobrescreve as
        constantes padrão do início do arquivo (COMPANY_NAME etc.), se
        existir algo salvo. Roda cedo no __init__, antes de qualquer invoice
        ser gerado. Se a tabela/linha não existir ainda (primeira vez), os
        valores padrão do código continuam valendo normalmente."""
        global COMPANY_NAME, COMPANY_TAGLINE, COMPANY_PHONE, COMPANY_EMAIL, COMPANY_WEBSITE
        global COMPANY_BANK_INFO, COMPANY_PAYMENT_METHODS
        global EMAIL_SMTP_HOST, EMAIL_SMTP_PORT, EMAIL_SMTP_USER, EMAIL_SMTP_PASSWORD, EMAIL_FROM_NAME
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

        COMPANY_NAME = data.get("COMPANY_NAME") or COMPANY_NAME
        COMPANY_TAGLINE = data.get("COMPANY_TAGLINE") or COMPANY_TAGLINE
        COMPANY_PHONE = data.get("COMPANY_PHONE") or COMPANY_PHONE
        COMPANY_EMAIL = data.get("COMPANY_EMAIL") or COMPANY_EMAIL
        COMPANY_WEBSITE = data.get("COMPANY_WEBSITE") or COMPANY_WEBSITE
        COMPANY_BANK_INFO = {
            "account_no": data.get("BANK_ACCOUNT_NO") or COMPANY_BANK_INFO["account_no"],
            "account_name": data.get("BANK_ACCOUNT_NAME") or COMPANY_BANK_INFO["account_name"],
            "bank_details": data.get("BANK_DETAILS") or COMPANY_BANK_INFO["bank_details"],
        }
        if data.get("PAYMENT_METHODS"):
            COMPANY_PAYMENT_METHODS = [m.strip() for m in data["PAYMENT_METHODS"].split(",") if m.strip()]
        EMAIL_SMTP_HOST = data.get("SMTP_HOST") or EMAIL_SMTP_HOST
        EMAIL_SMTP_PORT = data.get("SMTP_PORT") or EMAIL_SMTP_PORT
        EMAIL_SMTP_USER = data.get("SMTP_USER") or EMAIL_SMTP_USER
        EMAIL_SMTP_PASSWORD = data.get("SMTP_PASSWORD") or EMAIL_SMTP_PASSWORD
        EMAIL_FROM_NAME = data.get("SMTP_FROM_NAME") or EMAIL_FROM_NAME

    def load_settings_form(self):
        """Preenche o formulário de Settings com os valores atuais (já
        carregados do banco no início, ou os padrões do código)."""
        self.ui.txt_settings_company_name.setText(COMPANY_NAME)
        self.ui.txt_settings_company_tagline.setText(COMPANY_TAGLINE)
        self.ui.txt_settings_company_phone.setText(COMPANY_PHONE)
        self.ui.txt_settings_company_email.setText(COMPANY_EMAIL)
        self.ui.txt_settings_company_website.setText(COMPANY_WEBSITE)

        self.ui.txt_settings_bank_account_no.setText(COMPANY_BANK_INFO["account_no"])
        self.ui.txt_settings_bank_account_name.setText(COMPANY_BANK_INFO["account_name"])
        self.ui.txt_settings_bank_details.setText(COMPANY_BANK_INFO["bank_details"])

        pm_checks = {
            "Zelle": self.ui.chk_settings_pm_zelle,
            "Check": self.ui.chk_settings_pm_check,
            "Cash": self.ui.chk_settings_pm_cash,
            "Bank Transfer": self.ui.chk_settings_pm_bank_transfer,
            "Credit Card": self.ui.chk_settings_pm_credit_card,
        }
        for label, chk in pm_checks.items():
            chk.setChecked(label in COMPANY_PAYMENT_METHODS)

        self.ui.txt_settings_smtp_host.setText(EMAIL_SMTP_HOST)
        self.ui.spn_settings_smtp_port.setValue(int(EMAIL_SMTP_PORT))
        self.ui.txt_settings_smtp_user.setText(EMAIL_SMTP_USER)
        self.ui.txt_settings_smtp_password.setText(EMAIL_SMTP_PASSWORD)

        if os.path.exists(COMPANY_LOGO_PATH):
            self.ui.lbl_settings_logo_preview.setPixmap(QPixmap(COMPANY_LOGO_PATH))
        else:
            self.ui.lbl_settings_logo_preview.setText("No logo")

    def save_settings_form(self):
        """Salva o formulário de Settings no banco (app_settings) e já
        atualiza as constantes em memória, pra valer imediatamente sem
        precisar reiniciar o app."""
        global COMPANY_NAME, COMPANY_TAGLINE, COMPANY_PHONE, COMPANY_EMAIL, COMPANY_WEBSITE
        global COMPANY_BANK_INFO, COMPANY_PAYMENT_METHODS
        global EMAIL_SMTP_HOST, EMAIL_SMTP_PORT, EMAIL_SMTP_USER, EMAIL_SMTP_PASSWORD, EMAIL_FROM_NAME

        company_name = self.ui.txt_settings_company_name.text().strip()
        if not company_name:
            QMessageBox.warning(self, "Missing data", "Company Name is required.")
            return

        pm_checks = {
            "Zelle": self.ui.chk_settings_pm_zelle,
            "Check": self.ui.chk_settings_pm_check,
            "Cash": self.ui.chk_settings_pm_cash,
            "Bank Transfer": self.ui.chk_settings_pm_bank_transfer,
            "Credit Card": self.ui.chk_settings_pm_credit_card,
        }
        selected_methods = [label for label, chk in pm_checks.items() if chk.isChecked()]

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
                    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM_NAME)
                VALUES (1, %(COMPANY_NAME)s, %(COMPANY_TAGLINE)s, %(COMPANY_PHONE)s, %(COMPANY_EMAIL)s,
                    %(COMPANY_WEBSITE)s, %(BANK_ACCOUNT_NO)s, %(BANK_ACCOUNT_NAME)s, %(BANK_DETAILS)s,
                    %(PAYMENT_METHODS)s, %(SMTP_HOST)s, %(SMTP_PORT)s, %(SMTP_USER)s, %(SMTP_PASSWORD)s,
                    %(SMTP_FROM_NAME)s)
                ON DUPLICATE KEY UPDATE
                    COMPANY_NAME=VALUES(COMPANY_NAME), COMPANY_TAGLINE=VALUES(COMPANY_TAGLINE),
                    COMPANY_PHONE=VALUES(COMPANY_PHONE), COMPANY_EMAIL=VALUES(COMPANY_EMAIL),
                    COMPANY_WEBSITE=VALUES(COMPANY_WEBSITE), BANK_ACCOUNT_NO=VALUES(BANK_ACCOUNT_NO),
                    BANK_ACCOUNT_NAME=VALUES(BANK_ACCOUNT_NAME), BANK_DETAILS=VALUES(BANK_DETAILS),
                    PAYMENT_METHODS=VALUES(PAYMENT_METHODS), SMTP_HOST=VALUES(SMTP_HOST),
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
        COMPANY_NAME = data["COMPANY_NAME"]
        COMPANY_TAGLINE = data["COMPANY_TAGLINE"]
        COMPANY_PHONE = data["COMPANY_PHONE"]
        COMPANY_EMAIL = data["COMPANY_EMAIL"]
        COMPANY_WEBSITE = data["COMPANY_WEBSITE"]
        COMPANY_BANK_INFO = {
            "account_no": data["BANK_ACCOUNT_NO"],
            "account_name": data["BANK_ACCOUNT_NAME"],
            "bank_details": data["BANK_DETAILS"],
        }
        COMPANY_PAYMENT_METHODS = selected_methods
        EMAIL_SMTP_HOST = data["SMTP_HOST"]
        EMAIL_SMTP_PORT = data["SMTP_PORT"]
        EMAIL_SMTP_USER = data["SMTP_USER"]
        EMAIL_SMTP_PASSWORD = data["SMTP_PASSWORD"]
        EMAIL_FROM_NAME = data["SMTP_FROM_NAME"]

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

    def _get_connection(self):
        """Abre e retorna uma nova conexao com o MySQL usando self.db_config."""
        if mysql is None:
            raise RuntimeError(
                "mysql-connector-python não instalado. Rode: pip install mysql-connector-python"
            )
        return mysql.connector.connect(**self.db_config)

    # ══════════════════════════════════════════════════════════════
    # WORK_DAYS — LISTAGEM
    # ══════════════════════════════════════════════════════════════

    # ══════════════════════════════════════════════════════════════
    # JOB RECORDS — SCHEDULE (calendário mensal)
    # ══════════════════════════════════════════════════════════════

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

    def _setup_projects_dashboard_feature(self):
        """Cria, em tempo de execução (sem editar o .ui), o botão 'Projects
        Dashboard' no submenu Registrations e o painel 'Projects Overview'
        (gráfico de rosca com os projetos por status + 2 KPIs extras) no
        final da página Home — mesmo padrão de sempre: QDialog/QWidget
        montado 100% em Python, nunca mexendo no main_window_vl_flooring_6.ui
        nem no ui_main_window_vl_flooring.py compilado."""
        self.ui.btn_reg_projects_dashboard = QPushButton(self.ui.frame_registrations_submenu)
        self.ui.btn_reg_projects_dashboard.setObjectName(u"btn_reg_projects_dashboard")
        self.ui.btn_reg_projects_dashboard.setCheckable(False)
        self.ui.btn_reg_projects_dashboard.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ui.layout_registrations_submenu.addWidget(self.ui.btn_reg_projects_dashboard)

        # ── Painel "Projects Overview" no final da Home ────────────────
        self.ui.frame_projects_overview = QFrame(self.ui.pg_home)
        self.ui.frame_projects_overview.setObjectName(u"frame_projects_overview")
        self.ui.frame_projects_overview.setStyleSheet(
            "#frame_projects_overview { background-color:#FFFFFF; border:1px solid #E3E8EE; border-radius:10px; }"
            "#frame_projects_overview QLabel { background:transparent; }"
        )
        overview_layout = QVBoxLayout(self.ui.frame_projects_overview)

        title_row = QHBoxLayout()
        lbl_title = QLabel("📊 Projects Overview")
        lbl_title.setStyleSheet("font-weight:700; font-size:14px; color:#1C2B3A;")
        title_row.addWidget(lbl_title)
        title_row.addStretch()
        btn_open_dashboard = QPushButton("Open Full Dashboard")
        btn_open_dashboard.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_open_dashboard.setStyleSheet(
            "QPushButton { background-color:#1565C0; color:#FFFFFF; border:none; "
            "border-radius:5px; padding:5px 12px; font-weight:600; } "
            "QPushButton:hover { background-color:#1976D2; }"
        )
        btn_open_dashboard.clicked.connect(self.open_projects_dashboard_dialog)
        title_row.addWidget(btn_open_dashboard)
        overview_layout.addLayout(title_row)

        content_row = QHBoxLayout()
        self.ui.donut_projects_status = _DonutChartWidget(self.ui.frame_projects_overview)
        self.ui.donut_projects_status.setMinimumSize(150, 150)
        self.ui.donut_projects_status.setMaximumSize(150, 150)
        content_row.addWidget(self.ui.donut_projects_status)

        self.ui.layout_projects_status_legend = QVBoxLayout()
        content_row.addLayout(self.ui.layout_projects_status_legend, 1)

        kpi_col = QVBoxLayout()
        self.ui.lbl_home_compliance_kpi = QLabel("—")
        self.ui.lbl_home_compliance_kpi.setStyleSheet("font-weight:700; font-size:18px; color:#E65100;")
        kpi_compliance_title = QLabel("Compliance due (30d)")
        kpi_compliance_title.setStyleSheet("color:#6B7C93; font-size:11px;")
        kpi_col.addWidget(self.ui.lbl_home_compliance_kpi)
        kpi_col.addWidget(kpi_compliance_title)

        self.ui.lbl_home_bank_kpi = QLabel("—")
        self.ui.lbl_home_bank_kpi.setStyleSheet("font-weight:700; font-size:18px; color:#1565C0;")
        kpi_bank_title = QLabel("Unmatched bank txns")
        kpi_bank_title.setStyleSheet("color:#6B7C93; font-size:11px;")
        kpi_col.addWidget(self.ui.lbl_home_bank_kpi)
        kpi_col.addWidget(kpi_bank_title)
        kpi_col.addStretch()
        content_row.addLayout(kpi_col)

        overview_layout.addLayout(content_row)
        self.ui.layout_pg_home_outer.addWidget(self.ui.frame_projects_overview)

    def _classify_project_status(self, total_days, completed_days, cancelled_days):
        """Deriva um status de projeto (Active/Completed/Cancelled/No Jobs
        Yet) a partir dos jobs (work_days) ligados ao Job Code —
        job_projects.STATUS sempre fica 'ACTIVE' desde a criação (nunca é
        atualizado em nenhum lugar do código hoje), então quem manda de
        verdade é o conjunto de jobs daquele projeto."""
        total_days = total_days or 0
        completed_days = completed_days or 0
        cancelled_days = cancelled_days or 0
        if total_days == 0:
            return "NO_JOBS"
        if completed_days == total_days:
            return "COMPLETED"
        if cancelled_days == total_days:
            return "CANCELLED"
        return "ACTIVE"

    def _fetch_projects_overview_rows(self):
        """Busca cada projeto (job_projects) com o total de dias de trabalho,
        quantos estão concluídos/cancelados, orçamento (se a coluna já
        existir — Fase 3) e receita total — usado tanto pelo Projects
        Dashboard quanto pelo gráfico de rosca da Home. Retorna
        (lista_de_dicts, None) ou (None, mensagem_de_erro)."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    SELECT jp.ID, jp.CODE, jp.PROJECT_TYPE,
                           COALESCE(cl.FULL_NAME, '—') AS client_name,
                           COALESCE(co.COMPANY_NAME, '—') AS company_name,
                           COALESCE(c.COMPANY_NAME, c.FULL_NAME, '—') AS contractor_name,
                           COALESCE(jp.JOB_ADDRESS, '—') AS job_address,
                           jp.BUDGET_AMOUNT,
                           COUNT(wd.ID) AS total_days,
                           SUM(CASE WHEN wd.STATUS = 'COMPLETED' THEN 1 ELSE 0 END) AS completed_days,
                           SUM(CASE WHEN wd.STATUS = 'CANCELLED' THEN 1 ELSE 0 END) AS cancelled_days,
                           COALESCE(SUM(wd.VALUE), 0) AS total_value
                    FROM job_projects jp
                    LEFT JOIN clients cl ON cl.ID = jp.CLIENT_ID
                    LEFT JOIN companies co ON co.ID = jp.COMPANY_ID
                    LEFT JOIN contractors c ON c.ID = jp.CONTRACTOR_ID
                    LEFT JOIN work_days wd ON wd.JOB_PROJECT_ID = jp.ID
                    GROUP BY jp.ID, jp.CODE, jp.PROJECT_TYPE, cl.FULL_NAME, co.COMPANY_NAME,
                             c.COMPANY_NAME, c.FULL_NAME, jp.JOB_ADDRESS, jp.BUDGET_AMOUNT
                    ORDER BY jp.ID DESC
                    """
                )
            except MySQLError:
                conn.rollback()
                cursor.execute(
                    """
                    SELECT jp.ID, jp.CODE, jp.PROJECT_TYPE,
                           COALESCE(cl.FULL_NAME, '—') AS client_name,
                           COALESCE(co.COMPANY_NAME, '—') AS company_name,
                           COALESCE(c.COMPANY_NAME, c.FULL_NAME, '—') AS contractor_name,
                           COALESCE(jp.JOB_ADDRESS, '—') AS job_address,
                           NULL AS budget_amount,
                           COUNT(wd.ID) AS total_days,
                           SUM(CASE WHEN wd.STATUS = 'COMPLETED' THEN 1 ELSE 0 END) AS completed_days,
                           SUM(CASE WHEN wd.STATUS = 'CANCELLED' THEN 1 ELSE 0 END) AS cancelled_days,
                           COALESCE(SUM(wd.VALUE), 0) AS total_value
                    FROM job_projects jp
                    LEFT JOIN clients cl ON cl.ID = jp.CLIENT_ID
                    LEFT JOIN companies co ON co.ID = jp.COMPANY_ID
                    LEFT JOIN contractors c ON c.ID = jp.CONTRACTOR_ID
                    LEFT JOIN work_days wd ON wd.JOB_PROJECT_ID = jp.ID
                    GROUP BY jp.ID, jp.CODE, jp.PROJECT_TYPE, cl.FULL_NAME, co.COMPANY_NAME,
                             c.COMPANY_NAME, c.FULL_NAME, jp.JOB_ADDRESS
                    ORDER BY jp.ID DESC
                    """
                )
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            return None, str(e)

        result = []
        for (jp_id, code, ptype, client_name, company_name, contractor_name, address,
             budget, total_days, completed_days, cancelled_days, total_value) in rows:
            status = self._classify_project_status(total_days, completed_days, cancelled_days)
            progress_pct = int(round((completed_days or 0) / total_days * 100)) if total_days else 0
            result.append({
                "ID": jp_id, "CODE": code, "PROJECT_TYPE": ptype,
                "CLIENT": client_name, "COMPANY": company_name, "CONTRACTOR": contractor_name,
                "ADDRESS": address, "BUDGET": budget, "TOTAL_DAYS": total_days or 0,
                "COMPLETED_DAYS": completed_days or 0, "CANCELLED_DAYS": cancelled_days or 0,
                "TOTAL_VALUE": float(total_value or 0), "STATUS": status, "PROGRESS_PCT": progress_pct,
            })
        return result, None

    def _refresh_projects_overview_widget(self):
        """Atualiza o gráfico de rosca + legenda + os 2 KPIs extras do
        painel 'Projects Overview' na Home. Chamado toda vez que a Home é
        carregada (load_home_dashboard) — se não der pra buscar os dados
        (ex: sem conexão), só mostra o gráfico vazio em vez de travar."""
        rows, error = self._fetch_projects_overview_rows()
        if error is not None:
            rows = []

        counts = {"ACTIVE": 0, "COMPLETED": 0, "CANCELLED": 0, "NO_JOBS": 0}
        for r in rows:
            counts[r["STATUS"]] = counts.get(r["STATUS"], 0) + 1

        segments = [
            (PROJECT_STATUS_LABELS[key], counts[key], PROJECT_STATUS_COLORS[key])
            for key in ("ACTIVE", "COMPLETED", "NO_JOBS", "CANCELLED")
        ]
        self.ui.donut_projects_status.set_data(segments)

        legend_layout = self.ui.layout_projects_status_legend
        while legend_layout.count():
            child = legend_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                sub = child.layout()
                while sub.count():
                    sub_child = sub.takeAt(0)
                    if sub_child.widget():
                        sub_child.widget().deleteLater()

        for key in ("ACTIVE", "COMPLETED", "NO_JOBS", "CANCELLED"):
            row = QHBoxLayout()
            dot = QLabel("●")
            dot.setStyleSheet(f"color:{PROJECT_STATUS_COLORS[key].name()}; font-size:14px;")
            row.addWidget(dot)
            lbl = QLabel(f"{PROJECT_STATUS_LABELS[key]}: {counts[key]}")
            lbl.setStyleSheet("color:#4A5568; font-size:12px;")
            row.addWidget(lbl)
            row.addStretch()
            legend_layout.addLayout(row)
        legend_layout.addStretch()

        self.ui.lbl_home_compliance_kpi.setText(str(getattr(self, "_compliance_due_soon", 0)))

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM bank_transactions WHERE STATUS = 'UNMATCHED'")
            unmatched = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            self.ui.lbl_home_bank_kpi.setText(str(unmatched or 0))
        except (MySQLError, RuntimeError):
            self.ui.lbl_home_bank_kpi.setText("—")

    def open_projects_dashboard_dialog(self):
        """Painel geral dos projetos: uma linha por Job Code, com status
        calculado a partir dos jobs (work_days) ligados a ele (Active/
        Completed/Cancelled/No Jobs Yet), barra de progresso, receita total
        e orçamento — inspirado em painéis de 'todos os projetos numa lista
        só, com abas de status e progresso' que ferramentas de gestão de
        obra costumam ter. Dá pra abrir a ficha completa do projeto (mesma
        tela de sempre, open_project_view_dialog) direto daqui."""
        rows, error = self._fetch_projects_overview_rows()
        if error is not None:
            QMessageBox.critical(self, "Database Error", f"Could not load projects:\n{error}")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Projects Dashboard")
        dialog.resize(980, 620)
        dialog.setStyleSheet("""
            QTableWidget { background-color: #FFFFFF; color: #1C2B3A; gridline-color: #E3E8EE; }
            QHeaderView::section { background-color: #F0F4F8; color: #1C2B3A; padding: 6px; border: none; font-weight: 600; }
        """)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(
            "<b>Projects Dashboard</b> — every Job Code, with status figured out from its jobs "
            "(Pending/Started/In Progress → Active), progress and revenue. Double-click a row "
            "(or select it and click 'Open Project') for the full project view."
        ))

        top_row = QHBoxLayout()
        tabs_holder = QHBoxLayout()
        tab_buttons = {}
        filter_state = {"status": None}

        def make_tab_button(label, status_key):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setAutoDefault(False)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                "QPushButton { padding: 6px 14px; border: 1px solid #D7DEE7; border-radius: 6px; "
                "background-color: #FFFFFF; color: #4A5568; font-weight: 600; } "
                "QPushButton:checked { background-color: #1565C0; color: #FFFFFF; border-color: #1565C0; }"
            )
            tab_buttons[status_key] = btn
            tabs_holder.addWidget(btn)

        make_tab_button("All", None)
        make_tab_button("Active", "ACTIVE")
        make_tab_button("Completed", "COMPLETED")
        make_tab_button("No Jobs Yet", "NO_JOBS")
        make_tab_button("Cancelled", "CANCELLED")
        tab_buttons[None].setChecked(True)
        top_row.addLayout(tabs_holder)
        top_row.addStretch()

        txt_search = QLineEdit()
        txt_search.setPlaceholderText("Search code, client, address...")
        txt_search.setMaximumWidth(240)
        top_row.addWidget(txt_search)
        layout.addLayout(top_row)

        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels(
            ["Code", "Client / Company / Contractor", "Address", "Status", "Progress", "Jobs", "Revenue", "Budget"]
        )
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(table, 1)

        row_codes = {}

        def matches_search(row, text):
            if not text:
                return True
            text = text.lower()
            haystack = " ".join([
                str(row["CODE"] or ""), str(row["CLIENT"] or ""), str(row["COMPANY"] or ""),
                str(row["CONTRACTOR"] or ""), str(row["ADDRESS"] or ""),
            ]).lower()
            return text in haystack

        def reload_table():
            status_filter = filter_state["status"]
            search_text = txt_search.text().strip()
            filtered = [
                r for r in rows
                if (status_filter is None or r["STATUS"] == status_filter) and matches_search(r, search_text)
            ]

            table.setRowCount(len(filtered))
            row_codes.clear()
            for i, r in enumerate(filtered):
                who = r["CLIENT"] if r["CLIENT"] != "—" else (r["COMPANY"] if r["COMPANY"] != "—" else r["CONTRACTOR"])

                item_code = QTableWidgetItem(r["CODE"])
                item_code.setFlags(item_code.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(i, 0, item_code)

                item_who = QTableWidgetItem(who)
                item_who.setFlags(item_who.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(i, 1, item_who)

                item_addr = QTableWidgetItem(r["ADDRESS"])
                item_addr.setFlags(item_addr.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(i, 2, item_addr)

                item_status = QTableWidgetItem(PROJECT_STATUS_LABELS.get(r["STATUS"], r["STATUS"]))
                item_status.setFlags(item_status.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item_status.setBackground(PROJECT_STATUS_COLORS.get(r["STATUS"], QColor("#EEEEEE")).lighter(170))
                table.setItem(i, 3, item_status)

                progress_bar = QProgressBar()
                progress_bar.setRange(0, 100)
                progress_bar.setValue(r["PROGRESS_PCT"])
                progress_bar.setTextVisible(True)
                progress_bar.setFormat(f"{r['PROGRESS_PCT']}%")
                progress_bar.setStyleSheet(
                    "QProgressBar { border: 1px solid #D7DEE7; border-radius: 4px; background: #F0F4F8; "
                    "text-align: center; } QProgressBar::chunk { background-color: #2E7D32; border-radius: 4px; }"
                )
                table.setCellWidget(i, 4, progress_bar)

                item_jobs = QTableWidgetItem(str(r["TOTAL_DAYS"]))
                item_jobs.setFlags(item_jobs.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(i, 5, item_jobs)

                item_rev = QTableWidgetItem(f"${r['TOTAL_VALUE']:,.2f}")
                item_rev.setFlags(item_rev.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(i, 6, item_rev)

                budget_text = f"${float(r['BUDGET']):,.2f}" if r["BUDGET"] is not None else "—"
                item_budget = QTableWidgetItem(budget_text)
                item_budget.setFlags(item_budget.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(i, 7, item_budget)

                row_codes[i] = r["CODE"]

        def select_tab(status_key):
            for key, btn in tab_buttons.items():
                btn.setChecked(key == status_key)
            filter_state["status"] = status_key
            reload_table()

        for key, btn in tab_buttons.items():
            btn.clicked.connect(lambda checked, k=key: select_tab(k))

        txt_search.textChanged.connect(reload_table)

        def open_selected_project():
            current = table.currentRow()
            if current < 0:
                QMessageBox.information(dialog, "No selection", "Select a project from the list first.")
                return
            code = row_codes.get(current)
            if not code:
                return
            dialog.close()
            self.open_project_view_dialog(job_code=code)

        table.cellDoubleClicked.connect(lambda r, c: open_selected_project())

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_open = QPushButton("Open Project")
        btn_open.setAutoDefault(False)
        btn_open.clicked.connect(open_selected_project)
        btn_close = QPushButton("Close")
        btn_close.setAutoDefault(False)
        btn_close.clicked.connect(dialog.close)
        btn_row.addWidget(btn_open)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

        reload_table()
        dialog.exec()

    def open_clean_empty_job_codes_dialog(self):
        """Acha os Job Codes que não têm nenhum job (work_days) nem material
        (job_materials) ligado a eles — "códigos fantasma" criados sem querer
        antes da validação existir — e deixa escolher quais apagar."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT jp.ID, jp.CODE, jp.CREATED_AT
                FROM job_projects jp
                LEFT JOIN work_days wd ON wd.JOB_PROJECT_ID = jp.ID
                LEFT JOIN job_materials jm ON jm.JOB_PROJECT_ID = jp.ID
                WHERE wd.ID IS NULL AND jm.ID IS NULL
                ORDER BY jp.CREATED_AT DESC
                """
            )
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not check job codes:\n{e}")
            return

        if not rows:
            QMessageBox.information(self, "All Clean", "No empty Job Codes found — everything is linked to a job.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Clean Empty Job Codes")
        dialog.resize(480, 520)
        dialog.setStyleSheet("""
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

        layout.addWidget(QLabel(
            f"Found {len(rows)} Job Code(s) with no jobs or materials linked. "
            f"Select which ones to delete — this cannot be undone."
        ))

        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["✓", "Code", "Created At"])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.setColumnWidth(0, 30)
        table.setColumnWidth(2, 140)
        table.setRowCount(len(rows))

        row_ids = {}
        for row_idx, (jp_id, code, created_at) in enumerate(rows):
            chk_item = QTableWidgetItem()
            chk_item.setFlags((chk_item.flags() | Qt.ItemFlag.ItemIsUserCheckable) & ~Qt.ItemFlag.ItemIsEditable)
            chk_item.setCheckState(Qt.CheckState.Checked)
            table.setItem(row_idx, 0, chk_item)

            created_str = created_at.strftime("%m/%d/%Y %I:%M %p") if created_at else "—"
            for c, text in enumerate([str(code), created_str], start=1):
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(row_idx, c, item)

            row_ids[row_idx] = jp_id

        layout.addWidget(table)

        bottom_row = QHBoxLayout()
        bottom_row.addStretch()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setAutoDefault(False)
        btn_delete = QPushButton("Delete Selected")
        btn_delete.setAutoDefault(False)
        btn_delete.setStyleSheet(
            "QPushButton { background-color: #C62828; color: #FFFFFF; border: none; "
            "border-radius: 6px; padding: 8px 14px; font-weight: 600; } "
            "QPushButton:hover { background-color: #E53935; }"
        )
        bottom_row.addWidget(btn_cancel)
        bottom_row.addWidget(btn_delete)
        layout.addLayout(bottom_row)

        def delete_selected():
            selected_ids = [
                row_ids[r] for r in range(table.rowCount())
                if table.item(r, 0).checkState() == Qt.CheckState.Checked
            ]
            if not selected_ids:
                QMessageBox.information(dialog, "No selection", "Select at least one Job Code to delete.")
                return

            confirm = QMessageBox.question(
                dialog, "Confirm delete",
                f"Delete {len(selected_ids)} empty Job Code(s)? This cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return

            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                placeholders = ", ".join(["%s"] * len(selected_ids))
                cursor.execute(f"DELETE FROM job_projects WHERE ID IN ({placeholders})", selected_ids)
                conn.commit()
                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not delete job codes:\n{e}")
                return

            QMessageBox.information(dialog, "Deleted", f"{len(selected_ids)} Job Code(s) deleted.")
            self._refresh_job_code_completer()
            dialog.accept()

        btn_cancel.clicked.connect(dialog.reject)
        btn_delete.clicked.connect(delete_selected)
        dialog.exec()

    def open_project_view_dialog(self, job_code=None):
        """Abre uma 'ficha do projeto': mostra todos os Jobs (work_days) e os
        materiais gastos sob um Job Code. Se `job_code` já vier preenchido
        (ex: chamado a partir do Projects Dashboard, com
        self.open_project_view_dialog(job_code="...")), usa ele direto —
        senão (comportamento original, botão "View Project" da lista de
        Work Days) lê da linha selecionada na tabela."""
        if not job_code:
            table = self.ui.table_work_days
            selected = table.currentRow()
            if selected < 0:
                QMessageBox.information(self, "No selection", "Select a job from the list first.")
                return

            job_code = table.item(selected, 15).text().strip()
            if not job_code or job_code == "—":
                QMessageBox.information(self, "No Job Code",
                                         "This job doesn't have a Job Code assigned yet.")
                return

        budget_amount = None
        expense_rows = []
        has_expense_link_column = True
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            try:
                cursor.execute(
                    """
                    SELECT jp.ID, jp.PROJECT_TYPE, COALESCE(cl.FULL_NAME, '—'),
                           COALESCE(co.COMPANY_NAME, '—'), COALESCE(c.COMPANY_NAME, c.FULL_NAME, '—'),
                           COALESCE(jp.JOB_ADDRESS, '—'), jp.BUDGET_AMOUNT
                    FROM job_projects jp
                    LEFT JOIN clients cl ON cl.ID = jp.CLIENT_ID
                    LEFT JOIN companies co ON co.ID = jp.COMPANY_ID
                    LEFT JOIN contractors c ON c.ID = jp.CONTRACTOR_ID
                    WHERE jp.CODE = %s
                    """,
                    (job_code,),
                )
                project_row = cursor.fetchone()
                has_budget_column = True
            except MySQLError:
                # migration_fase3_budget_expenses.sql ainda não rodou nesse banco —
                # carrega sem a coluna de orçamento em vez de travar a tela.
                cursor.execute(
                    """
                    SELECT jp.ID, jp.PROJECT_TYPE, COALESCE(cl.FULL_NAME, '—'),
                           COALESCE(co.COMPANY_NAME, '—'), COALESCE(c.COMPANY_NAME, c.FULL_NAME, '—'),
                           COALESCE(jp.JOB_ADDRESS, '—')
                    FROM job_projects jp
                    LEFT JOIN clients cl ON cl.ID = jp.CLIENT_ID
                    LEFT JOIN companies co ON co.ID = jp.COMPANY_ID
                    LEFT JOIN contractors c ON c.ID = jp.CONTRACTOR_ID
                    WHERE jp.CODE = %s
                    """,
                    (job_code,),
                )
                project_row = cursor.fetchone()
                has_budget_column = False

            if not project_row:
                cursor.close()
                conn.close()
                QMessageBox.warning(self, "Not Found", f"Job Code '{job_code}' was not found.")
                return

            if has_budget_column:
                (job_project_id, project_type, client_name, company_name,
                 contractor_name, job_address, budget_amount) = project_row
            else:
                (job_project_id, project_type, client_name, company_name,
                 contractor_name, job_address) = project_row

            cursor.execute(
                "SELECT COUNT(DISTINCT WORK_DATE), MIN(WORK_DATE), MAX(WORK_DATE), COALESCE(SUM(VALUE), 0) "
                "FROM work_days WHERE JOB_PROJECT_ID = %s",
                (job_project_id,),
            )
            days_count, min_date, max_date, total_value = cursor.fetchone()

            cursor.execute(
                """
                SELECT wd.WORK_DATE, COALESCE(c.COMPANY_NAME, c.FULL_NAME, '—'), wd.VALUE, wd.STATUS
                FROM work_days wd
                LEFT JOIN contractors c ON c.ID = wd.CONTRACTOR_ID
                WHERE wd.JOB_PROJECT_ID = %s
                ORDER BY wd.WORK_DATE
                """,
                (job_project_id,),
            )
            job_rows = cursor.fetchall()

            cursor.execute(
                """
                SELECT COALESCE(p.NAME, '—'), jm.QUANTITY, COALESCE(p.UNIT, ''), jm.UNIT_PRICE
                FROM job_materials jm
                LEFT JOIN products p ON p.ID = jm.PRODUCT_ID
                WHERE jm.JOB_PROJECT_ID = %s
                ORDER BY jm.ID
                """,
                (job_project_id,),
            )
            material_rows = cursor.fetchall()

            try:
                cursor.execute(
                    "SELECT EXPENSE_DATE, CATEGORY, DESCRIPTION, AMOUNT "
                    "FROM expenses WHERE JOB_PROJECT_ID = %s ORDER BY EXPENSE_DATE",
                    (job_project_id,),
                )
                expense_rows = cursor.fetchall()
            except MySQLError:
                # migration_fase3_budget_expenses.sql ainda não rodou nesse banco.
                has_expense_link_column = False

            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not load project:\n{e}")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Project {job_code}")
        dialog.resize(600, 780)
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel(f"<b>Job Code:</b> {job_code}"))
        layout.addWidget(QLabel(f"<b>Client:</b> {client_name} &nbsp;&nbsp; <b>Company:</b> {company_name}"))
        layout.addWidget(QLabel(f"<b>Contractor:</b> {contractor_name} &nbsp;&nbsp; <b>Address:</b> {job_address}"))
        layout.addWidget(QLabel(""))

        days_count = days_count or 0
        if days_count:
            span_days = (max_date - min_date).days + 1 if min_date and max_date else days_count
            gaps = span_days - days_count
            gap_text = f" ({gaps} day{'s' if gaps != 1 else ''} with no work)" if gaps > 0 else ""
            period_text = (
                f"{min_date.strftime('%m/%d/%Y')} to {max_date.strftime('%m/%d/%Y')}{gap_text}"
                if min_date and max_date else ""
            )
        else:
            period_text = "No days recorded yet"
        lbl_days = QLabel(f"<span style='font-size:18px; font-weight:800; color:#1565C0;'>"
                           f"🗓 {days_count} day{'s' if days_count != 1 else ''} worked</span><br/>{period_text}")
        layout.addWidget(lbl_days)
        layout.addWidget(QLabel(f"<b>Total Value:</b> ${float(total_value or 0):,.2f}"))
        layout.addWidget(QLabel(""))

        layout.addWidget(QLabel("<b>Jobs Under This Code</b>"))
        table_jobs = QTableWidget()
        table_jobs.setColumnCount(4)
        table_jobs.setHorizontalHeaderLabels(["Date", "Contractor", "Value", "Status"])
        table_jobs.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table_jobs.horizontalHeader().setStretchLastSection(True)
        table_jobs.setMaximumHeight(180)
        table_jobs.setRowCount(len(job_rows))
        for r, (wdate, cname, val, status) in enumerate(job_rows):
            date_str = wdate.strftime("%m/%d/%Y") if isinstance(wdate, date) else str(wdate)
            for c, text in enumerate([date_str, cname, f"${float(val or 0):,.2f}",
                                       JOB_STATUS_LABELS.get(status, status)]):
                table_jobs.setItem(r, c, QTableWidgetItem(text))
        layout.addWidget(table_jobs)

        layout.addWidget(QLabel("<b>Materials Used</b>"))
        table_materials = QTableWidget()
        table_materials.setColumnCount(3)
        table_materials.setHorizontalHeaderLabels(["Product", "Qty", "Unit"])
        table_materials.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table_materials.horizontalHeader().setStretchLastSection(True)
        table_materials.setMaximumHeight(140)
        table_materials.setRowCount(len(material_rows))
        material_cost_total = 0.0
        for r, (pname, qty, unit, unit_price) in enumerate(material_rows):
            qty = float(qty or 0)
            material_cost_total += qty * float(unit_price or 0)
            for c, text in enumerate([pname, f"{qty:g}", unit]):
                table_materials.setItem(r, c, QTableWidgetItem(text))
        layout.addWidget(table_materials)

        if project_type == "PRIVATE":
            layout.addWidget(QLabel(f"<b>Total Material Cost:</b> ${material_cost_total:,.2f}"))

        # ── Expenses vinculadas a este projeto (job_costing) ──────────
        expense_total = sum(float(amount or 0) for (_edate, _cat, _desc, amount) in expense_rows)
        table_expenses_linked = None
        if has_expense_link_column:
            layout.addWidget(QLabel("<b>Expenses Linked to This Project</b>"))
            table_expenses_linked = QTableWidget()
            table_expenses_linked.setColumnCount(4)
            table_expenses_linked.setHorizontalHeaderLabels(["Date", "Category", "Description", "Amount"])
            table_expenses_linked.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            table_expenses_linked.horizontalHeader().setStretchLastSection(True)
            table_expenses_linked.setMaximumHeight(140)
            table_expenses_linked.setRowCount(len(expense_rows))
            for r, (edate, category, description, amount) in enumerate(expense_rows):
                date_str = edate.strftime("%m/%d/%Y") if isinstance(edate, date) else str(edate or "")
                values = [date_str, category or "", description or "", f"${float(amount or 0):,.2f}"]
                for c, text in enumerate(values):
                    table_expenses_linked.setItem(r, c, QTableWidgetItem(text))
            layout.addWidget(table_expenses_linked)
            if not expense_rows:
                lbl_no_expenses = QLabel(
                    "No expenses linked to this project yet — pick this Job Code in the "
                    "'Job Code (optional)' field on the Expenses tab to link one."
                )
                lbl_no_expenses.setWordWrap(True)
                lbl_no_expenses.setStyleSheet("color:#6B7C93; font-style:italic;")
                layout.addWidget(lbl_no_expenses)
        else:
            lbl_no_expense_link = QLabel(
                "Linking expenses to a project requires migration_fase3_budget_expenses.sql — "
                "not run yet on this database."
            )
            lbl_no_expense_link.setWordWrap(True)
            lbl_no_expense_link.setStyleSheet("color:#C62828; font-style:italic;")
            layout.addWidget(lbl_no_expense_link)

        # ── Budget x Actual (orçado x realizado) ──────────────────────
        layout.addWidget(QLabel(""))
        actual_cost = material_cost_total + expense_total
        estimated_profit = float(total_value or 0) - actual_cost

        def variance_html(budget_value):
            lines = [f"<b>Actual Cost</b> (materials + linked expenses): ${actual_cost:,.2f}"]
            if budget_value:
                variance = budget_value - actual_cost
                color = "#C62828" if variance < 0 else "#2E7D32"
                status = "OVER budget" if variance < 0 else "under budget"
                lines.append(
                    f"<span style='color:{color}; font-weight:700;'>"
                    f"${abs(variance):,.2f} {status}</span> (budget ${budget_value:,.2f})"
                )
            profit_color = "#2E7D32" if estimated_profit >= 0 else "#C62828"
            lines.append(
                f"<b>Estimated Profit</b> (Total Value − Actual Cost): "
                f"<span style='color:{profit_color}; font-weight:700;'>${estimated_profit:,.2f}</span>"
            )
            return "<br/>".join(lines)

        lbl_variance = QLabel(variance_html(float(budget_amount or 0)))
        lbl_variance.setWordWrap(True)

        budget_row = QHBoxLayout()
        budget_row.addWidget(QLabel("<b>Budget:</b>"))
        spin_budget = QDoubleSpinBox()
        spin_budget.setRange(0, 99999999)
        spin_budget.setDecimals(2)
        spin_budget.setPrefix("$ ")
        spin_budget.setValue(float(budget_amount or 0))
        budget_row.addWidget(spin_budget)
        btn_save_budget = QPushButton("Save Budget")

        def save_budget():
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE job_projects SET BUDGET_AMOUNT = %s WHERE ID = %s",
                    (spin_budget.value(), job_project_id),
                )
                conn.commit()
                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(
                    dialog, "Database Error",
                    f"Could not save budget:\n{e}\n\n"
                    f"(Did you run migration_fase3_budget_expenses.sql yet?)",
                )
                return
            lbl_variance.setText(variance_html(spin_budget.value()))
            QMessageBox.information(dialog, "Saved", "Budget updated.")

        btn_save_budget.clicked.connect(save_budget)
        budget_row.addWidget(btn_save_budget)
        budget_row.addStretch()
        layout.addLayout(budget_row)
        layout.addWidget(lbl_variance)
        layout.addWidget(QLabel(""))

        def export_excel():
            path, _ = QFileDialog.getSaveFileName(
                dialog, "Export Project to Excel", f"Project_{job_code}.xlsx", "Excel Files (*.xlsx)"
            )
            if not path:
                return
            if not path.lower().endswith(".xlsx"):
                path += ".xlsx"
            try:
                import openpyxl
                from openpyxl.styles import Font, PatternFill, Alignment
                from openpyxl.utils import get_column_letter
            except ImportError:
                QMessageBox.critical(dialog, "Missing Dependency",
                                      "The 'openpyxl' package is not installed.\n\nRun:\npip install openpyxl")
                return

            try:
                wb = openpyxl.Workbook()
                header_font = Font(bold=True, color="FFFFFF")
                header_fill = PatternFill(start_color="1C2B3A", end_color="1C2B3A", fill_type="solid")

                ws_summary = wb.active
                ws_summary.title = "Summary"
                summary_rows = [
                    ("Job Code", job_code),
                    ("Client", client_name), ("Company", company_name),
                    ("Contractor", contractor_name), ("Address", job_address),
                    ("Days Worked", days_count), ("Period", period_text),
                    ("Total Value", f"${float(total_value or 0):,.2f}"),
                ]
                if project_type == "PRIVATE":
                    summary_rows.append(("Total Material Cost", f"${material_cost_total:,.2f}"))
                if has_expense_link_column:
                    summary_rows.append(("Linked Expenses Total", f"${expense_total:,.2f}"))
                summary_rows.append(("Actual Cost (materials + expenses)", f"${actual_cost:,.2f}"))
                if budget_amount:
                    summary_rows.append(("Budget", f"${float(budget_amount):,.2f}"))
                    summary_rows.append(("Variance", f"${float(budget_amount) - actual_cost:,.2f}"))
                summary_rows.append(("Estimated Profit", f"${estimated_profit:,.2f}"))
                for row_vals in summary_rows:
                    ws_summary.append(row_vals)
                ws_summary.column_dimensions["A"].width = 26
                ws_summary.column_dimensions["B"].width = 40
                for cell in ws_summary["A"]:
                    cell.font = Font(bold=True)

                ws_jobs = wb.create_sheet("Jobs")
                ws_jobs.append(["Date", "Contractor", "Value", "Status"])
                for c in range(1, 5):
                    cell = ws_jobs.cell(row=1, column=c)
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = Alignment(horizontal="center")
                for r in range(table_jobs.rowCount()):
                    ws_jobs.append([table_jobs.item(r, c).text() for c in range(4)])
                for c in range(1, 5):
                    ws_jobs.column_dimensions[get_column_letter(c)].width = 18

                ws_materials = wb.create_sheet("Materials")
                ws_materials.append(["Product", "Qty", "Unit"])
                for c in range(1, 4):
                    cell = ws_materials.cell(row=1, column=c)
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = Alignment(horizontal="center")
                for r in range(table_materials.rowCount()):
                    ws_materials.append([table_materials.item(r, c).text() for c in range(3)])
                for c in range(1, 4):
                    ws_materials.column_dimensions[get_column_letter(c)].width = 20

                if table_expenses_linked is not None and table_expenses_linked.rowCount():
                    ws_expenses = wb.create_sheet("Expenses")
                    ws_expenses.append(["Date", "Category", "Description", "Amount"])
                    for c in range(1, 5):
                        cell = ws_expenses.cell(row=1, column=c)
                        cell.font = header_font
                        cell.fill = header_fill
                        cell.alignment = Alignment(horizontal="center")
                    for r in range(table_expenses_linked.rowCount()):
                        ws_expenses.append([table_expenses_linked.item(r, c).text() for c in range(4)])
                    for c in range(1, 5):
                        ws_expenses.column_dimensions[get_column_letter(c)].width = 18

                wb.save(path)
                QMessageBox.information(dialog, "Export Complete", f"Saved to:\n{path}")
            except Exception as e:
                QMessageBox.critical(dialog, "Export Error", f"Could not export to Excel:\n{e}")

        def export_pdf():
            if not REPORTLAB_AVAILABLE:
                QMessageBox.critical(dialog, "Missing Dependency",
                                      "The 'reportlab' package is not installed.\n\nRun:\npip install reportlab")
                return
            path, _ = QFileDialog.getSaveFileName(
                dialog, "Export Project to PDF", f"Project_{job_code}.pdf", "PDF Files (*.pdf)"
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
                    Paragraph(f"<b>Project {job_code}</b>", styles["Title"]),
                    Spacer(1, 10),
                    Paragraph(f"<b>Client:</b> {client_name} &nbsp;&nbsp; <b>Company:</b> {company_name}",
                              styles["Normal"]),
                    Paragraph(f"<b>Contractor:</b> {contractor_name} &nbsp;&nbsp; <b>Address:</b> {job_address}",
                              styles["Normal"]),
                    Spacer(1, 10),
                    Paragraph(f"<b>{days_count} day(s) worked</b> — {period_text}", styles["Normal"]),
                    Paragraph(f"<b>Total Value:</b> ${float(total_value or 0):,.2f}", styles["Normal"]),
                    Spacer(1, 16),
                    Paragraph("<b>Jobs Under This Code</b>", styles["Heading3"]),
                ]

                jobs_data = [["Date", "Contractor", "Value", "Status"]]
                for r in range(table_jobs.rowCount()):
                    jobs_data.append([table_jobs.item(r, c).text() for c in range(4)])
                jobs_table_pdf = Table(jobs_data, colWidths=[1.1 * inch, 2.0 * inch, 1.1 * inch, 1.4 * inch],
                                        repeatRows=1)
                jobs_table_pdf.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(BRAND_NAVY)),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DDDDDD")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F9FC")]),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]))
                story.append(jobs_table_pdf)

                story.append(Spacer(1, 16))
                story.append(Paragraph("<b>Materials Used</b>", styles["Heading3"]))
                materials_data = [["Product", "Qty", "Unit"]]
                for r in range(table_materials.rowCount()):
                    materials_data.append([table_materials.item(r, c).text() for c in range(3)])
                materials_table_pdf = Table(materials_data, colWidths=[2.6 * inch, 1.3 * inch, 1.3 * inch],
                                             repeatRows=1)
                materials_table_pdf.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#37474F")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DDDDDD")),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]))
                story.append(materials_table_pdf)

                if project_type == "PRIVATE":
                    story.append(Spacer(1, 10))
                    story.append(Paragraph(f"<b>Total Material Cost:</b> ${material_cost_total:,.2f}",
                                            styles["Normal"]))

                if table_expenses_linked is not None and table_expenses_linked.rowCount():
                    story.append(Spacer(1, 16))
                    story.append(Paragraph("<b>Expenses Linked to This Project</b>", styles["Heading3"]))
                    expenses_data = [["Date", "Category", "Description", "Amount"]]
                    for r in range(table_expenses_linked.rowCount()):
                        expenses_data.append([table_expenses_linked.item(r, c).text() for c in range(4)])
                    expenses_table_pdf = Table(
                        expenses_data,
                        colWidths=[1.0 * inch, 1.2 * inch, 2.2 * inch, 1.0 * inch],
                        repeatRows=1,
                    )
                    expenses_table_pdf.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#37474F")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DDDDDD")),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ]))
                    story.append(expenses_table_pdf)

                story.append(Spacer(1, 16))
                story.append(Paragraph("<b>Budget x Actual</b>", styles["Heading3"]))
                story.append(Paragraph(f"<b>Actual Cost</b> (materials + linked expenses): ${actual_cost:,.2f}",
                                        styles["Normal"]))
                if budget_amount:
                    variance = float(budget_amount) - actual_cost
                    status = "OVER budget" if variance < 0 else "under budget"
                    story.append(Paragraph(
                        f"<b>Budget:</b> ${float(budget_amount):,.2f} — ${abs(variance):,.2f} {status}",
                        styles["Normal"],
                    ))
                story.append(Paragraph(f"<b>Estimated Profit</b> (Total Value − Actual Cost): "
                                        f"${estimated_profit:,.2f}", styles["Normal"]))

                doc.build(story)
                QMessageBox.information(dialog, "Export Complete", f"Saved to:\n{path}")
            except Exception as e:
                QMessageBox.critical(dialog, "Export Error", f"Could not export to PDF:\n{e}")

        export_row = QHBoxLayout()
        btn_export_excel = QPushButton("⤓  Excel")
        btn_export_excel.clicked.connect(export_excel)
        btn_export_pdf = QPushButton("⤓  PDF")
        btn_export_pdf.clicked.connect(export_pdf)
        btn_generate_invoice = QPushButton("🧾  Generate Invoice")
        btn_generate_invoice.setStyleSheet(
            "QPushButton { background-color: #1565C0; color: #FFFFFF; border: none; "
            "border-radius: 6px; padding: 8px 14px; font-weight: 600; } "
            "QPushButton:hover { background-color: #1E88E5; }"
        )

        def go_generate_invoice_for_job_code():
            dialog.accept()
            self.open_generate_invoices_dialog(prefill_job_code=job_code)

        btn_generate_invoice.clicked.connect(go_generate_invoice_for_job_code)

        btn_documents = QPushButton("📁  Documents")

        def go_documents_for_project():
            self.open_documents_manager_dialog(prefill_entity_type="PROJECT", prefill_entity_id=job_project_id)

        btn_documents.clicked.connect(go_documents_for_project)

        export_row.addWidget(btn_export_excel)
        export_row.addWidget(btn_export_pdf)
        export_row.addWidget(btn_generate_invoice)
        export_row.addWidget(btn_documents)
        export_row.addStretch()
        layout.addLayout(export_row)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)

        dialog.exec()

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
            return "Yes" if any(i is not None for i in ids) else "Not"

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

    # ══════════════════════════════════════════════════════════════
    # WORK_DAYS — FORMULÁRIO (CREATE / UPDATE / DELETE)
    # ══════════════════════════════════════════════════════════════

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

    # ══════════════════════════════════════════════════════════════
    # JOB CODE (job_projects) — agrupa vários dias de trabalho num só projeto
    # ══════════════════════════════════════════════════════════════

    def _setup_job_code_completer(self):
        """Configura o autocomplete do campo Job Code."""
        self._job_code_to_id = {}
        self._job_code_completer = QCompleter([], self)
        self._job_code_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._job_code_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._job_code_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.ui.cmb_job_code.setCompleter(self._job_code_completer)

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
        """Cria um novo projeto (job_projects) com um código sequencial novo
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

            cursor.execute(
                "INSERT INTO job_projects (CODE, PROJECT_TYPE, STATUS) VALUES (%s, 'DAY_WORK', 'ACTIVE')",
                (new_code,),
            )
            conn.commit()
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
            self._update_days_worked_label()
            return

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
                "FROM work_days WHERE JOB_PROJECT_ID = %s ORDER BY ID DESC LIMIT 1",
                (job_id,),
            )
            row = cursor.fetchone()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError):
            row = None

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
        sob o código de projeto atual."""
        typed = self.ui.cmb_job_code.currentText().strip().upper()
        job_id = self._job_code_to_id.get(typed)

        if not job_id:
            self.ui.lbl_days_worked_value.setText("—")
            return

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(DISTINCT WORK_DATE) FROM work_days WHERE JOB_PROJECT_ID = %s",
                (job_id,),
            )
            days_count = cursor.fetchone()[0] or 0
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError):
            self.ui.lbl_days_worked_value.setText("—")
            return

        self.ui.lbl_days_worked_value.setText(f"🗓 {days_count} day{'s' if days_count != 1 else ''}")

    # ══════════════════════════════════════════════════════════════
    # MATERIALS USED (job_materials) — ligado ao projeto (Job Code), não ao dia
    # ══════════════════════════════════════════════════════════════

    def _refresh_material_product_combo(self):
        """Popula o combo de produtos usado pra adicionar material gasto."""
        self.ui.cmb_material_product.clear()
        self.ui.cmb_material_product.addItem("— Select a product —", None)
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT ID, NAME, UNIT, PRICE FROM products ORDER BY NAME")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError):
            rows = []
        self._products_cache = {}
        for product_id, name, unit, price in rows:
            self.ui.cmb_material_product.addItem(name, product_id)
            self._products_cache[product_id] = (name, unit or "", float(price or 0))

    def _load_job_materials(self):
        """Carrega a lista de materiais gastos no projeto (Job Code) atual."""
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
                SELECT jm.ID, COALESCE(p.NAME, '—'), jm.QUANTITY, COALESCE(p.UNIT, ''), jm.UNIT_PRICE
                FROM job_materials jm
                LEFT JOIN products p ON p.ID = jm.PRODUCT_ID
                WHERE jm.JOB_PROJECT_ID = %s
                ORDER BY jm.ID
                """,
                (job_id,),
            )
            rows = cursor.fetchall()
            cursor.execute("SELECT PROJECT_TYPE FROM job_projects WHERE ID = %s", (job_id,))
            project_type_row = cursor.fetchone()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.warning(self, "Database Error", f"Could not load materials:\n{e}")
            return

        table.setRowCount(len(rows))
        total_cost = 0.0
        for row_idx, (material_id, name, qty, unit, unit_price) in enumerate(rows):
            qty = float(qty or 0)
            total_cost += qty * float(unit_price or 0)
            item_id = QTableWidgetItem(name)
            item_id.setData(Qt.ItemDataRole.UserRole, material_id)
            table.setItem(row_idx, 0, item_id)
            table.setItem(row_idx, 1, QTableWidgetItem(f"{qty:g}"))
            table.setItem(row_idx, 2, QTableWidgetItem(unit))
            for col in range(3):
                table.item(row_idx, col).setFlags(
                    table.item(row_idx, col).flags() & ~Qt.ItemFlag.ItemIsEditable
                )

        # O custo total de material só é mostrado em trabalhos do tipo "Particular"
        # (por enquanto todo Job Code criado é DAY_WORK, então isso fica reservado
        # pra quando a área de trabalhos particulares existir).
        project_type = project_type_row[0] if project_type_row else "DAY_WORK"
        if project_type == "PRIVATE":
            self.ui.lbl_materials_total_cost.setText(f"Total Material Cost: ${total_cost:,.2f}")
            self.ui.lbl_materials_total_cost.setVisible(True)
        else:
            self.ui.lbl_materials_total_cost.setVisible(False)

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
        if self._table_column_exists("work_days", "HELPER_ID"):
            data["HELPER_ID"] = self.ui.cmb_helper.currentData()

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
        for prefix, combo, spin in work_type_fields:
            type_id = combo.currentData()
            data[f"{prefix}_ID"] = type_id
            data[f"{prefix}_QTY"] = spin.value() if type_id else None

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

            if self._current_job_id:
                set_clause = ", ".join(f"{k} = %s" for k in data)
                query = f"UPDATE work_days SET {set_clause} WHERE ID = %s"
                cursor.execute(query, list(data.values()) + [self._current_job_id])
            else:
                cols = ", ".join(data.keys())
                placeholders = ", ".join(["%s"] * len(data))
                query = f"INSERT INTO work_days ({cols}) VALUES ({placeholders})"
                cursor.execute(query, list(data.values()))

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

    # ══════════════════════════════════════════════════════════════
    # SPLIT DAILY TOTAL — divide um valor recebido no dia entre os jobs
    # ══════════════════════════════════════════════════════════════

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


    # ══════════════════════════════════════════════════════════════
    # COMPANY — LISTAGEM
    # ══════════════════════════════════════════════════════════════

    def load_companies(self):
        """Carrega os registros de company na tabela, aplicando filtros de busca e status."""
        search_text = self.ui.txt_search_companies.text().strip()
        status_filter = self.ui.cmb_filter_company_status.currentText()

        query = """
            SELECT
                co.ID, co.COMPANY_NAME, co.CONTACT_NAME, co.EMAIL,
                co.PHONE_NUMBER, co.PHONE_NUMBER2, co.ADDRESS,
                COALESCE(city.CITY, co.CITY_ID) AS CITY_NAME,
                COALESCE(st.STATE_NAME, co.STATE_ID) AS STATE_NAME,
                co.ZIP_CODE, co.WEBSITE, co.STATUS
            FROM companies co
            LEFT JOIN cities city ON city.ID = co.CITY_ID
            LEFT JOIN states st ON st.ID = co.STATE_ID
            WHERE 1=1
        """
        params = []

        if search_text:
            query += """
                AND (co.COMPANY_NAME LIKE %s
                     OR co.CONTACT_NAME LIKE %s
                     OR COALESCE(city.CITY, '') LIKE %s)
            """
            like = f"%{search_text}%"
            params.extend([like, like, like])

        if status_filter and status_filter != "All Status":
            query += " AND co.STATUS = %s"
            params.append(status_filter)

        query += " ORDER BY co.COMPANY_NAME ASC"

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except MySQLError as e:
            QMessageBox.critical(self, "Database Error", f"Could not load companies:\n{e}")
            return
        except RuntimeError as e:
            QMessageBox.warning(self, "Driver Missing", str(e))
            return

        self._populate_companies_table(rows)

    def _populate_companies_table(self, rows):
        """Preenche a tabela de Companies linha a linha."""
        table = self.ui.table_companies
        table.setSortingEnabled(False)
        table.setRowCount(0)
        table.setRowCount(len(rows))

        for row_idx, row_data in enumerate(rows):
            (company_id, name, contact_name, email, phone, phone2,
             address, city, state, zip_code, website, status) = row_data

            values = [
                str(company_id),
                str(name or ""),
                str(contact_name or "—"),
                str(email or ""),
                self._format_phone(phone) or "",
                self._format_phone(phone2) or "",
                str(address or ""),
                str(city or "—"),
                str(state or "—"),
                str(zip_code or ""),
                str(website or ""),
                str(status or ""),
            ]

            for col_idx, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(row_idx, col_idx, item)

        table.setSortingEnabled(True)

    # ══════════════════════════════════════════════════════════════
    # COMPANY — FORMULÁRIO (CREATE / UPDATE / DELETE)
    # ══════════════════════════════════════════════════════════════

    def new_company_record(self):
        """Limpa o formulário para criar uma nova empresa."""
        self._current_company_id = None
        self.ui.txt_company_id.clear()
        self.ui.lbl_company_id_display.setText("#ID: New")
        for field in (self.ui.txt_company_name, self.ui.txt_contact_name,
                      self.ui.txt_company_email, self.ui.txt_company_phone,
                      self.ui.txt_company_phone2, self.ui.txt_company_address,
                      self.ui.txt_company_address2, self.ui.txt_company_zip,
                      self.ui.txt_company_website, self.ui.txt_company_instagram,
                      self.ui.txt_company_facebook, self.ui.txt_company_linkedin,
                      self.ui.txt_company_twitter):
            field.clear()
        self.ui.txt_company_notes.clear()
        self.ui.cmb_company_city.setCurrentIndex(0)
        self.ui.cmb_company_state.setCurrentIndex(0)
        self._reload_city_combo_for_state(self.ui.cmb_company_city, None)
        self.ui.cmb_company_status.setCurrentIndex(0)
        self.ui.tabWidget_companies_page.setCurrentWidget(self.ui.tab_companies_master)

    def load_company_into_form(self):
        """Carrega a empresa selecionada na tabela para edição."""
        table = self.ui.table_companies
        selected = table.currentRow()
        if selected < 0:
            return

        company_id = table.item(selected, 0).text()
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM companies WHERE ID = %s", (company_id,))
            columns = [d[0] for d in cursor.description]
            row = cursor.fetchone()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not load company:\n{e}")
            return

        if not row:
            return

        data = dict(zip(columns, row))
        self._current_company_id = data["ID"]
        self.ui.txt_company_id.setText(str(data["ID"]))
        self.ui.lbl_company_id_display.setText(f"#ID: {data['ID']}")

        self.ui.txt_company_name.setText(data.get("COMPANY_NAME") or "")
        self.ui.txt_contact_name.setText(data.get("CONTACT_NAME") or "")
        self.ui.txt_company_email.setText(data.get("EMAIL") or "")
        self.ui.txt_company_phone.setText(self._format_phone(data.get("PHONE_NUMBER")) or "")
        self.ui.txt_company_phone2.setText(self._format_phone(data.get("PHONE_NUMBER2")) or "")
        self.ui.txt_company_address.setText(data.get("ADDRESS") or "")
        self.ui.txt_company_address2.setText(data.get("ADDRESS2") or "")
        self.ui.txt_company_zip.setText(self._format_zip(data.get("ZIP_CODE")) or "")
        self.ui.txt_company_website.setText(data.get("WEBSITE") or "")
        self.ui.txt_company_instagram.setText(data.get("INSTAGRAM") or "")
        self.ui.txt_company_facebook.setText(data.get("FACEBOOK") or "")
        self.ui.txt_company_linkedin.setText(data.get("LINKEDIN") or "")
        self.ui.txt_company_twitter.setText(data.get("TWITTER") or "")
        self.ui.txt_company_notes.setPlainText(data.get("NOTES") or "")

        self._set_combo_by_data(self.ui.cmb_company_state, data.get("STATE_ID"))
        self._reload_city_combo_for_state(self.ui.cmb_company_city, data.get("STATE_ID"), keep_city_id=data.get("CITY_ID"))
        self._set_combo_by_data(self.ui.cmb_company_status, data.get("STATUS"), by_text=True)

        self.ui.tabWidget_companies_page.setCurrentWidget(self.ui.tab_companies_master)

    def save_company_record(self):
        """Insere ou atualiza um registro em company."""
        name = self.ui.txt_company_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing data", "Company Name is required.")
            return

        data = {
            "COMPANY_NAME": name,
            "CONTACT_NAME": self.ui.txt_contact_name.text(),
            "EMAIL": self.ui.txt_company_email.text(),
            "PHONE_NUMBER": self._format_phone(self.ui.txt_company_phone.text()),
            "PHONE_NUMBER2": self._format_phone(self.ui.txt_company_phone2.text()),
            "ADDRESS": self.ui.txt_company_address.text(),
            "ADDRESS2": self.ui.txt_company_address2.text(),
            "CITY_ID": self.ui.cmb_company_city.currentData(),
            "STATE_ID": self.ui.cmb_company_state.currentData(),
            "ZIP_CODE": self._format_zip(self.ui.txt_company_zip.text()),
            "WEBSITE": self.ui.txt_company_website.text(),
            "INSTAGRAM": self.ui.txt_company_instagram.text(),
            "FACEBOOK": self.ui.txt_company_facebook.text(),
            "LINKEDIN": self.ui.txt_company_linkedin.text(),
            "TWITTER": self.ui.txt_company_twitter.text(),
            "STATUS": self.ui.cmb_company_status.currentText(),
            "NOTES": self.ui.txt_company_notes.toPlainText(),
        }

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            if getattr(self, "_current_company_id", None):
                set_clause = ", ".join(f"{k} = %s" for k in data)
                query = f"UPDATE companies SET {set_clause} WHERE ID = %s"
                cursor.execute(query, list(data.values()) + [self._current_company_id])
            else:
                cols = ", ".join(data.keys())
                placeholders = ", ".join(["%s"] * len(data))
                query = f"INSERT INTO companies ({cols}) VALUES ({placeholders})"
                cursor.execute(query, list(data.values()))

            conn.commit()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not save company:\n{e}")
            return

        QMessageBox.information(self, "Success", "Company saved successfully.")
        self.load_companies()
        self.load_combo_data()  # atualiza combo de company usado no form de Jobs
        self.new_company_record()
        self.ui.tabWidget_companies_page.setCurrentWidget(self.ui.tab_companies_master)

    def delete_company_record(self):
        """Exclui a empresa atualmente carregada no formulário."""
        if not getattr(self, "_current_company_id", None):
            QMessageBox.information(self, "No record selected",
                                     "Select a company from the list before deleting.")
            return

        confirm = QMessageBox.question(
            self, "Confirm delete",
            f"Are you sure you want to delete company #{self._current_company_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM companies WHERE ID = %s", (self._current_company_id,))
            conn.commit()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not delete company:\n{e}")
            return

        QMessageBox.information(self, "Deleted", "Company deleted.")
        self.new_company_record()
        self.load_companies()
        self.ui.tabWidget_companies_page.setCurrentWidget(self.ui.tab_companies_master)

    # ══════════════════════════════════════════════════════════════
    # CONTRACTOR — LISTAGEM
    # ══════════════════════════════════════════════════════════════

    def load_contractors(self):
        """Carrega os registros de contractor na tabela, aplicando filtros de busca e status."""
        search_text = self.ui.txt_search_contractors.text().strip()
        status_filter = self.ui.cmb_filter_contractor_status.currentText()

        query = """
            SELECT
                c.ID, c.FULL_NAME, c.EMAIL, c.PHONE_NUMBER, c.POSITION,
                c.COMPANY_NAME, c.COMPANY_PHONE_NUMBER,
                COALESCE(city.CITY, c.CITY_ID) AS CITY_NAME,
                COALESCE(st.STATE_NAME, c.STATE_ID) AS STATE_NAME,
                c.STATUS
            FROM contractors c
            LEFT JOIN cities city ON city.ID = c.CITY_ID
            LEFT JOIN states st ON st.ID = c.STATE_ID
            WHERE 1=1
        """
        params = []

        if search_text:
            query += """
                AND (c.FULL_NAME LIKE %s
                     OR c.COMPANY_NAME LIKE %s
                     OR COALESCE(city.CITY, '') LIKE %s)
            """
            like = f"%{search_text}%"
            params.extend([like, like, like])

        if status_filter and status_filter != "All Status":
            query += " AND c.STATUS = %s"
            params.append(status_filter)

        query += " ORDER BY c.FULL_NAME ASC"

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except MySQLError as e:
            QMessageBox.critical(self, "Database Error", f"Could not load contractors:\n{e}")
            return
        except RuntimeError as e:
            QMessageBox.warning(self, "Driver Missing", str(e))
            return

        self._populate_contractors_table(rows)

    def _populate_contractors_table(self, rows):
        """Preenche a tabela de Contractors linha a linha."""
        table = self.ui.table_contractors
        table.setSortingEnabled(False)
        table.setRowCount(0)
        table.setRowCount(len(rows))

        for row_idx, row_data in enumerate(rows):
            (contractor_id, full_name, email, phone, position,
             company_name, company_phone, city, state, status) = row_data

            values = [
                str(contractor_id),
                str(full_name or ""),
                str(email or ""),
                self._format_phone(phone) or "",
                str(position or ""),
                str(company_name or "—"),
                self._format_phone(company_phone) or "",
                str(city or "—"),
                str(state or "—"),
                str(status or ""),
            ]

            for col_idx, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(row_idx, col_idx, item)

        table.setSortingEnabled(True)

    # ══════════════════════════════════════════════════════════════
    # CONTRACTOR — FORMULÁRIO (CREATE / UPDATE / DELETE)
    # ══════════════════════════════════════════════════════════════

    def new_contractor_record(self):
        """Limpa o formulário para criar um novo contractor."""
        self._current_contractor_id = None
        self.ui.txt_contractor_id.clear()
        self.ui.lbl_contractor_id_display.setText("#ID: New")
        for field in (self.ui.txt_contractor_full_name, self.ui.txt_contractor_position,
                      self.ui.txt_contractor_email, self.ui.txt_contractor_phone,
                      self.ui.txt_contractor_phone2, self.ui.txt_contractor_company_name,
                      self.ui.txt_contractor_company_email, self.ui.txt_contractor_company_phone,
                      self.ui.txt_contractor_company_phone2, self.ui.txt_contractor_address,
                      self.ui.txt_contractor_address2, self.ui.txt_contractor_zip,
                      self.ui.txt_contractor_website, self.ui.txt_contractor_instagram,
                      self.ui.txt_contractor_facebook, self.ui.txt_contractor_linkedin,
                      self.ui.txt_contractor_twitter):
            field.clear()
        self.ui.txt_contractor_notes.clear()
        self.ui.cmb_contractor_city.setCurrentIndex(0)
        self.ui.cmb_contractor_state.setCurrentIndex(0)
        self._reload_city_combo_for_state(self.ui.cmb_contractor_city, None)
        self.ui.cmb_contractor_status.setCurrentIndex(0)
        self.ui.cmb_contractor_payment_cycle_type.setCurrentIndex(0)
        self.ui.cmb_contractor_payment_cycle_weekday.setCurrentIndex(5)  # Friday por padrão
        self.ui.spin_contractor_payment_cycle_days.setValue(30)
        self.ui.tabWidget_contractors_page.setCurrentWidget(self.ui.tab_contractors_master)

    def load_contractor_into_form(self):
        """Carrega o contractor selecionado na tabela para edição."""
        table = self.ui.table_contractors
        selected = table.currentRow()
        if selected < 0:
            return

        contractor_id = table.item(selected, 0).text()
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM contractors WHERE ID = %s", (contractor_id,))
            columns = [d[0] for d in cursor.description]
            row = cursor.fetchone()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not load contractor:\n{e}")
            return

        if not row:
            return

        data = dict(zip(columns, row))
        self._current_contractor_id = data["ID"]
        self.ui.txt_contractor_id.setText(str(data["ID"]))
        self.ui.lbl_contractor_id_display.setText(f"#ID: {data['ID']}")

        self.ui.txt_contractor_full_name.setText(data.get("FULL_NAME") or "")
        self.ui.txt_contractor_position.setText(data.get("POSITION") or "")
        self.ui.txt_contractor_email.setText(data.get("EMAIL") or "")
        self.ui.txt_contractor_phone.setText(self._format_phone(data.get("PHONE_NUMBER")) or "")
        self.ui.txt_contractor_phone2.setText(self._format_phone(data.get("PHONE_NUMBER2")) or "")
        self.ui.txt_contractor_company_name.setText(data.get("COMPANY_NAME") or "")
        self.ui.txt_contractor_company_email.setText(data.get("COMPANY_EMAIL") or "")
        self.ui.txt_contractor_company_phone.setText(self._format_phone(data.get("COMPANY_PHONE_NUMBER")) or "")
        self.ui.txt_contractor_company_phone2.setText(self._format_phone(data.get("COMPANY_PHONE_NUMBER2")) or "")
        self.ui.txt_contractor_address.setText(data.get("ADDRESS") or "")
        self.ui.txt_contractor_address2.setText(data.get("ADDRESS2") or "")
        self.ui.txt_contractor_zip.setText(self._format_zip(data.get("ZIP_CODE")) or "")
        self.ui.txt_contractor_website.setText(data.get("WEBSITE") or "")
        self.ui.txt_contractor_instagram.setText(data.get("INSTAGRAM") or "")
        self.ui.txt_contractor_facebook.setText(data.get("FACEBOOK") or "")
        self.ui.txt_contractor_linkedin.setText(data.get("LINKEDIN") or "")
        self.ui.txt_contractor_twitter.setText(data.get("TWITTER") or "")
        self.ui.txt_contractor_notes.setPlainText(data.get("NOTES") or "")

        self._set_combo_by_data(self.ui.cmb_contractor_state, data.get("STATE_ID"))
        self._reload_city_combo_for_state(self.ui.cmb_contractor_city, data.get("STATE_ID"), keep_city_id=data.get("CITY_ID"))
        self._set_combo_by_data(self.ui.cmb_contractor_status, data.get("STATUS"), by_text=True)

        cycle_type = data.get("PAYMENT_CYCLE_TYPE") or "CUSTOM_DAYS"
        cycle_type_display = {"WEEKLY": "Weekly", "BIWEEKLY": "Biweekly", "CUSTOM_DAYS": "Custom Days"}.get(cycle_type, "Custom Days")
        self.ui.cmb_contractor_payment_cycle_type.setCurrentText(cycle_type_display)
        weekday_idx = data.get("PAYMENT_CYCLE_WEEKDAY")
        self.ui.cmb_contractor_payment_cycle_weekday.setCurrentIndex(weekday_idx if weekday_idx is not None else 5)
        self.ui.spin_contractor_payment_cycle_days.setValue(data.get("PAYMENT_CYCLE_DAYS") or 30)

        self.ui.tabWidget_contractors_page.setCurrentWidget(self.ui.tab_contractors_master)

    def save_contractor_record(self):
        """Insere ou atualiza um registro em contractor."""
        full_name = self.ui.txt_contractor_full_name.text().strip()
        company_name = self.ui.txt_contractor_company_name.text().strip()

        if not full_name:
            QMessageBox.warning(self, "Missing data", "Full Name is required.")
            return
        if not company_name:
            QMessageBox.warning(self, "Missing data", "Company Name is required.")
            return

        cycle_type_map = {"Weekly": "WEEKLY", "Biweekly": "BIWEEKLY", "Custom Days": "CUSTOM_DAYS"}

        data = {
            "FULL_NAME": full_name,
            "EMAIL": self.ui.txt_contractor_email.text(),
            "PHONE_NUMBER": self._format_phone(self.ui.txt_contractor_phone.text()),
            "PHONE_NUMBER2": self._format_phone(self.ui.txt_contractor_phone2.text()),
            "COMPANY_NAME": company_name,
            "COMPANY_EMAIL": self.ui.txt_contractor_company_email.text(),
            "COMPANY_PHONE_NUMBER": self._format_phone(self.ui.txt_contractor_company_phone.text()),
            "COMPANY_PHONE_NUMBER2": self._format_phone(self.ui.txt_contractor_company_phone2.text()),
            "ADDRESS": self.ui.txt_contractor_address.text(),
            "ADDRESS2": self.ui.txt_contractor_address2.text(),
            "CITY_ID": self.ui.cmb_contractor_city.currentData(),
            "STATE_ID": self.ui.cmb_contractor_state.currentData(),
            "ZIP_CODE": self._format_zip(self.ui.txt_contractor_zip.text()),
            "INSTAGRAM": self.ui.txt_contractor_instagram.text(),
            "FACEBOOK": self.ui.txt_contractor_facebook.text(),
            "LINKEDIN": self.ui.txt_contractor_linkedin.text(),
            "TWITTER": self.ui.txt_contractor_twitter.text(),
            "WEBSITE": self.ui.txt_contractor_website.text(),
            "STATUS": self.ui.cmb_contractor_status.currentText(),
            "POSITION": self.ui.txt_contractor_position.text(),
            "NOTES": self.ui.txt_contractor_notes.toPlainText(),
            "PAYMENT_CYCLE_TYPE": cycle_type_map.get(self.ui.cmb_contractor_payment_cycle_type.currentText(), "CUSTOM_DAYS"),
            "PAYMENT_CYCLE_WEEKDAY": self.ui.cmb_contractor_payment_cycle_weekday.currentIndex(),
            "PAYMENT_CYCLE_DAYS": self.ui.spin_contractor_payment_cycle_days.value(),
        }

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            if getattr(self, "_current_contractor_id", None):
                set_clause = ", ".join(f"{k} = %s" for k in data)
                query = f"UPDATE contractors SET {set_clause} WHERE ID = %s"
                cursor.execute(query, list(data.values()) + [self._current_contractor_id])
            else:
                cols = ", ".join(data.keys())
                placeholders = ", ".join(["%s"] * len(data))
                query = f"INSERT INTO contractors ({cols}) VALUES ({placeholders})"
                cursor.execute(query, list(data.values()))

            conn.commit()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not save contractor:\n{e}")
            return

        QMessageBox.information(self, "Success", "Contractor saved successfully.")
        self.load_contractors()
        self.load_combo_data()  # atualiza combo de contractor usado no form de Jobs
        self.new_contractor_record()
        self.ui.tabWidget_contractors_page.setCurrentWidget(self.ui.tab_contractors_master)

    def delete_contractor_record(self):
        """Exclui o contractor atualmente carregado no formulário."""
        if not getattr(self, "_current_contractor_id", None):
            QMessageBox.information(self, "No record selected",
                                     "Select a contractor from the list before deleting.")
            return

        confirm = QMessageBox.question(
            self, "Confirm delete",
            f"Are you sure you want to delete contractor #{self._current_contractor_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM contractors WHERE ID = %s", (self._current_contractor_id,))
            conn.commit()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not delete contractor:\n{e}")
            return

        QMessageBox.information(self, "Deleted", "Contractor deleted.")
        self.new_contractor_record()
        self.load_contractors()
        self.ui.tabWidget_contractors_page.setCurrentWidget(self.ui.tab_contractors_master)

    # ══════════════════════════════════════════════════════════════
    # GENERATE INVOICES — cria um PDF de cobrança por contractor,
    # com os jobs feitos num período, pra enviar pedindo pagamento
    # ══════════════════════════════════════════════════════════════

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
            f"Please find attached your invoice from {COMPANY_NAME} for the period "
            f"{{period_from}} to {{period_to}}, totaling ${{total_amount}}.\n\n"
            f"Thank you for your business!\n{COMPANY_NAME}"
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
                            msg["Subject"] = f"Invoice from {COMPANY_NAME}"
                            msg["From"] = f"{EMAIL_FROM_NAME} <{EMAIL_SMTP_USER}>"
                            msg["To"] = item["email"]
                            msg.set_content(message_body)
                            with open(item["pdf_path"], "rb") as f:
                                msg.add_attachment(f.read(), maintype="application", subtype="pdf",
                                                    filename=os.path.basename(item["pdf_path"]))
                            with smtplib.SMTP(EMAIL_SMTP_HOST, EMAIL_SMTP_PORT) as server:
                                server.starttls()
                                server.login(EMAIL_SMTP_USER, EMAIL_SMTP_PASSWORD)
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


    # ══════════════════════════════════════════════════════════════
    # RECEIVABLES — DASHBOARD
    # ══════════════════════════════════════════════════════════════

    def _setup_dashboard_period_filter(self):
        """Popula os combos de Mês/Ano do Dashboard de Receivables (dinâmico, não dá pra fazer isso direto no Designer)."""
        self.ui.cmb_dashboard_month.blockSignals(True)
        self.ui.cmb_dashboard_month.addItem("All Months", 0)
        month_names = ["January", "February", "March", "April", "May", "June",
                       "July", "August", "September", "October", "November", "December"]
        for i, name in enumerate(month_names, start=1):
            self.ui.cmb_dashboard_month.addItem(name, i)
        self.ui.cmb_dashboard_month.setCurrentIndex(date.today().month)  # mês atual selecionado por padrão
        self.ui.cmb_dashboard_month.blockSignals(False)

        self.ui.cmb_dashboard_year.blockSignals(True)
        self.ui.cmb_dashboard_year.addItem("All Years", 0)
        current_year = date.today().year
        for y in range(current_year - 4, current_year + 1):
            self.ui.cmb_dashboard_year.addItem(str(y), y)
        self.ui.cmb_dashboard_year.setCurrentIndex(self.ui.cmb_dashboard_year.count() - 1)  # ano atual
        self.ui.cmb_dashboard_year.blockSignals(False)

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
                Paragraph(f"<b>{COMPANY_NAME}</b>", styles["Title"]),
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
                Paragraph(f"<b>{COMPANY_NAME}</b>", styles["Title"]),
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
                Paragraph(f"<b>{COMPANY_NAME}</b>", styles["Title"]),
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

    def _is_contractor_invoice_overdue(self, generated_at, cycle_type, cycle_weekday, cycle_days):
        """Decide se um invoice de Contractor está atrasado, respeitando a
        regra de pagamento configurada NAQUELE contractor (semanal num dia
        da semana específico, quinzenal, ou um número de dias corridos)."""
        if generated_at is None:
            return False
        generated_date = generated_at.date() if hasattr(generated_at, "date") else generated_at
        today = date.today()

        if cycle_type == "WEEKLY" or cycle_type == "BIWEEKLY":
            # O combo na tela usa Sunday=0..Saturday=6; o Python usa Monday=0..Sunday=6.
            combo_weekday = cycle_weekday if cycle_weekday is not None else 5  # Friday por padrão
            target_weekday = (combo_weekday - 1) % 7
            days_ahead = (target_weekday - generated_date.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7  # cai no mesmo dia da semana em que foi gerado: só vence na ocorrência seguinte
            due_date = generated_date + timedelta(days=days_ahead)
            if cycle_type == "BIWEEKLY":
                due_date += timedelta(days=7)
        else:  # CUSTOM_DAYS
            due_date = generated_date + timedelta(days=cycle_days or 30)

        return today > due_date

    def load_receivables_dashboard(self):
        """Atualiza os 4 cards de resumo e a tabela de detalhamento por
        Contractor/Company/Client do Dashboard de Receivables, respeitando
        o filtro de Mês/Ano selecionado."""
        month = self.ui.cmb_dashboard_month.currentData() or 0
        year = self.ui.cmb_dashboard_year.currentData() or 0

        # Monta a clausula de periodo (aplicada em cima de PERIOD_FROM de cada invoice)
        period_clause = ""
        period_params: list = []
        if month:
            period_clause += " AND MONTH(PERIOD_FROM) = %s"
            period_params.append(month)
        if year:
            period_clause += " AND YEAR(PERIOD_FROM) = %s"
            period_params.append(year)

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            total_receivable = 0.0
            received_month = 0.0
            open_entities = set()
            overdue = 0
            breakdown_rows = []  # (type, name, total, received, pending)
            aging_buckets = {"0_30": 0.0, "31_60": 0.0, "61_90": 0.0, "90_plus": 0.0}

            entity_tables = [
                ("Contractor", "contractor_invoices", "contractors", "CONTRACTOR_ID", "COALESCE(r.COMPANY_NAME, r.FULL_NAME)"),
                ("Company", "company_invoices", "companies", "COMPANY_ID", "r.COMPANY_NAME"),
                ("Client", "client_invoices", "clients", "CLIENT_ID", "r.FULL_NAME"),
            ]

            for label, table, ref_table, fk_col, name_col in entity_tables:
                # Totais gerais (respeitando o filtro de periodo)
                cursor.execute(
                    f"""
                    SELECT COALESCE(SUM(TOTAL_AMOUNT - AMOUNT_PAID), 0),
                           COUNT(DISTINCT {fk_col})
                    FROM {table}
                    WHERE STATUS IN ('PENDING','PARTIAL') {period_clause}
                    """,
                    period_params,
                )
                pending_sum, open_count = cursor.fetchone()
                total_receivable += float(pending_sum or 0)
                if open_count:
                    open_entities.add((label, open_count))

                cursor.execute(
                    f"""
                    SELECT COALESCE(SUM(AMOUNT_PAID), 0) FROM {table}
                    WHERE RECEIVED_AT IS NOT NULL
                    AND MONTH(RECEIVED_AT)=MONTH(CURDATE()) AND YEAR(RECEIVED_AT)=YEAR(CURDATE())
                    """
                )
                received_month += float(cursor.fetchone()[0] or 0)

                if label == "Contractor":
                    # Regra por contractor: cada um pode ter um ciclo de pagamento diferente
                    # (semanal num dia específico, quinzenal, ou N dias corridos).
                    cursor.execute(
                        f"""
                        SELECT t.GENERATED_AT, COALESCE(r.PAYMENT_CYCLE_TYPE, 'CUSTOM_DAYS'),
                               r.PAYMENT_CYCLE_WEEKDAY, COALESCE(r.PAYMENT_CYCLE_DAYS, 30)
                        FROM {table} t
                        LEFT JOIN {ref_table} r ON r.ID = t.{fk_col}
                        WHERE t.STATUS IN ('PENDING','PARTIAL')
                        """
                    )
                    for generated_at, cycle_type, cycle_weekday, cycle_days in cursor.fetchall():
                        if self._is_contractor_invoice_overdue(generated_at, cycle_type, cycle_weekday, cycle_days):
                            overdue += 1
                else:
                    cursor.execute(
                        f"""
                        SELECT COUNT(*) FROM {table}
                        WHERE STATUS IN ('PENDING','PARTIAL') AND DATEDIFF(CURDATE(), GENERATED_AT) > 30
                        """
                    )
                    overdue += cursor.fetchone()[0] or 0

                # Aging report: idade (em dias, a partir de GENERATED_AT) de cada saldo em aberto
                cursor.execute(
                    f"""
                    SELECT DATEDIFF(CURDATE(), GENERATED_AT), (TOTAL_AMOUNT - AMOUNT_PAID)
                    FROM {table} WHERE STATUS IN ('PENDING','PARTIAL')
                    """
                )
                for days_old, pending_amount in cursor.fetchall():
                    pending_amount = float(pending_amount or 0)
                    days_old = days_old or 0
                    if days_old <= 30:
                        aging_buckets["0_30"] += pending_amount
                    elif days_old <= 60:
                        aging_buckets["31_60"] += pending_amount
                    elif days_old <= 90:
                        aging_buckets["61_90"] += pending_amount
                    else:
                        aging_buckets["90_plus"] += pending_amount

                # Detalhamento por entidade (nome), respeitando o filtro de periodo
                cursor.execute(
                    f"""
                    SELECT COALESCE({name_col}, '—') AS NAME,
                           COALESCE(SUM(t.TOTAL_AMOUNT), 0) AS TOTAL,
                           COALESCE(SUM(t.AMOUNT_PAID), 0) AS RECEIVED
                    FROM {table} t
                    LEFT JOIN {ref_table} r ON r.ID = t.{fk_col}
                    WHERE 1=1 {period_clause}
                    GROUP BY t.{fk_col}, {name_col}
                    ORDER BY TOTAL DESC
                    """,
                    period_params,
                )
                for name, total, received in cursor.fetchall():
                    total = float(total or 0)
                    received = float(received or 0)
                    breakdown_rows.append((label, name, total, received, total - received))

            # Recebido por forma de pagamento (respeitando o filtro de mês/ano, se houver)
            pm_clause = ""
            pm_params: list = []
            if month:
                pm_clause += " AND MONTH(PAID_DATE) = %s"
                pm_params.append(month)
            if year:
                pm_clause += " AND YEAR(PAID_DATE) = %s"
                pm_params.append(year)
            cursor.execute(
                f"""
                SELECT COALESCE(PAYMENT_METHOD, 'Other'), COALESCE(SUM(AMOUNT), 0)
                FROM payments WHERE 1=1 {pm_clause}
                GROUP BY PAYMENT_METHOD ORDER BY SUM(AMOUNT) DESC
                """,
                pm_params,
            )
            payment_method_rows = cursor.fetchall()

            # Recebido por mês, últimos 6 meses (pra o gráfico)
            cursor.execute(
                """
                SELECT DATE_FORMAT(PAID_DATE, '%Y-%m') AS ym, COALESCE(SUM(AMOUNT), 0)
                FROM payments
                WHERE PAID_DATE >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
                GROUP BY ym ORDER BY ym
                """
            )
            received_by_month = cursor.fetchall()

            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.warning(self, "Database Error", f"Could not load dashboard:\n{e}")
            return

        open_count_total = sum(c for _, c in open_entities)

        self.ui.lbl_receivables_total_value.setText(f"${total_receivable:,.2f}")
        self.ui.lbl_receivables_month_value.setText(f"${received_month:,.2f}")
        self.ui.lbl_receivables_open_value.setText(str(open_count_total))
        self.ui.lbl_receivables_overdue_value.setText(str(overdue))

        # Preenche a tabela de detalhamento
        table_widget = self.ui.table_receivables_breakdown
        table_widget.setSortingEnabled(False)
        table_widget.setRowCount(0)
        table_widget.setRowCount(len(breakdown_rows))
        for row_idx, (label, name, total, received, pending) in enumerate(breakdown_rows):
            values = [label, str(name), f"${total:,.2f}", f"${received:,.2f}", f"${pending:,.2f}"]
            for col_idx, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table_widget.setItem(row_idx, col_idx, item)
        table_widget.setSortingEnabled(True)

        # Aging report
        self.ui.lbl_aging_0_30_value.setText(f"${aging_buckets['0_30']:,.2f}")
        self.ui.lbl_aging_31_60_value.setText(f"${aging_buckets['31_60']:,.2f}")
        self.ui.lbl_aging_61_90_value.setText(f"${aging_buckets['61_90']:,.2f}")
        self.ui.lbl_aging_90_plus_value.setText(f"${aging_buckets['90_plus']:,.2f}")

        # Recebido por forma de pagamento
        pm_table = self.ui.table_dashboard_payment_methods
        pm_table.setRowCount(len(payment_method_rows))
        for r, (method, amount) in enumerate(payment_method_rows):
            for c, text in enumerate([method, f"${float(amount or 0):,.2f}"]):
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                pm_table.setItem(r, c, item)

        # Top devedores: mesmas linhas do detalhamento, ordenadas por saldo pendente
        top_debtors = sorted(breakdown_rows, key=lambda row: row[4], reverse=True)[:10]
        debtors_table = self.ui.table_dashboard_top_debtors
        debtors_table.setRowCount(len(top_debtors))
        for r, (label, name, total, received, pending) in enumerate(top_debtors):
            for c, text in enumerate([label, str(name), f"${pending:,.2f}"]):
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                debtors_table.setItem(r, c, item)

        self._draw_dashboard_received_chart(received_by_month)

    def _draw_dashboard_received_chart(self, received_by_month):
        """Desenha o gráfico de barras de valores recebidos por mês (últimos
        6 meses), no mesmo estilo simples usado na Home."""
        layout = self.ui.layout_dashboard_received_chart
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not received_by_month:
            layout.addWidget(QLabel("No payments received yet"))
            return

        max_value = max(float(v) for _, v in received_by_month) or 1.0
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        for ym, value in received_by_month:
            value = float(value or 0)
            _, month_str = ym.split("-")
            label_text = month_names[int(month_str) - 1]

            col = QVBoxLayout()
            col.addStretch()
            value_lbl = QLabel(f"${value:,.0f}")
            value_lbl.setStyleSheet("font-size:10px; font-weight:700; color:#2E7D32; background:transparent;")
            value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.addWidget(value_lbl)

            bar_height = max(6, int((value / max_value) * 90))
            bar = QFrame()
            bar.setMinimumHeight(bar_height)
            bar.setMaximumHeight(bar_height)
            bar.setStyleSheet("background-color: #2E7D32; border-radius: 4px;")
            col.addWidget(bar)

            month_lbl = QLabel(label_text)
            month_lbl.setStyleSheet("font-size:11px; font-weight:600; color:#6B7C93; background:transparent;")
            month_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.addWidget(month_lbl)

            layout.addLayout(col)

    def open_record_payment_dialog(self):
        """Atalho do Dashboard: acha um invoice em aberto (Contractor/Company/
        Client) e registra um pagamento nele, sem precisar navegar até a
        lista de Invoices primeiro."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Record Payment")
        dialog.resize(480, 480)
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

        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Bill To:"))
        cmb_type = QComboBox()
        cmb_type.addItems(["Contractor", "Company", "Client"])
        type_row.addWidget(cmb_type)
        layout.addLayout(type_row)

        txt_search = QLineEdit()
        txt_search.setPlaceholderText("🔍  Search by name…")
        layout.addWidget(txt_search)

        layout.addWidget(QLabel("Open invoices:"))
        list_invoices = QListWidget()
        layout.addWidget(list_invoices)

        invoice_data = {}  # texto da linha -> (invoice_id, table_name, balance)

        def refresh_list():
            list_invoices.clear()
            invoice_data.clear()
            entity_type = cmb_type.currentText()
            table_name, ref_table, fk_col, name_col = {
                "Contractor": ("contractor_invoices", "contractors", "CONTRACTOR_ID", "COALESCE(r.COMPANY_NAME, r.FULL_NAME)"),
                "Company": ("company_invoices", "companies", "COMPANY_ID", "r.COMPANY_NAME"),
                "Client": ("client_invoices", "clients", "CLIENT_ID", "r.FULL_NAME"),
            }[entity_type]
            search_text = txt_search.text().strip()
            query = f"""
                SELECT ci.ID, COALESCE({name_col}, '—'), ci.TOTAL_AMOUNT - ci.AMOUNT_PAID
                FROM {table_name} ci
                LEFT JOIN {ref_table} r ON r.ID = ci.{fk_col}
                WHERE ci.STATUS IN ('PENDING','PARTIAL')
            """
            params = []
            if search_text:
                query += f" AND COALESCE({name_col}, '') LIKE %s"
                params.append(f"%{search_text}%")
            query += " ORDER BY ci.GENERATED_AT DESC"
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not load invoices:\n{e}")
                return
            for invoice_id, name, balance in rows:
                balance = float(balance or 0)
                text = f"#{invoice_id} — {name} — Balance: ${balance:,.2f}"
                list_invoices.addItem(text)
                invoice_data[text] = (invoice_id, table_name, balance)

        cmb_type.currentIndexChanged.connect(refresh_list)
        txt_search.textChanged.connect(refresh_list)

        layout.addWidget(QLabel("Payment details:"))
        pay_row1 = QHBoxLayout()
        pay_row1.addWidget(QLabel("Date:"))
        date_paid = QDateEdit()
        date_paid.setCalendarPopup(True)
        date_paid.setDisplayFormat("MM/dd/yyyy")
        date_paid.setDate(QDate.currentDate())
        pay_row1.addWidget(date_paid)
        pay_row1.addWidget(QLabel("Amount ($):"))
        spin_amount = QDoubleSpinBox()
        spin_amount.setMaximum(999999.99)
        spin_amount.setPrefix("$ ")
        pay_row1.addWidget(spin_amount)
        layout.addLayout(pay_row1)

        pay_row2 = QHBoxLayout()
        pay_row2.addWidget(QLabel("Method:"))
        cmb_method = QComboBox()
        cmb_method.addItems(COMPANY_PAYMENT_METHODS + ["Other"])
        pay_row2.addWidget(cmb_method)
        layout.addLayout(pay_row2)

        txt_note = QLineEdit()
        txt_note.setPlaceholderText("Note (optional)")
        layout.addWidget(txt_note)

        def fill_full_balance():
            selected = list_invoices.currentItem()
            if selected and selected.text() in invoice_data:
                spin_amount.setValue(invoice_data[selected.text()][2])

        list_invoices.itemSelectionChanged.connect(fill_full_balance)

        bottom_row = QHBoxLayout()
        bottom_row.addStretch()
        btn_cancel = QPushButton("Cancel")
        btn_record = QPushButton("Record Payment")
        btn_record.setObjectName("btn_save_job")
        bottom_row.addWidget(btn_cancel)
        bottom_row.addWidget(btn_record)
        layout.addLayout(bottom_row)

        def record_payment():
            selected = list_invoices.currentItem()
            if not selected or selected.text() not in invoice_data:
                QMessageBox.information(dialog, "No invoice selected", "Select an invoice from the list first.")
                return
            invoice_id, table_name, _ = invoice_data[selected.text()]
            amount = spin_amount.value()
            if amount <= 0:
                QMessageBox.warning(dialog, "Invalid amount", "Enter a payment amount greater than zero.")
                return

            entity_type = cmb_type.currentText()
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO payments (INVOICE_TYPE, INVOICE_ID, PAID_DATE, AMOUNT, PAYMENT_METHOD, NOTE) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (entity_type, invoice_id, date_paid.date().toString("yyyy-MM-dd"), amount,
                     cmb_method.currentText(), txt_note.text().strip() or None),
                )
                cursor.execute(
                    "SELECT COALESCE(SUM(AMOUNT), 0) FROM payments WHERE INVOICE_TYPE = %s AND INVOICE_ID = %s",
                    (entity_type, invoice_id),
                )
                total_paid = float(cursor.fetchone()[0] or 0)
                cursor.execute(f"SELECT TOTAL_AMOUNT FROM {table_name} WHERE ID = %s", (invoice_id,))
                total_amount = float(cursor.fetchone()[0] or 0)
                new_status = "RECEIVED" if total_paid >= total_amount else ("PARTIAL" if total_paid > 0 else "PENDING")
                received_clause = ", RECEIVED_AT = NOW()" if new_status == "RECEIVED" else ""
                cursor.execute(
                    f"UPDATE {table_name} SET AMOUNT_PAID = %s, STATUS = %s {received_clause} WHERE ID = %s",
                    (total_paid, new_status, invoice_id),
                )
                conn.commit()
                cursor.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not record payment:\n{e}")
                return

            QMessageBox.information(dialog, "Success", "Payment recorded successfully.")
            self.load_receivables_dashboard()
            dialog.accept()

        btn_cancel.clicked.connect(dialog.reject)
        btn_record.clicked.connect(record_payment)

        refresh_list()
        dialog.exec()

    # ══════════════════════════════════════════════════════════════
    # RECEIVABLES — LISTA DE INVOICES
    # ══════════════════════════════════════════════════════════════

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
        cmb_method.addItems(COMPANY_PAYMENT_METHODS + ["Other"])
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
                   wd.REPARO_1_ID, wd.REPARO_1_QTY, wd.REPARO_2_ID, wd.REPARO_2_QTY
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
        return cursor.fetchall()

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
            value = float(value or 0)
            jobs_total += value
            full_address = address or ""
            if address2:
                full_address += f", {address2}"
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

    def _build_invoice_pdf(self, filepath, invoice_number, entity_label, entity_name, entity_contact_lines,
                            d_from_qdate, d_to_qdate, item_rows, jobs_total, has_expenses, expenses_rows,
                            expenses_total, discount, addition, tax_percent, status):
        """Monta visualmente o PDF do invoice (logo + cores da marca Vertex Londe),
        com tabela de itens, ajustes de desconto/acréscimo/taxa, informações de
        pagamento e status. Usado por Contractor, Company e Client."""
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

            company_html = f"<b>{COMPANY_NAME}</b><br/><font size=7 color='{BRAND_ORANGE}'>{COMPANY_TAGLINE}</font>"
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
            f"<b>Invoice Date:</b> {date.today().strftime('%m/%d/%Y')}",
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

        # ── Payment Info + status ──
        bank_html = "<br/>".join([
            "<b>Payment Info:</b>",
            f"Account No: {COMPANY_BANK_INFO['account_no']}",
            f"A/C Name: {COMPANY_BANK_INFO['account_name']}",
            f"Bank Details: {COMPANY_BANK_INFO['bank_details']}",
            "<br/><b>Accepted Methods:</b>",
            ", ".join(COMPANY_PAYMENT_METHODS),
        ])
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
            f"<font size=8 color='#6B7C93'>{COMPANY_PHONE} &nbsp;|&nbsp; {COMPANY_EMAIL} &nbsp;|&nbsp; {COMPANY_WEBSITE}</font>",
            styles["Normal"],
        ))
        story.append(Paragraph("<font size=8 color='#6B7C93'>Thank you for your business with us.</font>",
                                styles["Normal"]))

        doc.build(story, canvasmaker=_InvoiceNumberedCanvas)
        return grand_total

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
                "SELECT EXPENSE_DATE, CATEGORY, DESCRIPTION, AMOUNT FROM expenses "
                "WHERE CONTRACTOR_ID = %s AND EXPENSE_DATE BETWEEN %s AND %s"
            )
            expense_params = [contractor_id, d_from, d_to]
            if expense_ids:
                placeholders = ", ".join(["%s"] * len(expense_ids))
                expense_query += f" AND ID IN ({placeholders})"
                expense_params.extend(expense_ids)
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
        for exp_date, category, description, amount in expenses:
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

    # ══════════════════════════════════════════════════════════════
    # USERS — LISTAGEM
    # ══════════════════════════════════════════════════════════════

    # ══════════════════════════════════════════════════════════════
    # EXPORTAÇÃO GENÉRICA (Excel / PDF) — usada por todas as tabelas
    # ══════════════════════════════════════════════════════════════

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

    # ══════════════════════════════════════════════════════════════
    # CUSTOMER — LISTAGEM
    # ══════════════════════════════════════════════════════════════

    # ══════════════════════════════════════════════════════════════
    # HOME — DASHBOARD (cards, jobs recentes, gráfico, atalhos)
    # ══════════════════════════════════════════════════════════════

    def load_home_dashboard(self):
        """Atualiza os 4 cards de resumo, a lista de Jobs recentes e o
        gráfico de faturamento dos últimos 6 meses, na página Home."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT COUNT(*), COALESCE(SUM(VALUE), 0) FROM work_days "
                "WHERE MONTH(WORK_DATE) = MONTH(CURDATE()) AND YEAR(WORK_DATE) = YEAR(CURDATE())"
            )
            jobs_month, revenue_month = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) FROM work_days WHERE STATUS IN ('PENDING', 'STARTED')")
            pending_jobs = cursor.fetchone()[0]

            overdue = 0
            for table in ("contractor_invoices", "company_invoices", "client_invoices"):
                cursor.execute(
                    f"SELECT COUNT(*) FROM {table} "
                    f"WHERE STATUS IN ('PENDING','PARTIAL') AND DATEDIFF(CURDATE(), GENERATED_AT) > 30"
                )
                overdue += cursor.fetchone()[0] or 0

            cursor.execute(
                """
                SELECT wd.WORK_DATE, COALESCE(c.COMPANY_NAME, c.FULL_NAME, '—'), COALESCE(cl.FULL_NAME, '—'),
                       wd.VALUE, wd.STATUS
                FROM work_days wd
                LEFT JOIN contractors c ON c.ID = wd.CONTRACTOR_ID
                LEFT JOIN clients cl ON cl.ID = wd.CLIENT_ID
                ORDER BY wd.WORK_DATE DESC, wd.ID DESC
                LIMIT 10
                """
            )
            recent_jobs = cursor.fetchall()

            cursor.execute(
                """
                SELECT DATE_FORMAT(WORK_DATE, '%Y-%m') AS ym, COALESCE(SUM(VALUE), 0)
                FROM work_days
                WHERE WORK_DATE >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
                GROUP BY ym
                ORDER BY ym
                """
            )
            revenue_by_month = cursor.fetchall()

            wt_columns = [
                "DEMOLITION_1_ID", "DEMOLITION_2_ID", "DEMOLITION_3_ID", "DEMOLITION_4_ID",
                "INSTALLATION_1_ID", "INSTALLATION_2_ID", "INSTALLATION_3_ID", "INSTALLATION_4_ID",
                "PREPARATION_1_ID", "PREPARATION_2_ID", "PREPARATION_3_ID", "PREPARATION_4_ID",
                "OTHERS_1_ID", "OTHERS_2_ID", "REPARO_1_ID", "REPARO_2_ID",
            ]
            union_query = " UNION ALL ".join(
                f"SELECT {col} AS WT_ID FROM work_days WHERE {col} IS NOT NULL" for col in wt_columns
            )
            cursor.execute(
                f"""
                SELECT wt.NAME, COUNT(*) AS cnt
                FROM ({union_query}) t
                JOIN work_types wt ON wt.ID = t.WT_ID
                GROUP BY wt.ID, wt.NAME
                ORDER BY cnt DESC
                LIMIT 8
                """
            )
            work_type_counts = cursor.fetchall()

            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.warning(self, "Database Error", f"Could not load the Home dashboard:\n{e}")
            return

        self.ui.lbl_home_jobs_month_value.setText(str(jobs_month or 0))
        self.ui.lbl_home_revenue_month_value.setText(f"${float(revenue_month or 0):,.2f}")
        self.ui.lbl_home_overdue_value.setText(str(overdue))
        self.ui.lbl_home_pending_jobs_value.setText(str(pending_jobs or 0))

        table = self.ui.table_home_recent_jobs
        table.setRowCount(len(recent_jobs))
        for r, (wdate, contractor, client, value, status) in enumerate(recent_jobs):
            date_str = wdate.strftime("%m/%d/%Y") if isinstance(wdate, date) else str(wdate)
            values = [date_str, contractor, client, f"${float(value or 0):,.2f}",
                      JOB_STATUS_LABELS.get(status, status)]
            for c, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(r, c, item)

        self._draw_home_revenue_chart(revenue_by_month)

        # Cards + gráfico dos tipos de trabalho mais feitos
        wt_cards = [
            (self.ui.lbl_home_work_type_1_value, self.ui.lbl_home_work_type_1_label),
            (self.ui.lbl_home_work_type_2_value, self.ui.lbl_home_work_type_2_label),
            (self.ui.lbl_home_work_type_3_value, self.ui.lbl_home_work_type_3_label),
            (self.ui.lbl_home_work_type_4_value, self.ui.lbl_home_work_type_4_label),
        ]
        for i, (value_lbl, name_lbl) in enumerate(wt_cards):
            if i < len(work_type_counts):
                name, count = work_type_counts[i]
                value_lbl.setText(str(count))
                name_lbl.setText(str(name))
            else:
                value_lbl.setText("—")
                name_lbl.setText("—")

        self._draw_home_work_types_chart(work_type_counts)
        self._refresh_projects_overview_widget()

    def _draw_home_work_types_chart(self, work_type_counts):
        """Desenha um gráfico de barras simples com a frequência de cada
        tipo de trabalho (quantas vezes cada Work Type foi usado em jobs)."""
        layout = self.ui.layout_home_work_types_chart
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not work_type_counts:
            layout.addWidget(QLabel("No work type data yet"))
            return

        max_count = max(count for _, count in work_type_counts) or 1

        for name, count in work_type_counts:
            col = QVBoxLayout()
            col.addStretch()

            count_lbl = QLabel(str(count))
            count_lbl.setStyleSheet("font-size:10px; font-weight:700; color:#6A1B9A; background:transparent;")
            count_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.addWidget(count_lbl)

            bar_height = max(6, int((count / max_count) * 90))
            bar = QFrame()
            bar.setMinimumHeight(bar_height)
            bar.setMaximumHeight(bar_height)
            bar.setStyleSheet("background-color: #6A1B9A; border-radius: 4px;")
            col.addWidget(bar)

            name_lbl = QLabel(name if len(name) <= 12 else name[:11] + "…")
            name_lbl.setToolTip(name)
            name_lbl.setStyleSheet("font-size:10px; font-weight:600; color:#6B7C93; background:transparent;")
            name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_lbl.setWordWrap(True)
            col.addWidget(name_lbl)

            layout.addLayout(col)

    def _draw_home_revenue_chart(self, revenue_by_month):
        """Desenha um gráfico de barras simples (sem depender de bibliotecas
        externas de gráfico) mostrando o faturamento por mês, usando QFrames
        com altura proporcional ao valor."""
        layout = self.ui.layout_home_revenue_chart
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not revenue_by_month:
            layout.addWidget(QLabel("No revenue data yet"))
            return

        max_value = max(float(v) for _, v in revenue_by_month) or 1.0
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        for ym, value in revenue_by_month:
            value = float(value or 0)
            year_str, month_str = ym.split("-")
            label_text = month_names[int(month_str) - 1]

            col = QVBoxLayout()
            col.addStretch()

            value_lbl = QLabel(f"${value:,.0f}")
            value_lbl.setStyleSheet("font-size:10px; font-weight:700; color:#1565C0; background:transparent;")
            value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.addWidget(value_lbl)

            bar_height = max(6, int((value / max_value) * 130))
            bar = QFrame()
            bar.setMinimumHeight(bar_height)
            bar.setMaximumHeight(bar_height)
            bar.setStyleSheet(f"background-color: {BRAND_ORANGE}; border-radius: 4px;")
            col.addWidget(bar)

            month_lbl = QLabel(label_text)
            month_lbl.setStyleSheet("font-size:11px; font-weight:600; color:#6B7C93; background:transparent;")
            month_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.addWidget(month_lbl)

            layout.addLayout(col)

    def _go_home_new_job(self):
        self._go_to_page(1, self.ui.btn_jobs)
        self._on_new_job_button_clicked()

    def _go_home_generate_invoices(self):
        self._go_to_page(5, self.ui.btn_nav_receivables)
        self.open_generate_invoices_dialog()

    def _go_home_schedule(self):
        self._go_to_page(1, self.ui.btn_jobs)
        self.ui.tabWidget_jobs.setCurrentWidget(self.ui.tab_schedule)

    def _go_home_new_customer(self):
        self._go_to_page(6, self.ui.btn_customer)
        self.new_customer_record()

    def load_customers(self):
        """Carrega os clientes na tabela, aplicando filtro de busca (nome, email ou telefone)."""
        search_text = self.ui.txt_search_customers.text().strip()

        query = """
            SELECT cl.ID, cl.FULL_NAME, cl.EMAIL, cl.PHONE_NUMBER,
                   COALESCE(city.CITY, '—') AS CITY_NAME,
                   COALESCE(st.STATE_NAME, '—') AS STATE_NAME
            FROM clients cl
            LEFT JOIN cities city ON city.ID = cl.CITY_ID
            LEFT JOIN states st ON st.ID = cl.STATE_ID
            WHERE 1=1
        """
        params = []
        if search_text:
            query += " AND (cl.FULL_NAME LIKE %s OR cl.EMAIL LIKE %s OR cl.PHONE_NUMBER LIKE %s)"
            like = f"%{search_text}%"
            params.extend([like, like, like])
        query += " ORDER BY cl.FULL_NAME"

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except MySQLError as e:
            QMessageBox.critical(self, "Database Error", f"Could not load customers:\n{e}")
            return
        except RuntimeError as e:
            QMessageBox.warning(self, "Driver Missing", str(e))
            return

        table = self.ui.table_customers
        table.setSortingEnabled(False)
        table.setRowCount(0)
        table.setRowCount(len(rows))
        for row_idx, (cid, name, email, phone, city, state) in enumerate(rows):
            values = [str(cid), str(name or ""), str(email or ""), self._format_phone(phone) or "",
                      str(city or "—"), str(state or "—")]
            for col_idx, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(row_idx, col_idx, item)
        table.setSortingEnabled(True)

    # ══════════════════════════════════════════════════════════════
    # CUSTOMER — FORMULÁRIO (CREATE / UPDATE / DELETE) + HISTÓRICO DE JOBS
    # ══════════════════════════════════════════════════════════════

    def new_customer_record(self):
        """Limpa o formulário para criar um novo cliente."""
        self._current_customer_id = None
        self.ui.table_customers.clearSelection()
        self.ui.table_customers.setCurrentCell(-1, -1)
        self.ui.txt_customer_id.clear()
        self.ui.lbl_customer_id_display.setText("#ID: New")
        self.ui.txt_customer_name.clear()
        self.ui.txt_customer_email.clear()
        self.ui.txt_customer_phone.clear()
        self.ui.txt_customer_phone2.clear()
        self.ui.txt_customer_address.clear()
        self.ui.txt_customer_address2.clear()
        self.ui.txt_customer_zip.clear()
        self.ui.cmb_customer_state.setCurrentIndex(0)
        self._reload_city_combo_for_state(self.ui.cmb_customer_city, None)
        self.ui.table_customer_job_history.setRowCount(0)
        self.ui.lbl_customer_job_history_total.setText("Total: $0.00")

    def load_customer_into_form(self):
        """Carrega o cliente selecionado na tabela para edição, junto com o
        histórico de Jobs feitos para ele."""
        table = self.ui.table_customers
        selected = table.currentRow()
        if selected < 0:
            return

        customer_id = table.item(selected, 0).text()
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clients WHERE ID = %s", (customer_id,))
            columns = [d[0] for d in cursor.description]
            row = cursor.fetchone()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not load customer:\n{e}")
            return

        if not row:
            return
        data = dict(zip(columns, row))

        self._current_customer_id = data.get("ID")
        self.ui.txt_customer_id.setText(str(data.get("ID")))
        self.ui.lbl_customer_id_display.setText(f"#ID: {data.get('ID')}")
        self.ui.txt_customer_name.setText(data.get("FULL_NAME") or "")
        self.ui.txt_customer_email.setText(data.get("EMAIL") or "")
        self.ui.txt_customer_phone.setText(self._format_phone(data.get("PHONE_NUMBER")) or "")
        self.ui.txt_customer_phone2.setText(self._format_phone(data.get("PHONE_NUMBER2")) or "")
        self.ui.txt_customer_address.setText(data.get("ADDRESS") or "")
        self.ui.txt_customer_address2.setText(data.get("ADDRESS2") or "")
        self.ui.txt_customer_zip.setText(self._format_zip(data.get("ZIP_CODE")) or "")
        self._set_combo_by_data(self.ui.cmb_customer_state, data.get("STATE_ID"))
        self._reload_city_combo_for_state(self.ui.cmb_customer_city, data.get("STATE_ID"),
                                           keep_city_id=data.get("CITY_ID"))

        self._load_customer_job_history(data.get("ID"))

    def _load_customer_job_history(self, customer_id):
        """Mostra todos os Jobs (work_days) feitos para esse cliente."""
        table = self.ui.table_customer_job_history
        table.setRowCount(0)
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT wd.WORK_DATE, COALESCE(c.COMPANY_NAME, c.FULL_NAME, '—'), COALESCE(co.COMPANY_NAME, '—'),
                       wd.JOB_ADDRESS, wd.VALUE, wd.STATUS
                FROM work_days wd
                LEFT JOIN contractors c ON c.ID = wd.CONTRACTOR_ID
                LEFT JOIN companies co ON co.ID = wd.COMPANY_ID
                WHERE wd.CLIENT_ID = %s
                ORDER BY wd.WORK_DATE DESC
                """,
                (customer_id,),
            )
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.warning(self, "Database Error", f"Could not load job history:\n{e}")
            return

        table.setRowCount(len(rows))
        total = 0.0
        for r, (wdate, contractor, company, address, value, status) in enumerate(rows):
            value = float(value or 0)
            total += value
            date_str = wdate.strftime("%m/%d/%Y") if isinstance(wdate, date) else str(wdate)
            values = [date_str, contractor, company, address or "", f"${value:,.2f}",
                      JOB_STATUS_LABELS.get(status, status)]
            for c, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(r, c, item)
        self.ui.lbl_customer_job_history_total.setText(f"Total: ${total:,.2f}")

    def save_customer_record(self):
        """Insere ou atualiza um registro em clients."""
        name = self.ui.txt_customer_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing data", "Full Name is required.")
            return

        data = (
            name,
            self.ui.txt_customer_email.text(),
            self._format_phone(self.ui.txt_customer_phone.text()),
            self._format_phone(self.ui.txt_customer_phone2.text()),
            self.ui.txt_customer_address.text(),
            self.ui.txt_customer_address2.text(),
            self.ui.cmb_customer_city.currentData(),
            self.ui.cmb_customer_state.currentData(),
            self._format_zip(self.ui.txt_customer_zip.text()),
        )

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            if getattr(self, "_current_customer_id", None):
                cursor.execute(
                    "UPDATE clients SET FULL_NAME=%s, EMAIL=%s, PHONE_NUMBER=%s, PHONE_NUMBER2=%s, "
                    "ADDRESS=%s, ADDRESS2=%s, CITY_ID=%s, STATE_ID=%s, ZIP_CODE=%s WHERE ID=%s",
                    data + (self._current_customer_id,),
                )
            else:
                cursor.execute(
                    "INSERT INTO clients (FULL_NAME, EMAIL, PHONE_NUMBER, PHONE_NUMBER2, ADDRESS, "
                    "ADDRESS2, CITY_ID, STATE_ID, ZIP_CODE) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    data,
                )
            conn.commit()
            cursor.close()
            conn.close()
        except MySQLError as e:
            QMessageBox.critical(self, "Database Error", f"Could not save customer:\n{e}")
            return
        except RuntimeError as e:
            QMessageBox.warning(self, "Driver Missing", str(e))
            return

        QMessageBox.information(self, "Success", "Customer saved successfully.")
        self.load_customers()
        self._refresh_client_name_completer()
        self.new_customer_record()

    def delete_customer_record(self):
        """Exclui o cliente atualmente carregado no formulário."""
        if not getattr(self, "_current_customer_id", None):
            QMessageBox.information(self, "No record selected",
                                     "Select a customer from the list before deleting.")
            return

        confirm = QMessageBox.question(
            self, "Confirm delete",
            f"Are you sure you want to delete customer #{self._current_customer_id}? "
            f"This may fail if this customer has Jobs linked to them.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM clients WHERE ID = %s", (self._current_customer_id,))
            conn.commit()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error",
                                  f"Could not delete customer (it may have Jobs linked to it):\n{e}")
            return

        QMessageBox.information(self, "Deleted", "Customer deleted.")
        self.new_customer_record()
        self.load_customers()
        self._refresh_client_name_completer()

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

    def load_users(self):
        """Carrega os registros de users na tabela, aplicando filtros de busca e status."""
        search_text = self.ui.txt_search_users.text().strip()
        status_filter = self.ui.cmb_filter_user_status.currentText()

        query = """
            SELECT id, full_name, email, phone_number, username,
                   role, status, last_login, created_at
            FROM users
            WHERE 1=1
        """
        params = []

        if search_text:
            query += """
                AND (full_name LIKE %s
                     OR username LIKE %s
                     OR email LIKE %s)
            """
            like = f"%{search_text}%"
            params.extend([like, like, like])

        if status_filter and status_filter != "All Status":
            query += " AND status = %s"
            params.append(status_filter)

        query += " ORDER BY full_name ASC"

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except MySQLError as e:
            QMessageBox.critical(self, "Database Error", f"Could not load users:\n{e}")
            return
        except RuntimeError as e:
            QMessageBox.warning(self, "Driver Missing", str(e))
            return

        self._populate_users_table(rows)

    def _populate_users_table(self, rows):
        """Preenche a tabela de Users linha a linha."""
        table = self.ui.table_users
        table.setSortingEnabled(False)
        table.setRowCount(0)
        table.setRowCount(len(rows))

        for row_idx, row_data in enumerate(rows):
            (user_id, full_name, email, phone, username,
             role, status, last_login, created_at) = row_data

            values = [
                str(user_id),
                str(full_name or ""),
                str(email or ""),
                self._format_phone(phone) or "",
                str(username or ""),
                str(role or ""),
                str(status or ""),
                last_login.strftime("%m/%d/%Y %H:%M") if isinstance(last_login, datetime) else str(last_login or "—"),
                created_at.strftime("%m/%d/%Y %H:%M") if isinstance(created_at, datetime) else str(created_at or "—"),
            ]

            for col_idx, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(row_idx, col_idx, item)

        table.setSortingEnabled(True)

    # ══════════════════════════════════════════════════════════════
    # USERS — FORMULÁRIO (CREATE / UPDATE / DELETE)
    # ══════════════════════════════════════════════════════════════

    def new_user_record(self):
        """Limpa o formulário para criar um novo usuário."""
        self._current_user_id = None
        self.ui.txt_user_id.clear()
        self.ui.lbl_user_id_display.setText("#ID: New")
        for field in (self.ui.txt_user_full_name, self.ui.txt_user_username,
                      self.ui.txt_user_email, self.ui.txt_user_phone,
                      self.ui.txt_user_phone2, self.ui.txt_user_password,
                      self.ui.txt_user_confirm_password):
            field.clear()
        self.ui.txt_user_last_login.clear()
        self.ui.txt_user_created_at.clear()
        self.ui.cmb_user_role.setCurrentIndex(0)
        self.ui.cmb_user_status.setCurrentIndex(0)
        self.ui.tabWidget_user.setCurrentWidget(self.ui.tab_users_master)

    def load_user_into_form(self):
        """Carrega o usuário selecionado na tabela para edição (dispara ao
        clicar numa linha — padrão master-detail)."""
        table = self.ui.table_users
        selected = table.currentRow()
        if selected < 0:
            return

        user_id = table.item(selected, 0).text()
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            columns = [d[0] for d in cursor.description]
            row = cursor.fetchone()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not load user:\n{e}")
            return

        if not row:
            return

        data = dict(zip(columns, row))
        self._current_user_id = data["id"]
        self.ui.txt_user_id.setText(str(data["id"]))
        self.ui.lbl_user_id_display.setText(f"#ID: {data['id']}")

        self.ui.txt_user_full_name.setText(data.get("full_name") or "")
        self.ui.txt_user_username.setText(data.get("username") or "")
        self.ui.txt_user_email.setText(data.get("email") or "")
        self.ui.txt_user_phone.setText(self._format_phone(data.get("phone_number")) or "")
        self.ui.txt_user_phone2.setText(self._format_phone(data.get("phone_number2")) or "")

        # Senha nunca é preenchida de volta — deixe em branco para manter a atual
        self.ui.txt_user_password.clear()
        self.ui.txt_user_confirm_password.clear()

        last_login = data.get("last_login")
        created_at = data.get("created_at")
        self.ui.txt_user_last_login.setText(
            last_login.strftime("%m/%d/%Y %H:%M") if isinstance(last_login, datetime) else str(last_login or "—")
        )
        self.ui.txt_user_created_at.setText(
            created_at.strftime("%m/%d/%Y %H:%M") if isinstance(created_at, datetime) else str(created_at or "—")
        )

        self._set_combo_by_data(self.ui.cmb_user_role, data.get("role"), by_text=True)
        self._set_combo_by_data(self.ui.cmb_user_status, data.get("status"), by_text=True)

        self.ui.tabWidget_user.setCurrentWidget(self.ui.tab_users_master)

    def save_user_record(self):
        """Insere ou atualiza um registro em users.

        Se a senha for deixada em branco numa atualização, o password_hash
        atual é preservado — só é sobrescrito se o usuário digitar uma nova senha.
        """
        full_name = self.ui.txt_user_full_name.text().strip()
        username = self.ui.txt_user_username.text().strip()
        email = self.ui.txt_user_email.text().strip()

        if not full_name or not username or not email:
            QMessageBox.warning(self, "Missing data", "Full Name, Username and Email are required.")
            return

        password = self.ui.txt_user_password.text()
        confirm_password = self.ui.txt_user_confirm_password.text()
        is_update = bool(getattr(self, "_current_user_id", None))

        if not is_update and not password:
            QMessageBox.warning(self, "Missing data", "Password is required for a new user.")
            return

        if password != confirm_password:
            QMessageBox.warning(self, "Password mismatch", "Passwords do not match.")
            return

        data = {
            "full_name": full_name,
            "email": email,
            "phone_number": self._format_phone(self.ui.txt_user_phone.text()),
            "phone_number2": self._format_phone(self.ui.txt_user_phone2.text()),
            "username": username,
            "role": self.ui.cmb_user_role.currentText(),
            "status": self.ui.cmb_user_status.currentText(),
        }

        if password:
            data["password_hash"] = hash_password(password)

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            if is_update:
                set_clause = ", ".join(f"{k} = %s" for k in data)
                query = f"UPDATE users SET {set_clause} WHERE id = %s"
                cursor.execute(query, list(data.values()) + [self._current_user_id])
            else:
                cols = ", ".join(data.keys())
                placeholders = ", ".join(["%s"] * len(data))
                query = f"INSERT INTO users ({cols}) VALUES ({placeholders})"
                cursor.execute(query, list(data.values()))

            conn.commit()
            cursor.close()
            conn.close()
        except MySQLError as e:
            if e.errno == 1062:  # Duplicate entry (violação de UNIQUE)
                error_text = str(e)
                if "email" in error_text.lower():
                    QMessageBox.warning(self, "Duplicate Email",
                                         "This email is already in use by another user.")
                elif "username" in error_text.lower():
                    QMessageBox.warning(self, "Duplicate Username",
                                         "This username is already in use by another user.")
                else:
                    QMessageBox.warning(self, "Duplicate Entry",
                                         "Email or Username is already in use by another user.")
            else:
                QMessageBox.critical(self, "Database Error", f"Could not save user:\n{e}")
            return
        except RuntimeError as e:
            QMessageBox.warning(self, "Driver Missing", str(e))
            return

        QMessageBox.information(self, "Success", "User saved successfully.")
        self.load_users()
        self.new_user_record()
        self.ui.tabWidget_user.setCurrentWidget(self.ui.tab_users_master)

    def delete_user_record(self):
        """Exclui o usuário atualmente carregado no formulário."""
        if not getattr(self, "_current_user_id", None):
            QMessageBox.information(self, "No record selected",
                                     "Select a user from the list (Update) before deleting.")
            return

        confirm = QMessageBox.question(
            self, "Confirm delete",
            f"Are you sure you want to delete user #{self._current_user_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = %s", (self._current_user_id,))
            conn.commit()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not delete user:\n{e}")
            return

        QMessageBox.information(self, "Deleted", "User deleted.")
        self.new_user_record()
        self.load_users()
        self.ui.tabWidget_user.setCurrentWidget(self.ui.tab_users_master)


    # ══════════════════════════════════════════════════════════════
    # WORK TYPES — LISTAGEM
    # ══════════════════════════════════════════════════════════════

    def load_work_types(self):
        """Carrega os registros de work_types na tabela, aplicando filtros de busca e categoria."""
        search_text = self.ui.txt_search_work_types.text().strip()
        category_filter = self.ui.cmb_filter_work_type_category.currentText()

        query = "SELECT ID, CATEGORY, NAME, UNIT FROM work_types WHERE 1=1"
        params = []

        if search_text:
            query += " AND NAME LIKE %s"
            params.append(f"%{search_text}%")

        if category_filter and category_filter != "All Categories":
            query += " AND CATEGORY = %s"
            params.append(category_filter)

        query += " ORDER BY CATEGORY, NAME"

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except MySQLError as e:
            QMessageBox.critical(self, "Database Error", f"Could not load work types:\n{e}")
            return
        except RuntimeError as e:
            QMessageBox.warning(self, "Driver Missing", str(e))
            return

        self._populate_work_types_table(rows)

    def _populate_work_types_table(self, rows):
        """Preenche a tabela de Work Types linha a linha."""
        table = self.ui.table_work_types
        table.setSortingEnabled(False)
        table.setRowCount(0)
        table.setRowCount(len(rows))

        for row_idx, (type_id, category, name, unit) in enumerate(rows):
            values = [str(type_id), str(category or ""), str(name or ""), str(unit or "")]
            for col_idx, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(row_idx, col_idx, item)

        table.setSortingEnabled(True)

    # ══════════════════════════════════════════════════════════════
    # WORK TYPES — FORMULÁRIO (CREATE / UPDATE / DELETE)
    # ══════════════════════════════════════════════════════════════

    def new_work_type_record(self):
        """Limpa o formulário para criar um novo tipo de trabalho."""
        self._current_work_type_id = None
        self.ui.txt_work_type_id.clear()
        self.ui.lbl_work_type_id_display.setText("#ID: New")
        self.ui.cmb_work_type_category.setCurrentIndex(0)
        self.ui.txt_work_type_unit.clear()
        self.ui.txt_work_type_name.clear()
        self.ui.tabWidget_work_types_page.setCurrentWidget(self.ui.tab_work_types_master)

    def load_work_type_into_form(self):
        """Carrega o tipo de trabalho selecionado na tabela para edição."""
        table = self.ui.table_work_types
        selected = table.currentRow()
        if selected < 0:
            return

        type_id = table.item(selected, 0).text()
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT ID, CATEGORY, NAME, UNIT FROM work_types WHERE ID = %s", (type_id,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not load work type:\n{e}")
            return

        if not row:
            return

        wt_id, category, name, unit = row
        self._current_work_type_id = wt_id
        self.ui.txt_work_type_id.setText(str(wt_id))
        self.ui.lbl_work_type_id_display.setText(f"#ID: {wt_id}")
        self._set_combo_by_data(self.ui.cmb_work_type_category, category, by_text=True)
        self.ui.txt_work_type_unit.setText(unit or "")
        self.ui.txt_work_type_name.setText(name or "")

        self.ui.tabWidget_work_types_page.setCurrentWidget(self.ui.tab_work_types_master)

    def save_work_type_record(self):
        """Insere ou atualiza um registro em work_types."""
        name = self.ui.txt_work_type_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing data", "Name is required.")
            return

        category = self.ui.cmb_work_type_category.currentText()
        unit = self.ui.txt_work_type_unit.text().strip().upper()

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            if getattr(self, "_current_work_type_id", None):
                cursor.execute(
                    "UPDATE work_types SET CATEGORY = %s, NAME = %s, UNIT = %s WHERE ID = %s",
                    (category, name, unit, self._current_work_type_id),
                )
            else:
                cursor.execute(
                    "INSERT INTO work_types (CATEGORY, NAME, UNIT) VALUES (%s, %s, %s)",
                    (category, name, unit),
                )

            conn.commit()
            cursor.close()
            conn.close()
        except MySQLError as e:
            if e.errno == 1062:
                QMessageBox.warning(self, "Duplicate Entry",
                                     "This name already exists for this category.")
            else:
                QMessageBox.critical(self, "Database Error", f"Could not save work type:\n{e}")
            return
        except RuntimeError as e:
            QMessageBox.warning(self, "Driver Missing", str(e))
            return

        QMessageBox.information(self, "Success", "Work type saved successfully.")
        self.load_work_types()
        self.new_work_type_record()
        self.ui.tabWidget_work_types_page.setCurrentWidget(self.ui.tab_work_types_master)

    def delete_work_type_record(self):
        """Exclui o tipo de trabalho atualmente carregado no formulário."""
        if not getattr(self, "_current_work_type_id", None):
            QMessageBox.information(self, "No record selected",
                                     "Select a work type from the list before deleting.")
            return

        confirm = QMessageBox.question(
            self, "Confirm delete",
            f"Are you sure you want to delete work type #{self._current_work_type_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM work_types WHERE ID = %s", (self._current_work_type_id,))
            conn.commit()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not delete work type:\n{e}")
            return

        QMessageBox.information(self, "Deleted", "Work type deleted.")
        self.new_work_type_record()
        self.load_work_types()
        self.ui.tabWidget_work_types_page.setCurrentWidget(self.ui.tab_work_types_master)

    # ══════════════════════════════════════════════════════════════
    # PRODUCTS — LISTAGEM
    # ══════════════════════════════════════════════════════════════

    def _setup_product_unit_completer(self):
        """Configura o autocomplete dos campos Type, Name, Unit e Coverage Unit
        (sugere o que já foi usado antes em outros produtos)."""
        self._product_type_completer = QCompleter([], self)
        self._product_type_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._product_type_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._product_type_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.ui.txt_product_type.setCompleter(self._product_type_completer)

        self._product_name_completer = QCompleter([], self)
        self._product_name_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._product_name_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._product_name_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.ui.txt_product_name.setCompleter(self._product_name_completer)

        self._product_brand_completer = QCompleter([], self)
        self._product_brand_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._product_brand_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._product_brand_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.ui.txt_product_brand.setCompleter(self._product_brand_completer)

        self._product_unit_completer = QCompleter([], self)
        self._product_unit_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._product_unit_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._product_unit_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.ui.txt_product_unit.setCompleter(self._product_unit_completer)

        self._product_coverage_unit_completer = QCompleter([], self)
        self._product_coverage_unit_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._product_coverage_unit_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._product_coverage_unit_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.ui.txt_product_coverage_unit.setCompleter(self._product_coverage_unit_completer)

    def _refresh_product_unit_completer(self):
        """Recarrega a lista de valores já usados, pros autocompletes de
        Type, Name, Unit e Coverage Unit."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT DISTINCT TYPE FROM products WHERE TYPE IS NOT NULL AND TYPE != '' ORDER BY TYPE"
            )
            types = [row[0] for row in cursor.fetchall()]
            cursor.execute(
                "SELECT DISTINCT NAME FROM products WHERE NAME IS NOT NULL AND NAME != '' ORDER BY NAME"
            )
            names = [row[0] for row in cursor.fetchall()]
            cursor.execute(
                "SELECT DISTINCT BRAND FROM products WHERE BRAND IS NOT NULL AND BRAND != '' ORDER BY BRAND"
            )
            brands = [row[0] for row in cursor.fetchall()]
            cursor.execute(
                "SELECT DISTINCT UNIT FROM products WHERE UNIT IS NOT NULL AND UNIT != '' ORDER BY UNIT"
            )
            units = [row[0] for row in cursor.fetchall()]
            cursor.execute(
                "SELECT DISTINCT COVERAGE_UNIT FROM products "
                "WHERE COVERAGE_UNIT IS NOT NULL AND COVERAGE_UNIT != '' ORDER BY COVERAGE_UNIT"
            )
            coverage_units = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError):
            types, names, units, coverage_units, brands = [], [], [], [], []
        self._product_type_completer.setModel(QStringListModel(types))
        self._product_name_completer.setModel(QStringListModel(names))
        self._product_brand_completer.setModel(QStringListModel(brands))
        self._product_unit_completer.setModel(QStringListModel(units))
        self._product_coverage_unit_completer.setModel(QStringListModel(coverage_units))

    def _suggest_unit_for_product_type(self):
        """Quando o usuário termina de digitar o Type, sugere automaticamente
        a unidade mais usada nos produtos que já têm esse mesmo Type (ex:
        'Flooring' → sugere 'SF', 'Adhesive' → sugere 'GAL'). Só preenche se
        o campo Unit ainda estiver vazio, pra não sobrescrever o que o
        usuário já escolheu."""
        if self.ui.txt_product_unit.text().strip():
            return  # já tem algo digitado, não mexe
        ptype = self.ui.txt_product_type.text().strip()
        if not ptype:
            return
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT UNIT, COUNT(*) AS cnt FROM products
                WHERE LOWER(TYPE) = LOWER(%s) AND UNIT IS NOT NULL AND UNIT != ''
                GROUP BY UNIT ORDER BY cnt DESC LIMIT 1
                """,
                (ptype,),
            )
            row = cursor.fetchone()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError):
            row = None

        if row:
            self.ui.txt_product_unit.setText(row[0])

    def load_products(self):
        """Carrega os registros de products na tabela, aplicando filtro de busca (nome, tipo ou marca)."""
        search_text = self.ui.txt_search_products.text().strip()

        query = "SELECT ID, TYPE, NAME, SPECIFICATION, PRICE, UNIT, BRAND FROM products WHERE 1=1"
        params = []
        if search_text:
            query += " AND (NAME LIKE %s OR TYPE LIKE %s OR BRAND LIKE %s)"
            like = f"%{search_text}%"
            params.extend([like, like, like])
        query += " ORDER BY TYPE, NAME"

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except MySQLError as e:
            QMessageBox.critical(self, "Database Error", f"Could not load products:\n{e}")
            return
        except RuntimeError as e:
            QMessageBox.warning(self, "Driver Missing", str(e))
            return

        self._populate_products_table(rows)
        self._refresh_product_unit_completer()

    def _populate_products_table(self, rows):
        """Preenche a tabela de Products linha a linha."""
        table = self.ui.table_products
        table.setSortingEnabled(False)
        table.setRowCount(0)
        table.setRowCount(len(rows))

        for row_idx, (product_id, ptype, name, specification, price, unit, brand) in enumerate(rows):
            price_str = f"${float(price or 0):,.2f}"
            if unit:
                price_str += f" / {unit}"
            values = [
                str(product_id), str(ptype or ""), str(name or ""),
                str(specification or ""), price_str, str(brand or ""),
            ]
            for col_idx, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(row_idx, col_idx, item)

        table.setSortingEnabled(True)

    # ══════════════════════════════════════════════════════════════
    # PRODUCTS — FORMULÁRIO (CREATE / UPDATE / DELETE)
    # ══════════════════════════════════════════════════════════════

    def _update_product_unit_price_display(self):
        """Mostra, em destaque, o preço por unidade de cobertura (ex: $2.13 /
        SF), calculado na hora a partir de Price ÷ Coverage Quantity."""
        price = self.ui.dspn_product_price.value()
        coverage_qty = self.ui.dspn_product_coverage_qty.value()
        coverage_unit = self.ui.txt_product_coverage_unit.text().strip()

        if coverage_qty > 0 and coverage_unit:
            unit_price = price / coverage_qty
            self.ui.lbl_product_unit_price_display.setText(f"${unit_price:,.2f} / {coverage_unit}")
        else:
            self.ui.lbl_product_unit_price_display.setText("—")

    def new_product_record(self):
        """Limpa o formulário para criar um novo produto."""
        self._current_product_id = None
        self.ui.txt_product_id.clear()
        self.ui.lbl_product_id_display.setText("#ID: New")
        self.ui.txt_product_type.clear()
        self.ui.txt_product_name.clear()
        self.ui.txt_product_brand.clear()
        self.ui.txt_product_specification.clear()
        self.ui.dspn_product_price.setValue(0)
        self.ui.txt_product_unit.clear()
        self.ui.dspn_product_coverage_qty.setValue(0)
        self.ui.txt_product_coverage_unit.clear()
        self.ui.chk_product_tax_paid_at_purchase.setChecked(True)
        self._update_product_unit_price_display()
        self.ui.tabWidget_products_page.setCurrentWidget(self.ui.tab_product_form)

    def load_product_into_form(self):
        """Carrega o produto selecionado na tabela para edição."""
        table = self.ui.table_products
        selected = table.currentRow()
        if selected < 0:
            return

        product_id = table.item(selected, 0).text()
        tax_paid_at_purchase = True
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "SELECT ID, TYPE, NAME, SPECIFICATION, PRICE, UNIT, COVERAGE_QTY, COVERAGE_UNIT, BRAND, "
                    "SALES_TAX_PAID_AT_PURCHASE FROM products WHERE ID = %s",
                    (product_id,),
                )
                row = cursor.fetchone()
                has_tax_column = True
            except MySQLError:
                # migration_fase4_w9_salestax.sql ainda não rodou nesse banco —
                # carrega sem a coluna nova em vez de travar a tela.
                cursor.execute(
                    "SELECT ID, TYPE, NAME, SPECIFICATION, PRICE, UNIT, COVERAGE_QTY, COVERAGE_UNIT, BRAND "
                    "FROM products WHERE ID = %s",
                    (product_id,),
                )
                row = cursor.fetchone()
                has_tax_column = False
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not load product:\n{e}")
            return

        if not row:
            return

        if has_tax_column:
            p_id, ptype, name, specification, price, unit, coverage_qty, coverage_unit, brand, tax_flag = row
            tax_paid_at_purchase = bool(tax_flag) if tax_flag is not None else True
        else:
            p_id, ptype, name, specification, price, unit, coverage_qty, coverage_unit, brand = row

        self._current_product_id = p_id
        self.ui.txt_product_id.setText(str(p_id))
        self.ui.lbl_product_id_display.setText(f"#ID: {p_id}")
        self.ui.txt_product_type.setText(ptype or "")
        self.ui.txt_product_name.setText(name or "")
        self.ui.txt_product_brand.setText(brand or "")
        self.ui.txt_product_specification.setText(specification or "")
        self.ui.dspn_product_price.setValue(float(price or 0))
        self.ui.txt_product_unit.setText(unit or "")
        self.ui.dspn_product_coverage_qty.setValue(float(coverage_qty or 0))
        self.ui.txt_product_coverage_unit.setText(coverage_unit or "")
        self.ui.chk_product_tax_paid_at_purchase.setChecked(tax_paid_at_purchase)
        self._update_product_unit_price_display()

        self.ui.tabWidget_products_page.setCurrentWidget(self.ui.tab_product_form)

    def save_product_record(self):
        """Insere ou atualiza um registro em products."""
        name = self.ui.txt_product_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing data", "Name is required.")
            return

        ptype = self.ui.txt_product_type.text().strip()
        specification = self.ui.txt_product_specification.text().strip()
        price = self.ui.dspn_product_price.value()
        unit = self.ui.txt_product_unit.text().strip().upper()
        coverage_qty = self.ui.dspn_product_coverage_qty.value() or None
        coverage_unit = self.ui.txt_product_coverage_unit.text().strip().upper() or None
        brand = self.ui.txt_product_brand.text().strip()
        tax_paid_at_purchase = 1 if self.ui.chk_product_tax_paid_at_purchase.isChecked() else 0

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            try:
                if getattr(self, "_current_product_id", None):
                    cursor.execute(
                        "UPDATE products SET TYPE = %s, NAME = %s, SPECIFICATION = %s, PRICE = %s, UNIT = %s, "
                        "COVERAGE_QTY = %s, COVERAGE_UNIT = %s, BRAND = %s, SALES_TAX_PAID_AT_PURCHASE = %s "
                        "WHERE ID = %s",
                        (ptype, name, specification, price, unit, coverage_qty, coverage_unit, brand,
                         tax_paid_at_purchase, self._current_product_id),
                    )
                else:
                    cursor.execute(
                        "INSERT INTO products (TYPE, NAME, SPECIFICATION, PRICE, UNIT, COVERAGE_QTY, "
                        "COVERAGE_UNIT, BRAND, SALES_TAX_PAID_AT_PURCHASE) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (ptype, name, specification, price, unit, coverage_qty, coverage_unit, brand,
                         tax_paid_at_purchase),
                    )
                tax_column_saved = True
            except MySQLError:
                # migration_fase4_w9_salestax.sql ainda não rodou nesse banco —
                # salva sem a coluna nova em vez de travar o cadastro de produto.
                conn.rollback()
                if getattr(self, "_current_product_id", None):
                    cursor.execute(
                        "UPDATE products SET TYPE = %s, NAME = %s, SPECIFICATION = %s, PRICE = %s, UNIT = %s, "
                        "COVERAGE_QTY = %s, COVERAGE_UNIT = %s, BRAND = %s WHERE ID = %s",
                        (ptype, name, specification, price, unit, coverage_qty, coverage_unit, brand,
                         self._current_product_id),
                    )
                else:
                    cursor.execute(
                        "INSERT INTO products (TYPE, NAME, SPECIFICATION, PRICE, UNIT, COVERAGE_QTY, "
                        "COVERAGE_UNIT, BRAND) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                        (ptype, name, specification, price, unit, coverage_qty, coverage_unit, brand),
                    )
                tax_column_saved = False

            conn.commit()
            cursor.close()
            conn.close()
        except MySQLError as e:
            QMessageBox.critical(self, "Database Error", f"Could not save product:\n{e}")
            return
        except RuntimeError as e:
            QMessageBox.warning(self, "Driver Missing", str(e))
            return

        if not tax_column_saved:
            QMessageBox.information(
                self, "Success",
                "Product saved successfully.\n\n"
                "Note: the 'sales tax paid at purchase' checkbox was NOT saved — "
                "run migration_fase4_w9_salestax.sql on the database to enable it.",
            )
        else:
            QMessageBox.information(self, "Success", "Product saved successfully.")
        self.load_products()
        self.new_product_record()
        self.ui.tabWidget_products_page.setCurrentWidget(self.ui.tab_products_list)

    def delete_product_record(self):
        """Exclui o produto atualmente carregado no formulário."""
        if not getattr(self, "_current_product_id", None):
            QMessageBox.information(self, "No record selected",
                                     "Select a product from the list before deleting.")
            return

        confirm = QMessageBox.question(
            self, "Confirm delete",
            f"Are you sure you want to delete product #{self._current_product_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products WHERE ID = %s", (self._current_product_id,))
            conn.commit()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not delete product:\n{e}")
            return

        QMessageBox.information(self, "Deleted", "Product deleted.")
        self.new_product_record()
        self.load_products()
        self.ui.tabWidget_products_page.setCurrentWidget(self.ui.tab_products_list)

    # ══════════════════════════════════════════════════════════════
    # EXPENSES — LISTAGEM
    # ══════════════════════════════════════════════════════════════

    def load_expenses(self):
        """Carrega os registros de expenses na tabela, aplicando filtros."""
        search_text = self.ui.txt_search_expenses.text().strip()
        category_filter = self.ui.cmb_filter_expense_category.currentText()
        contractor_id_filter = self.ui.cmb_filter_expense_contractor.currentData()

        query = """
            SELECT e.ID, e.EXPENSE_DATE, e.CATEGORY, e.DESCRIPTION, e.AMOUNT,
                   COALESCE(c.COMPANY_NAME, c.FULL_NAME, co.COMPANY_NAME, cl.FULL_NAME, e.OTHER_NAME, '—') AS ENTITY_NAME,
                   e.SUBMITTED_BY
            FROM expenses e
            LEFT JOIN contractors c ON c.ID = e.CONTRACTOR_ID
            LEFT JOIN companies co ON co.ID = e.COMPANY_ID
            LEFT JOIN clients cl ON cl.ID = e.CLIENT_ID
            WHERE 1=1
        """
        params = []

        if search_text:
            query += " AND e.DESCRIPTION LIKE %s"
            params.append(f"%{search_text}%")

        if category_filter and category_filter != "All Categories":
            query += " AND e.CATEGORY = %s"
            params.append(category_filter)

        if contractor_id_filter:
            query += " AND e.CONTRACTOR_ID = %s"
            params.append(contractor_id_filter)

        query += " ORDER BY e.EXPENSE_DATE DESC, e.ID DESC"

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except MySQLError as e:
            QMessageBox.critical(self, "Database Error", f"Could not load expenses:\n{e}")
            return
        except RuntimeError as e:
            QMessageBox.warning(self, "Driver Missing", str(e))
            return

        self._populate_expenses_table(rows)
        self._refresh_expense_vendor_completer()

    def _populate_expenses_table(self, rows):
        """Preenche a tabela de Expenses linha a linha."""
        table = self.ui.table_expenses
        table.setSortingEnabled(False)
        table.setRowCount(0)
        table.setRowCount(len(rows))

        for row_idx, row_data in enumerate(rows):
            (expense_id, expense_date, category, description, amount,
             contractor_name, submitted_by) = row_data

            values = [
                str(expense_id),
                expense_date.strftime("%m/%d/%Y") if isinstance(expense_date, date) else str(expense_date or ""),
                str(category or ""),
                str(description or ""),
                f"${float(amount or 0):,.2f}",
                str(contractor_name or "—"),
                str(submitted_by or ""),
            ]

            for col_idx, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(row_idx, col_idx, item)

        table.setSortingEnabled(True)

    # ══════════════════════════════════════════════════════════════
    # EXPENSES — FORMULÁRIO (CREATE / UPDATE / DELETE)
    # ══════════════════════════════════════════════════════════════

    def _refresh_expense_entity_combo(self):
        """Repopula o combo de Name (cmb_expense_contractor) de acordo com o
        tipo escolhido (Contractor/Company/Client mostram só os cadastrados
        desse tipo; Others deixa livre pra digitar qualquer nome)."""
        entity_type = self.ui.cmb_expense_entity_type.currentText()
        combo = self.ui.cmb_expense_contractor
        combo.blockSignals(True)
        combo.clear()

        if entity_type == "Others":
            combo.setEditable(True)
            combo.blockSignals(False)
            return

        combo.setEditable(True)  # continua editável, mas populado com sugestões
        query_map = {
            "Contractor": "SELECT ID, COALESCE(COMPANY_NAME, FULL_NAME) FROM contractors ORDER BY COALESCE(COMPANY_NAME, FULL_NAME)",
            "Company": "SELECT ID, COMPANY_NAME FROM companies ORDER BY COMPANY_NAME",
            "Client": "SELECT ID, FULL_NAME FROM clients ORDER BY FULL_NAME",
        }
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query_map[entity_type])
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError):
            rows = []

        combo.addItem("— Select —", None)
        for entity_id, name in rows:
            combo.addItem(name or "", entity_id)
        combo.blockSignals(False)

    def _refresh_expense_vendor_completer(self):
        """Recarrega a lista de vendors/lojas já usados antes, pro combo
        de Vendor / Store (editável, com sugestões)."""
        combo = self.ui.cmb_expense_vendor
        current_text = combo.currentText()
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT DISTINCT VENDOR FROM expenses WHERE VENDOR IS NOT NULL AND VENDOR != '' ORDER BY VENDOR"
            )
            vendors = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError):
            vendors = []
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(vendors)
        combo.setCurrentText(current_text)
        combo.blockSignals(False)

    def new_expense_record(self):
        """Limpa o formulário para criar uma nova despesa."""
        self._current_expense_id = None
        self._current_expense_receipt_path = None
        self.ui.txt_expense_id.clear()
        self.ui.lbl_expense_id_display.setText("#ID: New")
        self.ui.date_expense.setDate(date.today())
        self.ui.cmb_expense_category.setCurrentIndex(0)
        self.ui.txt_expense_description.clear()
        self.ui.cmb_expense_vendor.setCurrentText("")
        self.ui.dspn_expense_amount.setValue(0)
        self.ui.cmb_expense_submitted_by.setCurrentIndex(0)
        self.ui.cmb_expense_entity_type.setCurrentIndex(0)
        self._refresh_expense_entity_combo()
        self.ui.cmb_expense_contractor.setCurrentIndex(0)
        self._refresh_expense_job_code_combo()
        self.ui.cmb_expense_job_code.setCurrentIndex(0)
        self.ui.txt_expense_receipt_path.clear()
        self.ui.tabWidget_receivables.setCurrentWidget(self.ui.tab_expenses_master)

    def load_expense_into_form(self):
        """Carrega a despesa selecionada na tabela para edição."""
        table = self.ui.table_expenses
        selected = table.currentRow()
        if selected < 0:
            return

        expense_id = table.item(selected, 0).text()
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM expenses WHERE ID = %s", (expense_id,))
            columns = [d[0] for d in cursor.description]
            row = cursor.fetchone()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not load expense:\n{e}")
            return

        if not row:
            return

        data = dict(zip(columns, row))
        self._current_expense_id = data["ID"]
        self._current_expense_receipt_path = data.get("RECEIPT_PATH")
        self.ui.txt_expense_id.setText(str(data["ID"]))
        self.ui.lbl_expense_id_display.setText(f"#ID: {data['ID']}")

        expense_date = data.get("EXPENSE_DATE")
        self.ui.date_expense.setDate(expense_date if isinstance(expense_date, date) else date.today())

        self._set_combo_by_data(self.ui.cmb_expense_category, data.get("CATEGORY"), by_text=True)
        self.ui.txt_expense_description.setText(data.get("DESCRIPTION") or "")
        self.ui.cmb_expense_vendor.setCurrentText(data.get("VENDOR") or "")
        try:
            self.ui.dspn_expense_amount.setValue(float(data.get("AMOUNT") or 0))
        except (TypeError, ValueError):
            self.ui.dspn_expense_amount.setValue(0)
        self._set_combo_by_data(self.ui.cmb_expense_submitted_by, data.get("SUBMITTED_BY"), by_text=True)

        entity_type = data.get("ENTITY_TYPE") or "Contractor"
        self._set_combo_by_data(self.ui.cmb_expense_entity_type, entity_type, by_text=True)
        self._refresh_expense_entity_combo()
        if entity_type == "Contractor":
            self._set_combo_by_data(self.ui.cmb_expense_contractor, data.get("CONTRACTOR_ID"))
        elif entity_type == "Company":
            self._set_combo_by_data(self.ui.cmb_expense_contractor, data.get("COMPANY_ID"))
        elif entity_type == "Client":
            self._set_combo_by_data(self.ui.cmb_expense_contractor, data.get("CLIENT_ID"))
        else:
            self.ui.cmb_expense_contractor.setCurrentText(data.get("OTHER_NAME") or "")

        self._refresh_expense_job_code_combo()
        self._set_combo_by_data(self.ui.cmb_expense_job_code, data.get("JOB_PROJECT_ID"))

        self.ui.txt_expense_receipt_path.setText(data.get("RECEIPT_PATH") or "")

        self.ui.tabWidget_receivables.setCurrentWidget(self.ui.tab_expenses_master)

    def attach_expense_receipt(self):
        """Abre um seletor de arquivo pra anexar o recibo (foto ou PDF) da despesa."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select Receipt File", "", "Images and PDFs (*.png *.jpg *.jpeg *.pdf)"
        )
        if filepath:
            self._current_expense_receipt_path = filepath
            self.ui.txt_expense_receipt_path.setText(filepath)

    def save_expense_record(self):
        """Insere ou atualiza um registro em expenses."""
        amount = self.ui.dspn_expense_amount.value()
        if amount <= 0:
            QMessageBox.warning(self, "Missing data", "Amount must be greater than zero.")
            return

        entity_type = self.ui.cmb_expense_entity_type.currentText()
        contractor_id = company_id = client_id = other_name = None
        if entity_type == "Contractor":
            contractor_id = self.ui.cmb_expense_contractor.currentData()
        elif entity_type == "Company":
            company_id = self.ui.cmb_expense_contractor.currentData()
        elif entity_type == "Client":
            client_id = self.ui.cmb_expense_contractor.currentData()
        else:
            other_name = self.ui.cmb_expense_contractor.currentText().strip() or None

        data = {
            "EXPENSE_DATE": self.ui.date_expense.date().toString("yyyy-MM-dd"),
            "CATEGORY": self.ui.cmb_expense_category.currentText(),
            "DESCRIPTION": self.ui.txt_expense_description.text(),
            "VENDOR": self.ui.cmb_expense_vendor.currentText().strip() or None,
            "AMOUNT": amount,
            "ENTITY_TYPE": entity_type,
            "CONTRACTOR_ID": contractor_id,
            "COMPANY_ID": company_id,
            "CLIENT_ID": client_id,
            "OTHER_NAME": other_name,
            "SUBMITTED_BY": self.ui.cmb_expense_submitted_by.currentText(),
            "RECEIPT_PATH": self.ui.txt_expense_receipt_path.text() or None,
        }
        data_with_job = dict(data, JOB_PROJECT_ID=self.ui.cmb_expense_job_code.currentData())

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            try:
                if getattr(self, "_current_expense_id", None):
                    set_clause = ", ".join(f"{k} = %s" for k in data_with_job)
                    query = f"UPDATE expenses SET {set_clause} WHERE ID = %s"
                    cursor.execute(query, list(data_with_job.values()) + [self._current_expense_id])
                else:
                    cols = ", ".join(data_with_job.keys())
                    placeholders = ", ".join(["%s"] * len(data_with_job))
                    query = f"INSERT INTO expenses ({cols}) VALUES ({placeholders})"
                    cursor.execute(query, list(data_with_job.values()))
                job_link_saved = True
            except MySQLError:
                # migration_fase3_budget_expenses.sql ainda não rodou nesse banco —
                # salva sem o vínculo de Job Code em vez de travar o cadastro de despesa.
                conn.rollback()
                if getattr(self, "_current_expense_id", None):
                    set_clause = ", ".join(f"{k} = %s" for k in data)
                    query = f"UPDATE expenses SET {set_clause} WHERE ID = %s"
                    cursor.execute(query, list(data.values()) + [self._current_expense_id])
                else:
                    cols = ", ".join(data.keys())
                    placeholders = ", ".join(["%s"] * len(data))
                    query = f"INSERT INTO expenses ({cols}) VALUES ({placeholders})"
                    cursor.execute(query, list(data.values()))
                job_link_saved = False

            conn.commit()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not save expense:\n{e}")
            return

        if not job_link_saved and self.ui.cmb_expense_job_code.currentData():
            QMessageBox.information(
                self, "Success",
                "Expense saved successfully.\n\n"
                "Note: the Job Code link was NOT saved — run migration_fase3_budget_expenses.sql "
                "on the database to enable it.",
            )
        else:
            QMessageBox.information(self, "Success", "Expense saved successfully.")
        self.load_expenses()
        self.new_expense_record()
        self.ui.tabWidget_receivables.setCurrentWidget(self.ui.tab_expenses_master)

    def delete_expense_record(self):
        """Exclui a despesa atualmente carregada no formulário."""
        if not getattr(self, "_current_expense_id", None):
            QMessageBox.information(self, "No record selected",
                                     "Select an expense from the list before deleting.")
            return

        confirm = QMessageBox.question(
            self, "Confirm delete",
            f"Are you sure you want to delete expense #{self._current_expense_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM expenses WHERE ID = %s", (self._current_expense_id,))
            conn.commit()
            cursor.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not delete expense:\n{e}")
            return

        QMessageBox.information(self, "Deleted", "Expense deleted.")
        self.new_expense_record()
        self.load_expenses()
        self.ui.tabWidget_receivables.setCurrentWidget(self.ui.tab_expenses_master)


# ── ENTRY POINT ───────────────────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())