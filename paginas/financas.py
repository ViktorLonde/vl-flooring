# -*- coding: utf-8 -*-
"""
Números para decidir preço e dinheiro:

• Price per SF — por Job Code: área (SF), valor, material, helpers, lucro e
  tudo isso por pé quadrado; e $/SF de cada tipo de serviço. A área de um
  job é o maior total em SF entre as categorias (instalação, preparação,
  demolição). Jobs com menos de 20 SF lançados aparecem como "not measured"
  (muitos dias antigos têm quantidade 1–4 nos Work Types) e não entram nas
  médias.
• Suggest prices (no Estimate) — preenche serviços com $0: primeiro a
  Service Rate (contractor/company/default), senão a média $/SF do serviço
  nos jobs passados.
• Cash forecast — próximos 30 dias: invoices em aberto, dias trabalhados
  ainda sem invoice, dias agendados, pagamento de helpers e média de
  despesas. É uma estimativa.
• Tax reserve — lucro por período do IRS (estimated tax: 15/abr, 15/jun,
  15/set, 15/jan) × % de reserva (padrão 25%, ajustável). Só referência —
  confirme com o contador. Avisa na Home 15 dias antes do vencimento.

Métodos da MainWindow (mixin) — veja main_.py.
"""

from datetime import date, timedelta
from statistics import median

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QInputDialog

from app_common import *  # noqa: F401,F403
from paginas.moderno import show_toast

MIN_SF = 20  # abaixo disso a área não foi medida de verdade
SF_UNITS = ("SF", "SQFT", "SQ FT")
_HELP_QSS = "color:#64748B; font-size:12px;"


def _money(v):
    return f"${float(v or 0):,.2f}"


def irs_periods(year):
    """[(rótulo, início, fim, vencimento)] dos pagamentos estimados do ano."""
    return [("Q1", date(year, 1, 1), date(year, 3, 31), date(year, 4, 15)),
            ("Q2", date(year, 4, 1), date(year, 5, 31), date(year, 6, 15)),
            ("Q3", date(year, 6, 1), date(year, 8, 31), date(year, 9, 15)),
            ("Q4", date(year, 9, 1), date(year, 12, 31), date(year + 1, 1, 15))]


def _table(headers, rows, stretch=0):
    t = QTableWidget(len(rows), len(headers))
    t.setHorizontalHeaderLabels(headers)
    t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    t.verticalHeader().setVisible(False)
    t.horizontalHeader().setSectionResizeMode(stretch, QHeaderView.ResizeMode.Stretch)
    for r, row in enumerate(rows):
        for c, v in enumerate(row):
            if isinstance(v, tuple):  # (texto, valor para ordenar)
                text, sort = v
            else:
                text, sort = v, None
            it = QTableWidgetItem(str(text))
            if sort is not None:
                it.setData(Qt.ItemDataRole.UserRole, sort)
                it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            t.setItem(r, c, it)
    return t


class FinanceInsightsMixin:
    def _setup_finance_tools(self):
        for attr, handler in (("btn_tool_price_sf", self.open_price_per_sf_dialog),
                              ("btn_tool_cash_forecast", self.open_cash_forecast_dialog),
                              ("btn_tool_tax_reserve", self.open_tax_reserve_dialog),
                              ("btn_tool_statements", lambda: self.open_statements_dialog())):
            btn = QPushButton()
            btn.setObjectName(attr)
            btn.clicked.connect(lambda _c=False, h=handler: h())
            setattr(self.ui, attr, btn)

    # ═════════════════════════ PRICE PER SF ═════════════════════════
    def _price_per_sf_data(self):
        conn = self._get_connection()
        cur = conn.cursor()
        # área por job e categoria (só unidades SF)
        cur.execute(f"""
            SELECT wd.JOB_PROJECT_ID, x.CATEGORY, SUM(x.QTY)
            FROM work_day_work_types x JOIN work_types wt ON wt.ID = x.WORK_TYPE_ID
            JOIN work_days wd ON wd.ID = x.WORK_DAY_ID
            WHERE UPPER(COALESCE(wt.UNIT, '')) IN ({','.join(['%s'] * len(SF_UNITS))})
              AND COALESCE(wd.STATUS, '') <> 'CANCELLED' AND wd.JOB_PROJECT_ID IS NOT NULL
            GROUP BY 1, 2""", SF_UNITS)
        area = {}
        for pid, _cat, qty in cur.fetchall():
            area[pid] = max(area.get(pid, 0.0), float(qty or 0))
        cur.execute("""
            SELECT jp.ID, jp.CODE,
                   COALESCE(NULLIF(cl.FULL_NAME, ''), NULLIF(co.COMPANY_NAME, ''), NULLIF(ct.COMPANY_NAME, ''), ct.FULL_NAME, ''),
                   COALESCE(SUM(wd.VALUE), 0), COALESCE(SUM(wd.HELPER_PAY), 0), COALESCE(SUM(wd.DAY_FRACTION), 0),
                   (SELECT COALESCE(SUM(m.QUANTITY * m.UNIT_PRICE), 0) FROM job_materials m WHERE m.JOB_PROJECT_ID = jp.ID)
            FROM job_projects jp
            JOIN work_days wd ON wd.JOB_PROJECT_ID = jp.ID AND COALESCE(wd.STATUS, '') <> 'CANCELLED'
            LEFT JOIN clients cl ON cl.ID = jp.CLIENT_ID
            LEFT JOIN companies co ON co.ID = jp.COMPANY_ID
            LEFT JOIN contractors ct ON ct.ID = jp.CONTRACTOR_ID
            GROUP BY jp.ID, jp.CODE, 3 ORDER BY jp.CODE DESC""")
        jobs = []
        for pid, code, who, value, crew, days, material in cur.fetchall():
            sf = area.get(pid, 0.0)
            jobs.append({"id": pid, "code": code, "who": who, "sf": sf, "value": float(value), "crew": float(crew),
                         "material": float(material), "days": float(days), "measured": sf >= MIN_SF})
        # $/SF por serviço: valor do dia dividido entre os serviços em SF pela quantidade
        cur.execute(f"""
            SELECT x.WORK_DAY_ID, wt.ID, wt.CATEGORY, wt.NAME, x.QTY, COALESCE(wd.VALUE, 0)
            FROM work_day_work_types x JOIN work_types wt ON wt.ID = x.WORK_TYPE_ID
            JOIN work_days wd ON wd.ID = x.WORK_DAY_ID
            WHERE UPPER(COALESCE(wt.UNIT, '')) IN ({','.join(['%s'] * len(SF_UNITS))})
              AND COALESCE(wd.STATUS, '') <> 'CANCELLED' AND x.QTY > 0""", SF_UNITS)
        by_day = {}
        for wid, wtid, cat, name, qty, value in cur.fetchall():
            by_day.setdefault(wid, {"value": float(value), "items": []})["items"].append((wtid, cat, name, float(qty)))
        services = {}
        for d in by_day.values():
            total_sf = sum(q for *_x, q in d["items"])
            if total_sf < MIN_SF or d["value"] <= 0:
                continue
            for wtid, cat, name, qty in d["items"]:
                s = services.setdefault(wtid, {"id": wtid, "category": cat, "name": name, "sf": 0.0, "value": 0.0,
                                               "days": 0, "rates": []})
                s["sf"] += qty
                s["value"] += d["value"] * qty / total_sf
                s["days"] += 1
                s["rates"].append(d["value"] / total_sf)
        cur.close()
        conn.close()
        return jobs, sorted(services.values(), key=lambda s: -s["sf"])

    def open_price_per_sf_dialog(self):
        try:
            jobs, services = self._price_per_sf_data()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not load the jobs:\n{e}")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Price per SF")
        dialog.resize(1100, 640)
        layout = QVBoxLayout(dialog)
        measured = [j for j in jobs if j["measured"]]
        sf = sum(j["sf"] for j in measured)
        value = sum(j["value"] for j in measured)
        cost = sum(j["material"] + j["crew"] for j in measured)
        head = QLabel(f"{len(measured)} measured job(s) · {sf:,.0f} SF · {_money(value / sf if sf else 0)}/SF charged · "
                      f"{_money((value - cost) / sf if sf else 0)}/SF after material and helpers")
        head.setStyleSheet("font-size:15px; font-weight:700; color:#1565C0;")
        layout.addWidget(head)
        hint = QLabel(f"Area = the biggest SF total among installation / preparation / demolition of the job. Jobs with "
                      f"less than {MIN_SF} SF entered in the Work Types are marked 'not measured' and left out of the "
                      f"averages — enter the real SF in the days to make this more accurate.")
        hint.setWordWrap(True)
        hint.setStyleSheet(_HELP_QSS)
        layout.addWidget(hint)
        tabs = QTabWidget()
        rows = []
        for j in jobs:
            s = j["sf"] if j["measured"] else 0
            profit = j["value"] - j["material"] - j["crew"]

            def per(x):
                return (_money(x / s), x / s) if s else ("—", -1)
            rows.append([j["code"], j["who"], (f"{j['sf']:,.0f}" if j["measured"] else "not measured", j["sf"]),
                         (_money(j["value"]), j["value"]), (_money(j["material"]), j["material"]),
                         (_money(j["crew"]), j["crew"]), (_money(profit), profit),
                         per(j["value"]), per(j["material"]), per(profit)])
        t_jobs = _table(["Job Code", "Customer", "SF", "Value", "Material", "Helpers", "Profit",
                         "Value/SF", "Material/SF", "Profit/SF"], rows, stretch=1)
        t_jobs.setObjectName("table_price_sf_jobs")
        t_jobs.setSortingEnabled(True)
        tabs.addTab(t_jobs, "By Job Code")
        srows = []
        for s in services:
            avg = s["value"] / s["sf"] if s["sf"] else 0
            srows.append([s["category"].title() if s["category"] else "", s["name"], (f"{s['sf']:,.0f}", s["sf"]),
                          (str(s["days"]), s["days"]), (_money(avg), avg),
                          (_money(median(s["rates"])), median(s["rates"])) if s["rates"] else ("—", 0)])
        t_srv = _table(["Category", "Service", "SF", "Days", "Avg $/SF", "Median $/SF"], srows, stretch=1)
        t_srv.setObjectName("table_price_sf_services")
        t_srv.setSortingEnabled(True)
        tabs.addTab(t_srv, "By service")
        layout.addWidget(tabs, 1)
        close = QPushButton("Close")
        close.clicked.connect(dialog.accept)
        b = QHBoxLayout()
        b.addStretch(1)
        b.addWidget(close)
        layout.addLayout(b)
        dialog._jobs, dialog._services = jobs, services  # testes
        dialog.exec()

    def suggest_service_price(self, name, unit=None, contractor_id=None, company_id=None, services=None):
        """(preço, de onde veio) para um serviço pelo nome, ou (None, motivo)."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT ID FROM work_types WHERE LOWER(NAME) = LOWER(%s)", (name.strip(),))
            ids = [r[0] for r in cur.fetchall()]
            cur.close()
            conn.close()
        except (MySQLError, RuntimeError):
            ids = []
        for wid in ids:
            if hasattr(self, "_rate_for"):
                rate = self._rate_for(wid, contractor_id, company_id)
                if rate:
                    return rate, "Service Rate"
        if services is None:
            try:
                _jobs, services = self._price_per_sf_data()
            except (MySQLError, RuntimeError):
                services = []
        if unit and unit.upper() not in SF_UNITS:
            return None, "no rate (history only works for SF)"
        for s in services:
            if s["id"] in ids and s["rates"] and s["sf"] >= 100:
                return round(median(s["rates"]), 2), f"median of {s['days']} past day(s)"
        return None, "no rate and not enough history"

    def suggest_estimate_prices(self, parent, rows, client_id=None):
        """rows: [(descrição, unidade, spin do preço)]. Preenche os que estão $0."""
        if not rows:
            QMessageBox.information(parent, "Suggest prices", "There are no service lines.")
            return
        try:
            _jobs, services = self._price_per_sf_data()
        except (MySQLError, RuntimeError):
            services = []
        filled, kept, none = [], [], []
        for desc, unit, spin in rows:
            if not desc:
                continue
            price, basis = self.suggest_service_price(desc, unit, services=services)
            if price is None:
                none.append(f"{desc}: {basis}")
            elif spin.value() <= 0:
                spin.setValue(price)
                filled.append(f"{desc}: {_money(price)}/{unit or 'unit'} ({basis})")
            else:
                kept.append(f"{desc}: you have {_money(spin.value())}, suggestion {_money(price)} ({basis})")
        parts = []
        if filled:
            parts.append("Filled:\n• " + "\n• ".join(filled))
        if kept:
            parts.append("Kept your price:\n• " + "\n• ".join(kept))
        if none:
            parts.append("No suggestion:\n• " + "\n• ".join(none))
        QMessageBox.information(parent, "Suggest prices", "\n\n".join(parts) or "Nothing to suggest.")

    # ═════════════════════════ CASH FORECAST ═════════════════════════
    def _cash_forecast_data(self, today=None):
        today = today or date.today()
        end = today + timedelta(days=30)
        conn = self._get_connection()
        cur = conn.cursor()
        d = {"today": today, "end": end}
        open_total, open_old = 0.0, 0.0
        for table in ("contractor_invoices", "company_invoices", "client_invoices"):
            cur.execute(f"SELECT COALESCE(SUM(TOTAL_AMOUNT - COALESCE(AMOUNT_PAID, 0)), 0), "
                        f"COALESCE(SUM(CASE WHEN DATEDIFF(CURDATE(), GENERATED_AT) > 60 "
                        f"THEN TOTAL_AMOUNT - COALESCE(AMOUNT_PAID, 0) ELSE 0 END), 0) "
                        f"FROM {table} WHERE STATUS IN ('PENDING', 'PARTIAL')")
            a, b = cur.fetchone()
            open_total += float(a or 0)
            open_old += float(b or 0)
        d["open_invoices"], d["open_old"] = open_total, open_old
        cur.execute("SELECT COALESCE(SUM(wd.VALUE), 0), COUNT(*) FROM work_days wd WHERE wd.WORK_DATE <= %s "
                    "AND COALESCE(wd.STATUS, '') <> 'CANCELLED' AND COALESCE(wd.VALUE, 0) > 0 "
                    "AND NOT EXISTS (SELECT 1 FROM invoice_work_days i WHERE i.WORK_DAY_ID = wd.ID)", (today,))
        v, n = cur.fetchone()
        d["to_invoice"], d["to_invoice_days"] = float(v or 0), int(n or 0)
        cur.execute("SELECT COALESCE(SUM(VALUE), 0), COALESCE(SUM(HELPER_PAY), 0), COUNT(*) FROM work_days "
                    "WHERE WORK_DATE > %s AND WORK_DATE <= %s AND COALESCE(STATUS, '') <> 'CANCELLED'", (today, end))
        v, p, n = cur.fetchone()
        d["scheduled"], d["crew_future"], d["scheduled_days"] = float(v or 0), float(p or 0), int(n or 0)
        cur.execute("SELECT COALESCE(SUM(HELPER_PAY), 0) FROM work_days WHERE WORK_DATE BETWEEN %s AND %s "
                    "AND COALESCE(STATUS, '') <> 'CANCELLED'", (today - timedelta(days=13), today))
        d["crew_recent"] = float(cur.fetchone()[0] or 0)
        cur.execute("SELECT COALESCE(SUM(AMOUNT), 0) FROM expenses WHERE EXPENSE_DATE BETWEEN %s AND %s",
                    (today - timedelta(days=90), today))
        d["expenses_month"] = float(cur.fetchone()[0] or 0) / 3
        weeks = []
        for i in range(5):
            a = today + timedelta(days=1 + 7 * i)
            b = min(a + timedelta(days=6), end)
            if a > end:
                break
            cur.execute("SELECT COALESCE(SUM(VALUE), 0), COALESCE(SUM(HELPER_PAY), 0), COALESCE(SUM(DAY_FRACTION), 0) "
                        "FROM work_days WHERE WORK_DATE BETWEEN %s AND %s AND COALESCE(STATUS, '') <> 'CANCELLED'", (a, b))
            v, p, days = cur.fetchone()
            weeks.append((a, b, float(v or 0), float(p or 0), float(days or 0)))
        d["weeks"] = weeks
        cur.close()
        conn.close()
        d["in"] = d["open_invoices"] + d["to_invoice"] + d["scheduled"]
        d["out"] = d["crew_future"] + d["crew_recent"] + d["expenses_month"]
        d["net"] = d["in"] - d["out"]
        return d

    def open_cash_forecast_dialog(self):
        try:
            d = self._cash_forecast_data()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not load the numbers:\n{e}")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Cash forecast — next 30 days")
        dialog.resize(820, 620)
        layout = QVBoxLayout(dialog)
        head = QLabel(f"Next 30 days (until {d['end']:%m/%d}): about {_money(d['in'])} coming in, "
                      f"{_money(d['out'])} going out → {_money(d['net'])}")
        head.setWordWrap(True)
        head.setStyleSheet(f"font-size:15px; font-weight:700; color:{'#15803D' if d['net'] >= 0 else '#C62828'};")
        layout.addWidget(head)
        rows = [["Coming in", "Open invoices (not paid yet)", (_money(d["open_invoices"]), d["open_invoices"])],
                ["", f"   of which over 60 days old", (_money(d["open_old"]), d["open_old"])],
                ["", f"Days worked without an invoice yet ({d['to_invoice_days']})", (_money(d["to_invoice"]), d["to_invoice"])],
                ["", f"Days scheduled in the next 30 days ({d['scheduled_days']})", (_money(d["scheduled"]), d["scheduled"])],
                ["Going out", "Helper pay of the days scheduled", (_money(d["crew_future"]), d["crew_future"])],
                ["", "Helper pay of the last 2 weeks (if not paid yet)", (_money(d["crew_recent"]), d["crew_recent"])],
                ["", "Expenses — monthly average of the last 3 months", (_money(d["expenses_month"]), d["expenses_month"])],
                ["Balance", "In − out", (_money(d["net"]), d["net"])]]
        t = _table(["", "What", "Amount"], rows, stretch=1)
        t.setObjectName("table_cash_forecast")
        t.setColumnWidth(0, 110)
        t.setColumnWidth(2, 150)
        layout.addWidget(t, 1)
        layout.addWidget(QLabel("<b>Week by week (scheduled days)</b>"))
        wrows = [[f"{a:%m/%d} – {b:%m/%d}", (f"{days:g}", days), (_money(v), v), (_money(p), p), (_money(v - p), v - p)]
                 for a, b, v, p, days in d["weeks"]]
        layout.addWidget(_table(["Week", "Days", "Value", "Helper pay", "Net"], wrows), 1)
        note = QLabel("Estimate only: invoices are counted as if paid in the next 30 days, and expenses use your recent "
                      "average. Days scheduled without a Value show as $0 — set the Value (or Service Rates) to "
                      "improve it.")
        note.setWordWrap(True)
        note.setStyleSheet(_HELP_QSS)
        layout.addWidget(note)
        close = QPushButton("Close")
        close.clicked.connect(dialog.accept)
        b = QHBoxLayout()
        b.addStretch(1)
        b.addWidget(close)
        layout.addLayout(b)
        dialog._data = d  # testes
        dialog.exec()

    # ═════════════════════════ TAX RESERVE ═════════════════════════
    def _tax_reserve_pct(self):
        return QSettings("VL Flooring", "app").value("tax/reserve_pct", 25.0, type=float)

    def _tax_reserve_data(self, year):
        """Por período do IRS: recebido (payments), despesas, helpers, lucro, reserva.
        Regime de caixa: conta o que foi RECEBIDO no período."""
        pct = self._tax_reserve_pct() / 100
        conn = self._get_connection()
        cur = conn.cursor()
        out = []
        for label, a, b, due in irs_periods(year):
            cur.execute("SELECT COALESCE(SUM(AMOUNT), 0) FROM payments WHERE PAID_DATE BETWEEN %s AND %s", (a, b))
            income = float(cur.fetchone()[0] or 0)
            cur.execute("SELECT COALESCE(SUM(AMOUNT), 0) FROM expenses WHERE EXPENSE_DATE BETWEEN %s AND %s", (a, b))
            expenses = float(cur.fetchone()[0] or 0)
            cur.execute("SELECT COALESCE(SUM(HELPER_PAY), 0) FROM work_days WHERE WORK_DATE BETWEEN %s AND %s "
                        "AND COALESCE(STATUS, '') <> 'CANCELLED'", (a, b))
            crew = float(cur.fetchone()[0] or 0)
            profit = income - expenses - crew
            out.append({"label": label, "start": a, "end": b, "due": due, "income": income, "expenses": expenses,
                        "crew": crew, "profit": profit, "reserve": round(max(profit, 0) * pct, 2)})
        cur.close()
        conn.close()
        return out

    def _next_tax_due(self, today=None):
        today = today or date.today()
        for year in (today.year - 1, today.year):
            for label, a, b, due in irs_periods(year):
                if due >= today:
                    return year, label, due
        return today.year, "Q4", date(today.year + 1, 1, 15)

    def open_tax_reserve_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Estimated tax reserve")
        dialog.resize(940, 560)
        layout = QVBoxLayout(dialog)
        top = QHBoxLayout()
        top.addWidget(QLabel("Year:"))
        cmb_year = QComboBox()
        this = date.today().year
        for y in (this, this - 1, this + 1):
            cmb_year.addItem(str(y), y)
        top.addWidget(cmb_year)
        btn_pct = QPushButton()
        top.addWidget(btn_pct)
        top.addStretch(1)
        layout.addLayout(top)
        head = QLabel()
        head.setWordWrap(True)
        head.setStyleSheet("font-size:15px; font-weight:700; color:#1565C0;")
        layout.addWidget(head)
        holder = QVBoxLayout()
        layout.addLayout(holder, 1)
        note = QLabel("Reference only — this is not tax advice. Income = payments RECEIVED in the period (cash basis); "
                      "costs = expenses + helper pay. Self-employment tax plus income tax is often 25–30% of profit, "
                      "but confirm the % and the amounts with your accountant. IRS due dates: Apr 15, Jun 15, Sep 15 "
                      "and Jan 15 (next business day when it falls on a weekend).")
        note.setWordWrap(True)
        note.setStyleSheet(_HELP_QSS)
        layout.addWidget(note)
        close = QPushButton("Close")
        close.clicked.connect(dialog.accept)
        b = QHBoxLayout()
        b.addStretch(1)
        b.addWidget(close)
        layout.addLayout(b)
        state = {"table": None}

        def load(*_a):
            btn_pct.setText(f"Reserve: {self._tax_reserve_pct():g}% of profit — change")
            try:
                data = self._tax_reserve_data(cmb_year.currentData())
            except (MySQLError, RuntimeError) as e:
                head.setText(f"Could not load: {e}")
                return
            if state["table"] is not None:
                state["table"].deleteLater()
            rows = [[f"{p['label']}  ({p['start']:%m/%d} – {p['end']:%m/%d})", f"{p['due']:%m/%d/%Y}",
                     (_money(p["income"]), p["income"]), (_money(p["expenses"]), p["expenses"]),
                     (_money(p["crew"]), p["crew"]), (_money(p["profit"]), p["profit"]),
                     (_money(p["reserve"]), p["reserve"])] for p in data]
            total = [sum(p[k] for p in data) for k in ("income", "expenses", "crew", "profit", "reserve")]
            rows.append(["Year", ""] + [(_money(x), x) for x in total])
            t = _table(["Period", "Due", "Received", "Expenses", "Helpers", "Profit", "Set aside"], rows)
            t.setObjectName("table_tax_reserve")
            holder.addWidget(t)
            state["table"] = t
            year, label, due = self._next_tax_due()
            nxt = next((p for p in data if p["due"] == due), None)
            head.setText(f"Next estimated payment: {label} {year} — due {due:%m/%d/%Y} "
                         f"({(due - date.today()).days} days). Suggested to set aside: "
                         f"{_money(nxt['reserve']) if nxt else 'see the table'}.  Year so far: {_money(total[4])}.")
            dialog._data = data  # testes

        def change_pct():
            v, ok = QInputDialog.getDouble(dialog, "Reserve", "Percent of profit to set aside for taxes:",
                                           self._tax_reserve_pct(), 0, 60, 1)
            if ok:
                QSettings("VL Flooring", "app").setValue("tax/reserve_pct", v)
                load()

        cmb_year.currentIndexChanged.connect(load)
        btn_pct.clicked.connect(change_pct)
        load()
        dialog.exec()

    def _tax_attention_item(self):
        if not self._role_rule("finance"):
            return None
        year, label, due = self._next_tax_due()
        days = (due - date.today()).days
        if days > 15:
            return None
        if QSettings("VL Flooring", "app").value("tax/seen_due", "") == due.isoformat():
            return None

        def open_it():
            QSettings("VL Flooring", "app").setValue("tax/seen_due", due.isoformat())
            self.open_tax_reserve_dialog()
        return ("cash", "#B26A00", f"Estimated tax {label} due {due:%m/%d} — check the reserve", open_it)
