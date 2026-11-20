# -*- coding: utf-8 -*-
"""
Parte do dia trabalhada (Day portion): dia inteiro, ¾, ⅔, ½, ⅓, ¼.

Gravada em work_days.DAY_FRACTION e work_day_helpers.DAY_FRACTION
(1 = dia inteiro). Os "dias trabalhados" de um Job Code e do Helper Pay
somam essas frações — ex.: 1 + ⅓ = 1⅓ dia.

Métodos da MainWindow (mixin) — veja main_.py.
"""

from app_common import *  # noqa: F401,F403

DAY_PORTIONS = [(1.0, "Full day"), (0.75, "¾ day"), (0.667, "⅔ day"), (0.5, "½ day"),
                (0.333, "⅓ day"), (0.25, "¼ day")]
_SYMBOLS = [(0.25, "¼"), (0.333, "⅓"), (0.5, "½"), (0.667, "⅔"), (0.75, "¾")]


def fmt_days(x):
    """4.333 → '4⅓', 0.5 → '½', 2 → '2'."""
    x = float(x or 0)
    whole = int(x + 1e-6)
    frac = x - whole
    if frac < 0.02:
        return str(whole)
    if frac > 0.98:
        return str(whole + 1)
    for value, sym in _SYMBOLS:
        if abs(frac - value) < 0.02:
            return f"{whole or ''}{sym}"
    return f"{x:.2f}".rstrip("0").rstrip(".")


def days_word(x):
    return "day" if abs(float(x or 0) - 1) < 0.02 or float(x or 0) < 1 else "days"


def portion_label(x):
    x = float(x or 1)
    for value, label in DAY_PORTIONS:
        if abs(x - value) < 0.01:
            return label
    return f"{fmt_days(x)} day"


def make_portion_combo(value=1.0):
    combo = QComboBox()
    for v, label in DAY_PORTIONS:
        combo.addItem(label, v)
    set_portion(combo, value)
    combo.setToolTip("How much of the day was spent here (e.g. ⅓ in one job and the rest in another)")
    return combo


def set_portion(combo, value):
    value = float(value if value is not None else 1)
    best = min(range(combo.count()), key=lambda i: abs(combo.itemData(i) - value))
    if abs(combo.itemData(best) - value) > 0.01:  # fração fora da lista (veio do banco): acrescenta
        combo.addItem(portion_label(value), value)
        best = combo.count() - 1
    combo.setCurrentIndex(best)


class DayPortionMixin:
    def _setup_day_portion_field(self):
        """Campo DAY PORTION no Job Info, embaixo do STATUS."""
        ui = self.ui
        lbl = QLabel("DAY PORTION")
        lbl.setObjectName("lbl_day_portion")
        ref = getattr(ui, "lbl_helper", None)
        if ref is not None:
            lbl.setStyleSheet(ref.styleSheet())
            lbl.setFont(ref.font())
        combo = make_portion_combo(1.0)
        combo.setObjectName("cmb_day_portion")
        combo.setMinimumWidth(115)
        ui.grid_job_info.addWidget(lbl, 4, 2, 1, 1)
        ui.grid_job_info.addWidget(combo, 5, 2, 1, 1)
        ui.lbl_day_portion, ui.cmb_day_portion = lbl, combo
        combo.currentIndexChanged.connect(lambda *_a: self._mark_job_form_dirty())

    def _day_portion_value(self):
        combo = getattr(self.ui, "cmb_day_portion", None)
        return float(combo.currentData()) if combo is not None and combo.currentData() else 1.0

    def _set_day_portion(self, value):
        combo = getattr(self.ui, "cmb_day_portion", None)
        if combo is not None:
            set_portion(combo, value)
