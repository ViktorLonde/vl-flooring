# -*- coding: utf-8 -*-
"""
Aplica o padrão de escrita (formatar_texto.smart_title) nos campos de nome e
endereço assim que o usuário sai do campo — "3331 FOUNDERS CLUB DR" vira
"3331 Founders Club Dr" na hora, e é isso que é salvo.

E-mail, telefone, ZIP, site, usuário, observações e os dados da empresa em
Settings (que aparecem na invoice do jeito que foram escritos) não são
mexidos.

Métodos da MainWindow (mixin) — veja main_.py.
"""

from app_common import *  # noqa: F401,F403
from formatar_texto import smart_title

TITLE_CASE_FIELDS = [
    # Job Records + gaveta Client Info
    "txt_client_name", "cmb_client_address", "txt_client_address2",
    # Companies
    "txt_company_name", "txt_contact_name", "txt_company_address", "txt_company_address2",
    # Contractors
    "txt_contractor_full_name", "txt_contractor_position", "txt_contractor_company_name",
    "txt_contractor_address", "txt_contractor_address2",
    # Customer
    "txt_customer_name", "txt_customer_address", "txt_customer_address2",
    # Users, Products, Work Types
    "txt_user_full_name", "txt_product_name", "txt_product_brand", "txt_work_type_name",
]


def attach_title_case(line_edit):
    """Liga o padrão a um QLineEdit (também usado nos diálogos)."""
    def fix():
        text = line_edit.text()
        fixed = smart_title(text)
        if fixed != text:
            line_edit.setText(fixed)
    line_edit.editingFinished.connect(fix)
    line_edit.setProperty("_vl_title_case", True)
    return line_edit


class TextStandardMixin:
    def _setup_title_case_fields(self):
        for name in TITLE_CASE_FIELDS:
            widget = getattr(self.ui, name, None)
            if widget is None:
                continue
            if isinstance(widget, QComboBox):
                widget = widget.lineEdit() if widget.isEditable() else None
            if isinstance(widget, QLineEdit):
                attach_title_case(widget)
