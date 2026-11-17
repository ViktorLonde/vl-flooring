# -*- coding: utf-8 -*-
"""
Toques de interface moderna, aplicados em todas as telas sem mexer em cada uma:

• Tabelas: sem a coluna de numeração, linhas mais altas, destaque ao passar
  o mouse, texto cortado aparece inteiro ao parar o mouse, status como
  etiqueta colorida e uma mensagem quando a lista está vazia.
• Avisos ("toasts"): as mensagens de informação (ex.: "Job saved") aparecem
  num aviso pequeno no canto que some sozinho, em vez de uma janela com OK.
  Erros e confirmações continuam em janela.
• Atalhos: Ctrl+S salvar, Ctrl+N novo, Ctrl+F buscar na tela, Ctrl+K busca
  geral, F5 atualizar.
• Busca geral no topo: jobs, customers, companies e contractors.

Métodos da MainWindow (mixin) — veja main_.py.
"""

from PySide6.QtCore import QObject, QPropertyAnimation, QRect
from PySide6.QtGui import QFont, QFontMetrics, QPainter, QPen, QPalette
from PySide6.QtWidgets import (QStyledItemDelegate, QStyle, QStyleOptionViewItem, QToolTip,
                               QGraphicsOpacityEffect, QListWidget, QListWidgetItem)

import shiboken6

from app_common import *  # noqa: F401,F403
from paginas.visual import tabler_icon
from paginas import tema

# ── status coloridos ──────────────────────────────────────────────────
#                  texto,     fundo
_GREEN = ("#166534", "#DCFCE7")
_AMBER = ("#92400E", "#FEF3C7")
_BLUE = ("#1E40AF", "#DBEAFE")
_RED = ("#991B1B", "#FEE2E2")
_GRAY = ("#475569", "#E2E8F0")
STATUS_COLORS = {
    "COMPLETED": _GREEN, "PAID": _GREEN, "RECEIVED": _GREEN, "ACTIVE": _GREEN, "DONE": _GREEN,
    "MATCHED": _GREEN, "OK": _GREEN, "VALID": _GREEN,
    "PENDING": _AMBER, "PARTIAL": _AMBER, "UNPAID": _AMBER, "DUE SOON": _AMBER, "EXPIRING": _AMBER,
    "IN PROGRESS": _BLUE, "STARTED": _BLUE, "SENT": _BLUE, "OPEN": _BLUE, "SCHEDULED": _BLUE,
    "OVERDUE": _RED, "SUSPENDED": _RED, "EXPIRED": _RED, "UNMATCHED": _RED,
    "CANCELLED": _GRAY, "CANCELED": _GRAY, "INACTIVE": _GRAY, "DRAFT": _GRAY, "ON HOLD": _GRAY,
}


def _status_key(text):
    return " ".join((text or "").replace("_", " ").upper().split())


class StatusPillDelegate(QStyledItemDelegate):
    """Delegate de todas as tabelas: na coluna Status desenha o status como
    etiqueta arredondada; nas outras, só ajusta as cores no modo escuro."""

    def _is_status_column(self, index):
        table = self.parent()
        header = table.horizontalHeaderItem(index.column()) if isinstance(table, QTableWidget) else None
        return bool(header and "status" in header.text().lower())

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        if tema.is_dark():
            if option.backgroundBrush.style() != Qt.BrushStyle.NoBrush:
                option.backgroundBrush = QBrush(tema.adapt_brush_color(option.backgroundBrush.color()))
            fg = index.data(Qt.ItemDataRole.ForegroundRole)
            if fg is not None:
                color = fg.color() if hasattr(fg, "color") else QColor(fg)
                option.palette.setColor(QPalette.ColorRole.Text, tema.adapt_text_color(color))

    def paint(self, painter, option, index):
        text = index.data(Qt.ItemDataRole.DisplayRole)
        colors = None
        if isinstance(text, str) and self._is_status_column(index):
            colors = STATUS_COLORS.get(_status_key(text))
        if not colors:
            return super().paint(painter, option, index)
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        opt.text = ""
        opt.backgroundBrush = QBrush(Qt.BrushStyle.NoBrush)  # a etiqueta já tem cor
        style = opt.widget.style() if opt.widget else QApplication.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, opt, painter, opt.widget)

        fg, bg = colors
        if tema.is_dark():
            fg, bg = tema.TEXT_MAP.get(fg.upper(), fg), tema.BG_MAP.get(bg.upper(), bg)
        font = QFont(option.font)
        font.setPointSizeF(max(font.pointSizeF() - 1, 7))
        font.setWeight(QFont.Weight.DemiBold)
        label = text.replace("_", " ").title()
        fm = QFontMetrics(font)
        w = fm.horizontalAdvance(label) + 20
        h = fm.height() + 6
        rect = option.rect
        x = rect.x() + 8
        y = rect.y() + (rect.height() - h) // 2
        w = min(w, rect.width() - 12)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(bg))
        painter.drawRoundedRect(QRect(x, y, w, h), h / 2, h / 2)
        painter.setPen(QPen(QColor(fg)))
        painter.setFont(font)
        painter.drawText(QRect(x, y, w, h), Qt.AlignmentFlag.AlignCenter,
                         fm.elidedText(label, Qt.TextElideMode.ElideRight, w - 12))
        painter.restore()


# ── tabelas ───────────────────────────────────────────────────────────
_EMPTY_STYLE = "color: #94A3B8; font-size: 13px; background: transparent;"


def _update_empty_state(table):
    if not shiboken6.isValid(table):  # tabela de um diálogo que já fechou
        return
    label = getattr(table, "_vl_empty_label", None)
    if label is None or not shiboken6.isValid(label):
        return
    empty = table.rowCount() == 0
    label.setVisible(empty)
    if empty:
        vp = table.viewport()
        label.setGeometry(0, 0, vp.width(), max(vp.height(), 80))
        label.raise_()


def _refresh_status_delegates(table):
    if getattr(table, "_vl_status_delegate", None) is None:
        table._vl_status_delegate = StatusPillDelegate(table)
        table.setItemDelegate(table._vl_status_delegate)


def polish_table(table):
    if table.property("_vl_polished"):
        _refresh_status_delegates(table)
        return
    table.setProperty("_vl_polished", True)
    table.verticalHeader().setVisible(False)
    table.verticalHeader().setDefaultSectionSize(max(table.verticalHeader().defaultSectionSize(), 38))
    table.setMouseTracking(True)
    table.setWordWrap(False)
    table.setTextElideMode(Qt.TextElideMode.ElideRight)
    table.viewport().installEventFilter(_TABLE_FILTER)
    _refresh_status_delegates(table)

    label = QLabel(table.viewport())
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setStyleSheet(_EMPTY_STYLE)
    label.setText("No records to show")
    label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    table._vl_empty_label = label
    # O "vigia" é filho da tabela: quando a tabela é apagada, ele também é,
    # e o Qt desliga as conexões sozinho (antes uma lambda solta tentava usar
    # a tabela já apagada e dava erro ao fechar diálogos).
    watcher = _EmptyStateWatcher(table)
    model = table.model()
    for signal in (model.rowsInserted, model.rowsRemoved, model.modelReset, model.layoutChanged):
        signal.connect(watcher.update)
    _update_empty_state(table)


class _EmptyStateWatcher(QObject):
    def __init__(self, table):
        super().__init__(table)
        self._table = table

    def update(self, *_args):
        _update_empty_state(self._table)


class _TableViewportFilter(QObject):
    def eventFilter(self, obj, event):
        if not shiboken6.isValid(obj):
            return False
        table = obj.parent()
        if not isinstance(table, QTableWidget):
            return False
        if event.type() == QEvent.Type.ToolTip:
            item = table.itemAt(event.pos())
            if item and item.text() and not item.toolTip():
                col_width = table.columnWidth(item.column()) - 20
                if QFontMetrics(table.font()).horizontalAdvance(item.text()) > col_width:
                    QToolTip.showText(event.globalPos(), item.text(), table)
                    return True
        elif event.type() == QEvent.Type.Resize:
            _update_empty_state(table)
        return False


_TABLE_FILTER = _TableViewportFilter()

TABLE_EXTRA_QSS = """
QTableWidget::item:hover { background-color: #F3F7FB; }
QTableWidget::item:selected { background-color: #E3F2FD; color: #0D47A1; }
QHeaderView::section { padding: 9px 10px; }
#frame_jobs_right_panel QComboBox, #frame_client_drawer QComboBox { min-height: 20px; padding: 6px 12px; }
"""


# ── toasts ────────────────────────────────────────────────────────────
class Toast(QFrame):
    """Aviso pequeno no canto de baixo à direita que some sozinho."""
    _active = []

    def __init__(self, window, text, kind="success"):
        super().__init__(window)
        self.setObjectName("vl_toast")
        icon_name, color = {"success": ("circle-check", "#16A34A"),
                            "info": ("info-circle", "#2563EB")}.get(kind, ("circle-check", "#16A34A"))
        self.setStyleSheet(
            "#vl_toast { background-color: #1F2937; border-radius: 10px; }"
            "#vl_toast QLabel { color: #F9FAFB; font-size: 13px; background: transparent; }")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 11, 16, 11)
        layout.setSpacing(10)
        icon = QLabel()
        icon.setPixmap(tabler_icon(icon_name, "#4ADE80" if kind == "success" else "#93C5FD", 20).pixmap(20, 20))
        icon.setAlignment(Qt.AlignmentFlag.AlignTop)
        msg = QLabel(text)
        msg.setWordWrap(True)
        msg.setMaximumWidth(380)
        layout.addWidget(icon)
        layout.addWidget(msg, 1)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Click to close")

        self._effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._effect)
        self._anim = QPropertyAnimation(self._effect, b"opacity", self)
        self._anim.setDuration(220)

        self.adjustSize()
        Toast._active.append(self)
        self._place_all(window)
        self.show()
        self.raise_()
        self._fade(0.0, 1.0)
        duration = min(9000, 3000 + 45 * len(text))
        QTimer.singleShot(duration, self.close_toast)

    @staticmethod
    def _place_all(window):
        y = window.height() - 24
        for toast in reversed([t for t in Toast._active if t.parent() is window]):
            y -= toast.height()
            toast.move(window.width() - toast.width() - 24, y)
            y -= 10

    def _fade(self, start, end, after=None):
        self._anim.stop()
        self._anim.setStartValue(start)
        self._anim.setEndValue(end)
        if after:
            self._anim.finished.connect(after)
        self._anim.start()

    def mousePressEvent(self, event):
        self.close_toast()

    def close_toast(self):
        if self not in Toast._active:
            return
        Toast._active.remove(self)
        window = self.parent()
        self._fade(1.0, 0.0, self.deleteLater)
        if window is not None:
            Toast._place_all(window)


_SUCCESS_WORDS = ("saved", "success", "updated", "deleted", "created", "sent", "generated",
                  "added", "removed", "recorded", "exported", "imported", "copied", "done")


def show_toast(text, kind=None, window=None):
    if window is None:
        window = next((w for w in QApplication.topLevelWidgets()
                       if isinstance(w, QMainWindow) and w.isVisible()), None)
    if window is None:
        return False
    if kind is None:
        kind = "success" if any(w in text.lower() for w in _SUCCESS_WORDS) else "info"
    Toast(window, text, kind)
    return True


def install_toasts():
    """QMessageBox.information com só o botão OK vira toast."""
    if getattr(QMessageBox, "_vl_original_information", None) is not None:
        return
    original = QMessageBox.information
    QMessageBox._vl_original_information = original

    def information(parent, title, text, buttons=QMessageBox.StandardButton.Ok, *args, **kwargs):
        only_ok = buttons in (QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.NoButton)
        if only_ok and len(str(text)) <= 500 and show_toast(str(text)):
            return QMessageBox.StandardButton.Ok
        return original(parent, title, text, buttons, *args, **kwargs)

    QMessageBox.information = staticmethod(information)


class _PolishFilter(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Show and isinstance(obj, QTableWidget):
            polish_table(obj)
        return False


def install_modern_ui(app):
    """Chamado uma vez, logo depois de criar o QApplication."""
    install_toasts()
    app._vl_polish_filter = _PolishFilter(app)
    app.installEventFilter(app._vl_polish_filter)


# ── mixin: atalhos e busca geral ─────────────────────────────────────
class ModernMixin:
    def _setup_modern_ui(self):
        self.setStyleSheet(self.styleSheet() + TABLE_EXTRA_QSS)
        for table in self.findChildren(QTableWidget):
            polish_table(table)
        self._setup_shortcuts()
        self._setup_global_search()

        self._compact_job_form()

        # "P&L" aparecia como "PL": no Qt um "&" sozinho vira atalho de teclado
        for tabs in self.findChildren(QTabWidget):
            for i in range(tabs.count()):
                text = tabs.tabText(i)
                if "&" in text and "&&" not in text:
                    tabs.setTabText(i, text.replace("&", "&&"))

        # O formulário de Job abria com 01/01/2000 até clicar em New Job
        if getattr(self, "_current_job_id", None) is None:
            self._loading_job_form = True
            self.ui.date_work_date.setDate(QDate.currentDate())
            self._loading_job_form = False
            self._job_form_dirty = False

    def _compact_job_form(self):
        """Campos do formulário de Job com altura única (36px) — antes uns
        tinham 46px e outros 36px — e o rótulo HELPER no mesmo padrão dos
        outros (maiúsculo, mesma cor)."""
        ui = self.ui
        for area in (ui.frame_jobs_right_panel, getattr(ui, "frame_client_drawer", None)):
            if area is None:
                continue
            for cls in (QComboBox, QLineEdit, QDateEdit, QDoubleSpinBox, QSpinBox):
                for field in area.findChildren(cls):
                    if field.minimumHeight() > 36:
                        field.setMinimumHeight(36)
                    if field.maximumHeight() < 36 or field.maximumHeight() > 40:
                        field.setMaximumHeight(38)
        if hasattr(ui, "lbl_helper"):
            ui.lbl_helper.setText("HELPER")
            ui.lbl_helper.setStyleSheet(ui.lbl_contractor.styleSheet())
            ui.lbl_helper.setFont(ui.lbl_contractor.font())
        if hasattr(ui, "lbl_helper_pay"):
            ui.lbl_helper_pay.setStyleSheet(ui.lbl_contractor.styleSheet())
            ui.lbl_helper_pay.setFont(ui.lbl_contractor.font())

    # atalhos
    def _setup_shortcuts(self):
        for keys, handler in (("Ctrl+S", lambda: self._click_page_button(("btn_save_", "btn_settings_save"))),
                              ("Ctrl+N", lambda: self._click_page_button(("btn_new_",))),
                              ("F5", lambda: self._click_page_button(("btn_refresh_",))),
                              ("Ctrl+F", self._focus_page_search),
                              ("Ctrl+K", self._focus_global_search)):
            sc = QShortcut(QKeySequence(keys), self)
            sc.activated.connect(handler)

    def _page_widgets(self, cls):
        page = self.ui.Pages.currentWidget()
        return [w for w in page.findChildren(cls) if w.isVisible() and w.isEnabled()]

    def _click_page_button(self, prefixes):
        for btn in self._page_widgets(QPushButton):
            if btn.objectName().startswith(prefixes):
                btn.click()
                return

    def _focus_page_search(self):
        for edit in self._page_widgets(QLineEdit):
            if edit.objectName().startswith("txt_search"):
                edit.setFocus()
                edit.selectAll()
                return
        self._focus_global_search()

    def _focus_global_search(self):
        self._global_search.setFocus()
        self._global_search.selectAll()

    # busca geral
    def _setup_global_search(self):
        edit = QLineEdit()
        edit.setObjectName("txt_global_search")
        edit.setPlaceholderText("Search jobs, customers, companies…   Ctrl+K")
        edit.setClearButtonEnabled(True)
        edit.setFixedWidth(360)
        edit.addAction(tabler_icon("search", "#7A8A9A", 16), QLineEdit.ActionPosition.LeadingPosition)
        edit.setStyleSheet(
            "QLineEdit { background-color: #F1F5F9; border: 1px solid #E2E8F0; border-radius: 8px; "
            "padding: 6px 10px; font-size: 13px; color: #1C2B3A; } "
            "QLineEdit:focus { background-color: #FFFFFF; border: 1px solid #1565C0; }")
        layout = self.ui.horizontalLayout_top
        layout.insertWidget(layout.indexOf(self.ui.lbl_user), edit)
        layout.insertSpacing(layout.indexOf(self.ui.lbl_user), 16)
        self._global_search = edit

        popup = QListWidget(self)
        popup.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        popup.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        popup.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        popup.setStyleSheet(
            "QListWidget { background: #FFFFFF; border: 1px solid #D0D7DE; border-radius: 8px; padding: 4px; "
            "font-size: 13px; color: #1C2B3A; outline: none; } "
            "QListWidget::item { padding: 7px 8px; border-radius: 6px; } "
            "QListWidget::item:selected, QListWidget::item:hover { background: #EEF4FB; color: #0D47A1; }")
        popup.itemClicked.connect(self._open_global_result)
        self._global_popup = popup

        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.setInterval(250)
        timer.timeout.connect(self._run_global_search)
        self._global_timer = timer
        edit.textChanged.connect(lambda _t: timer.start())
        edit.installEventFilter(self)
        edit.returnPressed.connect(lambda: self._open_global_result(popup.currentItem()))

    def _global_search_key(self, event):
        """Setas/Esc dentro do campo de busca geral (chamado pelo eventFilter)."""
        popup = self._global_popup
        if event.type() == QEvent.Type.KeyPress and event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Up) and popup.isVisible() and popup.count():
            step = 1 if event.key() == Qt.Key.Key_Down else -1
            row = (popup.currentRow() + step) % popup.count()
            popup.setCurrentRow(row)
            return True
        if event.type() == QEvent.Type.FocusOut:
            QTimer.singleShot(200, lambda: None if popup.underMouse() else popup.hide())
            return False
        if event.type() != QEvent.Type.KeyPress:
            return False
        if event.key() == Qt.Key.Key_Escape:
            popup.hide()
            self._global_search.clear()
            return True
        return False

    def _run_global_search(self):
        text = self._global_search.text().strip()
        popup = self._global_popup
        if len(text) < 2:
            popup.hide()
            return
        like = f"%{text}%"
        queries = [
            ("job", "clipboard-list",
             "SELECT MAX(wd.ID), CONCAT(COALESCE(MAX(jp.CODE), CONCAT('Job #', MAX(wd.ID))), ' — ', "
             "COALESCE(MAX(wd.JOB_ADDRESS), '')), MAX(wd.WORK_DATE) "
             "FROM work_days wd LEFT JOIN job_projects jp ON jp.ID = wd.JOB_PROJECT_ID "
             "WHERE jp.CODE LIKE %s OR wd.JOB_ADDRESS LIKE %s GROUP BY COALESCE(jp.ID, -wd.ID) "
             "ORDER BY MAX(wd.WORK_DATE) DESC LIMIT 6", (like, like)),
            ("customer", "address-book",
             "SELECT ID, FULL_NAME, NULL FROM clients WHERE FULL_NAME LIKE %s OR EMAIL LIKE %s "
             "OR PHONE_NUMBER LIKE %s ORDER BY FULL_NAME LIMIT 5", (like, like, like)),
            ("company", "building",
             "SELECT ID, COMPANY_NAME, NULL FROM companies WHERE COMPANY_NAME LIKE %s OR CONTACT_NAME LIKE %s "
             "ORDER BY COMPANY_NAME LIMIT 5", (like, like)),
            ("contractor", "briefcase",
             "SELECT ID, COALESCE(NULLIF(COMPANY_NAME, ''), FULL_NAME), NULL FROM contractors "
             "WHERE COMPANY_NAME LIKE %s OR FULL_NAME LIKE %s ORDER BY 2 LIMIT 5", (like, like)),
        ]
        results = []
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            for kind, icon, sql, params in queries:
                cur.execute(sql, params)
                for rid, label, extra in cur.fetchall():
                    results.append((kind, icon, rid, label or "", extra))
            cur.close()
            conn.close()
        except (MySQLError, RuntimeError):
            logging.getLogger("vl_flooring").exception("global search failed")
            popup.hide()
            return

        popup.clear()
        names = {"job": "Job", "customer": "Customer", "company": "Company", "contractor": "Contractor"}
        for kind, icon, rid, label, extra in results:
            item = QListWidgetItem(tabler_icon(icon, "#64748B", 16), f"{label}    ·  {names[kind]}")
            item.setData(Qt.ItemDataRole.UserRole, (kind, rid, label, extra))
            popup.addItem(item)
        if not results:
            item = QListWidgetItem("No results")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            popup.addItem(item)
        popup.setCurrentRow(0)
        edit = self._global_search
        pos = edit.mapToGlobal(edit.rect().bottomLeft())
        width = max(edit.width(), 460)
        height = min(popup.sizeHintForRow(0) * popup.count() + 12, 420) if popup.count() else 40
        popup.setGeometry(pos.x() + edit.width() - width, pos.y() + 4, width, height)
        popup.show()

    def _open_global_result(self, item):
        if item is None:
            return
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return
        self._global_popup.hide()
        kind, rid, label, extra = data
        self._global_search.blockSignals(True)
        self._global_search.clear()
        self._global_search.blockSignals(False)
        if kind == "job":
            self._open_job_by_id(rid, extra)
            return
        page, button, search, table = {
            "customer": (6, self.ui.btn_customer, self.ui.txt_search_customers, self.ui.table_customers),
            "company": (2, self.ui.btn_reg_companies, self.ui.txt_search_companies, self.ui.table_companies),
            "contractor": (3, self.ui.btn_reg_contractors, self.ui.txt_search_contractors, self.ui.table_contractors),
        }[kind]
        self._go_to_page(page, button)
        search.setText(label)  # filtra a lista (textChanged recarrega)
        for r in range(table.rowCount()):
            cell = table.item(r, 0)
            if cell and cell.text() == str(rid):
                table.selectRow(r)
                return
        if table.rowCount():
            table.selectRow(0)
