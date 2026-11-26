# -*- coding: utf-8 -*-
"""
Receivables — melhorias de 25/11/2026 (pedido do Viktor: "pode fazer tudo"):

Dashboard
• Card "Not invoiced yet": dias de trabalho já feitos que não estão em nenhuma
  invoice, por quem paga; "Invoice these…" abre o Generate Invoices já com o
  período, o pagador e os dias marcados.
• Card "Expected": quanto deve entrar (atrasado / esta semana / próximas 2
  semanas), pela data de vencimento de cada invoice (ciclo do contractor;
  Company/Client = 30 dias).
• Aviso de pagamento a mais (pago > cobrado) com revisão: guardar como
  extra/gorjeta ou abrir a invoice para corrigir.
• Filtro de período com atalhos (This month, Last month, This year…) e uma
  linha dizendo o que o período afeta. Os cards do topo mostram sempre o que
  está em aberto agora.

Invoices
• Botões rápidos All / Overdue / Pending / Partial / Paid.
• Vencimento e dias de atraso no status; linhas atrasadas em vermelho.
• Ações na invoice selecionada (botões e clique direito): Record payment,
  Send by e-mail, Open PDF, Send reminder.

Pagamentos
• Ao registrar um valor maior que o saldo: registrar só o saldo, guardar a
  diferença como extra/gorjeta, ou cancelar.

Métodos da MainWindow (mixin) — veja main_.py.
"""
from datetime import date, timedelta

from PySide6.QtWidgets import QMenu, QButtonGroup

from app_common import *  # noqa: F401,F403
import arquivos
from paginas.visual import tabler_icon

EXTRA_TAG = "Extra/tip received"

ENTITY_SQL = {
    "Contractor": ("contractor_invoices", "contractors", "CONTRACTOR_ID",
                   "COALESCE(NULLIF(r.COMPANY_NAME, ''), r.FULL_NAME)"),
    "Company": ("company_invoices", "companies", "COMPANY_ID", "r.COMPANY_NAME"),
    "Client": ("client_invoices", "clients", "CLIENT_ID", "r.FULL_NAME"),
}

_CARD_QSS = ("QFrame#{name} {{ background-color:#FFFFFF; border:1px solid #E3E8EE; border-radius:12px; }}"
             " QFrame#{name} QLabel {{ background: transparent; border: none; }}")
_SMALL_BTN = ("QPushButton { background-color:#F0F4F8; color:#1C2B3A; border:1px solid #D0D7DE; "
              "border-radius:6px; padding:6px 12px; font-weight:600; } "
              "QPushButton:hover { background-color:#E3E8EE; } "
              "QPushButton:disabled { color:#9AA5B1; } "
              "QPushButton:checked { background-color:#1565C0; color:#FFFFFF; border:1px solid #1565C0; }")


def money(v):
    return f"${float(v or 0):,.2f}"


def _norm_company(name):
    """'Vertex Londe Flooring LLC' e 'Vertex Londe Flooring' viram o mesmo nome."""
    words = [w for w in "".join(ch if ch.isalnum() else " " for ch in (name or "").lower()).split()
             if w not in ("llc", "inc", "corp", "co", "ltd")]
    return " ".join(words)


def contractor_due_date(generated_at, cycle_type, cycle_weekday, cycle_days):
    """Vencimento de uma invoice de Contractor pelo ciclo dele (mesma regra de
    _is_contractor_invoice_overdue)."""
    if generated_at is None:
        return None
    gen = generated_at.date() if hasattr(generated_at, "date") else generated_at
    if cycle_type in ("WEEKLY", "BIWEEKLY"):
        combo_weekday = cycle_weekday if cycle_weekday is not None else 5  # Friday
        target = (combo_weekday - 1) % 7
        ahead = (target - gen.weekday()) % 7 or 7
        due = gen + timedelta(days=ahead)
        return due + timedelta(days=7) if cycle_type == "BIWEEKLY" else due
    return gen + timedelta(days=cycle_days or 30)


def invoice_due_date(entity_type, generated_at, cycle_type=None, cycle_weekday=None, cycle_days=None):
    if entity_type == "Contractor":
        return contractor_due_date(generated_at, cycle_type or "CUSTOM_DAYS", cycle_weekday, cycle_days or 30)
    if generated_at is None:
        return None
    gen = generated_at.date() if hasattr(generated_at, "date") else generated_at
    return gen + timedelta(days=30)


class ReceivablesPlusMixin:
    # ═════════════════════════ dados ═════════════════════════
    def _not_invoiced_groups(self, today=None):
        """Dias já trabalhados (até hoje), com valor, não cancelados e fora de
        qualquer invoice — agrupados por quem paga (Contractor > Company > Client)."""
        today = today or date.today()
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT wd.ID, wd.WORK_DATE, COALESCE(wd.VALUE, 0), wd.CONTRACTOR_ID, wd.COMPANY_ID, wd.CLIENT_ID,
                       COALESCE(NULLIF(ct.COMPANY_NAME, ''), ct.FULL_NAME), co.COMPANY_NAME, cl.FULL_NAME
                FROM work_days wd
                LEFT JOIN contractors ct ON ct.ID = wd.CONTRACTOR_ID
                LEFT JOIN companies co ON co.ID = wd.COMPANY_ID
                LEFT JOIN clients cl ON cl.ID = wd.CLIENT_ID
                WHERE wd.WORK_DATE <= %s AND COALESCE(wd.STATUS, '') <> 'CANCELLED'
                  AND COALESCE(wd.VALUE, 0) > 0
                  AND COALESCE(wd.PAYMENT_METHOD, 'Receivable') = 'Receivable'
                  AND NOT EXISTS (SELECT 1 FROM invoice_work_days i WHERE i.WORK_DAY_ID = wd.ID)
                ORDER BY wd.WORK_DATE, wd.ID
            """, (today,))
            rows = cur.fetchall()
        finally:
            cur.close()
            conn.close()
        groups = {}
        own = _norm_company(company_settings.COMPANY_NAME)
        for wid, wdate, value, ct_id, co_id, cl_id, ct_name, co_name, cl_name in rows:
            if ct_id and own and _norm_company(ct_name) == own:
                ct_id = None  # "contractor" = a própria empresa: quem paga é a company/cliente do dia
            if ct_id:
                key, name = ("Contractor", ct_id), ct_name
            elif co_id:
                key, name = ("Company", co_id), co_name
            elif cl_id:
                key, name = ("Client", cl_id), cl_name
            else:
                key, name = ("Contractor", None), "(no payer set)"
            g = groups.setdefault(key, {"kind": key[0], "entity_id": key[1], "name": name or "—",
                                        "days": [], "total": 0.0, "first": wdate, "last": wdate})
            g["days"].append(wid)
            g["total"] += float(value)
            g["first"], g["last"] = min(g["first"], wdate), max(g["last"], wdate)
        return sorted(groups.values(), key=lambda g: -g["total"])

    def _open_invoices_with_due(self):
        """[(kind, id, name, balance, due_date)] das invoices em aberto."""
        out = []
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            for kind, (table, ref, fk, name_sql) in ENTITY_SQL.items():
                cycle = (", r.PAYMENT_CYCLE_TYPE, r.PAYMENT_CYCLE_WEEKDAY, r.PAYMENT_CYCLE_DAYS"
                         if kind == "Contractor" else ", NULL, NULL, NULL")
                cur.execute(f"""
                    SELECT t.ID, COALESCE({name_sql}, '—'), t.TOTAL_AMOUNT - COALESCE(t.AMOUNT_PAID, 0),
                           t.GENERATED_AT {cycle}
                    FROM {table} t LEFT JOIN {ref} r ON r.ID = t.{fk}
                    WHERE t.STATUS IN ('PENDING', 'PARTIAL')
                """)
                for iid, name, bal, gen, ctype, cwd, cdays in cur.fetchall():
                    out.append((kind, iid, name, float(bal or 0),
                                invoice_due_date(kind, gen, ctype, cwd, cdays)))
        finally:
            cur.close()
            conn.close()
        return out

    def _expected_buckets(self, today=None):
        today = today or date.today()
        b = {"overdue": 0.0, "week": 0.0, "two_weeks": 0.0, "later": 0.0}
        for _k, _i, _n, bal, due in self._open_invoices_with_due():
            if bal <= 0:
                continue
            if due is None or due < today:
                b["overdue"] += bal
            elif due <= today + timedelta(days=6):
                b["week"] += bal
            elif due <= today + timedelta(days=20):
                b["two_weeks"] += bal
            else:
                b["later"] += bal
        return b

    def _overpaid_invoices(self):
        """Invoices em que o pago passou do cobrado e que ainda não foram
        marcadas como extra/gorjeta."""
        out = []
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            for kind, (table, ref, fk, name_sql) in ENTITY_SQL.items():
                cur.execute(f"""
                    SELECT t.ID, COALESCE({name_sql}, '—'), t.TOTAL_AMOUNT, t.AMOUNT_PAID
                    FROM {table} t LEFT JOIN {ref} r ON r.ID = t.{fk}
                    WHERE t.AMOUNT_PAID > t.TOTAL_AMOUNT + 0.005
                      AND COALESCE(t.ADJUSTMENT_NOTE, '') NOT LIKE %s
                """, (f"%{EXTRA_TAG}%",))
                for iid, name, total, paid in cur.fetchall():
                    out.append({"kind": kind, "id": iid, "name": name, "total": float(total or 0),
                                "paid": float(paid or 0), "extra": float(paid or 0) - float(total or 0)})
        finally:
            cur.close()
            conn.close()
        return out

    # ═════════════════════════ pagamento a mais ═════════════════════════
    def _check_overpayment(self, parent, entity_type, invoice_id, amount):
        """Antes de gravar um pagamento: se passa do saldo, pergunta o que fazer.
        Devolve (valor a gravar, é_extra) ou None para cancelar."""
        table = ENTITY_SQL[entity_type][0]
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(f"SELECT TOTAL_AMOUNT - COALESCE(AMOUNT_PAID, 0) FROM {table} WHERE ID = %s", (invoice_id,))
            row = cur.fetchone()
            cur.close()
            conn.close()
        except (MySQLError, RuntimeError):
            return amount, False
        balance = max(0.0, float(row[0] or 0)) if row else 0.0
        if amount <= balance + 0.005:
            return amount, False
        extra = amount - balance
        box = QMessageBox(parent)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle("More than the balance")
        box.setText(f"This payment ({money(amount)}) is {money(extra)} more than the balance due "
                    f"({money(balance)}).")
        box.setInformativeText("Was the extra a tip or extra charge? Or was the amount typed wrong?")
        btn_balance = box.addButton(f"Record only {money(balance)}", QMessageBox.ButtonRole.AcceptRole) \
            if balance > 0 else None
        btn_tip = box.addButton(f"Keep {money(extra)} as extra/tip", QMessageBox.ButtonRole.ActionRole)
        box.addButton(QMessageBox.StandardButton.Cancel)
        box.exec()
        clicked = box.clickedButton()
        if btn_balance is not None and clicked is btn_balance:
            return balance, False
        if clicked is btn_tip:
            return amount, True
        return None

    def _mark_invoice_extra(self, entity_type, invoice_id):
        """Anota na invoice que o valor acima do total é extra/gorjeta (o aviso
        de pagamento a mais deixa de aparecer para ela)."""
        table = ENTITY_SQL[entity_type][0]
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute(f"SELECT TOTAL_AMOUNT, AMOUNT_PAID, COALESCE(ADJUSTMENT_NOTE, '') FROM {table} WHERE ID=%s",
                        (invoice_id,))
            total, paid, note = cur.fetchone()
            extra = float(paid or 0) - float(total or 0)
            tag = f"{EXTRA_TAG}: {money(extra)}"
            new_note = (note + " | " + tag) if note and EXTRA_TAG not in note else (tag if not note else note)
            cur.execute(f"UPDATE {table} SET ADJUSTMENT_NOTE=%s WHERE ID=%s", (new_note[:255], invoice_id))
            conn.commit()
        finally:
            cur.close()
            conn.close()

    # ═════════════════════════ setup ═════════════════════════
    def _setup_receivables_plus(self):
        self._setup_dashboard_extras()
        self._setup_dashboard_period_presets()
        self._setup_invoice_quick_filters()

    # ── Dashboard: cards novos ──
    def _make_card(self, name):
        card = QFrame()
        card.setObjectName(name)
        card.setStyleSheet(_CARD_QSS.format(name=name))
        card.setMinimumHeight(118)
        v = QVBoxLayout(card)
        v.setContentsMargins(18, 14, 18, 14)
        v.setSpacing(4)
        return card, v

    def _setup_dashboard_extras(self):
        ui = self.ui
        outer = ui.layout_scroll_receivables_dashboard_contents
        idx = outer.indexOf(ui.layout_receivables_stats)
        idx = idx + 1 if idx >= 0 else 1

        # aviso de pagamento a mais
        banner = QFrame()
        banner.setObjectName("frame_overpaid_banner")
        banner.setStyleSheet("QFrame#frame_overpaid_banner { background:#FFF3E0; border:1px solid #FFB74D; "
                             "border-radius:10px; } QFrame#frame_overpaid_banner QLabel { background:transparent; "
                             "border:none; color:#8A4B00; }")
        bl = QHBoxLayout(banner)
        bl.setContentsMargins(14, 8, 10, 8)
        self._lbl_overpaid = QLabel()
        self._lbl_overpaid.setWordWrap(True)
        bl.addWidget(self._lbl_overpaid, 1)
        btn_review = QPushButton("Review")
        btn_review.setObjectName("btn_review_overpaid")
        btn_review.setStyleSheet(_SMALL_BTN)
        btn_review.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_review.clicked.connect(self.open_overpaid_review_dialog)
        bl.addWidget(btn_review)
        banner.hide()
        self._frame_overpaid = banner

        row = QHBoxLayout()
        row.setSpacing(16)

        # card: não faturado
        card, v = self._make_card("card_receivables_not_invoiced")
        title = QLabel("🧾  Not invoiced yet")
        title.setStyleSheet("font-size:13px; font-weight:700; color:#1C2B3A;")
        v.addWidget(title)
        self._lbl_not_invoiced_value = QLabel("$0.00")
        self._lbl_not_invoiced_value.setObjectName("lbl_not_invoiced_value")
        self._lbl_not_invoiced_value.setStyleSheet("font-size:24px; font-weight:800; color:#E65100;")
        v.addWidget(self._lbl_not_invoiced_value)
        self._lbl_not_invoiced_detail = QLabel("")
        self._lbl_not_invoiced_detail.setWordWrap(True)
        self._lbl_not_invoiced_detail.setStyleSheet("font-size:12px; color:#6B7C93;")
        v.addWidget(self._lbl_not_invoiced_detail)
        btn = QPushButton("  Invoice these…")
        btn.setObjectName("btn_invoice_not_invoiced")
        btn.setIcon(tabler_icon("file-type-pdf", "#1C2B3A", 16))
        btn.setStyleSheet(_SMALL_BTN)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self.open_not_invoiced_dialog)
        h = QHBoxLayout()
        h.addWidget(btn)
        h.addStretch(1)
        v.addLayout(h)
        row.addWidget(card, 1)

        # card: previsão de recebimento
        card2, v2 = self._make_card("card_receivables_expected")
        t2 = QLabel("📅  Expected to come in")
        t2.setStyleSheet("font-size:13px; font-weight:700; color:#1C2B3A;")
        v2.addWidget(t2)
        grid = QHBoxLayout()
        grid.setSpacing(18)
        self._lbl_expected = {}
        for key, label, color in (("overdue", "Overdue", "#C62828"), ("week", "This week", "#1565C0"),
                                  ("two_weeks", "Next 2 weeks", "#2E7D32"), ("later", "Later", "#6B7C93")):
            col = QVBoxLayout()
            col.setSpacing(0)
            val = QLabel("$0.00")
            val.setObjectName(f"lbl_expected_{key}")
            val.setStyleSheet(f"font-size:20px; font-weight:800; color:{color};")
            cap = QLabel(label)
            cap.setStyleSheet("font-size:12px; color:#6B7C93;")
            col.addWidget(val)
            col.addWidget(cap)
            grid.addLayout(col)
            self._lbl_expected[key] = val
        grid.addStretch(1)
        v2.addLayout(grid)
        note = QLabel("Open invoices by due date (each contractor's payment cycle; companies and clients: 30 days).")
        note.setWordWrap(True)
        note.setStyleSheet("font-size:11px; color:#6B7C93;")
        v2.addWidget(note)
        row.addWidget(card2, 2)

        outer.insertWidget(idx, banner)
        outer.insertLayout(idx + 1, row)

        # o card "Total Receivable" mostra sempre o que está em aberto agora
        ui.lbl_receivables_total_label.setText("Total Receivable (open now)")

    def _refresh_receivables_extra(self):
        if not hasattr(self, "_lbl_not_invoiced_value"):
            return
        try:
            groups = self._not_invoiced_groups()
            buckets = self._expected_buckets()
            overpaid = self._overpaid_invoices()
        except (MySQLError, RuntimeError) as e:
            self._lbl_not_invoiced_detail.setText(f"Could not load: {e}")
            return
        self._not_invoiced_cache = groups
        total = sum(g["total"] for g in groups)
        ndays = sum(len(g["days"]) for g in groups)
        self._lbl_not_invoiced_value.setText(money(total))
        if groups:
            names = ", ".join(f"{g['name']} {money(g['total'])}" for g in groups[:3])
            self._lbl_not_invoiced_detail.setText(f"{ndays} work day(s) done but not on any invoice — {names}")
        else:
            self._lbl_not_invoiced_detail.setText("Every work day is already on an invoice. ✔")
        for key, lbl in self._lbl_expected.items():
            lbl.setText(money(buckets[key]))
        if overpaid:
            first = overpaid[0]
            more = f" (+{len(overpaid) - 1} more)" if len(overpaid) > 1 else ""
            self._lbl_overpaid.setText(
                f"⚠  Invoice #{first['id']} ({first['name']}) was paid <b>{money(first['extra'])}</b> more than "
                f"billed ({money(first['paid'])} paid, {money(first['total'])} billed){more}.")
            self._frame_overpaid.show()
        else:
            self._frame_overpaid.hide()

    # ── Dashboard: período ──
    def _setup_dashboard_period_presets(self):
        ui = self.ui
        cmb = QComboBox()
        cmb.setObjectName("cmb_dashboard_preset")
        cmb.setMinimumSize(150, 46)
        cmb.addItems(["This month", "Last month", "This year", "Last year", "All time", "Custom"])
        lay = ui.layout_dashboard_filter
        lay.insertWidget(lay.indexOf(ui.lbl_dashboard_period) + 1, cmb)
        self._cmb_dashboard_preset = cmb
        hint = QLabel("Applies to the table below and to payments by method. The cards above show what is open now.")
        hint.setStyleSheet("font-size:11px; color:#6B7C93; background:transparent;")
        hint.setWordWrap(True)
        lay.insertWidget(lay.count() - 1 if lay.count() else 0, hint, 1)
        self._applying_preset = False

        def apply_preset(i):
            text = cmb.itemText(i)
            if text == "Custom":
                return
            today = date.today()
            month, year = {
                "This month": (today.month, today.year),
                "Last month": ((today.month - 2) % 12 + 1, today.year - (1 if today.month == 1 else 0)),
                "This year": (0, today.year),
                "Last year": (0, today.year - 1),
                "All time": (0, 0),
            }[text]
            self._applying_preset = True
            try:
                ui.cmb_dashboard_month.blockSignals(True)
                ui.cmb_dashboard_year.blockSignals(True)
                ui.cmb_dashboard_month.setCurrentIndex(max(0, ui.cmb_dashboard_month.findData(month)))
                yi = ui.cmb_dashboard_year.findData(year)
                if yi < 0:  # ano fora da lista (ex.: muito antigo)
                    ui.cmb_dashboard_year.addItem(str(year), year)
                    yi = ui.cmb_dashboard_year.count() - 1
                ui.cmb_dashboard_year.setCurrentIndex(yi)
            finally:
                ui.cmb_dashboard_month.blockSignals(False)
                ui.cmb_dashboard_year.blockSignals(False)
                self._applying_preset = False
            self.load_receivables_dashboard()

        def manual_change(*_a):
            if not self._applying_preset:
                cmb.blockSignals(True)
                cmb.setCurrentText("Custom")
                cmb.blockSignals(False)

        cmb.currentIndexChanged.connect(apply_preset)
        ui.cmb_dashboard_month.currentIndexChanged.connect(manual_change)
        ui.cmb_dashboard_year.currentIndexChanged.connect(manual_change)

    # ── Dashboard: diálogos ──
    def open_not_invoiced_dialog(self):
        try:
            groups = self._not_invoiced_groups()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not load:\n{e}")
            return
        if not groups:
            QMessageBox.information(self, "Not invoiced yet", "Every work day is already on an invoice.")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Work not invoiced yet")
        dialog.resize(760, 420)
        v = QVBoxLayout(dialog)
        info = QLabel("Work days already done (up to today) that are not on any invoice yet. "
                      "Choose one and click <b>Generate invoice</b> — the invoice window opens with these days "
                      "already selected.")
        info.setWordWrap(True)
        v.addWidget(info)
        table = QTableWidget(len(groups), 5)
        table.setObjectName("table_not_invoiced")
        table.setHorizontalHeaderLabels(["Bill to", "Name", "Days", "From – To", "Amount"])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        for r, g in enumerate(groups):
            vals = [g["kind"], g["name"], str(len(g["days"])),
                    f"{g['first']:%m/%d/%Y} – {g['last']:%m/%d/%Y}", money(g["total"])]
            for c, t in enumerate(vals):
                it = QTableWidgetItem(t)
                if c in (2, 4):
                    it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                table.setItem(r, c, it)
        table.selectRow(0)
        v.addWidget(table, 1)
        total = QLabel(f"<b>Total:</b> {money(sum(g['total'] for g in groups))}")
        v.addWidget(total)
        row = QHBoxLayout()
        row.addStretch(1)
        btn_close = QPushButton("Close")
        btn_gen = QPushButton("Generate invoice")
        btn_gen.setObjectName("btn_save_job")
        row.addWidget(btn_close)
        row.addWidget(btn_gen)
        v.addLayout(row)

        def generate():
            r = table.currentRow()
            if r < 0:
                return
            g = groups[r]
            if g["entity_id"] is None:
                QMessageBox.information(dialog, "No payer", "These days have no contractor, company or client set. "
                                        "Open them in Job Records and choose who pays first.")
                return
            dialog.accept()
            self.open_generate_invoices_dialog(prefill_bill_to=g["kind"], prefill_entity_id=g["entity_id"],
                                               prefill_from=g["first"], prefill_to=g["last"],
                                               prefill_day_ids=set(g["days"]))
            self.load_receivables_dashboard()

        btn_close.clicked.connect(dialog.reject)
        btn_gen.clicked.connect(generate)
        table.itemDoubleClicked.connect(lambda *_: generate())
        dialog.exec()

    def open_overpaid_review_dialog(self):
        try:
            items = self._overpaid_invoices()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not load:\n{e}")
            return
        if not items:
            QMessageBox.information(self, "Payments", "No invoice was paid more than it was billed.")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Paid more than billed")
        dialog.resize(720, 360)
        v = QVBoxLayout(dialog)
        info = QLabel("These invoices received more than their total. If the extra was a tip or an extra charge, "
                      "click <b>Keep as extra/tip</b>. If a payment was typed wrong or entered twice, click "
                      "<b>Open invoice</b> and remove or fix it in the payment history.")
        info.setWordWrap(True)
        v.addWidget(info)
        table = QTableWidget(len(items), 5)
        table.setObjectName("table_overpaid")
        table.setHorizontalHeaderLabels(["Invoice", "Name", "Billed", "Paid", "Extra"])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        for r, it in enumerate(items):
            for c, t in enumerate([f"{it['kind']} #{it['id']}", it["name"], money(it["total"]),
                                   money(it["paid"]), money(it["extra"])]):
                table.setItem(r, c, QTableWidgetItem(t))
        table.selectRow(0)
        v.addWidget(table, 1)
        row = QHBoxLayout()
        btn_open = QPushButton("Open invoice")
        btn_tip = QPushButton("Keep as extra/tip")
        btn_tip.setObjectName("btn_keep_extra")
        btn_close = QPushButton("Close")
        row.addWidget(btn_open)
        row.addWidget(btn_tip)
        row.addStretch(1)
        row.addWidget(btn_close)
        v.addLayout(row)

        def current():
            r = table.currentRow()
            return items[r] if 0 <= r < len(items) else None

        def keep():
            it = current()
            if not it:
                return
            try:
                self._mark_invoice_extra(it["kind"], it["id"])
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", str(e))
                return
            table.removeRow(items.index(it))
            items.remove(it)
            self.load_receivables_dashboard()
            if not items:
                dialog.accept()

        def open_inv():
            it = current()
            if it:
                dialog.accept()
                self.open_invoice_detail_dialog(invoice_id=it["id"], entity_type=it["kind"])
                self.load_receivables_dashboard()

        btn_tip.clicked.connect(keep)
        btn_open.clicked.connect(open_inv)
        btn_close.clicked.connect(dialog.reject)
        dialog.exec()

    # ═════════════════════════ Invoices: filtros e ações ═════════════════════════
    def _setup_invoice_quick_filters(self):
        ui = self.ui
        bar = QHBoxLayout()
        bar.setSpacing(6)
        group = QButtonGroup(ui.tab_receivables_invoices)
        group.setExclusive(True)
        self._invoice_quick_buttons = {}
        for key, label in (("all", "All"), ("overdue", "⚠ Overdue"), ("PENDING", PAYMENT_STATUS_LABELS["PENDING"]),
                           ("PARTIAL", PAYMENT_STATUS_LABELS["PARTIAL"]),
                           ("RECEIVED", PAYMENT_STATUS_LABELS["RECEIVED"])):
            b = QPushButton(label)
            b.setObjectName(f"btn_invoice_filter_{key.lower()}")
            b.setCheckable(True)
            b.setStyleSheet(_SMALL_BTN)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            group.addButton(b)
            bar.addWidget(b)
            self._invoice_quick_buttons[key] = b
            b.clicked.connect(lambda _c=False, k=key: self._apply_invoice_quick_filter(k))
        self._invoice_quick_buttons["all"].setChecked(True)
        self._invoice_overdue_only = False
        bar.addSpacing(16)

        self._invoice_action_buttons = []
        for name, label, icon, slot in (
                ("btn_invoice_action_pay", "Record payment", "circle-check", self.invoice_action_record_payment),
                ("btn_invoice_action_email", "Send by e-mail", "send", self.invoice_action_send_email),
                ("btn_invoice_action_pdf", "Open PDF", "file-type-pdf", self.invoice_action_open_pdf),
                ("btn_invoice_action_reminder", "Send reminder", "alert-triangle", self.invoice_action_reminder)):
            b = QPushButton("  " + label)
            b.setObjectName(name)
            b.setIcon(tabler_icon(icon, "#37474F", 16))
            b.setStyleSheet(_SMALL_BTN)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setEnabled(False)
            b.setToolTip("Select an invoice in the list first")
            b.clicked.connect(slot)
            bar.addWidget(b)
            self._invoice_action_buttons.append(b)
        bar.addStretch(1)

        lay = ui.layout_receivables_invoices
        lay.insertLayout(lay.indexOf(ui.layout_invoices_toolbar) + 1, bar)

        t = ui.table_contractor_invoices
        header = t.horizontalHeader()
        header.setStretchLastSection(False)  # a coluna Select só tem o checkbox
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # nome de quem paga
        t.itemSelectionChanged.connect(self._update_invoice_action_buttons)
        t.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        t.customContextMenuRequested.connect(self._invoice_context_menu)
        # mantém os botões rápidos iguais ao combo de status
        ui.cmb_filter_invoice_status.currentIndexChanged.connect(self._sync_quick_from_combo)

    def _sync_quick_from_combo(self, *_a):
        if getattr(self, "_quick_filter_busy", False):
            return
        status = self.ui.cmb_filter_invoice_status.currentText()
        self._invoice_overdue_only = False
        key = status if status in self._invoice_quick_buttons else "all"
        self._invoice_quick_buttons[key].setChecked(True)

    def _apply_invoice_quick_filter(self, key):
        self._quick_filter_busy = True
        try:
            self._invoice_overdue_only = key == "overdue"
            combo = self.ui.cmb_filter_invoice_status
            target = key if key in ("PENDING", "PARTIAL", "RECEIVED") else "All Status"
            if combo.currentText() != target:
                combo.setCurrentText(target)  # recarrega pelo sinal já ligado
            else:
                self.load_contractor_invoices()
        finally:
            self._quick_filter_busy = False

    def _decorate_invoice_rows(self, overdue_rows, due_info):
        """Chamado no fim de load_contractor_invoices: vencimento/atraso no
        status, linhas atrasadas em vermelho e o filtro "Overdue"."""
        t = self.ui.table_contractor_invoices
        only_overdue = getattr(self, "_invoice_overdue_only", False)
        for r in range(t.rowCount()):
            id_item = t.item(r, 0)
            if id_item is None:
                continue
            iid = int(id_item.text())
            info = due_info.get(iid)
            st = t.item(r, 7)
            if st is not None and info:
                st.setText(f"{st.text().replace(' ⚠ Overdue', '')} · {info}")
            if iid in overdue_rows:
                for c in (5, 6):
                    it = t.item(r, c)
                    if it is not None:
                        it.setForeground(QColor("#C62828"))
            t.setRowHidden(r, only_overdue and iid not in overdue_rows)
        # status com vencimento precisa de espaço; a coluna Select (checkbox) não
        t.resizeColumnToContents(7)
        t.setColumnWidth(7, max(160, min(t.columnWidth(7) + 16, 280)))
        t.setColumnWidth(8, 70)
        self._update_invoice_action_buttons()

    def _selected_invoice(self):
        t = self.ui.table_contractor_invoices
        r = t.currentRow()
        if r < 0 or t.isRowHidden(r) or not t.selectionModel().isRowSelected(r, t.rootIndex()):
            return None
        item = t.item(r, 0)
        if item is None:
            return None
        iid = int(item.text())
        meta = getattr(self, "_invoice_row_meta", {}).get(iid, {})
        return {"row": r, "id": iid, "kind": self.ui.cmb_invoice_entity_type.currentText() or "Contractor",
                "pdf": meta.get("pdf_path"), "status": (t.item(r, 7).text() if t.item(r, 7) else "")}

    def _update_invoice_action_buttons(self):
        inv = self._selected_invoice()
        for b in getattr(self, "_invoice_action_buttons", []):
            b.setEnabled(inv is not None)
            b.setToolTip("" if inv else "Select an invoice in the list first")
        if inv is not None and self._invoice_action_buttons:
            paid = inv["status"].startswith(PAYMENT_STATUS_LABELS.get("RECEIVED", "Received"))
            self._invoice_action_buttons[0].setEnabled(not paid)
            self._invoice_action_buttons[3].setEnabled(not paid)

    def _invoice_context_menu(self, pos):
        t = self.ui.table_contractor_invoices
        r = t.rowAt(pos.y())
        if r < 0:
            return
        t.selectRow(r)
        inv = self._selected_invoice()
        if inv is None:
            return
        menu = QMenu(t)
        paid = not self._invoice_action_buttons[0].isEnabled()
        a_pay = menu.addAction("Record payment…")
        a_pay.setEnabled(not paid)
        a_mail = menu.addAction("Send by e-mail…")
        a_pdf = menu.addAction("Open PDF")
        a_rem = menu.addAction("Send reminder…")
        a_rem.setEnabled(not paid)
        menu.addSeparator()
        a_det = menu.addAction("Open details…")
        chosen = menu.exec(t.viewport().mapToGlobal(pos))
        actions = {a_pay: self.invoice_action_record_payment, a_mail: self.invoice_action_send_email,
                   a_pdf: self.invoice_action_open_pdf, a_rem: self.invoice_action_reminder,
                   a_det: self.open_invoice_detail_dialog}
        if chosen in actions:
            actions[chosen]()

    def invoice_action_record_payment(self):
        inv = self._selected_invoice()
        if inv:
            self.open_record_payment_dialog(preselect=(inv["kind"], inv["id"]))
            self.load_contractor_invoices()

    def invoice_action_send_email(self):
        inv = self._selected_invoice()
        if not inv:
            return
        t = self.ui.table_contractor_invoices
        saved = {}
        for r in range(t.rowCount()):
            chk = t.item(r, 8)
            if chk is not None:
                saved[r] = chk.checkState()
                chk.setCheckState(Qt.CheckState.Checked if r == inv["row"] else Qt.CheckState.Unchecked)
        try:
            self.open_send_invoices_dialog()
        finally:
            for r, state in saved.items():
                if t.item(r, 8) is not None:
                    t.item(r, 8).setCheckState(state)

    def invoice_action_open_pdf(self):
        inv = self._selected_invoice()
        if not inv:
            return
        path = arquivos.resolve(inv["pdf"]) if inv["pdf"] else None
        if path and os.path.exists(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        else:
            QMessageBox.information(self, "PDF not found",
                                    f"The PDF of invoice #{inv['id']} was not found"
                                    + (f":\n{path}" if path else "."))

    def invoice_action_reminder(self):
        inv = self._selected_invoice()
        if inv:
            self.open_reminders_dialog(only=(inv["kind"], inv["id"]))
