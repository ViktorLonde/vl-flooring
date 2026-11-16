# -*- coding: utf-8 -*-
"""
Visual dos ícones (estilo "A": ícones de linha fina, item ativo em laranja).

• Sidebar: ícones Tabler de 20px; o item aberto fica com fundo laranja suave
  e ícone/texto laranja.
• Botões das telas: o emoji no começo do texto (ex.: "🧹  Clean…") é trocado
  por um ícone de linha da mesma cor do texto do botão. Vale também para os
  botões criados depois (diálogos) e para textos trocados com setText.
• Campos de busca com "🔍" no placeholder ganham uma lupa de verdade.

Os ícones ficam em assets/icons (Tabler Icons, licença MIT —
assets/icons/LICENSE-tabler.txt). Para trocar um ícone, mude o nome nos
dicionários abaixo (veja os nomes em https://tabler.io/icons).

Métodos da MainWindow (mixin) — veja main_.py.
"""

import os

from PySide6.QtCore import QObject, QByteArray, QRectF
from PySide6.QtGui import QIcon, QPixmap, QPainter, QPalette
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication, QPushButton, QLineEdit, QLabel

from app_common import *  # noqa: F401,F403

ICON_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icons")

ORANGE = "#FF8A4C"          # ícone/texto do item ativo
SIDEBAR_IDLE = "#A9BCCF"    # ícone em repouso
SIDEBAR_BG = "#1C2B3A"

# botão da sidebar → (ícone, texto)
SIDEBAR_ITEMS = {
    "btn_home": ("layout-dashboard", "Home"),
    "btn_jobs": ("clipboard-list", "Job Records"),
    "btn_registrations": ("folders", "Registrations"),
    "btn_reg_companies": ("building", "Companies"),
    "btn_reg_contractors": ("briefcase", "Contractors"),
    "btn_reg_helpers": ("users", "Helpers"),
    "btn_reg_work_types": ("wall", "Work Types"),
    "btn_reg_products": ("package", "Products"),
    "btn_reg_compliance": ("clipboard-check", "Compliance"),
    "btn_reg_documents": ("folder", "Documents"),
    "btn_reg_bank_reconciliation": ("building-bank", "Bank Reconciliation"),
    "btn_reg_receipt_inbox": ("inbox", "Receipt Inbox"),
    "btn_reg_job_site_inbox": ("map-pin", "Job Site Inbox"),
    "btn_reg_projects_dashboard": ("chart-bar", "Projects Dashboard"),
    "btn_nav_receivables": ("receipt-2", "Receivables"),
    "btn_customer": ("address-book", "Customer"),
    "btn_user": ("user-cog", "Users"),
    "btn_settings": ("settings", "Settings"),
}

# emoji no começo do texto de um botão → ícone
EMOJI_ICONS = {
    "✔": "check", "✓": "check", "✅": "check",
    "⤓": "download", "⤒": "upload",
    "📁": "folder", "🗂": "folder-open",
    "👤": "user", "🧾": "receipt", "⛶": "arrows-maximize",
    "🔄": "refresh", "↻": "refresh", "📜": "history", "🕘": "history",
    "👁": "eye", "✕": "x", "⚠": "alert-triangle", "📅": "calendar", "🗓": "calendar",
    "🔀": "arrows-split-2", "🧹": "eraser", "💳": "credit-card", "📤": "send",
    "📎": "paperclip", "✎": "pencil", "📊": "chart-bar", "📋": "clipboard-check",
    "🔍": "search",
}

# Cartões do Dashboard/Receivables: emoji sozinho num QLabel → (ícone, cor, fundo)
LABEL_ICONS = {
    "💰": ("cash", "#15803D", "#DCFCE7"),
    "✅": ("circle-check", "#15803D", "#DCFCE7"),
    "👷": ("users", "#1D4ED8", "#DBEAFE"),
    "⚠": ("alert-triangle", "#B91C1C", "#FEE2E2"),
    "🛠": ("tool", "#C2410C", "#FFEDD5"),
    "⏳": ("hourglass", "#B45309", "#FEF3C7"),
}

_SIDEBAR_QSS = f"""
#Left_container {{ background-color: {SIDEBAR_BG}; }}
#Left_container QPushButton {{
    background-color: transparent; color: #C9D3DD; text-align: left;
    padding: 9px 0px 9px 12px; margin: 1px 8px; border: none; border-radius: 8px;
    font-size: 13px; font-weight: 500;
}}
#Left_container QPushButton:hover {{ background-color: rgba(255,255,255,0.07); color: #FFFFFF; }}
#Left_container QPushButton:checked {{
    background-color: rgba(232,89,12,0.20); color: {ORANGE}; font-weight: 600;
}}
#frame_registrations_submenu {{ background: transparent; }}
#frame_registrations_submenu QPushButton {{
    font-size: 12px; padding: 7px 0px 7px 12px; margin: 0px 8px; color: #B4C2D0;
    background-color: transparent;
}}
#frame_registrations_submenu QPushButton:hover {{ background-color: rgba(255,255,255,0.07); color: #FFFFFF; }}
#frame_registrations_submenu QPushButton:checked {{ background-color: rgba(232,89,12,0.20); color: {ORANGE}; }}
#btn_toggle {{ padding: 9px 0px 9px 12px; }}
#label_logo {{
    color: #FFFFFF; font-size: 14px; font-weight: 700; padding: 6px 12px 12px 14px;
    background: transparent; border: none; border-bottom: 1px solid rgba(255,255,255,0.10);
}}
"""

_icon_cache = {}


def tabler_icon(name, color, size=20, checked_color=None):
    """QIcon de um ícone Tabler numa cor (e, opcionalmente, outra cor quando
    o botão está marcado/ativo)."""
    key = (name, color, size, checked_color)
    if key in _icon_cache:
        return _icon_cache[key]
    icon = QIcon()
    path = os.path.join(ICON_DIR, f"{name}.svg")
    try:
        svg = open(path, encoding="utf-8").read().replace('stroke-width="2"', 'stroke-width="1.75"')
    except OSError:
        _icon_cache[key] = icon
        return icon
    for state, col in ((QIcon.State.Off, color), (QIcon.State.On, checked_color or color)):
        for scale in (1, 2):
            renderer = QSvgRenderer(QByteArray(svg.replace("currentColor", col).encode("utf-8")))
            pix = QPixmap(size * scale, size * scale)
            pix.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pix)
            renderer.render(painter, QRectF(0, 0, size * scale, size * scale))
            painter.end()
            icon.addPixmap(pix, QIcon.Mode.Normal, state)
    _icon_cache[key] = icon
    return icon


def _raw_set_text(btn, text):
    """setText sem passar pela conversão de emoji."""
    original = getattr(QPushButton, "_vl_original_setText", None)
    (original or QPushButton.setText)(btn, text)


def _split_leading_emoji(text):
    """'🧹  Clean Empty' → ('eraser', 'Clean Empty'); sem emoji → (None, text)."""
    stripped = (text or "").lstrip()
    for emoji, name in EMOJI_ICONS.items():
        if stripped.startswith(emoji):
            rest = stripped[len(emoji):].lstrip("️").strip()
            return name, rest
    return None, text


def _button_text_color(btn):
    return btn.palette().color(QPalette.ColorRole.ButtonText).name()


def _apply_button_icon(btn):
    name = btn.property("_ti_name")
    if not name:
        return
    color = _button_text_color(btn)
    if btn.property("_ti_color") == color and not btn.icon().isNull():
        return
    btn.setProperty("_ti_color", color)
    btn.setIcon(tabler_icon(name, color, 16))
    if btn.iconSize().width() > 20 or btn.iconSize().width() < 14:
        btn.setIconSize(QSize(16, 16))


def _convert_button(btn, text=None):
    """Troca o emoji do começo do texto por um ícone. Retorna o texto limpo."""
    if btn.property("_ti_sidebar"):
        return text if text is not None else btn.text()
    name, clean = _split_leading_emoji(btn.text() if text is None else text)
    if name is None:
        return btn.text() if text is None else text
    btn.setProperty("_ti_name", name)
    if clean:
        clean = " " + clean  # respiro entre o ícone e o texto
    if text is None:
        _raw_set_text(btn, clean)
    if btn.isVisible():
        _apply_button_icon(btn)
    return clean


def _convert_search_field(edit):
    placeholder = edit.placeholderText()
    name, clean = _split_leading_emoji(placeholder)
    if name != "search" or edit.property("_ti_search"):
        return
    edit.setProperty("_ti_search", True)
    edit.setPlaceholderText(clean)
    edit.addAction(tabler_icon("search", "#7A8A9A", 16), QLineEdit.ActionPosition.LeadingPosition)


class _IconEventFilter(QObject):
    """Converte botões/campos na hora em que aparecem (inclui diálogos)."""

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Show:
            if isinstance(obj, QPushButton):
                if obj.property("_ti_name") is None:
                    _convert_button(obj)
                _apply_button_icon(obj)
            elif isinstance(obj, QLineEdit):
                _convert_search_field(obj)
        return False


def install_icon_theme(app):
    """Chamado uma vez, logo depois de criar o QApplication."""
    if getattr(QPushButton, "_vl_original_setText", None) is None:
        QPushButton._vl_original_setText = QPushButton.setText

        def set_text(btn, text):
            QPushButton._vl_original_setText(btn, _convert_button(btn, text))

        QPushButton.setText = set_text
    app._vl_icon_filter = _IconEventFilter(app)
    app.installEventFilter(app._vl_icon_filter)


class VisualMixin:
    def _setup_icon_theme(self):
        """Aplica o estilo A na sidebar. Chamar no fim do __init__, depois
        que todas as telas criaram seus botões."""
        ui = self.ui
        ui.Left_container.setStyleSheet(_SIDEBAR_QSS)

        ui.btn_toggle.setText("")
        ui.btn_toggle.setIcon(tabler_icon("menu-2", SIDEBAR_IDLE, 20))
        ui.btn_toggle.setIconSize(QSize(20, 20))
        ui.btn_toggle.setMinimumHeight(40)

        logo = os.path.join(os.path.dirname(ICON_DIR), "..", "icons_", "logo_icon_only_256.png")
        logo = os.path.normpath(logo).replace("\\", "/")
        ui.label_logo.setText(
            f'<img src="{logo}" width="22" height="22" style="vertical-align:middle">'
            f'&nbsp;&nbsp;VL Flooring')

        for attr, (icon_name, _label) in SIDEBAR_ITEMS.items():
            btn = getattr(ui, attr, None)
            if btn is None:
                continue
            btn.setProperty("_ti_sidebar", True)
            btn.setIcon(tabler_icon(icon_name, SIDEBAR_IDLE, 20, ORANGE))
            btn.setIconSize(QSize(20, 20))
            btn.setMinimumSize(0, 40 if btn.parent() is ui.Left_container else 34)
            btn.setMaximumSize(16777215, 16777215)  # Settings vinha travado em 56x56 (sem espaço pro nome)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

        # "Client Info" tinha texto branco num cartão branco (só o emoji aparecia)
        ui.btn_toggle_client_drawer.setStyleSheet(
            "QPushButton { background-color: #EEF2F7; color: #37474F; border: 1px solid #D0D7DE; "
            "border-radius: 6px; padding: 6px 14px; font-size: 12px; font-weight: 600; } "
            "QPushButton:hover { background-color: #E1E8F0; }")
        self._update_sidebar_labels()
        self._convert_card_icons()

    def _convert_card_icons(self):
        """Troca os emojis dos cartões (💰 ✅ ⚠ …) por ícones num quadrado colorido."""
        for label in self.findChildren(QLabel):
            text = label.text().strip().replace("️", "")
            if text in LABEL_ICONS:
                name, color, bg = LABEL_ICONS[text]
                label.setText("")
                label.setPixmap(tabler_icon(name, color, 22).pixmap(22, 22))
                label.setFixedSize(40, 40)
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                label.setStyleSheet(f"background-color: {bg}; border-radius: 10px; padding: 0px;")
            elif text.startswith("📊 "):
                label.setText(text[2:].strip())

    def _sidebar_label(self, attr, expanded, extra=""):
        """Texto do botão da sidebar: nome quando aberta, vazio quando fechada."""
        btn = getattr(self.ui, attr, None)
        if btn is None:
            return
        label = SIDEBAR_ITEMS[attr][1] + extra
        _raw_set_text(btn, f"   {label}" if expanded else "")
        btn.setToolTip("" if expanded else label)
