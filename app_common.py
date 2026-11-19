# -*- coding: utf-8 -*-
"""
VL FLOORING — imports, constantes e helpers compartilhados por main_.py e
pelas telas em paginas/ (que fazem "from app_common import *").
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
from PySide6.QtGui import QPalette, QColor, QDesktopServices, QTextCharFormat, QPixmap, QPainter, QBrush, QShortcut, QKeySequence

from ui_main_window_vl_flooring import Ui_MainWindow
from passwords import hash_password
import company_settings
import historico
import logging

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

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
# Nome, contatos, dados bancários e SMTP ficam em company_settings.py
# (são atualizados em tempo de execução pela tela Settings).
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
        # Cores do miolo seguem o tema (modo escuro → miolo escuro, número claro)
        from paginas import tema  # import aqui pra evitar import circular
        dark_theme = tema.is_dark()
        painter.setBrush(QBrush(QColor("#1B2533" if dark_theme else "#FFFFFF")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(hole_rect)

        painter.setPen(QColor("#E5E7EB" if dark_theme else "#1C2B3A"))
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
    "DELIVERY": "Delivery",
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


# Exporta tudo (inclusive nomes com _ como _InvoiceNumberedCanvas) para o
# "from app_common import *" das telas.
__all__ = [name for name in dir() if not name.startswith("__")]
