# -*- coding: utf-8 -*-
"""
Ordem do Tab nos formulários (pedido do Viktor, 26/11/2026: no Customer o Tab
pulava fora de ordem e, depois do Phone 2, sumia da tela).

O Qt segue a ordem em que os campos foram criados no Designer, que não é a
ordem da tela. Aqui a ordem é recalculada pela POSIÇÃO de cada campo na tela
(de cima para baixo, da esquerda para a direita), sempre que o formulário
aparece — assim também vale para campos que aparecem/somem e para os que
foram acrescentados por código. Campos escondidos, desabilitados ou só de
leitura (ex.: #ID) ficam fora; no fim vem o botão Save.

Métodos da MainWindow (mixin) — veja main_.py.
"""
from PySide6.QtCore import QPoint, QTimer
from PySide6.QtWidgets import (QAbstractSpinBox, QCheckBox, QComboBox, QDateEdit, QDoubleSpinBox, QLineEdit,
                               QPlainTextEdit, QRadioButton, QSpinBox, QTextEdit, QWidget)

from app_common import *  # noqa: F401,F403

INPUTS = (QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTextEdit, QPlainTextEdit, QCheckBox,
          QRadioButton)
ROW_TOLERANCE = 14  # px — campos na mesma linha da tela

# (primeiro campo do formulário, botão Save) — o formulário é o "pai" do primeiro campo
FORMS = [
    ("txt_customer_name", "btn_save_customer"),
    ("txt_company_name", "btn_save_company"),
    ("txt_contractor_full_name", "btn_save_contractor"),
    ("txt_product_name", "btn_save_product"),
    ("txt_work_type_name", "btn_save_work_type"),
    ("txt_user_full_name", "btn_save_user"),
]


def _usable(w, container):
    if not isinstance(w, INPUTS):
        return False
    parent = w.parentWidget()
    if isinstance(parent, (QComboBox, QAbstractSpinBox)):  # o QLineEdit de dentro de um combo/spin
        return False
    if not w.isVisibleTo(container) or not w.isEnabled():
        return False
    if isinstance(w, (QLineEdit, QTextEdit, QPlainTextEdit)) and w.isReadOnly():
        return False
    return bool(w.focusPolicy() & Qt.FocusPolicy.TabFocus)


def screen_order(container):
    """Campos do container na ordem da tela (linhas de cima para baixo, depois da esquerda para a direita)."""
    items = []
    for w in container.findChildren(QWidget):
        if _usable(w, container):
            p = w.mapTo(container, QPoint(0, 0))
            items.append((p.y(), p.x(), w))
    items.sort(key=lambda t: (t[0], t[1]))
    # agrupa em linhas (campos lado a lado podem ter alguns px de diferença na altura)
    rows, current, top = [], [], None
    for y, x, w in items:
        if top is None or y - top > ROW_TOLERANCE:
            if current:
                rows.append(current)
            current, top = [], y
        current.append((x, w))
    if current:
        rows.append(current)
    return [w for row in rows for _x, w in sorted(row, key=lambda t: t[0])]


def apply_tab_order(container, last=None):
    chain = screen_order(container)
    if last is not None and last.isVisibleTo(container.window()) and last.isEnabled():
        chain.append(last)
    for a, b in zip(chain, chain[1:]):
        QWidget.setTabOrder(a, b)
    return chain


class TabOrderMixin:
    def _tab_order_targets(self):
        out = []
        for first, save in FORMS:
            w = getattr(self.ui, first, None)
            if w is not None and w.parentWidget() is not None:
                out.append((w.parentWidget(), getattr(self.ui, save, None)))
        job = getattr(self.ui, "tab_jobs_master", None)
        if job is not None:
            out.append((job, getattr(self.ui, "btn_save_job", None)))
        return out

    def _refresh_tab_orders(self):
        """Recalcula a ordem do Tab dos formulários visíveis agora."""
        for container, save in self._tab_order_targets():
            if container.isVisible():
                apply_tab_order(container, save)

    def _schedule_tab_order_refresh(self, *_args):
        # depois do layout terminar (as posições só valem com o formulário na tela)
        QTimer.singleShot(0, self._refresh_tab_orders)

    def _setup_tab_order(self):
        self.ui.Pages.currentChanged.connect(self._schedule_tab_order_refresh)
        tabs = getattr(self.ui, "tabWidget_jobs", None)
        if tabs is not None:
            tabs.currentChanged.connect(self._schedule_tab_order_refresh)
