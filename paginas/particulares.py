# -*- coding: utf-8 -*-
"""
Projects — trabalhos particulares e subcontratos (pedido do Viktor, 26/11/2026).

Um projeto é um Job Code com PROJECT_TYPE='PRIVATE' e preço fechado:
• Quem paga: um Client (cliente direto) ou uma Company (você é o subcontratado
  dela). O preço vem digitado ou de um Estimate.
• Plano de pagamento (project_payment_plan): sinal e parcelas. "Bill" cria a
  invoice no Receivables (client_invoices / company_invoices) com o PDF, e a
  partir daí tudo segue igual: Record payment, lembrete, invoice PAID IN FULL.
• Subcontratados que VOCÊ contrata (subcontractors / project_subs): combinado,
  pago e quanto falta. Cada pagamento também vira uma despesa SUBCONTRACTOR do
  projeto (entra no P&L).
• Dias de trabalho continuam no Job Records com o mesmo Job Code (equipe,
  materiais, fotos). Eles não aparecem em "Not invoiced yet": o projeto é
  cobrado pelo plano de pagamento, não por dia.
• Lucro: preço − materiais − helpers − subcontratados − outras despesas do projeto.

Métodos da MainWindow (mixin) — veja main_.py.
"""
from datetime import date

from PySide6.QtWidgets import QCheckBox, QFormLayout, QTabWidget, QCompleter

from app_common import *  # noqa: F401,F403
import arquivos
from paginas import visual
from paginas.moderno import show_toast
from paginas.visual import tabler_icon

STAGES = [("ESTIMATE", "Estimate"), ("SCHEDULED", "Scheduled"), ("IN_PROGRESS", "In progress"),
          ("DONE", "Done"), ("PAID", "Paid"), ("CANCELLED", "Cancelled")]
STAGE_LABEL = dict(STAGES)
STAGE_COLOR = {"ESTIMATE": "#64748B", "SCHEDULED": "#1565C0", "IN_PROGRESS": "#B26A00", "DONE": "#2E7D32",
               "PAID": "#6A1B9A", "CANCELLED": "#9AA5B1"}
PLAN_TEMPLATES = [
    ("50% deposit + 50% at the end", [("Deposit", 50), ("Final payment", 50)]),
    ("30% / 40% / 30%", [("Deposit", 30), ("Progress payment", 40), ("Final payment", 30)]),
    ("1/3 each", [("Deposit", 100 / 3), ("Progress payment", 100 / 3), ("Final payment", 100 / 3)]),
    ("100% at the end", [("Final payment", 100)]),
]
PAY_METHODS = ["Zelle", "Check", "Cash", "Venmo", "Card", "Other"]

_PRIMARY = ("QPushButton { background-color:#1565C0; color:#FFFFFF; border:none; border-radius:8px; "
            "padding:9px 16px; font-weight:700; } QPushButton:hover { background-color:#1E88E5; }")
_SMALL = ("QPushButton { background-color:#F0F4F8; color:#1C2B3A; border:1px solid #D0D7DE; border-radius:6px; "
          "padding:6px 12px; font-weight:600; } QPushButton:hover { background-color:#E3E8EE; } "
          "QPushButton:disabled { color:#9AA5B1; }")
_CARD = ("QFrame#{n} {{ background-color:#FFFFFF; border:1px solid #E3E8EE; border-radius:12px; }}"
         " QFrame#{n} QLabel {{ background: transparent; border: none; }}")

# o botão "Projects" entra na barra lateral logo depois de "Job Records"
if "btn_projects" not in visual.SIDEBAR_ITEMS:
    _items = list(visual.SIDEBAR_ITEMS.items())
    _pos = [k for k, _v in _items].index("btn_jobs") + 1 if "btn_jobs" in visual.SIDEBAR_ITEMS else len(_items)
    _items.insert(_pos, ("btn_projects", ("tool", "Projects")))
    visual.SIDEBAR_ITEMS.clear()
    visual.SIDEBAR_ITEMS.update(_items)


def money(v):
    return f"${float(v or 0):,.2f}"


class _Cancelled(Exception):
    """O usuário não quis criar um cliente/empresa novo ao salvar o projeto."""


def _qdate(d):
    return QDate(d.year, d.month, d.day) if d else QDate.currentDate()


class PrivateProjectsMixin:
    # ═════════════════════════ dados ═════════════════════════
    def _project_rows(self):
        conn = self._get_connection()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("""
                SELECT jp.ID, jp.CODE, COALESCE(jp.PROJECT_NAME, '') AS NAME, jp.CLIENT_ID, jp.COMPANY_ID,
                       cl.FULL_NAME AS CLIENT, co.COMPANY_NAME AS COMPANY, COALESCE(jp.JOB_ADDRESS, '') AS ADDRESS,
                       COALESCE(jp.CONTRACT_PRICE, 0) AS PRICE, COALESCE(jp.PROJECT_STAGE, 'ESTIMATE') AS STAGE,
                       jp.START_DATE, jp.DUE_DATE, jp.CREATED_AT
                FROM job_projects jp
                LEFT JOIN clients cl ON cl.ID = jp.CLIENT_ID
                LEFT JOIN companies co ON co.ID = jp.COMPANY_ID
                WHERE jp.PROJECT_TYPE = 'PRIVATE'
                ORDER BY FIELD(COALESCE(jp.PROJECT_STAGE, 'ESTIMATE'), 'IN_PROGRESS', 'SCHEDULED', 'ESTIMATE', 'DONE',
                               'PAID', 'CANCELLED'), jp.ID DESC""")
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    def _project_financials(self, pid, price=None):
        """Dinheiro do projeto: cobrado, recebido, custos e lucro."""
        conn = self._get_connection()
        cur = conn.cursor()
        f = {}
        try:
            if price is None:
                cur.execute("SELECT COALESCE(CONTRACT_PRICE, 0) FROM job_projects WHERE ID=%s", (pid,))
                price = float(cur.fetchone()[0] or 0)
            f["price"] = float(price or 0)
            cur.execute("""
                SELECT COALESCE(SUM(p.AMOUNT), 0),
                       COALESCE(SUM(CASE WHEN p.INVOICE_ID IS NOT NULL THEN p.AMOUNT ELSE 0 END), 0),
                       COALESCE(SUM(COALESCE(ci.AMOUNT_PAID, co.AMOUNT_PAID, 0)), 0)
                FROM project_payment_plan p
                LEFT JOIN client_invoices ci ON p.INVOICE_TYPE = 'Client' AND ci.ID = p.INVOICE_ID
                LEFT JOIN company_invoices co ON p.INVOICE_TYPE = 'Company' AND co.ID = p.INVOICE_ID
                WHERE p.JOB_PROJECT_ID = %s""", (pid,))
            plan, billed, received = cur.fetchone()
            f["plan"], f["billed"], f["received"] = float(plan), float(billed), float(received)
            cur.execute("SELECT COALESCE(SUM(m.QUANTITY * COALESCE(m.UNIT_PRICE, 0)), 0), "
                        "COALESCE(SUM(COALESCE(m.UNIT_PRICE, 0) = 0), 0) FROM job_materials m WHERE m.JOB_PROJECT_ID=%s",
                        (pid,))
            mat, no_price = cur.fetchone()
            f["materials"], f["materials_no_price"] = float(mat or 0), int(no_price or 0)
            cur.execute("""
                SELECT COALESCE(SUM(x.PAY), 0) FROM work_day_helpers x JOIN work_days wd ON wd.ID = x.WORK_DAY_ID
                WHERE wd.JOB_PROJECT_ID = %s AND COALESCE(wd.STATUS, '') <> 'CANCELLED'""", (pid,))
            crew = float(cur.fetchone()[0] or 0)
            cur.execute("""
                SELECT COALESCE(SUM(wd.HELPER_PAY), 0) FROM work_days wd
                WHERE wd.JOB_PROJECT_ID = %s AND COALESCE(wd.STATUS, '') <> 'CANCELLED'
                  AND NOT EXISTS (SELECT 1 FROM work_day_helpers x WHERE x.WORK_DAY_ID = wd.ID)""", (pid,))
            f["helpers"] = crew + float(cur.fetchone()[0] or 0)
            cur.execute("""
                SELECT COALESCE(SUM(s.AGREED_AMOUNT), 0),
                       COALESCE((SELECT SUM(sp.AMOUNT) FROM project_sub_payments sp
                                 JOIN project_subs s2 ON s2.ID = sp.PROJECT_SUB_ID WHERE s2.JOB_PROJECT_ID = %s), 0)
                FROM project_subs s WHERE s.JOB_PROJECT_ID = %s""", (pid, pid))
            agreed, paid = cur.fetchone()
            f["subs"], f["subs_paid"] = float(agreed or 0), float(paid or 0)
            f["subs_owed"] = max(f["subs"] - f["subs_paid"], 0)
            # outras despesas do projeto (as de subcontratado já entram em "subs")
            cur.execute("""
                SELECT COALESCE(SUM(e.AMOUNT), 0) FROM expenses e WHERE e.JOB_PROJECT_ID = %s
                  AND NOT EXISTS (SELECT 1 FROM project_sub_payments sp WHERE sp.EXPENSE_ID = e.ID)""", (pid,))
            f["expenses"] = float(cur.fetchone()[0] or 0)
            cur.execute("SELECT COUNT(*), COALESCE(SUM(DAY_FRACTION), 0) FROM work_days WHERE JOB_PROJECT_ID=%s "
                        "AND COALESCE(STATUS, '') <> 'CANCELLED'", (pid,))
            n, days = cur.fetchone()
            f["day_rows"], f["days"] = int(n or 0), float(days or 0)
        finally:
            cur.close()
            conn.close()
        f["costs"] = f["materials"] + f["helpers"] + max(f["subs"], f["subs_paid"]) + f["expenses"]
        f["profit"] = f["price"] - f["costs"]
        f["margin"] = (f["profit"] / f["price"] * 100) if f["price"] else 0.0
        f["to_receive"] = max(f["price"] - f["received"], 0)
        return f

    # ═════════════════════════ página ═════════════════════════
    def _setup_private_projects(self):
        ui = self.ui
        btn = QPushButton(ui.Left_container)
        btn.setObjectName("btn_projects")
        btn.setCheckable(True)
        btn.setMinimumSize(QSize(0, 56))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        lay = ui.verticalLayout_left
        lay.insertWidget(lay.indexOf(ui.btn_jobs) + 1, btn)
        ui.btn_projects = btn

        page = QWidget()
        page.setObjectName("pg_projects")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(14)

        bar = QHBoxLayout()
        b_new = QPushButton("  New project")
        b_new.setObjectName("btn_new_project")
        b_new.setIcon(tabler_icon("plus", "#FFFFFF", 16))
        b_new.setStyleSheet(_PRIMARY)
        b_new.clicked.connect(lambda *_a: self.open_project_dialog(None))
        bar.addWidget(b_new)
        self._txt_project_search = QLineEdit()
        self._txt_project_search.setPlaceholderText("Search project, customer, address, Job Code…")
        self._txt_project_search.setMinimumHeight(38)
        self._txt_project_search.textChanged.connect(lambda *_a: self.load_projects_page())
        bar.addWidget(self._txt_project_search, 1)
        self._cmb_project_stage = QComboBox()
        self._cmb_project_stage.setMinimumHeight(38)
        self._cmb_project_stage.addItem("Open projects", "OPEN")
        self._cmb_project_stage.addItem("All projects", "ALL")
        for key, label in STAGES:
            self._cmb_project_stage.addItem(label, key)
        self._cmb_project_stage.currentIndexChanged.connect(lambda *_a: self.load_projects_page())
        bar.addWidget(self._cmb_project_stage)
        b_subs = QPushButton("  Subcontractors")
        b_subs.setObjectName("btn_subcontractors")
        b_subs.setIcon(tabler_icon("users", "#37474F", 16))
        b_subs.setStyleSheet(_SMALL)
        b_subs.clicked.connect(lambda *_a: self.open_subcontractors_dialog())
        bar.addWidget(b_subs)
        outer.addLayout(bar)

        cards = QHBoxLayout()
        cards.setSpacing(14)
        self._project_card_values = {}
        for key, label, color in (("active", "Open projects", "#1C2B3A"), ("contract", "Contract value (open)", "#1565C0"),
                                  ("received", "Received", "#2E7D32"), ("to_receive", "Still to receive", "#E65100"),
                                  ("subs_owed", "Owed to subcontractors", "#C62828")):
            name = f"card_projects_{key}"
            card = QFrame()
            card.setObjectName(name)
            card.setStyleSheet(_CARD.format(n=name))
            v = QVBoxLayout(card)
            v.setContentsMargins(16, 12, 16, 12)
            val = QLabel("—")
            val.setStyleSheet(f"font-size:22px; font-weight:800; color:{color};")
            cap = QLabel(label)
            cap.setStyleSheet("font-size:12px; color:#6B7C93;")
            v.addWidget(val)
            v.addWidget(cap)
            cards.addWidget(card, 1)
            self._project_card_values[key] = val
        outer.addLayout(cards)

        t = QTableWidget(0, 11)
        t.setObjectName("table_projects")
        t.setHorizontalHeaderLabels(["Job Code", "Project", "Customer", "Type", "Stage", "Price", "Billed",
                                     "Received", "To receive", "Subs owed", "Profit"])
        t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        t.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        t.verticalHeader().setVisible(False)
        h = t.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        t.itemDoubleClicked.connect(lambda item: self.open_project_dialog(
            t.item(item.row(), 0).data(Qt.ItemDataRole.UserRole)))
        outer.addWidget(t, 1)
        self._table_projects = t
        hint = QLabel("Fixed-price jobs: your own clients, and companies that hire you as a subcontractor. "
                      "Double-click a project to open it. Work days, crew, materials and photos still go in "
                      "Job Records with the same Job Code.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#6B7C93;")
        outer.addWidget(hint)

        ui.Pages.addWidget(page)
        self._projects_index = ui.Pages.indexOf(page)
        self._projects_page = page
        btn.clicked.connect(lambda *_a: self._go_to_page(self._projects_index, ui.btn_projects))

    def load_projects_page(self):
        t = getattr(self, "_table_projects", None)
        if t is None:
            return
        try:
            rows = self._project_rows()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.warning(self, "Database Error", f"Could not load projects:\n{e}")
            return
        wanted = self._cmb_project_stage.currentData()
        search = self._txt_project_search.text().strip().lower()
        totals = {"active": 0, "contract": 0.0, "received": 0.0, "to_receive": 0.0, "subs_owed": 0.0}
        shown = []
        for r in rows:
            stage = r["STAGE"]
            customer = r["CLIENT"] or r["COMPANY"] or "—"
            try:
                fin = self._project_financials(r["ID"], r["PRICE"])
            except (MySQLError, RuntimeError):
                continue
            is_open = stage not in ("PAID", "CANCELLED")
            if is_open:
                totals["active"] += 1
                totals["contract"] += fin["price"]
                totals["to_receive"] += fin["to_receive"]
            if stage != "CANCELLED":
                totals["received"] += fin["received"]
                totals["subs_owed"] += fin["subs_owed"]
            if wanted == "OPEN" and not is_open or wanted not in ("OPEN", "ALL") and stage != wanted:
                continue
            text = " ".join([r["CODE"] or "", r["NAME"], customer, r["ADDRESS"]]).lower()
            if search and search not in text:
                continue
            shown.append((r, customer, fin))
        for key, val in totals.items():
            self._project_card_values[key].setText(str(val) if key == "active" else money(val))
        t.setSortingEnabled(False)
        t.setRowCount(len(shown))
        for i, (r, customer, fin) in enumerate(shown):
            kind = "Direct client" if r["CLIENT_ID"] else ("Sub for company" if r["COMPANY_ID"] else "—")
            vals = [r["CODE"], r["NAME"] or r["ADDRESS"], customer, kind, STAGE_LABEL.get(r["STAGE"], r["STAGE"]),
                    money(fin["price"]), money(fin["billed"]), money(fin["received"]), money(fin["to_receive"]),
                    money(fin["subs_owed"]), f"{money(fin['profit'])} ({fin['margin']:.0f}%)" if fin["price"] else "—"]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(v)
                if c == 0:
                    it.setData(Qt.ItemDataRole.UserRole, r["ID"])
                if c == 4:
                    it.setForeground(QColor(STAGE_COLOR.get(r["STAGE"], "#1C2B3A")))
                if c >= 5:
                    it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if c == 10 and fin["price"] and fin["profit"] < 0:
                    it.setForeground(QColor("#C62828"))
                if c == 9 and fin["subs_owed"] > 0:
                    it.setForeground(QColor("#C62828"))
                t.setItem(i, c, it)

    # ═════════════════════════ projeto ═════════════════════════
    def _payers(self, kind):
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            if kind == "Client":
                cur.execute("SELECT ID, FULL_NAME FROM clients WHERE FULL_NAME NOT LIKE '%%Select%%' ORDER BY FULL_NAME")
            else:
                cur.execute("SELECT ID, COMPANY_NAME FROM companies ORDER BY COMPANY_NAME")
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    def open_project_dialog(self, project_id=None):
        """Janela do projeto: Details · Payment plan · Subcontractors · Work & profit."""
        state = {"id": project_id, "code": None, "estimate_id": None}
        dialog = QDialog(self)
        dialog.setWindowTitle("New project" if not project_id else "Project")
        dialog.resize(980, 700)
        v = QVBoxLayout(dialog)
        head = QLabel()
        head.setStyleSheet("font-size:17px; font-weight:700;")
        v.addWidget(head)
        tabs = QTabWidget()
        tabs.setObjectName("tabs_project")
        v.addWidget(tabs, 1)

        # ── Details ──
        det = QWidget()
        form = QFormLayout(det)
        form.setVerticalSpacing(10)
        txt_name = QLineEdit()
        txt_name.setObjectName("txt_project_name")
        txt_name.setPlaceholderText("e.g. Kitchen + living room LVP")
        cmb_kind = QComboBox()
        cmb_kind.setObjectName("cmb_project_kind")
        cmb_kind.addItem("Client (my own customer)", "Client")
        cmb_kind.addItem("Company (they hire me as a sub)", "Company")
        cmb_payer = QComboBox()
        cmb_payer.setObjectName("cmb_project_payer")
        cmb_payer.setEditable(True)
        cmb_payer.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        cmb_payer.lineEdit().setPlaceholderText("Choose or type a new name")
        txt_address = QLineEdit()
        txt_address.setObjectName("txt_project_address")
        spin_price = QDoubleSpinBox()
        spin_price.setObjectName("spin_project_price")
        spin_price.setMaximum(9999999.99)
        spin_price.setPrefix("$ ")
        spin_price.setGroupSeparatorShown(True)
        d_start, d_due = QDateEdit(), QDateEdit()
        for d in (d_start, d_due):
            d.setCalendarPopup(True)
            d.setDisplayFormat("MM/dd/yyyy")
            d.setDate(QDate.currentDate())
            d.setMinimumWidth(140)
        chk_dates = QCheckBox("Dates not set yet")
        cmb_stage = QComboBox()
        cmb_stage.setObjectName("cmb_project_stage")
        for key, label in STAGES:
            cmb_stage.addItem(label, key)
        txt_notes = QTextEdit()
        txt_notes.setMaximumHeight(90)
        b_from_est = QPushButton("  Fill from an estimate…")
        b_from_est.setIcon(tabler_icon("file-type-pdf", "#37474F", 16))
        b_from_est.setStyleSheet(_SMALL)
        form.addRow("Project", txt_name)
        form.addRow("Who pays", cmb_kind)
        form.addRow("", cmb_payer)
        form.addRow("Job address", txt_address)
        form.addRow("Contract price", spin_price)
        drow = QHBoxLayout()
        drow.addWidget(QLabel("Start"))
        drow.addWidget(d_start)
        drow.addSpacing(12)
        drow.addWidget(QLabel("Finish by"))
        drow.addWidget(d_due)
        drow.addSpacing(12)
        drow.addWidget(chk_dates)
        drow.addStretch(1)
        form.addRow("Dates", drow)
        form.addRow("Stage", cmb_stage)
        form.addRow("Notes", txt_notes)
        erow = QHBoxLayout()
        erow.addWidget(b_from_est)
        erow.addStretch(1)
        form.addRow("", erow)
        tabs.addTab(det, "Details")
        chk_dates.toggled.connect(lambda on: (d_start.setEnabled(not on), d_due.setEnabled(not on)))

        def fill_payers(select_id=None, select_name=None):
            kind = cmb_kind.currentData()
            cmb_payer.blockSignals(True)
            cmb_payer.clear()
            try:
                for pid_, name in self._payers(kind):
                    cmb_payer.addItem(name, pid_)
            except (MySQLError, RuntimeError):
                pass
            comp = QCompleter([cmb_payer.itemText(i) for i in range(cmb_payer.count())], cmb_payer)
            comp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            comp.setFilterMode(Qt.MatchFlag.MatchContains)
            cmb_payer.setCompleter(comp)
            idx = cmb_payer.findData(select_id) if select_id else -1
            cmb_payer.setCurrentIndex(idx)
            if idx < 0:
                cmb_payer.setEditText(select_name or "")
            cmb_payer.blockSignals(False)
        cmb_kind.currentIndexChanged.connect(lambda *_a: fill_payers())

        # ── Payment plan ──
        plan_page = QWidget()
        pl = QVBoxLayout(plan_page)
        lbl_plan = QLabel()
        lbl_plan.setWordWrap(True)
        pl.addWidget(lbl_plan)
        plan_t = QTableWidget(0, 5)
        plan_t.setObjectName("table_project_plan")
        plan_t.setHorizontalHeaderLabels(["Payment", "%", "Amount", "Due", "Status"])
        plan_t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        plan_t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        plan_t.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        plan_t.verticalHeader().setVisible(False)
        plan_t.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        plan_t.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        pl.addWidget(plan_t, 1)
        prow = QHBoxLayout()
        cmb_tpl = QComboBox()
        cmb_tpl.setObjectName("cmb_plan_template")
        for name, _parts in PLAN_TEMPLATES:
            cmb_tpl.addItem(name)
        b_tpl = QPushButton("Use this plan")
        b_tpl.setObjectName("btn_plan_template")
        b_add = QPushButton("+ Add payment")
        b_add.setObjectName("btn_plan_add")
        b_del = QPushButton("Remove")
        b_bill = QPushButton("  Bill this payment")
        b_bill.setObjectName("btn_plan_bill")
        b_bill.setIcon(tabler_icon("send", "#FFFFFF", 16))
        b_bill.setStyleSheet(_PRIMARY)
        b_pay = QPushButton("Record payment")
        b_pay.setObjectName("btn_plan_record_payment")
        b_pdf = QPushButton("Open PDF")
        for b in (b_tpl, b_add, b_del, b_pay, b_pdf):
            b.setStyleSheet(_SMALL)
        for w_ in (cmb_tpl, b_tpl, b_add, b_del):
            prow.addWidget(w_)
        prow.addStretch(1)
        for w_ in (b_pdf, b_pay, b_bill):
            prow.addWidget(w_)
        pl.addLayout(prow)
        tabs.addTab(plan_page, "Payment plan")

        # ── Subcontractors ──
        sub_page = QWidget()
        sl = QVBoxLayout(sub_page)
        sinfo = QLabel("People or companies you hire for part of this project (e.g. carpet, tile, painting). "
                       "Payments to them are saved as project expenses too.")
        sinfo.setWordWrap(True)
        sinfo.setStyleSheet("color:#6B7C93;")
        sl.addWidget(sinfo)
        sub_t = QTableWidget(0, 5)
        sub_t.setObjectName("table_project_subs")
        sub_t.setHorizontalHeaderLabels(["Subcontractor", "Scope", "Agreed", "Paid", "Owed"])
        sub_t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        sub_t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        sub_t.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        sub_t.verticalHeader().setVisible(False)
        sub_t.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        sl.addWidget(sub_t, 1)
        srow = QHBoxLayout()
        b_sub_add = QPushButton("+ Add subcontractor")
        b_sub_add.setObjectName("btn_project_sub_add")
        b_sub_pay = QPushButton("  Pay subcontractor")
        b_sub_pay.setObjectName("btn_project_sub_pay")
        b_sub_pay.setIcon(tabler_icon("circle-check", "#FFFFFF", 16))
        b_sub_pay.setStyleSheet(_PRIMARY)
        b_sub_del = QPushButton("Remove")
        for b in (b_sub_add, b_sub_del):
            b.setStyleSheet(_SMALL)
        srow.addWidget(b_sub_add)
        srow.addWidget(b_sub_del)
        srow.addStretch(1)
        srow.addWidget(b_sub_pay)
        sl.addLayout(srow)
        tabs.addTab(sub_page, "Subcontractors")

        # ── Work & profit ──
        wp = QWidget()
        wl = QVBoxLayout(wp)
        lbl_profit = QLabel()
        lbl_profit.setObjectName("lbl_project_profit")
        lbl_profit.setTextFormat(Qt.TextFormat.RichText)
        lbl_profit.setWordWrap(True)
        wl.addWidget(lbl_profit)
        days_t = QTableWidget(0, 5)
        days_t.setObjectName("table_project_days")
        days_t.setHorizontalHeaderLabels(["Date", "Status", "Crew", "Day", "Note"])
        days_t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        days_t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        days_t.verticalHeader().setVisible(False)
        days_t.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        wl.addWidget(days_t, 1)
        wrow = QHBoxLayout()
        b_log = QPushButton("  Log a work day for this project")
        b_log.setObjectName("btn_project_log_day")
        b_log.setIcon(tabler_icon("plus", "#37474F", 16))
        b_log.setStyleSheet(_SMALL)
        wrow.addWidget(b_log)
        wrow.addStretch(1)
        wl.addLayout(wrow)
        tabs.addTab(wp, "Work && profit")

        # ── rodapé ──
        foot = QHBoxLayout()
        lbl_status = QLabel()
        lbl_status.setStyleSheet("color:#6B7C93;")
        foot.addWidget(lbl_status, 1)
        b_close = QPushButton("Close")
        b_save = QPushButton("  Save project")
        b_save.setObjectName("btn_save_project")
        b_save.setIcon(tabler_icon("device-floppy", "#FFFFFF", 16))
        b_save.setStyleSheet(_PRIMARY)
        foot.addWidget(b_close)
        foot.addWidget(b_save)
        v.addLayout(foot)

        plan_rows, sub_rows = [], []

        # ── carregar ──
        def kind_now():
            return cmb_kind.currentData()

        def load_details():
            if not state["id"]:
                head.setText("New project")
                fill_payers()
                cmb_stage.setCurrentIndex(0)
                chk_dates.setChecked(True)
                return
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT * FROM job_projects WHERE ID=%s", (state["id"],))
            r = cur.fetchone()
            cur.close()
            conn.close()
            state["code"] = r["CODE"]
            txt_name.setText(r.get("PROJECT_NAME") or "")
            cmb_kind.blockSignals(True)
            cmb_kind.setCurrentIndex(1 if r["COMPANY_ID"] and not r["CLIENT_ID"] else 0)
            cmb_kind.blockSignals(False)
            fill_payers(r["COMPANY_ID"] if kind_now() == "Company" else r["CLIENT_ID"])
            txt_address.setText(r.get("JOB_ADDRESS") or "")
            spin_price.setValue(float(r.get("CONTRACT_PRICE") or 0))
            chk_dates.setChecked(not r.get("START_DATE"))
            d_start.setDate(_qdate(r.get("START_DATE")))
            d_due.setDate(_qdate(r.get("DUE_DATE")))
            cmb_stage.setCurrentIndex(max(0, cmb_stage.findData(r.get("PROJECT_STAGE") or "ESTIMATE")))
            txt_notes.setPlainText(r.get("PROJECT_NOTES") or "")
            head.setText(f"{r['CODE']} — {r.get('PROJECT_NAME') or r.get('JOB_ADDRESS') or ''}")
            dialog.setWindowTitle(f"Project {r['CODE']}")

        def load_plan():
            plan_rows.clear()
            plan_t.setRowCount(0)
            if not state["id"]:
                lbl_plan.setText("Save the project first, then set how the customer pays (deposit and installments).")
                return
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT p.ID, p.NAME, p.AMOUNT, p.DUE_DATE, p.INVOICE_TYPE, p.INVOICE_ID,
                       COALESCE(ci.STATUS, co.STATUS), COALESCE(ci.AMOUNT_PAID, co.AMOUNT_PAID, 0),
                       COALESCE(ci.PDF_PATH, co.PDF_PATH)
                FROM project_payment_plan p
                LEFT JOIN client_invoices ci ON p.INVOICE_TYPE = 'Client' AND ci.ID = p.INVOICE_ID
                LEFT JOIN company_invoices co ON p.INVOICE_TYPE = 'Company' AND co.ID = p.INVOICE_ID
                WHERE p.JOB_PROJECT_ID = %s ORDER BY p.SORT_ORDER, p.ID""", (state["id"],))
            rows = cur.fetchall()
            cur.close()
            conn.close()
            price = spin_price.value()
            plan_t.setRowCount(len(rows))
            for i, (rid, name, amount, due, itype, iid, istatus, ipaid, pdf) in enumerate(rows):
                amount = float(amount or 0)
                if not iid:
                    st = "Not billed yet"
                    color = "#6B7C93"
                elif istatus == "RECEIVED":
                    st = f"Paid ✔ — invoice #{iid}"
                    color = "#2E7D32"
                elif istatus == "PARTIAL":
                    st = f"Partially paid ({money(ipaid)}) — invoice #{iid}"
                    color = "#1565C0"
                else:
                    st = f"Billed, waiting — invoice #{iid}"
                    color = "#E65100"
                pct = f"{amount / price * 100:.0f}%" if price else ""
                vals = [name, pct, money(amount), due.strftime("%m/%d/%Y") if due else "", st]
                for c, val in enumerate(vals):
                    it = QTableWidgetItem(val)
                    if c == 4:
                        it.setForeground(QColor(color))
                    if c in (1, 2):
                        it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    plan_t.setItem(i, c, it)
                plan_rows.append({"id": rid, "name": name, "amount": amount, "due": due, "itype": itype,
                                  "iid": iid, "status": istatus, "pdf": pdf})
            total = sum(p["amount"] for p in plan_rows)
            diff = round(price - total, 2)
            msg = f"Contract price {money(price)} · plan total {money(total)}"
            if plan_rows and abs(diff) >= 0.01:
                msg += (f" · <span style='color:#C62828'><b>{money(abs(diff))} "
                        f"{'missing from' if diff > 0 else 'more than'} the price</b></span>")
            elif not plan_rows:
                msg += " · choose a plan below (for example 50% deposit + 50% at the end)."
            lbl_plan.setText(msg)
            plan_selection_changed()

        def load_subs():
            sub_rows.clear()
            sub_t.setRowCount(0)
            if not state["id"]:
                return
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT s.ID, sc.NAME, COALESCE(s.SCOPE, ''), s.AGREED_AMOUNT,
                       COALESCE((SELECT SUM(AMOUNT) FROM project_sub_payments WHERE PROJECT_SUB_ID = s.ID), 0)
                FROM project_subs s JOIN subcontractors sc ON sc.ID = s.SUBCONTRACTOR_ID
                WHERE s.JOB_PROJECT_ID = %s ORDER BY s.ID""", (state["id"],))
            rows = cur.fetchall()
            cur.close()
            conn.close()
            sub_t.setRowCount(len(rows))
            for i, (sid, name, scope, agreed, paid) in enumerate(rows):
                owed = max(float(agreed) - float(paid), 0)
                for c, val in enumerate([name, scope, money(agreed), money(paid), money(owed)]):
                    it = QTableWidgetItem(val)
                    if c >= 2:
                        it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    if c == 4 and owed > 0:
                        it.setForeground(QColor("#C62828"))
                    sub_t.setItem(i, c, it)
                sub_rows.append({"id": sid, "name": name, "scope": scope, "agreed": float(agreed),
                                 "paid": float(paid), "owed": owed})

        def load_work():
            days_t.setRowCount(0)
            if not state["id"]:
                lbl_profit.setText("Save the project to see its costs and profit.")
                return
            f = self._project_financials(state["id"], spin_price.value())
            warn = (f"<br><span style='color:#B26A00'>⚠ {f['materials_no_price']} material line(s) without a price — "
                    f"material cost is too low.</span>" if f["materials_no_price"] else "")
            color = "#2E7D32" if f["profit"] >= 0 else "#C62828"
            per_day = f" · {money(f['profit'] / f['days'])} per day worked" if f["days"] else ""
            lbl_profit.setText(
                f"<table cellspacing='0' cellpadding='3'>"
                f"<tr><td>Contract price</td><td align='right'><b>{money(f['price'])}</b></td></tr>"
                f"<tr><td>− Materials</td><td align='right'>{money(f['materials'])}</td></tr>"
                f"<tr><td>− Helpers (crew pay)</td><td align='right'>{money(f['helpers'])}</td></tr>"
                f"<tr><td>− Subcontractors</td><td align='right'>{money(max(f['subs'], f['subs_paid']))}</td></tr>"
                f"<tr><td>− Other project expenses</td><td align='right'>{money(f['expenses'])}</td></tr>"
                f"<tr><td><b>Profit</b></td><td align='right'><b style='color:{color}'>{money(f['profit'])} "
                f"({f['margin']:.0f}%)</b></td></tr></table>"
                f"Received so far {money(f['received'])} · still to receive {money(f['to_receive'])} · "
                f"{f['days']:g} day(s) worked{per_day}{warn}")
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT wd.ID, wd.WORK_DATE, COALESCE(wd.STATUS, ''), COALESCE(wd.DAY_FRACTION, 1), COALESCE(wd.NOTE, ''),
                       (SELECT GROUP_CONCAT(h.FULL_NAME ORDER BY h.FULL_NAME SEPARATOR ', ')
                        FROM work_day_helpers x JOIN helpers h ON h.ID = x.HELPER_ID WHERE x.WORK_DAY_ID = wd.ID)
                FROM work_days wd WHERE wd.JOB_PROJECT_ID = %s ORDER BY wd.WORK_DATE DESC, wd.ID DESC""",
                        (state["id"],))
            rows = cur.fetchall()
            cur.close()
            conn.close()
            days_t.setRowCount(len(rows))
            for i, (wid, wdate, st, frac, note, crew) in enumerate(rows):
                for c, val in enumerate([wdate.strftime("%m/%d/%Y"), st.replace("_", " ").title(), crew or "—",
                                         "Full" if float(frac) >= 1 else f"{float(frac):g}", note]):
                    it = QTableWidgetItem(val)
                    if c == 0:
                        it.setData(Qt.ItemDataRole.UserRole, (wid, wdate))
                    days_t.setItem(i, c, it)

        def reload_all():
            load_plan()
            load_subs()
            load_work()
            for i in (1, 2, 3):
                tabs.setTabEnabled(i, bool(state["id"]))
            lbl_status.setText("" if state["id"] else "Fill in the details and click Save project.")

        # ── salvar ──
        def payer_id(cur):
            kind = kind_now()
            name = cmb_payer.currentText().strip()
            if not name:
                return None
            idx = cmb_payer.currentIndex()
            if idx >= 0 and cmb_payer.itemText(idx).strip().lower() == name.lower() and cmb_payer.itemData(idx):
                return cmb_payer.itemData(idx)
            # procura no banco sem diferenciar maiúsculas/espaços — nunca cria cliente repetido
            key = " ".join(name.split()).lower()
            if kind == "Client":
                cur.execute("SELECT ID FROM clients WHERE LOWER(TRIM(REPLACE(FULL_NAME, '  ', ' '))) = %s "
                            "ORDER BY ID LIMIT 1", (key,))
            else:
                cur.execute("SELECT ID FROM companies WHERE LOWER(TRIM(REPLACE(COMPANY_NAME, '  ', ' '))) = %s "
                            "ORDER BY ID LIMIT 1", (key,))
            row = cur.fetchone()
            if row:
                return row[0]
            answer = QMessageBox.question(
                dialog, "New " + ("client" if kind == "Client" else "company"),
                f"There is no {'client' if kind == 'Client' else 'company'} called “{name}” yet.\n\n"
                f"Create it now? (Choose No to pick one from the list.)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes)
            if answer != QMessageBox.StandardButton.Yes:
                raise _Cancelled()
            if kind == "Client":
                cur.execute("INSERT INTO clients (FULL_NAME, ADDRESS) VALUES (%s, %s)", (name, txt_address.text().strip()))
            else:
                cur.execute("INSERT INTO companies (COMPANY_NAME) VALUES (%s)", (name,))
            return cur.lastrowid

        def save(silent=False):
            name = txt_name.text().strip()
            if not name and not txt_address.text().strip():
                QMessageBox.information(dialog, "Project", "Type a project name or the job address.")
                return False
            if not cmb_payer.currentText().strip():
                QMessageBox.information(dialog, "Project", "Choose who pays for this project (client or company).")
                return False
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                pid_payer = payer_id(cur)
                client_id = pid_payer if kind_now() == "Client" else None
                company_id = pid_payer if kind_now() == "Company" else None
                start = None if chk_dates.isChecked() else d_start.date().toPython()
                due = None if chk_dates.isChecked() else d_due.date().toPython()
                vals = (name or None, client_id, company_id, txt_address.text().strip() or None, spin_price.value(),
                        cmb_stage.currentData(), start, due, txt_notes.toPlainText().strip() or None)
                if state["id"]:
                    cur.execute("""UPDATE job_projects SET PROJECT_NAME=%s, CLIENT_ID=%s, COMPANY_ID=%s, JOB_ADDRESS=%s,
                                   CONTRACT_PRICE=%s, PROJECT_STAGE=%s, START_DATE=%s, DUE_DATE=%s, PROJECT_NOTES=%s,
                                   PROJECT_TYPE='PRIVATE' WHERE ID=%s""", vals + (state["id"],))
                else:
                    code = self._next_code(cur, "job_projects", "JB")
                    cur.execute("""INSERT INTO job_projects (PROJECT_NAME, CLIENT_ID, COMPANY_ID, JOB_ADDRESS, CONTRACT_PRICE,
                                   PROJECT_STAGE, START_DATE, DUE_DATE, PROJECT_NOTES, PROJECT_TYPE, CODE, STATUS)
                                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'PRIVATE',%s,'ACTIVE')""", vals + (code,))
                    state["id"], state["code"] = cur.lastrowid, code
                if state["estimate_id"]:
                    cur.execute("UPDATE estimates SET STATUS='CONVERTED', JOB_PROJECT_ID=%s, CLIENT_ID=COALESCE(CLIENT_ID, %s) "
                                "WHERE ID=%s", (state["id"], client_id, state["estimate_id"]))
                    state["estimate_id"] = None
                conn.commit()
                cur.close()
                conn.close()
            except _Cancelled:
                conn.rollback()
                conn.close()
                return False
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not save the project:\n{e}")
                return False
            load_details()
            reload_all()
            self.load_projects_page()
            if hasattr(self, "_refresh_job_code_completer"):
                try:
                    self._refresh_job_code_completer()
                except Exception:
                    pass
            if not silent:
                show_toast(f"Project {state['code']} saved.", "success", self)
            return True

        def from_estimate():
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT ID, CODE, COALESCE(CLIENT_NAME, ''), COALESCE(JOB_ADDRESS, ''), TOTAL, STATUS, CLIENT_ID "
                        "FROM estimates WHERE STATUS <> 'CONVERTED' ORDER BY ID DESC")
            ests = cur.fetchall()
            cur.close()
            conn.close()
            if not ests:
                QMessageBox.information(dialog, "Estimates", "There is no open estimate to use.")
                return
            labels = [f"{c} — {n} — {a} — {money(t)} ({s})" for _i, c, n, a, t, s, _cid in ests]
            choice, ok = QInputDialog.getItem(dialog, "Fill from an estimate", "Estimate:", labels, 0, False)
            if not ok:
                return
            eid, ecode, ename, eaddr, etotal, _s, ecid = ests[labels.index(choice)]
            cmb_kind.setCurrentIndex(0)
            fill_payers(ecid, ename)
            if not ecid:
                cmb_payer.setEditText(ename)
            txt_address.setText(eaddr)
            spin_price.setValue(float(etotal or 0))
            if not txt_name.text().strip():
                txt_name.setText(f"{eaddr or ename} (from {ecode})")
            state["estimate_id"] = eid
            lbl_status.setText(f"Filled from estimate {ecode} — it is marked CONVERTED when you save.")

        # ── plano de pagamento ──
        def selected_plan():
            r = plan_t.currentRow()
            return plan_rows[r] if 0 <= r < len(plan_rows) else None

        def plan_selection_changed():
            p = selected_plan()
            b_bill.setEnabled(bool(p) and not p["iid"])
            b_del.setEnabled(bool(p) and not p["iid"])
            b_pay.setEnabled(bool(p) and bool(p["iid"]) and p["status"] != "RECEIVED")
            b_pdf.setEnabled(bool(p) and bool(p["iid"]))
        plan_t.itemSelectionChanged.connect(plan_selection_changed)

        def use_template():
            if any(p["iid"] for p in plan_rows):
                QMessageBox.information(dialog, "Payment plan", "Some payments were already billed — add or remove "
                                        "the others one by one.")
                return
            if not save(silent=True):
                return
            price = spin_price.value()
            if price <= 0:
                QMessageBox.information(dialog, "Payment plan", "Type the contract price first.")
                return
            _name, parts = PLAN_TEMPLATES[cmb_tpl.currentIndex()]
            amounts = [round(price * pct / 100, 2) for _n, pct in parts]
            amounts[-1] = round(price - sum(amounts[:-1]), 2)  # a última parcela fecha o valor certinho
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM project_payment_plan WHERE JOB_PROJECT_ID=%s AND INVOICE_ID IS NULL", (state["id"],))
            for i, ((pname, _pct), amt) in enumerate(zip(parts, amounts)):
                cur.execute("INSERT INTO project_payment_plan (JOB_PROJECT_ID, NAME, AMOUNT, SORT_ORDER) "
                            "VALUES (%s,%s,%s,%s)", (state["id"], pname, amt, i))
            conn.commit()
            cur.close()
            conn.close()
            load_plan()

        def add_payment_row():
            if not save(silent=True):
                return
            d = QDialog(dialog)
            d.setWindowTitle("Add payment")
            f = QFormLayout(d)
            t_name = QLineEdit("Progress payment")
            sp = QDoubleSpinBox()
            sp.setMaximum(9999999.99)
            sp.setPrefix("$ ")
            remaining = max(spin_price.value() - sum(p["amount"] for p in plan_rows), 0)
            sp.setValue(remaining)
            dd = QDateEdit(QDate.currentDate())
            dd.setCalendarPopup(True)
            dd.setDisplayFormat("MM/dd/yyyy")
            f.addRow("Name", t_name)
            f.addRow("Amount", sp)
            f.addRow("Due", dd)
            row = QHBoxLayout()
            ok, cancel = QPushButton("Add"), QPushButton("Cancel")
            ok.setObjectName("btn_plan_add_ok")
            row.addStretch(1)
            row.addWidget(cancel)
            row.addWidget(ok)
            f.addRow(row)
            ok.clicked.connect(d.accept)
            cancel.clicked.connect(d.reject)
            d._fields = (t_name, sp, dd)
            if d.exec() != QDialog.DialogCode.Accepted or sp.value() <= 0:
                return
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO project_payment_plan (JOB_PROJECT_ID, NAME, AMOUNT, DUE_DATE, SORT_ORDER) "
                        "VALUES (%s,%s,%s,%s,%s)", (state["id"], t_name.text().strip() or "Payment", sp.value(),
                                                    dd.date().toPython(), len(plan_rows)))
            conn.commit()
            cur.close()
            conn.close()
            load_plan()

        def remove_payment_row():
            p = selected_plan()
            if not p or p["iid"]:
                return
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM project_payment_plan WHERE ID=%s AND INVOICE_ID IS NULL", (p["id"],))
            conn.commit()
            cur.close()
            conn.close()
            load_plan()

        def bill_payment():
            p = selected_plan()
            if not p or p["iid"]:
                return
            if not save(silent=True):
                return
            if hasattr(self, "_confirm_bank_info_ready") and not self._confirm_bank_info_ready(dialog):
                return
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                kind, iid, path = self._bill_project_payment(state["id"], p["id"])
            except Exception as e:
                QApplication.restoreOverrideCursor()
                logging.getLogger("vl_flooring").exception("project invoice failed")
                QMessageBox.critical(dialog, "Invoice", f"Could not create the invoice:\n{e}")
                return
            QApplication.restoreOverrideCursor()
            if cmb_stage.currentData() == "ESTIMATE":
                cmb_stage.setCurrentIndex(cmb_stage.findData("SCHEDULED"))
                save(silent=True)
            load_plan()
            self.load_projects_page()
            if hasattr(self, "load_receivables_dashboard"):
                try:
                    self.load_contractor_invoices()
                except Exception:
                    pass
            info = self._invoice_partner(kind, iid) if hasattr(self, "_invoice_partner") else None
            if info is not None and hasattr(self, "_compose_dialog"):
                subject = f"Invoice #{iid} — {p['name']} — {company_settings.COMPANY_NAME}"
                body = (f"Hi {info['name'] or 'there'},\n\nAttached is invoice #{iid} for "
                        f"{txt_name.text().strip() or txt_address.text().strip()}: {p['name']}, {money(p['amount'])}.\n\n"
                        f"Thank you!\n{company_settings.COMPANY_NAME}")
                if self._compose_dialog(dialog, "Send invoice", info["email"], subject, body, attachments=(path,),
                                        note=f"Invoice #{iid} was created. Send it now?"):
                    return
            show_toast(f"Invoice #{iid} created ({money(p['amount'])}).", "success", self)

        def record_payment():
            p = selected_plan()
            if p and p["iid"]:
                self.open_record_payment_dialog(preselect=(p["itype"], p["iid"]))
                load_plan()
                load_work()
                auto_paid_stage()
                self.load_projects_page()

        def open_pdf():
            p = selected_plan()
            if not p or not p["iid"]:
                return
            path = arquivos.resolve(p["pdf"]) if p["pdf"] else None
            if path and os.path.exists(path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(path))
            else:
                QMessageBox.information(dialog, "PDF", "The PDF of this invoice was not found.")

        def auto_paid_stage():
            """Tudo pago e o plano cobre o preço → etapa Paid."""
            if not plan_rows or cmb_stage.currentData() in ("PAID", "CANCELLED"):
                return
            total = sum(p["amount"] for p in plan_rows)
            if all(p["status"] == "RECEIVED" for p in plan_rows) and total >= spin_price.value() - 0.01:
                cmb_stage.setCurrentIndex(cmb_stage.findData("PAID"))
                save(silent=True)
                show_toast(f"{state['code']} is paid in full 🎉", "success", self)

        # ── subcontratados ──
        def selected_sub():
            r = sub_t.currentRow()
            return sub_rows[r] if 0 <= r < len(sub_rows) else None

        def add_sub():
            if not save(silent=True):
                return
            result = self._ask_project_sub(dialog)
            if not result:
                return
            sub_id, scope, agreed = result
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO project_subs (JOB_PROJECT_ID, SUBCONTRACTOR_ID, SCOPE, AGREED_AMOUNT) "
                        "VALUES (%s,%s,%s,%s)", (state["id"], sub_id, scope, agreed))
            conn.commit()
            cur.close()
            conn.close()
            load_subs()
            load_work()

        def pay_sub():
            s = selected_sub()
            if not s:
                QMessageBox.information(dialog, "Subcontractor", "Select the subcontractor first.")
                return
            d = QDialog(dialog)
            d.setWindowTitle(f"Pay {s['name']}")
            f = QFormLayout(d)
            sp = QDoubleSpinBox()
            sp.setMaximum(9999999.99)
            sp.setPrefix("$ ")
            sp.setValue(s["owed"])
            dd = QDateEdit(QDate.currentDate())
            dd.setCalendarPopup(True)
            dd.setDisplayFormat("MM/dd/yyyy")
            cm = QComboBox()
            cm.addItems(PAY_METHODS)
            tn = QLineEdit()
            f.addRow("Amount", sp)
            f.addRow("Date", dd)
            f.addRow("Method", cm)
            f.addRow("Note", tn)
            row = QHBoxLayout()
            ok, cancel = QPushButton("Save payment"), QPushButton("Cancel")
            ok.setObjectName("btn_sub_pay_ok")
            row.addStretch(1)
            row.addWidget(cancel)
            row.addWidget(ok)
            f.addRow(row)
            ok.clicked.connect(d.accept)
            cancel.clicked.connect(d.reject)
            d._fields = (sp, dd, cm, tn)
            if d.exec() != QDialog.DialogCode.Accepted or sp.value() <= 0:
                return
            try:
                self._record_sub_payment(state["id"], s["id"], s["name"], s["scope"], sp.value(),
                                         dd.date().toPython(), cm.currentText(), tn.text().strip())
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", str(e))
                return
            load_subs()
            load_work()
            self.load_projects_page()
            show_toast(f"Paid {money(sp.value())} to {s['name']}.", "success", self)

        def remove_sub():
            s = selected_sub()
            if not s:
                return
            if s["paid"] > 0:
                QMessageBox.information(dialog, "Subcontractor", "This subcontractor already has payments — it can't "
                                        "be removed.")
                return
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM project_subs WHERE ID=%s", (s["id"],))
            conn.commit()
            cur.close()
            conn.close()
            load_subs()
            load_work()

        # ── dias ──
        def log_day():
            if not save(silent=True):
                return
            dialog.accept()
            self._go_to_page(1, self.ui.btn_jobs)
            self.new_job_record()
            self.ui.tabWidget_jobs.setCurrentWidget(self.ui.tab_jobs_master)
            self.ui.cmb_job_code.setEditText(state["code"])
            if hasattr(self, "_on_job_code_editing_finished"):
                try:
                    self._on_job_code_editing_finished()
                except Exception:
                    pass

        def open_day(item):
            data = days_t.item(item.row(), 0).data(Qt.ItemDataRole.UserRole)
            if data:
                dialog.accept()
                self._open_job_by_id(*data)

        b_save.clicked.connect(lambda *_a: save())
        b_close.clicked.connect(dialog.accept)
        b_from_est.clicked.connect(from_estimate)
        b_tpl.clicked.connect(use_template)
        b_add.clicked.connect(add_payment_row)
        b_del.clicked.connect(remove_payment_row)
        b_bill.clicked.connect(bill_payment)
        b_pay.clicked.connect(record_payment)
        b_pdf.clicked.connect(open_pdf)
        b_sub_add.clicked.connect(add_sub)
        b_sub_pay.clicked.connect(pay_sub)
        b_sub_del.clicked.connect(remove_sub)
        b_log.clicked.connect(log_day)
        days_t.itemDoubleClicked.connect(open_day)
        spin_price.valueChanged.connect(lambda *_a: load_plan() if state["id"] else None)

        load_details()
        reload_all()
        # usados nos testes
        dialog._state, dialog._save = state, save
        dialog._widgets = {"name": txt_name, "kind": cmb_kind, "payer": cmb_payer, "address": txt_address,
                           "price": spin_price, "stage": cmb_stage, "tabs": tabs, "plan": plan_t, "subs": sub_t,
                           "days": days_t, "profit": lbl_profit, "plan_label": lbl_plan, "template": cmb_tpl}
        dialog._actions = {"template": use_template, "bill": bill_payment, "record": record_payment,
                           "add_sub": add_sub, "pay_sub": pay_sub, "from_estimate": from_estimate,
                           "reload": reload_all}
        dialog.exec()
        self.load_projects_page()

    # ═════════════════════════ cobrança ═════════════════════════
    def _bill_project_payment(self, project_id, plan_id):
        """Cria a invoice (Client ou Company) de uma parcela, gera o PDF e liga à parcela.
        Devolve (tipo, id da invoice, caminho do PDF)."""
        conn = self._get_connection()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("SELECT * FROM job_projects WHERE ID=%s", (project_id,))
            pr = cur.fetchone()
            cur.execute("SELECT * FROM project_payment_plan WHERE ID=%s AND JOB_PROJECT_ID=%s", (plan_id, project_id))
            pl = cur.fetchone()
            if not pr or not pl:
                raise RuntimeError("Payment not found.")
            if pl["INVOICE_ID"]:
                raise RuntimeError("This payment was already billed.")
            kind = "Client" if pr["CLIENT_ID"] else "Company"
            payer = pr["CLIENT_ID"] or pr["COMPANY_ID"]
            if not payer:
                raise RuntimeError("Choose who pays for the project first.")
            table, fk = ("client_invoices", "CLIENT_ID") if kind == "Client" else ("company_invoices", "COMPANY_ID")
            today = date.today()
            amount = float(pl["AMOUNT"] or 0)
            cur.execute(f"INSERT INTO {table} ({fk}, PERIOD_FROM, PERIOD_TO, JOBS_TOTAL, TOTAL_AMOUNT, AMOUNT_PAID, STATUS, "
                        f"PDF_PATH, ADJUSTMENT_NOTE) VALUES (%s,%s,%s,%s,%s,0,'PENDING','',%s)",
                        (payer, pr.get("START_DATE") or today, today, amount, amount,
                         f"Project {pr['CODE']} — {pl['NAME']}"[:255]))
            iid = cur.lastrowid
            cur.execute("UPDATE project_payment_plan SET INVOICE_TYPE=%s, INVOICE_ID=%s WHERE ID=%s", (kind, iid, plan_id))
            conn.commit()
        finally:
            cur.close()
            conn.close()
        path = self._build_project_invoice_pdf(kind, iid)
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute(f"UPDATE {table} SET PDF_PATH=%s WHERE ID=%s", (path, iid))
        conn.commit()
        cur.close()
        conn.close()
        return kind, iid, path

    def _project_invoice_context(self, kind, invoice_id):
        """Dados de uma invoice de parcela de projeto, ou None se não for de projeto."""
        conn = self._get_connection()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("SHOW TABLES LIKE 'project_payment_plan'")
            if cur.fetchone() is None:
                return None
            cur.execute("SELECT * FROM project_payment_plan WHERE INVOICE_TYPE=%s AND INVOICE_ID=%s", (kind, invoice_id))
            pl = cur.fetchone()
            if not pl:
                return None
            cur.execute("SELECT * FROM job_projects WHERE ID=%s", (pl["JOB_PROJECT_ID"],))
            pr = cur.fetchone()
            # já cobrado ANTES desta invoice (parcelas cobradas em invoices mais antigas)
            cur.execute("SELECT COALESCE(SUM(AMOUNT), 0) AS S FROM project_payment_plan WHERE JOB_PROJECT_ID=%s "
                        "AND INVOICE_ID IS NOT NULL AND INVOICE_ID < %s", (pr["ID"], invoice_id))
            before = float(cur.fetchone()["S"] or 0)
            table, ref, fk, name_col = (("client_invoices", "clients", "CLIENT_ID", "FULL_NAME") if kind == "Client"
                                        else ("company_invoices", "companies", "COMPANY_ID", "COMPANY_NAME"))
            cur.execute(f"SELECT t.*, r.{name_col} AS PAYER, r.EMAIL AS EMAIL, r.PHONE_NUMBER AS PHONE "
                        f"FROM {table} t LEFT JOIN {ref} r ON r.ID = t.{fk} WHERE t.ID=%s", (invoice_id,))
            inv = cur.fetchone()
            cur.execute("SELECT PAID_DATE, AMOUNT, PAYMENT_METHOD FROM payments WHERE INVOICE_TYPE=%s AND INVOICE_ID=%s "
                        "ORDER BY PAID_DATE, ID", (kind, invoice_id))
            pays = [(r["PAID_DATE"], r["AMOUNT"], r["PAYMENT_METHOD"]) for r in cur.fetchall()]
            return {"plan": pl, "project": pr, "invoice": inv, "before": before, "payments": pays}
        finally:
            cur.close()
            conn.close()

    def _build_project_invoice_pdf(self, kind, invoice_id, paid=False):
        ctx = self._project_invoice_context(kind, invoice_id)
        if ctx is None:
            raise RuntimeError(f"Invoice #{invoice_id} is not a project payment.")
        pl, pr, inv = ctx["plan"], ctx["project"], ctx["invoice"]
        price = float(pr.get("CONTRACT_PRICE") or 0)
        amount = float(pl["AMOUNT"] or 0)
        remaining = max(price - ctx["before"] - amount, 0)
        styles = getSampleStyleSheet()
        cell = ParagraphStyle("proj_cell", parent=styles["Normal"], fontSize=8.5, leading=11)
        title = pr.get("PROJECT_NAME") or pr.get("JOB_ADDRESS") or pr["CODE"]
        pct = f" — {amount / price * 100:.0f}% of the contract" if price else ""
        work = Paragraph(
            f"<b>{html_escape(title)}</b> (Job {pr['CODE']})<br/>{html_escape(pl['NAME'])}{pct}<br/>"
            f"<font color='#6B7C93'>Contract price {money(price)} · billed before {money(ctx['before'])} · "
            f"remaining after this invoice {money(remaining)}</font>", cell)
        gen = inv["GENERATED_AT"].date() if hasattr(inv["GENERATED_AT"], "date") else inv["GENERATED_AT"]
        rows = [[gen.strftime("%m/%d/%Y"), Paragraph(html_escape(pr.get("JOB_ADDRESS") or ""), cell), work, money(amount)]]
        contact = [x for x in (inv.get("EMAIL"), self._format_phone(inv.get("PHONE")) if inv.get("PHONE") else None) if x]
        d_from = inv["PERIOD_FROM"] or gen
        d_to = inv["PERIOD_TO"] or gen
        safe = "".join(c if c.isalnum() or c in " _-" else "" for c in (inv.get("PAYER") or "")).strip().replace(" ", "_")
        name = f"Invoice_{invoice_id}_{safe}_{pr['CODE']}_{pl['NAME'].replace(' ', '_')}{'_PAID' if paid else ''}.pdf"
        path = os.path.join(arquivos.folder("invoices", str(gen.year)), name)
        status = "RECEIVED" if paid else (inv.get("STATUS") or "PENDING")
        self._build_invoice_pdf(path, invoice_id, kind, inv.get("PAYER") or "", contact, _qdate(d_from), _qdate(d_to),
                                rows, amount, False, [], 0.0, 0.0, 0.0, 0.0, status,
                                payments=ctx["payments"] if paid else None, invoice_date=gen)
        return path

    def _paid_project_invoice_pdf(self, kind, invoice_id):
        """Usado por _build_paid_invoice_pdf: versão PAGA de uma parcela de projeto (ou None)."""
        try:
            if self._project_invoice_context(kind, invoice_id) is None:
                return None
        except (MySQLError, RuntimeError):
            return None
        return self._build_project_invoice_pdf(kind, invoice_id, paid=True)

    # ═════════════════════════ subcontratados ═════════════════════════
    def _subcontractor_list(self):
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT ID, NAME, COALESCE(COMPANY, ''), COALESCE(TRADE, ''), COALESCE(PHONE, ''), "
                        "COALESCE(EMAIL, '') FROM subcontractors ORDER BY NAME")
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    def _ask_project_sub(self, parent):
        """Escolhe (ou cadastra) um subcontratado e o combinado. Devolve (id, escopo, valor) ou None."""
        subs = self._subcontractor_list()
        d = QDialog(parent)
        d.setWindowTitle("Add subcontractor")
        f = QFormLayout(d)
        cmb = QComboBox()
        cmb.setEditable(True)
        cmb.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        for sid, name, comp, trade, _p, _e in subs:
            cmb.addItem(name + (f" ({trade})" if trade else ""), sid)
        cmb.setCurrentIndex(-1)
        cmb.lineEdit().setPlaceholderText("Choose or type a new name")
        t_trade = QLineEdit()
        t_trade.setPlaceholderText("e.g. Carpet, Tile, Painting (only for a new one)")
        t_phone = QLineEdit()
        t_scope = QLineEdit()
        t_scope.setPlaceholderText("What they will do on this project")
        sp = QDoubleSpinBox()
        sp.setMaximum(9999999.99)
        sp.setPrefix("$ ")
        f.addRow("Subcontractor", cmb)
        f.addRow("Trade", t_trade)
        f.addRow("Phone", t_phone)
        f.addRow("Scope", t_scope)
        f.addRow("Agreed amount", sp)
        row = QHBoxLayout()
        ok, cancel = QPushButton("Add"), QPushButton("Cancel")
        ok.setObjectName("btn_sub_add_ok")
        row.addStretch(1)
        row.addWidget(cancel)
        row.addWidget(ok)
        f.addRow(row)
        ok.clicked.connect(d.accept)
        cancel.clicked.connect(d.reject)
        d._fields = (cmb, t_trade, t_phone, t_scope, sp)
        if d.exec() != QDialog.DialogCode.Accepted:
            return None
        text = cmb.currentText().strip()
        if not text:
            return None
        idx = cmb.findText(text, Qt.MatchFlag.MatchFixedString)
        sub_id = cmb.itemData(idx) if idx >= 0 else None
        if not sub_id:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO subcontractors (NAME, TRADE, PHONE) VALUES (%s,%s,%s)",
                        (text, t_trade.text().strip() or None, t_phone.text().strip() or None))
            sub_id = cur.lastrowid
            conn.commit()
            cur.close()
            conn.close()
        return sub_id, t_scope.text().strip() or None, sp.value()

    def _record_sub_payment(self, project_id, project_sub_id, sub_name, scope, amount, paid_date, method, note):
        """Grava o pagamento ao subcontratado e a despesa SUBCONTRACTOR do projeto (P&L)."""
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT CODE FROM job_projects WHERE ID=%s", (project_id,))
            code = (cur.fetchone() or [""])[0]
            desc = f"{sub_name} — {code}" + (f" ({scope})" if scope else "")
            cur.execute("INSERT INTO expenses (EXPENSE_DATE, CATEGORY, DESCRIPTION, VENDOR, AMOUNT, ENTITY_TYPE, "
                        "OTHER_NAME, JOB_PROJECT_ID) VALUES (%s,'SUBCONTRACTOR',%s,%s,%s,'Other',%s,%s)",
                        (paid_date, desc[:200], sub_name[:100], amount, sub_name[:150], project_id))
            eid = cur.lastrowid
            cur.execute("INSERT INTO project_sub_payments (PROJECT_SUB_ID, PAID_DATE, AMOUNT, METHOD, NOTE, EXPENSE_ID) "
                        "VALUES (%s,%s,%s,%s,%s,%s)", (project_sub_id, paid_date, amount, method, note or None, eid))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    def open_subcontractors_dialog(self):
        """Lista dos subcontratados com o total combinado / pago / devido em todos os projetos."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Subcontractors")
        dialog.resize(860, 480)
        v = QVBoxLayout(dialog)
        info = QLabel("People and companies you hire for part of a project. Paid this year is what goes on their 1099 "
                      "(file one when it is $600 or more).")
        info.setWordWrap(True)
        info.setStyleSheet("color:#6B7C93;")
        v.addWidget(info)
        t = QTableWidget(0, 7)
        t.setObjectName("table_subcontractors")
        t.setHorizontalHeaderLabels(["Name", "Trade", "Phone", "E-mail", "Agreed (all projects)", "Owed",
                                     f"Paid in {date.today().year}"])
        t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        t.verticalHeader().setVisible(False)
        t.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        v.addWidget(t, 1)
        row = QHBoxLayout()
        b_edit = QPushButton("Edit contact…")
        b_edit.setStyleSheet(_SMALL)
        b_close = QPushButton("Close")
        row.addWidget(b_edit)
        row.addStretch(1)
        row.addWidget(b_close)
        v.addLayout(row)
        data = []

        def load():
            data.clear()
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT sc.ID, sc.NAME, COALESCE(sc.TRADE, ''), COALESCE(sc.PHONE, ''), COALESCE(sc.EMAIL, ''),
                       COALESCE((SELECT SUM(AGREED_AMOUNT) FROM project_subs s WHERE s.SUBCONTRACTOR_ID = sc.ID), 0),
                       COALESCE((SELECT SUM(sp.AMOUNT) FROM project_sub_payments sp JOIN project_subs s ON s.ID = sp.PROJECT_SUB_ID
                                 WHERE s.SUBCONTRACTOR_ID = sc.ID), 0),
                       COALESCE((SELECT SUM(sp.AMOUNT) FROM project_sub_payments sp JOIN project_subs s ON s.ID = sp.PROJECT_SUB_ID
                                 WHERE s.SUBCONTRACTOR_ID = sc.ID AND YEAR(sp.PAID_DATE) = YEAR(CURDATE())), 0)
                FROM subcontractors sc ORDER BY sc.NAME""")
            rows = cur.fetchall()
            cur.close()
            conn.close()
            t.setRowCount(len(rows))
            for i, (sid, name, trade, phone, email, agreed, paid, paid_year) in enumerate(rows):
                owed = max(float(agreed) - float(paid), 0)
                for c, val in enumerate([name, trade, phone, email, money(agreed), money(owed), money(paid_year)]):
                    it = QTableWidgetItem(val)
                    if c == 5 and owed > 0:
                        it.setForeground(QColor("#C62828"))
                    if c == 6 and float(paid_year) >= 600:
                        it.setToolTip("$600 or more this year — they need a 1099-NEC.")
                        it.setForeground(QColor("#B26A00"))
                    t.setItem(i, c, it)
                data.append({"id": sid, "name": name, "trade": trade, "phone": phone, "email": email})

        def edit():
            r = t.currentRow()
            if r < 0:
                return
            s = data[r]
            d = QDialog(dialog)
            d.setWindowTitle(f"Edit {s['name']}")
            f = QFormLayout(d)
            fields = {k: QLineEdit(s[k]) for k in ("name", "trade", "phone", "email")}
            for k, label in (("name", "Name"), ("trade", "Trade"), ("phone", "Phone"), ("email", "E-mail")):
                f.addRow(label, fields[k])
            rr = QHBoxLayout()
            ok, cancel = QPushButton("Save"), QPushButton("Cancel")
            rr.addStretch(1)
            rr.addWidget(cancel)
            rr.addWidget(ok)
            f.addRow(rr)
            ok.clicked.connect(d.accept)
            cancel.clicked.connect(d.reject)
            if d.exec() != QDialog.DialogCode.Accepted or not fields["name"].text().strip():
                return
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("UPDATE subcontractors SET NAME=%s, TRADE=%s, PHONE=%s, EMAIL=%s WHERE ID=%s",
                        (fields["name"].text().strip(), fields["trade"].text().strip() or None,
                         fields["phone"].text().strip() or None, fields["email"].text().strip() or None, s["id"]))
            conn.commit()
            cur.close()
            conn.close()
            load()

        b_edit.clicked.connect(edit)
        t.itemDoubleClicked.connect(lambda *_a: edit())
        b_close.clicked.connect(dialog.accept)
        load()
        dialog._table = t
        dialog.exec()


def html_escape(s):
    import html
    return html.escape(str(s or ""))
