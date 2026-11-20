# -*- coding: utf-8 -*-
"""
Relatórios para fechar o ano e acompanhar o material:

• Accountant Package — escolhe o ano e gera uma pasta com uma planilha
  Excel (resumo, receita por mês, pagamentos recebidos, despesas, helper
  pay / 1099, milhas, invoices), os recibos das despesas e os PDFs dos
  invoices do ano, mais um .zip pronto para mandar ao contador.
• Material Usage — por Job Code: SF instalado (Work Types de instalação em
  SF) × SF de piso lançado (caixas × SF por caixa) = perda %, sobras que
  voltaram ao estoque e, se o job veio de um Estimate, previsto × usado.
• Calendar export (.ics) — os dias agendados viram eventos de calendário
  (Google Calendar, iPhone, Outlook): importa uma vez ou manda pro celular.

Métodos da MainWindow (mixin) — veja main_.py.
"""

import os
import shutil
import zipfile
from datetime import date, datetime, timedelta, timezone

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QSpinBox

from app_common import *  # noqa: F401,F403
from paginas.visual import tabler_icon
from paginas.moderno import show_toast
import registro

_PRIMARY_BTN = ("QPushButton { background-color: #1565C0; color: #FFFFFF; border: none; border-radius: 6px; "
                "padding: 8px 16px; font-weight: 700; } QPushButton:hover { background-color: #1E88E5; }")
_SMALL_BTN = ("QPushButton { background-color: #EEF2F7; color: #37474F; border: 1px solid #D0D7DE; "
              "border-radius: 6px; padding: 6px 12px; font-size: 12px; font-weight: 600; } "
              "QPushButton:hover { background-color: #E1E8F0; }")
DEFAULT_MILEAGE_RATE = 0.70
NEC_THRESHOLD = 600.0  # 1099-NEC: pagamentos de $600 ou mais no ano


def _money(v):
    return f"${float(v or 0):,.2f}"


def _safe(name):
    return "".join(c if c.isalnum() or c in " _-." else "_" for c in str(name)).strip() or "file"


class AccountantMixin:
    # ═════════════════════════ ACCOUNTANT PACKAGE ═════════════════════════
    def _accountant_data(self, year):
        start, end = date(year, 1, 1), date(year, 12, 31)
        conn = self._get_connection()
        cur = conn.cursor()
        d = {"year": year}
        cur.execute("""
            SELECT p.PAID_DATE, p.INVOICE_TYPE, p.INVOICE_ID,
                   CASE p.INVOICE_TYPE
                     WHEN 'Contractor' THEN (SELECT COALESCE(NULLIF(c.COMPANY_NAME, ''), c.FULL_NAME)
                                             FROM contractor_invoices i JOIN contractors c ON c.ID = i.CONTRACTOR_ID
                                             WHERE i.ID = p.INVOICE_ID)
                     WHEN 'Company' THEN (SELECT c.COMPANY_NAME FROM company_invoices i
                                          JOIN companies c ON c.ID = i.COMPANY_ID WHERE i.ID = p.INVOICE_ID)
                     ELSE (SELECT c.FULL_NAME FROM client_invoices i JOIN clients c ON c.ID = i.CLIENT_ID
                           WHERE i.ID = p.INVOICE_ID) END,
                   p.AMOUNT, p.PAYMENT_METHOD, p.NOTE
            FROM payments p WHERE p.PAID_DATE BETWEEN %s AND %s ORDER BY p.PAID_DATE""", (start, end))
        d["payments"] = cur.fetchall()
        cur.execute("""
            SELECT e.EXPENSE_DATE, e.CATEGORY, e.DESCRIPTION, e.VENDOR, e.AMOUNT, jp.CODE, e.RECEIPT_PATH, e.ID
            FROM expenses e LEFT JOIN job_projects jp ON jp.ID = e.JOB_PROJECT_ID
            WHERE e.EXPENSE_DATE BETWEEN %s AND %s ORDER BY e.EXPENSE_DATE""", (start, end))
        d["expenses"] = cur.fetchall()
        cur.execute("""
            SELECT MONTH(WORK_DATE), COUNT(*), COALESCE(SUM(VALUE), 0) FROM work_days
            WHERE WORK_DATE BETWEEN %s AND %s AND COALESCE(STATUS, '') <> 'CANCELLED'
            GROUP BY MONTH(WORK_DATE)""", (start, end))
        d["produced_by_month"] = {m: (n, float(v)) for m, n, v in cur.fetchall()}
        cur.execute("""
            SELECT COALESCE(NULLIF(h.FULL_NAME, ''), h.COMPANY_NAME), COUNT(DISTINCT x.WORK_DAY_ID),
                   COALESCE(SUM(x.PAY), 0)
            FROM work_day_helpers x JOIN work_days wd ON wd.ID = x.WORK_DAY_ID JOIN helpers h ON h.ID = x.HELPER_ID
            WHERE wd.WORK_DATE BETWEEN %s AND %s AND COALESCE(wd.STATUS, '') <> 'CANCELLED'
            GROUP BY h.ID ORDER BY 3 DESC""", (start, end))
        d["helpers"] = [(n, int(c), float(p)) for n, c, p in cur.fetchall()]
        cur.execute("""
            SELECT m.TRIP_DATE, m.MILES, m.PURPOSE, m.FROM_PLACE, m.TO_PLACE, jp.CODE
            FROM mileage m LEFT JOIN job_projects jp ON jp.ID = m.JOB_PROJECT_ID
            WHERE m.TRIP_DATE BETWEEN %s AND %s ORDER BY m.TRIP_DATE""", (start, end))
        d["mileage"] = cur.fetchall()
        invoices = []
        for kind, table, fk, partner, name_sql in (
                ("Contractor", "contractor_invoices", "CONTRACTOR_ID", "contractors",
                 "COALESCE(NULLIF(p.COMPANY_NAME, ''), p.FULL_NAME)"),
                ("Company", "company_invoices", "COMPANY_ID", "companies", "p.COMPANY_NAME"),
                ("Client", "client_invoices", "CLIENT_ID", "clients", "p.FULL_NAME")):
            cur.execute(f"""
                SELECT i.ID, {name_sql}, i.PERIOD_FROM, i.PERIOD_TO, i.TOTAL_AMOUNT, i.AMOUNT_PAID, i.STATUS,
                       DATE(i.GENERATED_AT), i.PDF_PATH
                FROM {table} i LEFT JOIN {partner} p ON p.ID = i.{fk}
                WHERE YEAR(i.GENERATED_AT) = %s OR YEAR(i.PERIOD_TO) = %s ORDER BY i.GENERATED_AT""", (year, year))
            invoices += [(kind, *r) for r in cur.fetchall()]
        d["invoices"] = invoices
        cur.close()
        conn.close()
        d["rate"] = QSettings("VL Flooring", "app").value("mileage/rate", DEFAULT_MILEAGE_RATE, type=float)
        d["received"] = sum(float(p[4] or 0) for p in d["payments"])
        d["produced"] = sum(v for _n, v in d["produced_by_month"].values())
        d["expense_total"] = sum(float(e[4] or 0) for e in d["expenses"])
        d["helper_total"] = sum(h[2] for h in d["helpers"])
        d["miles"] = sum(float(m[1] or 0) for m in d["mileage"])
        d["mileage_deduction"] = round(d["miles"] * d["rate"], 2)
        by_cat = {}
        for e in d["expenses"]:
            by_cat[e[1]] = by_cat.get(e[1], 0.0) + float(e[4] or 0)
        d["expenses_by_category"] = by_cat
        return d

    def _write_accountant_workbook(self, d, path):
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment
        wb = Workbook()
        bold = Font(bold=True)
        head_fill = PatternFill("solid", fgColor="1565C0")
        head_font = Font(bold=True, color="FFFFFF")
        money_fmt = '"$"#,##0.00'

        def sheet(title, headers, rows, money_cols=(), widths=None):
            ws = wb.create_sheet(title)
            ws.append(headers)
            for c in range(1, len(headers) + 1):
                cell = ws.cell(row=1, column=c)
                cell.font, cell.fill = head_font, head_fill
            for r in rows:
                ws.append(list(r))
            for col in money_cols:
                for row in ws.iter_rows(min_row=2, min_col=col, max_col=col):
                    for cell in row:
                        cell.number_format = money_fmt
            for i, w in enumerate(widths or [], start=1):
                ws.column_dimensions[chr(64 + i)].width = w
            ws.freeze_panes = "A2"
            return ws

        ws = wb.active
        ws.title = "Summary"
        ws["A1"] = f"{company_settings.COMPANY_NAME} — year {d['year']}"
        ws["A1"].font = Font(bold=True, size=14)
        ws["A2"] = f"Generated {datetime.now():%m/%d/%Y %H:%M} by VL Flooring. Figures for the accountant to review."
        lines = [
            ("Income received (payments)", d["received"]),
            ("Work produced (value of work days)", d["produced"]),
            ("", None),
            ("Expenses — total", d["expense_total"]),
            *[(f"   {str(cat).title()}", v) for cat, v in sorted(d["expenses_by_category"].items())],
            ("Helper pay (subcontractors)", d["helper_total"]),
            (f"Mileage: {d['miles']:,.1f} mi × ${d['rate']:.3f}/mi (standard rate — confirm with IRS)",
             d["mileage_deduction"]),
            ("", None),
            ("Estimated net (income − expenses − helper pay − mileage)",
             d["received"] - d["expense_total"] - d["helper_total"] - d["mileage_deduction"]),
        ]
        for i, (label, value) in enumerate(lines, start=4):
            ws.cell(row=i, column=1, value=label)
            if value is not None:
                c = ws.cell(row=i, column=2, value=round(value, 2))
                c.number_format = money_fmt
                if not label.startswith("   "):
                    ws.cell(row=i, column=1).font = bold
                    c.font = bold
        ws.column_dimensions["A"].width = 70
        ws.column_dimensions["B"].width = 18
        nec = [h for h in d["helpers"] if h[2] >= NEC_THRESHOLD]
        if nec:
            r = len(lines) + 6
            ws.cell(row=r, column=1, value=f"1099-NEC likely needed ($600+ paid in {d['year']}):").font = bold
            for j, (name, _days, pay) in enumerate(nec, start=1):
                ws.cell(row=r + j, column=1, value=f"   {name}")
                ws.cell(row=r + j, column=2, value=round(pay, 2)).number_format = money_fmt

        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        received_by_month = {}
        for p in d["payments"]:
            if p[0]:
                received_by_month[p[0].month] = received_by_month.get(p[0].month, 0.0) + float(p[4] or 0)
        sheet("By month", ["Month", "Work days", "Produced", "Received"],
              [(months[m - 1], d["produced_by_month"].get(m, (0, 0))[0], d["produced_by_month"].get(m, (0, 0.0))[1],
                received_by_month.get(m, 0.0)) for m in range(1, 13)], money_cols=(3, 4), widths=[10, 12, 16, 16])
        sheet("Payments received", ["Date", "Invoice type", "Invoice #", "Paid by", "Amount", "Method", "Note"],
              [(p[0], p[1], p[2], p[3] or "", float(p[4] or 0), p[5] or "", p[6] or "") for p in d["payments"]],
              money_cols=(5,), widths=[12, 14, 11, 34, 14, 14, 30])
        sheet("Expenses", ["Date", "Category", "Description", "Vendor", "Amount", "Job Code", "Receipt file"],
              [(e[0], e[1], e[2] or "", e[3] or "", float(e[4] or 0), e[5] or "",
                self._receipt_name(e) if e[6] else "") for e in d["expenses"]],
              money_cols=(5,), widths=[12, 12, 40, 24, 14, 12, 36])
        sheet("Helper pay (1099)", ["Helper", "Days", "Total paid", f"1099-NEC (${NEC_THRESHOLD:,.0f}+)"],
              [(n, c, p, "YES" if p >= NEC_THRESHOLD else "") for n, c, p in d["helpers"]],
              money_cols=(3,), widths=[34, 8, 16, 18])
        sheet("Mileage", ["Date", "Miles", "Purpose", "From", "To", "Job Code"],
              [(m[0], float(m[1] or 0), m[2] or "", m[3] or "", m[4] or "", m[5] or "") for m in d["mileage"]],
              widths=[12, 9, 34, 26, 26, 12])
        sheet("Invoices", ["Type", "#", "Billed to", "From", "To", "Total", "Paid", "Status", "Generated"],
              [(i[0], i[1], i[2] or "", i[3], i[4], float(i[5] or 0), float(i[6] or 0), i[7], i[8])
               for i in d["invoices"]], money_cols=(6, 7), widths=[12, 6, 30, 12, 12, 14, 14, 11, 12])
        for wsx in wb.worksheets[1:]:
            for row in wsx.iter_rows(min_row=2):
                for cell in row:
                    if isinstance(cell.value, (date, datetime)):
                        cell.number_format = "mm/dd/yyyy"
                        cell.alignment = Alignment(horizontal="left")
        wb.save(path)

    @staticmethod
    def _receipt_name(expense_row):
        exp_date, _cat, _desc, _vendor, _amount, _code, path, exp_id = expense_row
        ext = os.path.splitext(path or "")[1] or ".pdf"
        return f"{exp_date:%Y-%m-%d}_expense{exp_id}{ext}" if exp_date else f"expense{exp_id}{ext}"

    def build_accountant_package(self, year, base_dir=None):
        """Gera a pasta + .zip. Devolve (pasta, zip, faltando[])."""
        d = self._accountant_data(year)
        base_dir = base_dir or registro.EXPORTS_DIR
        folder = os.path.join(base_dir, f"Accountant {year}")
        if os.path.isdir(folder):
            shutil.rmtree(folder, ignore_errors=True)
        os.makedirs(os.path.join(folder, "receipts"), exist_ok=True)
        os.makedirs(os.path.join(folder, "invoices"), exist_ok=True)
        self._write_accountant_workbook(d, os.path.join(folder, f"VL Flooring {year}.xlsx"))
        missing = []
        for e in d["expenses"]:
            if e[6]:
                if os.path.exists(e[6]):
                    shutil.copy2(e[6], os.path.join(folder, "receipts", self._receipt_name(e)))
                else:
                    missing.append(f"receipt of expense #{e[7]} ({e[6]})")
        for inv in d["invoices"]:
            pdf = inv[9]
            if pdf and os.path.exists(pdf):
                shutil.copy2(pdf, os.path.join(folder, "invoices", f"{inv[0]}_{inv[1]}_{_safe(os.path.basename(pdf))}"))
            elif pdf:
                missing.append(f"invoice {inv[0]} #{inv[1]} PDF ({pdf})")
        zip_path = folder + ".zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for root, _dirs, files in os.walk(folder):
                for f in files:
                    full = os.path.join(root, f)
                    z.write(full, os.path.relpath(full, base_dir))
        logging.getLogger("vl_flooring").info("accountant package %s: %s (%d missing files)", year, zip_path, len(missing))
        return folder, zip_path, missing, d

    def open_accountant_package_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Accountant package")
        dialog.resize(560, 300)
        layout = QVBoxLayout(dialog)
        info = QLabel("Builds a folder (and a .zip) for your accountant: an Excel file with the year summary, income "
                      "received, expenses, helper pay with who needs a 1099-NEC, mileage and invoices — plus the "
                      "expense receipts and invoice PDFs.")
        info.setWordWrap(True)
        layout.addWidget(info)
        row = QHBoxLayout()
        row.addWidget(QLabel("Year:"))
        year = QSpinBox()
        year.setObjectName("spn_accountant_year")
        year.setRange(2020, 2100)
        year.setValue(date.today().year if date.today().month > 2 else date.today().year - 1)
        row.addWidget(year)
        row.addStretch(1)
        layout.addLayout(row)
        where = QLabel(f"Saved in: {registro.EXPORTS_DIR}")
        where.setStyleSheet("color:#64748B; font-size:12px;")
        layout.addWidget(where)
        layout.addStretch(1)
        bottom = QHBoxLayout()
        bottom.addStretch(1)
        close = QPushButton("Close")
        go = QPushButton("  Build package")
        go.setObjectName("btn_build_accountant_package")
        go.setIcon(tabler_icon("download", "#FFFFFF", 16))
        go.setStyleSheet(_PRIMARY_BTN)
        bottom.addWidget(close)
        bottom.addWidget(go)
        layout.addLayout(bottom)
        if not self._role_rule("finance"):
            go.setEnabled(False)
            go.setToolTip("Only users with access to the finances can export this.")

        def build():
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                folder, zip_path, missing, d = self.build_accountant_package(year.value())
            except Exception as e:  # noqa: BLE001 — mostra qualquer erro de disco/banco
                QApplication.restoreOverrideCursor()
                logging.getLogger("vl_flooring").exception("accountant package failed")
                QMessageBox.critical(dialog, "Accountant package", f"Could not build the package:\n{e}")
                return
            QApplication.restoreOverrideCursor()
            msg = (f"Year {year.value()}: income received {_money(d['received'])}, expenses {_money(d['expense_total'])}, "
                   f"helper pay {_money(d['helper_total'])}.\n\nFolder: {folder}\nZip: {zip_path}")
            if missing:
                msg += f"\n\n{len(missing)} file(s) not found (moved or deleted):\n• " + "\n• ".join(missing[:6])
            QMessageBox.information(dialog, "Accountant package ready", msg)
            try:
                os.startfile(folder)
            except OSError:
                pass

        go.clicked.connect(build)
        close.clicked.connect(dialog.accept)
        dialog._year = year  # usado nos testes
        dialog.exec()

    # ═════════════════════════ MATERIAL USAGE ═════════════════════════
    def _material_usage_rows(self):
        """Por Job Code: SF instalado, SF de piso lançado, perda %, sobras e
        previsto (Estimate) × usado."""
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT wd.JOB_PROJECT_ID, COALESCE(SUM(x.QTY), 0)
            FROM work_day_work_types x
            JOIN work_days wd ON wd.ID = x.WORK_DAY_ID
            JOIN work_types t ON t.ID = x.WORK_TYPE_ID
            WHERE x.CATEGORY = 'INSTALLATION' AND UPPER(t.UNIT) = 'SF' AND COALESCE(wd.STATUS, '') <> 'CANCELLED'
              AND wd.JOB_PROJECT_ID IS NOT NULL
            GROUP BY wd.JOB_PROJECT_ID""")
        installed = {pid: float(v) for pid, v in cur.fetchall()}
        cur.execute("""
            SELECT jm.JOB_PROJECT_ID, jp.CODE, pr.ID, pr.NAME, COALESCE(NULLIF(pr.TYPE, ''), 'Others'), pr.UNIT,
                   jm.QUANTITY, COALESCE(pr.COVERAGE_QTY, 0), UPPER(COALESCE(pr.COVERAGE_UNIT, '')), jm.UNIT_PRICE
            FROM job_materials jm JOIN products pr ON pr.ID = jm.PRODUCT_ID
            JOIN job_projects jp ON jp.ID = jm.JOB_PROJECT_ID
            ORDER BY jp.ID DESC, pr.TYPE, pr.NAME""")
        materials = cur.fetchall()
        cur.execute("SELECT JOB_PROJECT_ID, PRODUCT_ID, SUM(QUANTITY) FROM inventory_moves "
                    "WHERE QUANTITY > 0 AND JOB_PROJECT_ID IS NOT NULL GROUP BY JOB_PROJECT_ID, PRODUCT_ID")
        leftovers = {(pid, prod): float(q) for pid, prod, q in cur.fetchall()}
        cur.execute("""
            SELECT e.JOB_PROJECT_ID, i.PRODUCT_ID, SUM(i.QTY) FROM estimate_items i
            JOIN estimates e ON e.ID = i.ESTIMATE_ID
            WHERE e.JOB_PROJECT_ID IS NOT NULL AND i.PRODUCT_ID IS NOT NULL
            GROUP BY e.JOB_PROJECT_ID, i.PRODUCT_ID""")
        estimated = {(pid, prod): float(q) for pid, prod, q in cur.fetchall()}
        cur.close()
        conn.close()
        jobs = {}
        for pid, code, prod, name, ptype, unit, qty, cov, cov_unit, price in materials:
            j = jobs.setdefault(pid, {"id": pid, "code": code, "installed_sf": installed.get(pid, 0.0),
                                      "floor_sf": 0.0, "lines": []})
            qty = float(qty or 0)
            sf = qty * float(cov) if cov_unit == "SF" and ptype.lower() == "flooring" else 0.0
            j["floor_sf"] += sf
            j["lines"].append({"product": name, "type": ptype, "unit": unit or "", "used": qty,
                               "leftover": leftovers.get((pid, prod), 0.0), "estimated": estimated.get((pid, prod)),
                               "sf": sf, "cost": qty * float(price or 0)})
        out = []
        for j in jobs.values():
            inst, floor = j["installed_sf"], j["floor_sf"]
            # Só calcula a perda quando o SF instalado foi lançado de verdade nos
            # Work Types (muitos jobs antigos têm qty 1–4 em vez do SF)
            j["sf_missing"] = bool(floor) and inst < floor * 0.3
            j["waste_pct"] = ((floor - inst) / inst * 100) if inst and floor and not j["sf_missing"] else None
            out.append(j)
        return out

    def open_material_usage_dialog(self):
        try:
            jobs = self._material_usage_rows()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not load the materials:\n{e}")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Material usage")
        dialog.resize(1000, 640)
        layout = QVBoxLayout(dialog)
        intro = QLabel("Flooring launched (boxes × SF per box) against the SF installed in the Work Types = waste. "
                       "When the job came from an Estimate, Estimated × Used shows how close the quote was. "
                       "Leftover = what went back to Stock.")
        intro.setWordWrap(True)
        intro.setStyleSheet("color:#475569;")
        layout.addWidget(intro)
        jobs_t = QTableWidget(len(jobs), 5)
        jobs_t.setObjectName("table_material_usage_jobs")
        jobs_t.setHorizontalHeaderLabels(["Job Code", "Installed SF", "Flooring SF", "Waste", "Material cost"])
        jobs_t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        jobs_t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        jobs_t.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        jobs_t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        jobs_t.verticalHeader().setVisible(False)
        jobs_t.setMaximumHeight(260)
        for r, j in enumerate(jobs):
            waste = j["waste_pct"]
            cells = [j["code"], f"{j['installed_sf']:,.0f}" if j["installed_sf"] else "—",
                     f"{j['floor_sf']:,.0f}" if j["floor_sf"] else "—",
                     f"{waste:+.1f}%" if waste is not None else ("SF not entered" if j["sf_missing"] else "—"),
                     _money(sum(l["cost"] for l in j["lines"]))]
            for c, v in enumerate(cells):
                item = QTableWidgetItem(v)
                if c == 3 and waste is not None:
                    item.setForeground(QColor("#B91C1C" if waste > 15 else "#B26A00" if waste > 10 else "#15803D"))
                    item.setToolTip("More flooring launched than installed — boxes left over, cuts, or SF not "
                                    "entered in the Work Types." if waste > 0 else
                                    "Less flooring launched than installed — check the materials of this job.")
                if c == 3 and j["sf_missing"]:
                    item.setForeground(QColor("#64748B"))
                    item.setToolTip("Put the installed SF in the job's Work Types (e.g. Engineered Wood 2,400 SF) "
                                    "to see the waste.")
                jobs_t.setItem(r, c, item)
        layout.addWidget(jobs_t)
        detail_lbl = QLabel("Pick a Job Code to see its materials")
        detail_lbl.setStyleSheet("font-weight:700; color:#334155; padding-top:6px;")
        layout.addWidget(detail_lbl)
        lines_t = QTableWidget(0, 7)
        lines_t.setObjectName("table_material_usage_lines")
        lines_t.setHorizontalHeaderLabels(["Type", "Product", "Estimated", "Used", "Leftover",
                                           "Difference", "Cost"])
        lines_t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        lines_t.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        lines_t.verticalHeader().setVisible(False)
        layout.addWidget(lines_t, 1)
        close = QPushButton("Close")
        close.clicked.connect(dialog.accept)
        bottom = QHBoxLayout()
        bottom.addStretch(1)
        bottom.addWidget(close)
        layout.addLayout(bottom)

        def show_job(row):
            if row < 0 or row >= len(jobs):
                return
            j = jobs[row]
            detail_lbl.setText(f"{j['code']} — materials")
            lines_t.setRowCount(len(j["lines"]))
            for r, l in enumerate(j["lines"]):
                est = l["estimated"]
                diff = ""
                if est:
                    d = l["used"] - est
                    diff = f"{d:+g} ({d / est * 100:+.0f}%)"
                cells = [l["type"], l["product"], f"{est:g} {l['unit']}" if est else "—",
                         f"{l['used']:g} {l['unit']}", f"{l['leftover']:g}" if l["leftover"] else "",
                         diff, _money(l["cost"])]
                for c, v in enumerate(cells):
                    lines_t.setItem(r, c, QTableWidgetItem(v))

        jobs_t.currentCellChanged.connect(lambda r, *_: show_job(r))
        if jobs:
            jobs_t.selectRow(0)
            show_job(0)
        dialog._jobs = jobs  # usado nos testes
        dialog.exec()

    # ═════════════════════════ CALENDAR (.ics) ═════════════════════════
    @staticmethod
    def _ics_escape(text):
        return (str(text or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
                .replace("\r", "").replace("\n", "\\n"))

    def _schedule_ics(self, start, weeks=8):
        """Texto .ics com um evento (dia inteiro) por dia de trabalho agendado."""
        events = []
        monday = start - timedelta(days=start.weekday())
        for w in range(weeks):
            for r in self._week_schedule_rows(monday + timedelta(days=7 * w)):
                if r["WORK_DATE"] < start:
                    continue
                events.append(r)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//VL Flooring//Schedule//EN", "CALSCALE:GREGORIAN",
                 "METHOD:PUBLISH", f"X-WR-CALNAME:{self._ics_escape(company_settings.COMPANY_NAME)} jobs"]
        for r in events:
            d = r["WORK_DATE"]
            who = r.get("CLIENT_NAME") or r.get("COMPANY_NAME") or r.get("CONTRACTOR_NAME") or ""
            if who and "Select" in who:
                who = r.get("COMPANY_NAME") or r.get("CONTRACTOR_NAME") or ""
            title = " · ".join(x for x in (r.get("JOB_CODE"), who) if x) or "Job"
            place = ", ".join(x for x in (r.get("JOB_ADDRESS"), r.get("JOB_ADDRESS2"), r.get("CITY_NAME"),
                                          r.get("ZIP_CODE")) if x)
            desc = [x for x in (r.get("WORK_TYPES") and f"Services: {r['WORK_TYPES']}",
                                r.get("HELPER_NAME") and f"Crew: {r['HELPER_NAME']}",
                                r.get("STATUS") and f"Status: {r['STATUS']}",
                                r.get("NOTE") and f"Note: {r['NOTE']}") if x]
            lines += ["BEGIN:VEVENT", f"UID:vl-flooring-workday-{r['ID']}@vl-flooring", f"DTSTAMP:{stamp}",
                      f"DTSTART;VALUE=DATE:{d:%Y%m%d}", f"DTEND;VALUE=DATE:{d + timedelta(days=1):%Y%m%d}",
                      f"SUMMARY:{self._ics_escape(title)}"]
            if place:
                lines.append(f"LOCATION:{self._ics_escape(place)}")
            if desc:
                lines.append(f"DESCRIPTION:{self._ics_escape(chr(10).join(desc))}")
            lines.append("END:VEVENT")
        lines.append("END:VCALENDAR")
        return "\r\n".join(lines) + "\r\n", len(events)

    def export_schedule_ics(self, start=None, weeks=8, path=None, quiet=False):
        start = start or date.today()
        try:
            text, n = self._schedule_ics(start, weeks)
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not read the schedule:\n{e}")
            return None
        if not n and not quiet:
            QMessageBox.information(self, "Calendar", f"No jobs scheduled from {start:%m/%d/%Y} in the next {weeks} weeks.")
            return None
        if path is None:
            os.makedirs(registro.EXPORTS_DIR, exist_ok=True)
            suggested = os.path.join(registro.EXPORTS_DIR, f"VL Flooring schedule {start:%Y-%m-%d}.ics")
            path, _ = QFileDialog.getSaveFileName(self, "Save calendar file", suggested, "Calendar (*.ics)")
            if not path:
                return None
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        if not quiet:
            QMessageBox.information(
                self, "Calendar file saved",
                f"{n} work day(s) saved to:\n{path}\n\n"
                "Google Calendar: calendar.google.com → Settings → Import & export → Import → pick this file.\n"
                "iPhone / Outlook: open the file (or e-mail it to yourself and tap it).\n\n"
                "Export again after changing the schedule — days already imported are updated, not duplicated.")
        return path

    def _setup_accountant_tools(self):
        for attr, handler in (("btn_tool_accountant", self.open_accountant_package_dialog),
                              ("btn_tool_material_usage", self.open_material_usage_dialog),
                              ("btn_tool_calendar", lambda: self.export_schedule_ics())):
            btn = QPushButton()
            btn.setObjectName(attr)
            btn.clicked.connect(handler)
            setattr(self.ui, attr, btn)
        # botão no Schedule, junto do "Share week"
        layout = getattr(self.ui, "layout_schedule_side", None)
        if layout is not None:
            btn = QPushButton("  Export to calendar")
            btn.setObjectName("btn_export_schedule_ics")
            btn.setIcon(tabler_icon("calendar", "#37474F", 16))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip("Save the next 8 weeks as a calendar file (.ics) for Google Calendar / phone")
            btn.clicked.connect(lambda: self.export_schedule_ics(
                max(date.today(), self.ui.calendar_schedule.selectedDate().toPython())
                if hasattr(self.ui, "calendar_schedule") else None))
            share = self.findChild(QPushButton, "btn_share_week_schedule")
            idx = layout.indexOf(share) if share is not None else -1
            if idx >= 0:
                layout.insertWidget(idx + 1, btn)
            else:
                layout.addWidget(btn)
            self.ui.btn_export_schedule_ics = btn
