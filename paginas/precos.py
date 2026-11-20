# -*- coding: utf-8 -*-
"""
Tabela de preços por serviço (Service Rates) e cálculo automático do Value.

• Cada Work Type pode ter um preço PADRÃO (vale para todos) e preços
  combinados com um Contractor ou uma Company específicos.
• No Job: Value calculado = Σ (quantidade × preço) dos Work Types do dia.
  Ordem de procura do preço de cada serviço: Contractor do dia → Company
  do dia → padrão. Aparece embaixo do VALUE ("Rates: $812.50 · Use"); se o
  Value ainda estiver em $0, já entra sozinho.

Tabela: service_rates (WORK_TYPE_ID, ENTITY_TYPE, ENTITY_ID, RATE) — veja
migration-precos-faturas.sql.

Métodos da MainWindow (mixin) — veja main_.py.
"""

from PySide6.QtWidgets import QFormLayout

from app_common import *  # noqa: F401,F403
from paginas.visual import tabler_icon
from paginas.moderno import show_toast

_PRIMARY_BTN = ("QPushButton { background-color: #1565C0; color: #FFFFFF; border: none; border-radius: 6px; "
                "padding: 8px 16px; font-weight: 700; } QPushButton:hover { background-color: #1E88E5; }")
_HINT_BTN = ("QPushButton { background: transparent; border: none; color: #1565C0; font-size: 12px; "
             "font-weight: 600; text-align: left; padding: 2px 0; } QPushButton:hover { color: #1E88E5; "
             "text-decoration: underline; }")
_CATEGORY_LABEL = {"DEMOLITION": "Demolition", "INSTALLATION": "Installation", "PREPARATION": "Preparation",
                   "OTHERS": "Others", "REPARO": "Repair", "DELIVERY": "Delivery"}


def _money(v):
    return f"${float(v or 0):,.2f}"


class ServiceRatesMixin:
    # ── dados ───────────────────────────────────────────────────────
    def _load_service_rates(self, force=False):
        if getattr(self, "_service_rates", None) is not None and not force:
            return self._service_rates
        rates = {}
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT WORK_TYPE_ID, ENTITY_TYPE, ENTITY_ID, RATE FROM service_rates WHERE RATE > 0")
            for wt, etype, eid, rate in cur.fetchall():
                rates[(wt, etype, int(eid or 0))] = float(rate)
            cur.close()
            conn.close()
        except (MySQLError, RuntimeError):
            rates = {}
        self._service_rates = rates
        return rates

    def _rate_for(self, work_type_id, contractor_id=None, company_id=None):
        rates = self._load_service_rates()
        for key in (("Contractor", contractor_id), ("Company", company_id), ("Default", 0)):
            if key[1] is None:
                continue
            r = rates.get((work_type_id, key[0], int(key[1])))
            if r:
                return r
        return None

    def _calculate_value_from_rates(self, items, contractor_id=None, company_id=None):
        """(total, n_com_preço, n_sem_preço) para [(cat, work_type_id, qty)]."""
        total, priced, missing = 0.0, 0, 0
        for _cat, wid, qty in items:
            rate = self._rate_for(wid, contractor_id, company_id)
            if rate:
                total += float(qty or 0) * rate
                priced += 1
            else:
                missing += 1
        return round(total, 2), priced, missing

    # ── Job form ───────────────────────────────────────────────────
    def _setup_rate_hint(self):
        ui = self.ui
        btn = QPushButton()
        btn.setObjectName("btn_use_rate_value")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(_HINT_BTN)
        btn.setVisible(False)
        btn.clicked.connect(self._apply_rate_value)
        ui.grid_job_info.addWidget(btn, 5, 3, 1, 1, Qt.AlignmentFlag.AlignTop)
        ui.btn_use_rate_value = btn
        self._rate_value = 0.0
        for combo in (ui.cmb_contractor, ui.cmb_company_form):
            combo.currentIndexChanged.connect(lambda *_a: self._update_rate_hint())
        ui.dspn_value.valueChanged.connect(lambda *_a: self._update_rate_hint(auto_fill=False))

    def _update_rate_hint(self, auto_fill=True):
        btn = getattr(self.ui, "btn_use_rate_value", None)
        if btn is None:
            return
        items = self._get_work_type_list() if hasattr(self, "_get_work_type_list") else []
        if not items or not self._load_service_rates():
            btn.setVisible(False)
            self._rate_value = 0.0
            return
        total, priced, missing = self._calculate_value_from_rates(
            items, self.ui.cmb_contractor.currentData(), self.ui.cmb_company_form.currentData())
        self._rate_value = total
        if not priced:
            btn.setVisible(False)
            return
        current = round(self.ui.dspn_value.value(), 2)
        note = f" ({missing} without rate)" if missing else ""
        if abs(current - total) < 0.005:
            btn.setText(f"✓ Matches the rates{note}")
        else:
            btn.setText(f"Rates: {_money(total)}{note} · Use")
        btn.setToolTip("Quantity × rate of each Work Type (Contractor rate → Company rate → default rate). "
                       "Rates are set in Registrations → Service Rates.")
        btn.setVisible(True)
        # Value ainda em $0 — ou ainda com o valor que o próprio cálculo pôs —
        # acompanha o cálculo. Se o usuário digitou outro valor, não mexe.
        if getattr(self, "_loading_job_form", False):
            self._rate_autofilled = None  # job salvo: o Value dele vale como digitado
        last_auto = getattr(self, "_rate_autofilled", None)
        follows = current == 0 or (last_auto is not None and abs(current - last_auto) < 0.005)
        if auto_fill and follows and total > 0 and not getattr(self, "_loading_job_form", False):
            self._rate_autofilled = total
            self.ui.dspn_value.setValue(total)

    def _apply_rate_value(self):
        if self._rate_value > 0:
            self._rate_autofilled = self._rate_value
            self.ui.dspn_value.setValue(self._rate_value)
            if hasattr(self, "_mark_job_form_dirty"):
                self._mark_job_form_dirty()

    # ── cadastro de preços ─────────────────────────────────────────
    def open_service_rates_dialog(self):
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT ID, CATEGORY, NAME, UNIT FROM work_types "
                        "ORDER BY FIELD(CATEGORY,'INSTALLATION','DEMOLITION','PREPARATION','DELIVERY','OTHERS','REPARO'), NAME")
            work_types = cur.fetchall()
            cur.execute("SELECT ID, COALESCE(NULLIF(COMPANY_NAME, ''), FULL_NAME) FROM contractors ORDER BY 2")
            contractors = cur.fetchall()
            cur.execute("SELECT ID, COMPANY_NAME FROM companies WHERE COMPANY_NAME NOT LIKE '%%Select%%' ORDER BY 2")
            companies = cur.fetchall()
            cur.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not load the work types:\n{e}")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Service rates")
        dialog.resize(760, 680)
        layout = QVBoxLayout(dialog)
        intro = QLabel("How much you charge per unit of each service. The job Value is calculated from these "
                       "rates (quantity × rate). A rate agreed with a Contractor or Company wins over the default; "
                       "leave $0 to use the default.")
        intro.setWordWrap(True)
        intro.setStyleSheet("color:#475569;")
        layout.addWidget(intro)
        form = QFormLayout()
        who = QComboBox()
        who.setObjectName("cmb_rates_for")
        who.addItem("Default — everyone", "Default:0")
        for cid, name in contractors:
            who.addItem(f"Contractor: {name}", f"Contractor:{cid}")
        for cid, name in companies:
            who.addItem(f"Company: {name}", f"Company:{cid}")
        form.addRow("Rates for:", who)
        layout.addLayout(form)
        table = QTableWidget(len(work_types), 4)
        table.setObjectName("table_service_rates")
        table.setHorizontalHeaderLabels(["Category", "Work Type", "Unit", "Rate per unit"])
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(52)
        table.setColumnWidth(3, 150)
        spins = {}
        for r, (wid, cat, name, unit) in enumerate(work_types):
            for c, v in enumerate([_CATEGORY_LABEL.get(cat, cat), name, unit or ""]):
                item = QTableWidgetItem(v)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(r, c, item)
            spin = QDoubleSpinBox()
            spin.setDecimals(2)
            spin.setMaximum(99999.99)
            spin.setPrefix("$ ")
            table.setCellWidget(r, 3, spin)
            spins[wid] = spin
        layout.addWidget(table, 1)
        default_hint = QLabel()
        default_hint.setStyleSheet("color:#64748B; font-size:12px;")
        layout.addWidget(default_hint)
        bottom = QHBoxLayout()
        bottom.addStretch(1)
        btn_close = QPushButton("Close")
        btn_save = QPushButton("  Save rates")
        btn_save.setObjectName("btn_save_service_rates")
        btn_save.setIcon(tabler_icon("device-floppy", "#FFFFFF", 16))
        btn_save.setStyleSheet(_PRIMARY_BTN)
        bottom.addWidget(btn_close)
        bottom.addWidget(btn_save)
        layout.addLayout(bottom)
        if self._role_rule("read_only"):
            btn_save.setEnabled(False)
            btn_save.setToolTip("Your user has read-only access.")
        state = {"loaded_for": None}

        def load(*_a):
            etype, eid = who.currentData().split(":")
            eid = int(eid)
            rates = self._load_service_rates(force=True)
            for wid, spin in spins.items():
                spin.setValue(rates.get((wid, etype, eid), 0.0))
                default = rates.get((wid, "Default", 0))
                spin.setToolTip(f"Default: {_money(default)}" if etype != "Default" and default else "")
            state["loaded_for"] = (etype, eid)
            default_hint.setText("" if etype == "Default" else
                                 "Services left at $0 here use the default rate (hover a rate to see it).")

        def save():
            etype, eid = who.currentData().split(":")
            eid = int(eid)
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                n = 0
                for wid, spin in spins.items():
                    if spin.value() > 0:
                        cur.execute("INSERT INTO service_rates (WORK_TYPE_ID, ENTITY_TYPE, ENTITY_ID, RATE) "
                                    "VALUES (%s,%s,%s,%s) ON DUPLICATE KEY UPDATE RATE = VALUES(RATE)",
                                    (wid, etype, eid, spin.value()))
                        n += 1
                    else:
                        cur.execute("DELETE FROM service_rates WHERE WORK_TYPE_ID=%s AND ENTITY_TYPE=%s "
                                    "AND ENTITY_ID=%s", (wid, etype, eid))
                conn.commit()
                cur.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not save the rates:\n{e}")
                return
            self._load_service_rates(force=True)
            self._update_rate_hint(auto_fill=False)
            show_toast(f"{n} rate(s) saved for {who.currentText()}.", "success", self)

        who.currentIndexChanged.connect(load)
        btn_save.clicked.connect(save)
        btn_close.clicked.connect(dialog.accept)
        dialog._who, dialog._spins = who, spins  # usado nos testes
        load()
        dialog.exec()

    def _setup_rates_tools(self):
        btn = QPushButton()
        btn.setObjectName("btn_tool_service_rates")
        btn.clicked.connect(self.open_service_rates_dialog)
        self.ui.btn_tool_service_rates = btn
