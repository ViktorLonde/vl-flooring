# -*- coding: utf-8 -*-
"""
Modo escuro.

As telas têm as cores escritas nos estilos (QSS). Em vez de reescrever cada
tela, o modo escuro troca cada cor clara pela versão escura correspondente,
olhando se a cor é de FUNDO/borda ou de TEXTO (o branco, por exemplo, vira
fundo escuro mas continua branco quando é texto de botão).

• O botão de lua/sol no topo liga/desliga; a escolha fica salva no computador.
• Telas e diálogos abertos depois também são convertidos (filtro de eventos).
• Células de tabela com cor de fundo/texto definida no código são ajustadas
  na hora de desenhar (ver adapt_brush_color / adapt_text_color).

Para ajustar uma cor do modo escuro, mude BG_MAP ou TEXT_MAP.
"""

import re

from PySide6.QtCore import QObject, QSettings
from PySide6.QtGui import QPalette

from app_common import *  # noqa: F401,F403

# fundos e bordas: cor clara → cor escura
BG_MAP = {
    "#FFFFFF": "#1B2533", "#F0F4F8": "#111A24", "#F7F9FC": "#151F2B", "#F8FAFD": "#18222F",
    "#F5F8FC": "#1F2A38", "#EEF2F7": "#223041", "#F1F5F9": "#223041", "#F3F7FB": "#243246",
    "#E1E8F0": "#2B3A4E", "#EEF4FB": "#1E3A5F", "#E3F2FD": "#1E3A5F", "#BBDEFB": "#1E40AF",
    "#E3E8EE": "#2C3A4C", "#D0D7DE": "#334155", "#DDE4EE": "#2C3A4C", "#CBD5E1": "#3B4A5E",
    "#DDDDDD": "#334155", "#D7DEE7": "#334155", "#E2E8F0": "#334155", "#EEEEEE": "#2C3A4C",
    "#DCFCE7": "#14532D", "#DBEAFE": "#1E3A8A", "#FEE2E2": "#7F1D1D", "#FEF3C7": "#78350F",
    "#FFEDD5": "#7C2D12", "#FFF3CD": "#3F3615", "#FFE08A": "#6B5A1E", "#FFE9A8": "#57491A",
    "#FFF3E0": "#3D2A12", "#E8F5E9": "#163322", "#FFEBEE": "#3D1A1E", "#FBE9E7": "#3D1F18",
    "#90B8E0": "#3B5B7E",
}
# textos: cor escura → cor clara
TEXT_MAP = {
    "#1C2B3A": "#E5E7EB", "#1A1F36": "#F3F4F6", "#37474F": "#CBD5E1", "#6B7C93": "#94A3B8",
    "#4A5568": "#CBD5E1", "#546E7A": "#94A3B8", "#1565C0": "#60A5FA", "#0D47A1": "#93C5FD",
    "#1E88E5": "#60A5FA", "#1976D2": "#60A5FA", "#2E7D32": "#4ADE80", "#388E3C": "#4ADE80",
    "#C62828": "#F87171", "#E53935": "#F87171", "#B71C1C": "#F87171", "#E65100": "#FB923C",
    "#8A6D00": "#FCD34D", "#B26A00": "#FBBF24", "#6A1B9A": "#C084FC", "#15803D": "#4ADE80",
    "#166534": "#86EFAC", "#92400E": "#FCD34D", "#1E40AF": "#93C5FD", "#991B1B": "#FCA5A5",
    "#475569": "#CBD5E1", "#1D4ED8": "#93C5FD", "#B91C1C": "#FCA5A5", "#C2410C": "#FDBA74",
    "#B45309": "#FCD34D", "#7A8A9A": "#94A3B8", "#8A94A6": "#94A3B8", "#90A4AE": "#94A3B8",
    "#64748B": "#94A3B8", "#9BADBF": "#94A3B8", "#8AAEC8": "#A9BCCF",
}

_DECL_RE = re.compile(r"([A-Za-z-]+)\s*:\s*([^;{}]+)")
_HEX_RE = re.compile(r"#[0-9A-Fa-f]{6}\b")
_COMMENT_RE = re.compile(r"/\*.*?\*/", re.S)

_state = {"dark": False}


def is_dark():
    return _state["dark"]


def convert_qss(qss):
    """Versão escura de um stylesheet."""
    def decl(m):
        prop, value = m.group(1).lower(), m.group(2)
        table = TEXT_MAP if prop in ("color", "selection-color") else (
            BG_MAP if ("background" in prop or "border" in prop or prop == "gridline-color") else None)
        if table is None:
            return m.group(0)
        new_value = _HEX_RE.sub(lambda h: table.get(h.group(0).upper(), h.group(0)), value)
        return f"{m.group(1)}: {new_value}"
    # comentários /* ... */ têm ":" (ex.: "padrão: cinza") e confundiriam a leitura
    return _DECL_RE.sub(decl, _COMMENT_RE.sub("", qss))


def _apply_to_widget(widget):
    light = widget.property("_vl_light_qss")
    current = widget.styleSheet()
    if current and current != widget.property("_vl_dark_qss"):
        light = current  # o código trocou o estilo depois: essa é a nova versão clara
        widget.setProperty("_vl_light_qss", light)
    if not light:
        return
    if _state["dark"]:
        dark = convert_qss(light)
        widget.setProperty("_vl_dark_qss", dark)
        if current != dark:
            widget.setStyleSheet(dark)
    else:
        widget.setProperty("_vl_dark_qss", None)
        if current != light:
            widget.setStyleSheet(light)


# ── cores de células definidas no código (QTableWidgetItem) ──────────
_BASE_DARK = QColor("#1B2533")


def adapt_brush_color(color):
    """Fundo claro de célula → tom escuro da mesma cor (só no modo escuro)."""
    if not _state["dark"] or color.lightness() < 150:
        return color
    mix = 0.22
    return QColor(int(color.red() * mix + _BASE_DARK.red() * (1 - mix)),
                  int(color.green() * mix + _BASE_DARK.green() * (1 - mix)),
                  int(color.blue() * mix + _BASE_DARK.blue() * (1 - mix)))


def adapt_text_color(color):
    """Texto escuro de célula → versão clara (só no modo escuro)."""
    if not _state["dark"] or color.lightness() > 140:
        return color
    h, s, _l, a = color.getHsl()
    return QColor.fromHsl(max(h, 0), min(s, 200), 190, a)


def _dark_palette():
    p = QPalette()
    for role, value in ((QPalette.ColorRole.Window, "#111A24"), (QPalette.ColorRole.Base, "#1B2533"),
                        (QPalette.ColorRole.AlternateBase, "#1F2A38"), (QPalette.ColorRole.Text, "#E5E7EB"),
                        (QPalette.ColorRole.WindowText, "#E5E7EB"), (QPalette.ColorRole.Button, "#223041"),
                        (QPalette.ColorRole.ButtonText, "#E5E7EB"), (QPalette.ColorRole.Highlight, "#1E3A5F"),
                        (QPalette.ColorRole.HighlightedText, "#FFFFFF"), (QPalette.ColorRole.ToolTipBase, "#1F2937"),
                        (QPalette.ColorRole.ToolTipText, "#F9FAFB"), (QPalette.ColorRole.PlaceholderText, "#7C8A9C"),
                        (QPalette.ColorRole.Link, "#60A5FA")):
        p.setColor(role, QColor(value))
    return p


class _ThemeFilter(QObject):
    """Converte widgets que aparecem ou trocam de estilo enquanto o tema
    escuro está ligado (diálogos novos, labels que mudam de cor etc.)."""

    def eventFilter(self, obj, event):
        if _state["dark"] and event.type() in (QEvent.Type.Show, QEvent.Type.StyleChange) \
                and isinstance(obj, QWidget) and obj.styleSheet() \
                and obj.styleSheet() != obj.property("_vl_dark_qss"):
            _apply_to_widget(obj)
        return False


def set_dark_mode(app, dark):
    _state["dark"] = bool(dark)
    if not hasattr(app, "_vl_light_palette"):
        app._vl_light_palette = app.palette()
    app.setPalette(_dark_palette() if dark else app._vl_light_palette)
    if dark and getattr(app, "_vl_theme_filter", None) is None:
        app._vl_theme_filter = _ThemeFilter(app)
        app.installEventFilter(app._vl_theme_filter)
    for top in app.topLevelWidgets():
        for widget in [top] + top.findChildren(QWidget):
            if widget.styleSheet() or widget.property("_vl_light_qss"):
                _apply_to_widget(widget)
        top.update()


class ThemeMixin:
    def _setup_theme_toggle(self):
        btn = QPushButton()
        btn.setObjectName("btn_theme_toggle")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedSize(36, 36)
        btn.setStyleSheet("QPushButton { background: transparent; border: none; border-radius: 8px; } "
                          "QPushButton:hover { background: rgba(127,127,127,0.15); }")
        btn.clicked.connect(self._toggle_dark_mode)
        layout = self.ui.horizontalLayout_top
        layout.insertWidget(layout.indexOf(self.ui.lbl_user), btn)
        layout.insertSpacing(layout.indexOf(self.ui.lbl_user), 10)
        self._btn_theme = btn
        dark = QSettings("VL Flooring", "app").value("dark_mode", False, type=bool)
        if dark:
            set_dark_mode(QApplication.instance(), True)
        self._refresh_theme_button()
        self._refresh_card_icons()

    def _refresh_theme_button(self):
        from paginas.visual import tabler_icon
        dark = is_dark()
        self._btn_theme.setIcon(tabler_icon("sun" if dark else "moon", "#FBBF24" if dark else "#6B7C93", 20))
        self._btn_theme.setIconSize(QSize(20, 20))
        self._btn_theme.setToolTip("Light mode" if dark else "Dark mode")

    def _toggle_dark_mode(self):
        dark = not is_dark()
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            set_dark_mode(QApplication.instance(), dark)
        finally:
            QApplication.restoreOverrideCursor()
        QSettings("VL Flooring", "app").setValue("dark_mode", dark)
        self._refresh_theme_button()
        self._refresh_card_icons()
