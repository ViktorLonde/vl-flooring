# -*- coding: utf-8 -*-
"""
Work Types do job como LISTA sem limite de linhas.

Antes o formulário tinha espaços fixos (4 Demolition, 4 Installation,
4 Preparation, 2 Others, 2 Repair), porque cada um era uma coluna em
work_days. Agora:

• Cada serviço do dia é uma linha: Categoria · Serviço · Quantidade · Unidade.
  "+ Add work type" acrescenta quantas linhas forem precisas.
• A lista completa fica na tabela work_day_work_types (uma linha por serviço).
• As colunas antigas de work_days (DEMOLITION_1_ID…) continuam sendo
  preenchidas com os primeiros serviços de cada categoria, para tudo o que
  ainda lê essas colunas seguir funcionando. Invoices, agenda da semana e o
  gráfico da Home leem a lista completa.

Métodos da MainWindow (mixin) — veja main_.py.
"""

from app_common import *  # noqa: F401,F403
from paginas.visual import tabler_icon

CATEGORIES = [("DEMOLITION", "Demolition"), ("INSTALLATION", "Installation"), ("PREPARATION", "Preparation"),
              ("OTHERS", "Others"), ("REPARO", "Repair")]
# quantos serviços de cada categoria cabem nas colunas antigas de work_days
_FIXED_SLOTS = {"DEMOLITION": 4, "INSTALLATION": 4, "PREPARATION": 4, "OTHERS": 2, "REPARO": 2}

_ROW_QSS = ("#work_type_list { background: transparent; } "
            "QComboBox, QDoubleSpinBox { min-height: 20px; padding: 6px 10px; } "
            "QLabel#wt_unit { color: #6B7C93; font-weight: 600; background: transparent; }")


def fixed_column_values(items):
    """[(categoria, work_type_id, qty)] → {"DEMOLITION_1_ID": …, "DEMOLITION_1_QTY": …, …}
    com os primeiros serviços de cada categoria; o resto fica só na lista."""
    values = {}
    used = {cat: 0 for cat in _FIXED_SLOTS}
    for cat, slots in _FIXED_SLOTS.items():
        for n in range(1, slots + 1):
            values[f"{cat}_{n}_ID"] = None
            values[f"{cat}_{n}_QTY"] = None
    for cat, wt_id, qty in items:
        if cat not in used or used[cat] >= _FIXED_SLOTS[cat]:
            continue
        used[cat] += 1
        values[f"{cat}_{used[cat]}_ID"] = wt_id
        values[f"{cat}_{used[cat]}_QTY"] = qty
    return values


def items_from_columns(data):
    """Lista a partir das colunas antigas (dias que ainda não têm a lista)."""
    items = []
    for cat, slots in _FIXED_SLOTS.items():
        for n in range(1, slots + 1):
            wt_id = data.get(f"{cat}_{n}_ID")
            if wt_id:
                items.append((cat, wt_id, float(data.get(f"{cat}_{n}_QTY") or 0)))
    return items


class WorkTypeListMixin:
    # ── montagem ─────────────────────────────────────────────────────
    def _setup_work_type_list(self):
        ui = self.ui
        grid = ui.grid_work_types
        keep = {ui.lbl_note, ui.txt_note}
        for i in range(grid.count()):
            w = grid.itemAt(i).widget()
            if w is not None and w not in keep:
                w.setVisible(False)
                w.setProperty("_vl_old_work_type", True)

        box = QWidget()
        box.setObjectName("work_type_list")
        box.setStyleSheet(_ROW_QSS)
        outer = QVBoxLayout(box)
        outer.setContentsMargins(0, 0, 0, 8)
        outer.setSpacing(8)
        self._wt_rows_layout = QVBoxLayout()
        self._wt_rows_layout.setSpacing(6)
        outer.addLayout(self._wt_rows_layout)
        self._wt_empty = QLabel("No work types yet — click “Add work type”.")
        self._wt_empty.setStyleSheet("color:#94A3B8; background:transparent;")
        outer.addWidget(self._wt_empty)
        bottom = QHBoxLayout()
        btn_add = QPushButton("  Add work type")
        btn_add.setObjectName("btn_add_work_type_line")
        btn_add.setIcon(tabler_icon("plus", "#37474F", 16))
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.clicked.connect(lambda: self._add_work_type_row(focus=True))
        bottom.addWidget(btn_add)
        bottom.addStretch(1)
        self._wt_summary = QLabel("")
        self._wt_summary.setStyleSheet("color:#6B7C93; background:transparent;")
        bottom.addWidget(self._wt_summary)
        outer.addLayout(bottom)
        grid.addWidget(box, 0, 0, 1, 8)
        ui.work_type_list = box
        self._wt_rows = []
        self._wt_catalog = {}
        self._reload_work_type_catalog()
        self._refresh_work_type_list_state()

    def _reload_work_type_catalog(self):
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT ID, CATEGORY, NAME, UNIT FROM work_types ORDER BY NAME")
            rows = cur.fetchall()
            cur.close()
            conn.close()
        except (MySQLError, RuntimeError):
            rows = []
        self._wt_catalog = {wid: ((cat or "OTHERS").upper(), name or f"#{wid}", unit or "") for wid, cat, name, unit in rows}

    def _work_type_list_ready(self):
        return self._table_column_exists("work_day_work_types", "WORK_DAY_ID")

    # ── linhas ───────────────────────────────────────────────────────
    def _add_work_type_row(self, category=None, wt_id=None, qty=1.0, focus=False):
        if wt_id and not category:
            category = self._wt_catalog.get(wt_id, ("OTHERS",))[0]
        row_widget = QWidget()
        row_widget.setFixedHeight(46)
        h = QHBoxLayout(row_widget)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)
        cmb_cat = QComboBox()
        for key, label in CATEGORIES:
            cmb_cat.addItem(label, key)
        cmb_cat.setFixedWidth(170)
        cmb_type = QComboBox()
        cmb_type.setMinimumWidth(240)
        spin = QDoubleSpinBox()
        spin.setRange(0, 999999)
        spin.setDecimals(2)
        spin.setGroupSeparatorShown(True)
        spin.setFixedWidth(130)
        spin.setValue(float(qty or 0))
        lbl_unit = QLabel("")
        lbl_unit.setObjectName("wt_unit")
        lbl_unit.setFixedWidth(46)
        btn_rm = QPushButton()
        btn_rm.setIcon(tabler_icon("x", "#C62828", 16))
        btn_rm.setToolTip("Remove this line")
        btn_rm.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_rm.setFixedWidth(40)
        for w, stretch in ((cmb_cat, 0), (cmb_type, 1), (spin, 0), (lbl_unit, 0), (btn_rm, 0)):
            h.addWidget(w, stretch)
        entry = {"widget": row_widget, "cat": cmb_cat, "type": cmb_type, "qty": spin, "unit": lbl_unit}

        def fill_types(keep_id=None):
            cmb_type.blockSignals(True)
            cmb_type.clear()
            cmb_type.addItem("— Select —", None)
            cat = cmb_cat.currentData()
            for wid, (wcat, name, _unit) in sorted(self._wt_catalog.items(), key=lambda kv: kv[1][1].lower()):
                if wcat == cat:
                    cmb_type.addItem(name, wid)
            idx = cmb_type.findData(keep_id)
            cmb_type.setCurrentIndex(idx if idx >= 0 else 0)
            cmb_type.blockSignals(False)
            update_unit()

        def update_unit():
            wid = cmb_type.currentData()
            lbl_unit.setText(self._wt_catalog.get(wid, ("", "", ""))[2] if wid else "")

        def changed(*_a):
            update_unit()
            self._refresh_work_type_list_state()
            self._mark_job_form_dirty()

        def remove():
            self._wt_rows.remove(entry)
            row_widget.setParent(None)
            row_widget.deleteLater()
            self._refresh_work_type_list_state()
            self._mark_job_form_dirty()

        idx = cmb_cat.findData(category or "INSTALLATION")
        cmb_cat.setCurrentIndex(idx if idx >= 0 else 0)
        fill_types(wt_id)
        cmb_cat.currentIndexChanged.connect(lambda *_a: (fill_types(), changed()))
        cmb_type.currentIndexChanged.connect(changed)
        spin.valueChanged.connect(changed)
        btn_rm.clicked.connect(remove)
        self._wt_rows.append(entry)
        self._wt_rows_layout.addWidget(row_widget)
        self._refresh_work_type_list_state()
        if focus:
            cmb_type.setFocus()
            self._mark_job_form_dirty()
        return entry

    def _refresh_work_type_list_state(self):
        rows = getattr(self, "_wt_rows", [])
        self._wt_empty.setVisible(not rows)
        # o quadro cresce com o número de linhas (nada de linhas espremidas)
        box = getattr(self.ui, "work_type_list", None)
        if box is not None:
            box.setMinimumHeight(len(rows) * 52 + (40 if not rows else 0) + 56)
        items = self._get_work_type_list()
        if items:
            counts = {}
            for cat, _w, _q in items:
                counts[cat] = counts.get(cat, 0) + 1
            labels = dict(CATEGORIES)
            self._wt_summary.setText("  ·  ".join(f"{labels.get(c, c)}: {n}" for c, n in counts.items()))
        else:
            self._wt_summary.setText("")

    def _get_work_type_list(self):
        """[(categoria, work_type_id, qty)] das linhas com serviço escolhido."""
        out = []
        for e in getattr(self, "_wt_rows", []):
            wid = e["type"].currentData()
            if wid:
                out.append((e["cat"].currentData(), wid, round(e["qty"].value(), 2)))
        return out

    def _set_work_type_list(self, items):
        loading = getattr(self, "_loading_job_form", False)
        self._loading_job_form = True
        for e in list(getattr(self, "_wt_rows", [])):
            e["widget"].setParent(None)
            e["widget"].deleteLater()
        self._wt_rows = []
        for cat, wid, qty in items:
            self._add_work_type_row(cat, wid, qty)
        self._loading_job_form = loading
        self._refresh_work_type_list_state()

    # ── banco ────────────────────────────────────────────────────────
    def _load_work_type_list(self, work_day_id, data=None):
        items = []
        if work_day_id and self._work_type_list_ready():
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                cur.execute("SELECT CATEGORY, WORK_TYPE_ID, QTY FROM work_day_work_types "
                            "WHERE WORK_DAY_ID=%s ORDER BY SORT_ORDER, ID", (work_day_id,))
                items = [(c, w, float(q or 0)) for c, w, q in cur.fetchall()]
                cur.close()
                conn.close()
            except (MySQLError, RuntimeError):
                items = []
        if not items and data:
            items = items_from_columns(data)
        self._set_work_type_list(items)

    def _load_work_types_from_latest_day(self, job_project_id):
        """Novo dia de um Job Code: sugere os mesmos serviços do último dia."""
        if not job_project_id:
            return
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT * FROM work_days WHERE JOB_PROJECT_ID=%s ORDER BY WORK_DATE DESC, ID DESC LIMIT 1",
                        (job_project_id,))
            day = cur.fetchone()
            cur.close()
            conn.close()
        except (MySQLError, RuntimeError):
            return
        if day:
            self._load_work_type_list(day["ID"], day)

    def _save_work_type_list(self, cursor, work_day_id):
        """Grava a lista completa (mesma transação do Save do job)."""
        if not work_day_id or not self._work_type_list_ready():
            return
        cursor.execute("DELETE FROM work_day_work_types WHERE WORK_DAY_ID=%s", (work_day_id,))
        for order, (cat, wid, qty) in enumerate(self._get_work_type_list()):
            cursor.execute("INSERT INTO work_day_work_types (WORK_DAY_ID, CATEGORY, WORK_TYPE_ID, QTY, SORT_ORDER) "
                           "VALUES (%s, %s, %s, %s, %s)", (work_day_id, cat, wid, qty, order))

    def _work_types_by_day(self, cursor, day_ids):
        """{work_day_id: [(categoria, work_type_id, qty), …]} para relatórios e invoices."""
        if not day_ids or not self._work_type_list_ready():
            return {}
        out = {}
        ids = list(day_ids)
        for i in range(0, len(ids), 500):
            chunk = ids[i:i + 500]
            cursor.execute(f"SELECT WORK_DAY_ID, CATEGORY, WORK_TYPE_ID, QTY FROM work_day_work_types "
                           f"WHERE WORK_DAY_ID IN ({','.join(['%s'] * len(chunk))}) ORDER BY SORT_ORDER, ID", chunk)
            for wd, cat, wid, qty in cursor.fetchall():
                out.setdefault(wd, []).append((cat, wid, qty))
        return out
