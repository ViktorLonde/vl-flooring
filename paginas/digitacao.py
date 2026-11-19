# -*- coding: utf-8 -*-
"""
Comodidades de digitação:

• Campos de número/valor (Value, quantidades, preços…): ao entrar no campo
  o número fica todo selecionado — é só digitar o novo valor, sem apagar o
  antigo. Se sair sem digitar nada, o valor continua o mesmo.
• ZIP Code: ao escolher a cidade, o campo ZIP sugere os ZIPs que já foram
  usados nessa cidade (clientes, jobs, companies, contractors, helpers).
  Ao entrar no ZIP vazio, a lista aparece sozinha.

Métodos da MainWindow (mixin) — veja main_.py.
"""

from PySide6.QtCore import QObject, QStringListModel
from PySide6.QtWidgets import QAbstractSpinBox, QDateTimeEdit

from app_common import *  # noqa: F401,F403


class _SelectAllOnFocus(QObject):
    """Filtro global: seleciona o número inteiro ao entrar num campo numérico.
    O clique do mouse posiciona o cursor DEPOIS do foco, então também
    seleciona no primeiro clique logo após entrar no campo."""

    def eventFilter(self, obj, event):
        etype = event.type()
        if etype == QEvent.Type.FocusIn and isinstance(obj, QAbstractSpinBox) \
                and not isinstance(obj, QDateTimeEdit):
            obj.setProperty("_vl_just_focused", True)
            QTimer.singleShot(0, obj.selectAll)
        elif etype == QEvent.Type.MouseButtonRelease and isinstance(obj, QLineEdit):
            spin = obj.parent()
            if isinstance(spin, QAbstractSpinBox) and spin.property("_vl_just_focused"):
                spin.setProperty("_vl_just_focused", False)
                if not obj.hasSelectedText():
                    QTimer.singleShot(0, spin.selectAll)
        elif etype == QEvent.Type.FocusOut and isinstance(obj, QAbstractSpinBox):
            obj.setProperty("_vl_just_focused", False)
        return False


def install_select_all_on_focus(app):
    app._vl_select_all_filter = _SelectAllOnFocus(app)
    app.installEventFilter(app._vl_select_all_filter)


# (combo da cidade, campo ZIP, combo do estado)
_ZIP_PAIRS = [
    ("cmb_client_city", "txt_client_zip", "cmb_client_state"),
    ("cmb_company_city", "txt_company_zip", "cmb_company_state"),
    ("cmb_contractor_city", "txt_contractor_zip", "cmb_contractor_state"),
    ("cmb_customer_city", "txt_customer_zip", "cmb_customer_state"),
]
_ZIP_SOURCES = [("clients", "ZIP_CODE"), ("work_days", "ZIP_CODE"), ("companies", "ZIP_CODE"),
                ("contractors", "ZIP_CODE"), ("helpers", "ZIP_CODE")]


class _ZipFocusFilter(QObject):
    def __init__(self, owner):
        super().__init__(owner)
        self._owner = owner

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.FocusIn and isinstance(obj, QLineEdit) and not obj.text().strip():
            completer = obj.completer()
            if completer is not None and completer.model() is not None and completer.model().rowCount():
                completer.setCompletionPrefix("")
                QTimer.singleShot(0, completer.complete)
        return False


class InputHelpersMixin:
    def _setup_zip_suggestions(self):
        self._zip_focus_filter = _ZipFocusFilter(self)
        for city_name, zip_name, _state_name in _ZIP_PAIRS:
            city = getattr(self.ui, city_name, None)
            zip_field = getattr(self.ui, zip_name, None)
            if city is None or zip_field is None:
                continue
            completer = QCompleter([], zip_field)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            completer.setFilterMode(Qt.MatchFlag.MatchStartsWith)
            zip_field.setCompleter(completer)
            zip_field.installEventFilter(self._zip_focus_filter)
            city.currentIndexChanged.connect(
                lambda *_a, c=city, z=zip_field: self._refresh_zip_suggestions(c, z))

    def _zip_codes_for_city(self, city_text):
        if not city_text or city_text.startswith("—"):
            return []
        parts = " UNION ALL ".join(
            f"SELECT {col} AS Z, CITY_ID FROM {table} WHERE COALESCE({col}, '') <> ''" for table, col in _ZIP_SOURCES)
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(f"""
                SELECT t.Z, COUNT(*) AS n FROM ({parts}) t
                JOIN cities c ON c.ID = t.CITY_ID
                WHERE c.CITY = %s
                GROUP BY t.Z ORDER BY n DESC, t.Z
            """, (city_text,))
            rows = cur.fetchall()
            cur.close()
            conn.close()
        except (MySQLError, RuntimeError):
            return []
        seen, out = set(), []
        for z, _n in rows:
            formatted = self._format_zip(z) if hasattr(self, "_format_zip") else z
            if formatted and formatted not in seen:
                seen.add(formatted)
                out.append(formatted)
        return out

    def _refresh_zip_suggestions(self, city_combo, zip_field):
        completer = zip_field.completer()
        if completer is None:
            return
        zips = self._zip_codes_for_city(city_combo.currentText().strip())
        completer.setModel(QStringListModel(zips, completer))
        zip_field.setToolTip("Saved ZIPs for this city: " + ", ".join(zips[:6]) if zips else "")
