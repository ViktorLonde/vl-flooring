# -*- coding: utf-8 -*-
"""
Depois do job e estoque:

• Stock alerts — mínimo por produto (products.MIN_STOCK). Abaixo do mínimo,
  aparece no "Needs your attention" da Home.
• Sign-off PDF — botão no Job: PDF de entrega com serviços feitos,
  materiais, checklist marcado na hora, até 4 fotos "After" e linhas de
  assinatura do cliente e sua. Salvo em Documents\\VL Flooring\\Completion e
  nos documentos do job; pode ir por e-mail para o cliente.
• Follow-ups — job concluído (todos os dias COMPLETED): 30 dias depois,
  pedir avaliação / indicação; 1 ano depois, revisão da garantia. Tabela
  job_followups guarda o que já foi feito. A Home avisa quando vence.

Métodos da MainWindow (mixin) — veja main_.py.
"""

from datetime import date, timedelta

from app_common import *  # noqa: F401,F403
import registro
import arquivos
from paginas import correio
from paginas.correio import esc
from paginas.moderno import show_toast
from paginas.visual import tabler_icon

COMPLETION_DIR = os.path.join(registro.EXPORTS_DIR, "Completion")
CHECKLIST = [
    "All work in the scope was completed",
    "Floor is clean and free of debris",
    "Transitions, moldings and thresholds installed",
    "Furniture / items put back where agreed",
    "Leftover material left with the customer (or taken away)",
    "Care and maintenance instructions explained",
    "Customer walked through the finished work",
]
FOLLOWUPS = [("REVIEW_30", 30, "30-day check-in — review / referral"),
             ("WARRANTY_1Y", 365, "1-year warranty check")]
FOLLOWUP_TEXT = {
    "REVIEW_30": """Hi {name},

It's been about a month since we finished the floor at {address}. We hope you're enjoying it!

If you're happy with the work, a short review or referring a friend or neighbor would mean a lot to a small business like ours. And if anything doesn't look right, just reply to this e-mail and we'll take care of it.

Thank you!
{company}
{phone}""",
    "WARRANTY_1Y": """Hi {name},

It's been one year since we installed the floor at {address} ({code}). This is a good time for a quick check: gaps, squeaks, loose moldings or anything else you noticed.

Reply to this e-mail or give us a call and we'll schedule a free warranty visit.

Thank you for choosing us!
{company}
{phone}""",
}
_PRIMARY_BTN = ("QPushButton { background-color: #1565C0; color: #FFFFFF; border: none; border-radius: 6px; "
                "padding: 8px 16px; font-weight: 700; } QPushButton:hover { background-color: #1E88E5; }")
_SMALL_BTN = ("QPushButton { background-color: #EEF2F7; color: #37474F; border: 1px solid #D0D7DE; "
              "border-radius: 6px; padding: 6px 12px; font-size: 12px; font-weight: 600; } "
              "QPushButton:hover { background-color: #E1E8F0; }")


def _fmt_qty(q):
    return f"{float(q or 0):,.2f}".rstrip("0").rstrip(".")


class AfterJobMixin:
    def _setup_after_job_tools(self):
        ui = self.ui
        for attr, handler in (("btn_tool_stock_alerts", self.open_stock_alerts_dialog),
                              ("btn_tool_followups", self.open_followups_dialog)):
            btn = QPushButton()
            btn.setObjectName(attr)
            btn.clicked.connect(lambda _c=False, h=handler: h())
            setattr(ui, attr, btn)
        btn = QPushButton("  Sign-off PDF")
        btn.setObjectName("btn_job_signoff")
        btn.setIcon(tabler_icon("circle-check", "#37474F", 16))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip("Completion sheet with checklist and customer signature")
        btn.setStyleSheet(_SMALL_BTN)
        btn.clicked.connect(lambda: self.open_signoff_dialog())
        photos = getattr(ui, "btn_job_photos", None)
        header = ui.hboxLayout
        idx = header.indexOf(photos) + 1 if photos is not None else header.count()
        header.insertWidget(idx, btn)
        ui.btn_job_signoff = btn

    # ═════════════════════════ STOCK ALERTS ═════════════════════════
    def _stock_levels(self):
        """[(id, tipo, nome, marca, unidade, em estoque, mínimo)]"""
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT p.ID, p.TYPE, p.NAME, COALESCE(p.BRAND, ''), COALESCE(p.UNIT, ''),
                   COALESCE((SELECT SUM(m.QUANTITY) FROM inventory_moves m WHERE m.PRODUCT_ID = p.ID), 0),
                   COALESCE(p.MIN_STOCK, 0)
            FROM products p ORDER BY p.TYPE, p.NAME""")
        rows = [(a, b, c, d, e, float(f), float(g)) for a, b, c, d, e, f, g in cur.fetchall()]
        cur.close()
        conn.close()
        return rows

    def _low_stock(self):
        return [r for r in self._stock_levels() if r[6] > 0 and r[5] < r[6] - 1e-6]

    def open_stock_alerts_dialog(self):
        try:
            rows = self._stock_levels()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not load the stock:\n{e}")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Stock alerts — minimum per product")
        dialog.resize(900, 620)
        layout = QVBoxLayout(dialog)
        intro = QLabel("Set the minimum you want to keep of each product. When the stock goes below it, "
                       "Home → Needs your attention tells you to buy more. 0 = no alert.")
        intro.setWordWrap(True)
        layout.addWidget(intro)
        table = QTableWidget(len(rows), 5)
        table.setObjectName("table_stock_alerts")
        table.setHorizontalHeaderLabels(["Product", "Unit", "In stock", "Minimum", "Status"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(42)
        spins = []

        def status_item(stock, minimum):
            low = minimum > 0 and stock < minimum - 1e-6
            it = QTableWidgetItem("⚠️ buy more" if low else ("ok" if minimum > 0 else "—"))
            it.setForeground(QColor("#C62828" if low else "#15803D" if minimum > 0 else "#94A3B8"))
            return it

        for r, (pid, ptype, name, brand, unit, stock, minimum) in enumerate(rows):
            table.setItem(r, 0, QTableWidgetItem(f"{name}" + (f" ({brand})" if brand else "") +
                                                 (f"  ·  {ptype}" if ptype else "")))
            table.setItem(r, 1, QTableWidgetItem(unit))
            it = QTableWidgetItem(_fmt_qty(stock))
            it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(r, 2, it)
            s = QDoubleSpinBox()
            s.setRange(0, 100_000)
            s.setDecimals(2)
            s.setValue(minimum)
            s.valueChanged.connect(lambda v, row=r, st=stock: table.setItem(row, 4, status_item(st, v)))
            table.setCellWidget(r, 3, s)
            table.setItem(r, 4, status_item(stock, minimum))
            spins.append((pid, s, minimum))
        layout.addWidget(table, 1)
        row = QHBoxLayout()
        row.addStretch(1)
        cancel, save = QPushButton("Close"), QPushButton("  Save minimums")
        save.setObjectName("btn_save_stock_minimums")
        save.setIcon(tabler_icon("device-floppy", "#FFFFFF", 16))
        save.setStyleSheet(_PRIMARY_BTN)
        row.addWidget(cancel)
        row.addWidget(save)
        layout.addLayout(row)

        def do_save():
            changed = [(s.value(), pid) for pid, s, old in spins if abs(s.value() - old) > 1e-6]
            if changed:
                try:
                    conn = self._get_connection()
                    cur = conn.cursor()
                    cur.executemany("UPDATE products SET MIN_STOCK=%s WHERE ID=%s", changed)
                    conn.commit()
                    cur.close()
                    conn.close()
                except (MySQLError, RuntimeError) as e:
                    QMessageBox.critical(dialog, "Database Error", f"Could not save:\n{e}")
                    return
                show_toast(f"{len(changed)} minimum(s) saved.", "success", self)
            dialog.accept()
            if hasattr(self, "show_attention_summary"):
                self.show_attention_summary()

        save.clicked.connect(do_save)
        cancel.clicked.connect(dialog.reject)
        dialog._spins, dialog._save = spins, do_save  # testes
        dialog.exec()

    # ═════════════════════════ SIGN-OFF PDF ═════════════════════════
    def _signoff_data(self, project_id):
        conn = self._get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT jp.ID, jp.CODE, COALESCE(cl.FULL_NAME, '') AS CLIENT, COALESCE(cl.EMAIL, '') AS CLIENT_EMAIL,
                   COALESCE(NULLIF(co.COMPANY_NAME, ''), NULLIF(ct.COMPANY_NAME, ''), ct.FULL_NAME, '') AS PARTNER,
                   COALESCE(NULLIF(co.EMAIL, ''), NULLIF(ct.COMPANY_EMAIL, ''), ct.EMAIL, '') AS PARTNER_EMAIL
            FROM job_projects jp LEFT JOIN clients cl ON cl.ID = jp.CLIENT_ID
            LEFT JOIN companies co ON co.ID = jp.COMPANY_ID LEFT JOIN contractors ct ON ct.ID = jp.CONTRACTOR_ID
            WHERE jp.ID = %s""", (project_id,))
        d = cur.fetchone() or {}
        cur.execute("""
            SELECT MIN(wd.WORK_DATE) AS FIRST_DAY, MAX(wd.WORK_DATE) AS LAST_DAY, COUNT(*) AS N,
                   SUBSTRING_INDEX(GROUP_CONCAT(NULLIF(wd.JOB_ADDRESS, '') ORDER BY wd.WORK_DATE DESC SEPARATOR '\\n'), '\\n', 1) AS ADDRESS,
                   SUBSTRING_INDEX(GROUP_CONCAT(ci.CITY ORDER BY wd.WORK_DATE DESC SEPARATOR '\\n'), '\\n', 1) AS CITY,
                   SUBSTRING_INDEX(GROUP_CONCAT(NULLIF(cl.FULL_NAME, '') ORDER BY wd.WORK_DATE DESC SEPARATOR '\\n'), '\\n', 1) AS DAY_CLIENT
            FROM work_days wd LEFT JOIN cities ci ON ci.ID = wd.CITY_ID LEFT JOIN clients cl ON cl.ID = wd.CLIENT_ID
            WHERE wd.JOB_PROJECT_ID = %s AND COALESCE(wd.STATUS, '') <> 'CANCELLED'""", (project_id,))
        d.update(cur.fetchone() or {})
        cur.execute("""
            SELECT wt.CATEGORY, wt.NAME, wt.UNIT, SUM(x.QTY) AS QTY
            FROM work_day_work_types x JOIN work_types wt ON wt.ID = x.WORK_TYPE_ID
            JOIN work_days wd ON wd.ID = x.WORK_DAY_ID
            WHERE wd.JOB_PROJECT_ID = %s AND COALESCE(wd.STATUS, '') <> 'CANCELLED'
            GROUP BY wt.ID, wt.CATEGORY, wt.NAME, wt.UNIT ORDER BY FIELD(wt.CATEGORY, 'DEMOLITION', 'PREPARATION',
            'INSTALLATION', 'REPARO', 'OTHERS', 'DELIVERY'), wt.NAME""", (project_id,))
        d["services"] = cur.fetchall()
        cur.execute("""
            SELECT p.NAME, COALESCE(p.BRAND, '') AS BRAND, COALESCE(p.UNIT, '') AS UNIT, SUM(m.QUANTITY) AS QTY
            FROM job_materials m JOIN products p ON p.ID = m.PRODUCT_ID WHERE m.JOB_PROJECT_ID = %s
            GROUP BY p.ID, p.NAME, p.BRAND, p.UNIT ORDER BY p.TYPE, p.NAME""", (project_id,))
        d["materials"] = cur.fetchall()
        cur.execute("SELECT FILE_PATH FROM documents WHERE ENTITY_TYPE='JOB_PROJECT' AND ENTITY_ID=%s "
                    "AND CATEGORY = 'Job Photo - After' ORDER BY UPLOADED_AT DESC, ID DESC LIMIT 4", (project_id,))
        d["photos"] = [arquivos.resolve(p) for (p,) in cur.fetchall() if p]
        cur.close()
        conn.close()
        d["customer"] = d.get("CLIENT") or d.get("DAY_CLIENT") or d.get("PARTNER") or ""
        d["email"] = d.get("CLIENT_EMAIL") or d.get("PARTNER_EMAIL") or ""
        return d

    def _build_signoff_pdf(self, path, d, checked, notes=""):
        styles = getSampleStyleSheet()
        small = ParagraphStyle("so_small", parent=styles["Normal"], fontSize=9, leading=12)
        story = correio.brand_header("JOB COMPLETION", [f"<b>{esc(d['CODE'])}</b>", f"Date: {date.today():%m/%d/%Y}"])
        place = ", ".join(x for x in (d.get("ADDRESS"), d.get("CITY")) if x)
        when = ""
        if d.get("FIRST_DAY") and d.get("LAST_DAY"):
            when = (f"{d['FIRST_DAY']:%m/%d/%Y}" if d["FIRST_DAY"] == d["LAST_DAY"]
                    else f"{d['FIRST_DAY']:%m/%d/%Y} – {d['LAST_DAY']:%m/%d/%Y}")
        info = [f"<b>Customer:</b> {esc(d['customer'])}"]
        if place:
            info.append(f"<b>Job address:</b> {esc(place)}")
        if when:
            info.append(f"<b>Work dates:</b> {when}")
        story += [Paragraph("<br/>".join(info), styles["Normal"]), Spacer(1, 12)]
        if d["services"]:
            data = [["Work done", "Qty"]] + [[Paragraph(esc(f"{(s['CATEGORY'] or '').title()} — {s['NAME']}"), small),
                                              f"{_fmt_qty(s['QTY'])} {s['UNIT'] or ''}"] for s in d["services"]]
            t = Table(data, colWidths=[5.6 * inch, 1.4 * inch], repeatRows=1)
            t.setStyle(correio.table_style([("ALIGN", (1, 0), (1, -1), "RIGHT")]))
            story += [t, Spacer(1, 10)]
        if d["materials"]:
            data = [["Materials used", "Qty"]] + [[Paragraph(esc(m["NAME"] + (f" ({m['BRAND']})" if m["BRAND"] else "")), small),
                                                   f"{_fmt_qty(m['QTY'])} {m['UNIT']}"] for m in d["materials"]]
            t = Table(data, colWidths=[5.6 * inch, 1.4 * inch], repeatRows=1)
            t.setStyle(correio.table_style([("ALIGN", (1, 0), (1, -1), "RIGHT")]))
            story += [t, Spacer(1, 10)]
        story.append(Paragraph("<b>Checklist</b>", styles["Normal"]))
        story.append(Spacer(1, 2))
        rows =[[("[X]" if ok else "[  ]"), Paragraph(esc(text), small)] for text, ok in checked]
        if rows:
            t = Table(rows, colWidths=[0.45 * inch, 6.55 * inch])
            t.setStyle(TableStyle([("FONTNAME", (0, 0), (0, -1), "Courier-Bold"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                   ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
            story.append(t)
        if notes.strip():
            story += [Spacer(1, 8), Paragraph("<b>Notes</b>", styles["Normal"]),
                      Paragraph(esc(notes).replace("\n", "<br/>"), small)]
        photos = [p for p in d.get("photos", []) if os.path.exists(p)]
        if photos:
            cells = []
            for p in photos:
                try:
                    img = Image(p)
                    ratio = img.imageHeight / float(img.imageWidth or 1)
                    w = 1.65 * inch
                    cells.append(Image(p, width=w, height=min(w * ratio, 1.8 * inch)))
                except Exception:
                    continue
            if cells:
                story += [Spacer(1, 10), Paragraph("<b>Finished work</b>", styles["Normal"]), Spacer(1, 4),
                          Table([cells], colWidths=[1.75 * inch] * len(cells))]
        story += [Spacer(1, 16), Paragraph(
            "I confirm the work above was completed to my satisfaction and the job site was left clean.", small),
            Spacer(1, 28)]
        sig = Table([["_______________________________", "", "_______________________________"],
                     [f"Customer — {d['customer']}", "", f"{company_settings.COMPANY_NAME}"],
                     ["Date: ______________", "", "Date: ______________"]],
                    colWidths=[3.2 * inch, 0.6 * inch, 3.2 * inch])
        sig.setStyle(TableStyle([("FONTSIZE", (0, 0), (-1, -1), 9), ("TOPPADDING", (0, 0), (-1, -1), 3)]))
        story.append(sig)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        SimpleDocTemplate(path, pagesize=letter, leftMargin=0.6 * inch, rightMargin=0.6 * inch,
                          topMargin=0.6 * inch, bottomMargin=0.6 * inch).build(story)
        return path

    def open_signoff_dialog(self, project_id=None):
        if not REPORTLAB_AVAILABLE:
            QMessageBox.critical(self, "Missing Dependency", "The 'reportlab' package is not installed.")
            return
        if project_id is None:
            code, project_id = self._current_project()
            if not project_id:
                QMessageBox.information(self, "Choose a job", "Open a job with a Job Code first, then click Sign-off PDF.")
                return
        try:
            d = self._signoff_data(project_id)
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not load the job:\n{e}")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Sign-off — {d.get('CODE')}")
        dialog.resize(640, 600)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(f"<b>{esc(d.get('CODE'))}</b> · {esc(d['customer'])} · "
                                f"{len(d['services'])} service(s), {len(d['materials'])} material(s), "
                                f"{len(d['photos'])} 'After' photo(s)"))
        layout.addWidget(QLabel("Tick what was done:"))
        checks = []
        for text in CHECKLIST:
            c = QCheckBox(text)
            c.setChecked(True)
            layout.addWidget(c)
            checks.append(c)
        layout.addWidget(QLabel("Notes (optional):"))
        notes = QTextEdit()
        notes.setMaximumHeight(110)
        layout.addWidget(notes)
        layout.addStretch(1)
        row = QHBoxLayout()
        b_close, b_mail, b_pdf = QPushButton("Close"), QPushButton("  PDF + e-mail to customer"), QPushButton("  Create PDF")
        b_mail.setIcon(tabler_icon("send", "#37474F", 16))
        b_pdf.setIcon(tabler_icon("download", "#FFFFFF", 16))
        b_pdf.setStyleSheet(_PRIMARY_BTN)
        row.addWidget(b_mail)
        row.addStretch(1)
        row.addWidget(b_close)
        row.addWidget(b_pdf)
        layout.addLayout(row)

        def build():
            path = os.path.join(COMPLETION_DIR, f"Completion_{d['CODE']}_{date.today():%Y-%m-%d}.pdf")
            try:
                self._build_signoff_pdf(path, d, [(c.text(), c.isChecked()) for c in checks], notes.toPlainText())
            except Exception as e:
                logging.getLogger("vl_flooring").exception("sign-off PDF failed")
                QMessageBox.critical(dialog, "PDF Error", f"Could not create the PDF:\n{e}")
                return None
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                cur.execute("DELETE FROM documents WHERE ENTITY_TYPE='JOB_PROJECT' AND ENTITY_ID=%s AND FILE_PATH=%s",
                            (project_id, path))
                cur.execute("INSERT INTO documents (CATEGORY, ENTITY_TYPE, ENTITY_ID, NAME, FILE_PATH, NOTES) "
                            "VALUES ('Completion Sign-off', 'JOB_PROJECT', %s, %s, %s, '')",
                            (project_id, os.path.basename(path), path))
                conn.commit()
                cur.close()
                conn.close()
            except (MySQLError, RuntimeError):
                logging.getLogger("vl_flooring").exception("sign-off document not registered")
            dialog._path = path
            return path

        def make_pdf():
            path = build()
            if path:
                QDesktopServices.openUrl(QUrl.fromLocalFile(path))
                dialog.accept()

        def mail():
            path = build()
            if not path:
                return
            body = self._fill(
                "Hi {name},\n\nThank you for choosing us! Attached is the completion sheet for {code}. "
                "Please look it over, sign and send it back (a photo is fine).\n\n{company}\n{phone}",
                name=(d["customer"] or "there").split(" ")[0], code=d["CODE"])
            if self._compose_dialog(dialog, "Send sign-off", d["email"],
                                    f"Job completed — {d['CODE']} — {company_settings.COMPANY_NAME}", body,
                                    attachments=[path]):
                show_toast("Sign-off sent.", "success", self)
                dialog.accept()

        b_pdf.clicked.connect(make_pdf)
        b_mail.clicked.connect(mail)
        b_close.clicked.connect(dialog.reject)
        dialog._build, dialog._checks = build, checks  # testes
        dialog.exec()

    # ═════════════════════════ FOLLOW-UPS ═════════════════════════
    def _followups_due(self, today=None, ahead=7):
        """Follow-ups de jobs concluídos que vencem até hoje + ahead e não
        foram feitos: [{pid, code, customer, email, address, kind, label, due, finished}]."""
        today = today or date.today()
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT jp.ID, jp.CODE, MAX(wd.WORK_DATE),
                   COALESCE(NULLIF(cl.FULL_NAME, ''), NULLIF(co.COMPANY_NAME, ''), NULLIF(ct.COMPANY_NAME, ''), ct.FULL_NAME, ''),
                   COALESCE(cl.EMAIL, ''),  -- só o dono da casa (não o contractor)
                   SUBSTRING_INDEX(GROUP_CONCAT(NULLIF(wd.JOB_ADDRESS, '') ORDER BY wd.WORK_DATE DESC SEPARATOR '\\n'), '\\n', 1)
            FROM job_projects jp
            JOIN work_days wd ON wd.JOB_PROJECT_ID = jp.ID AND COALESCE(wd.STATUS, '') <> 'CANCELLED'
            LEFT JOIN clients cl ON cl.ID = jp.CLIENT_ID
            LEFT JOIN companies co ON co.ID = jp.COMPANY_ID
            LEFT JOIN contractors ct ON ct.ID = jp.CONTRACTOR_ID
            GROUP BY jp.ID, jp.CODE, 4, 5
            HAVING SUM(CASE WHEN wd.STATUS = 'COMPLETED' THEN 0 ELSE 1 END) = 0""")
        jobs = cur.fetchall()
        cur.execute("SELECT JOB_PROJECT_ID, KIND FROM job_followups")
        done = set(cur.fetchall())
        cur.close()
        conn.close()
        out = []
        for pid, code, last_day, customer, email, address in jobs:
            for kind, days, label in FOLLOWUPS:
                due = last_day + timedelta(days=days)
                if (pid, kind) in done or due > today + timedelta(days=ahead):
                    continue
                # o de 30 dias não faz sentido depois de 1 ano
                if kind == "REVIEW_30" and today > last_day + timedelta(days=180):
                    continue
                out.append({"pid": pid, "code": code, "customer": customer or "", "email": (email or "").strip(),
                            "address": address or "", "kind": kind, "label": label, "due": due, "finished": last_day})
        out.sort(key=lambda f: f["due"])
        return out

    def _mark_followup(self, pid, kind, result, note=""):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO job_followups (JOB_PROJECT_ID, KIND, RESULT, NOTE, DONE_AT) VALUES (%s,%s,%s,%s,NOW()) "
                    "ON DUPLICATE KEY UPDATE RESULT=VALUES(RESULT), NOTE=VALUES(NOTE), DONE_AT=NOW()",
                    (pid, kind, result, note or None))
        conn.commit()
        cur.close()
        conn.close()

    def open_followups_dialog(self):
        try:
            items = self._followups_due()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not load the follow-ups:\n{e}")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Follow-ups after the job")
        dialog.resize(940, 520)
        layout = QVBoxLayout(dialog)
        intro = QLabel("Finished jobs (all days COMPLETED): 30 days later ask for a review or a referral; one year "
                       "later offer the warranty check. Send the e-mail, or mark it done if you called.")
        intro.setWordWrap(True)
        layout.addWidget(intro)
        table = QTableWidget(0, 6)
        table.setObjectName("table_followups")
        table.setHorizontalHeaderLabels(["Due", "Job Code", "Customer", "E-mail", "Follow-up", "Finished"])
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        layout.addWidget(table, 1)
        empty = QLabel("Nothing due right now. 👍")
        empty.setStyleSheet("color:#6B7C93;")
        layout.addWidget(empty)
        row = QHBoxLayout()
        b_mail, b_done, b_skip, b_close = (QPushButton("  Send e-mail"), QPushButton("Mark done (called / visited)"),
                                           QPushButton("Skip"), QPushButton("Close"))
        b_mail.setIcon(tabler_icon("send", "#FFFFFF", 16))
        b_mail.setStyleSheet(_PRIMARY_BTN)
        for b in (b_mail, b_done, b_skip):
            row.addWidget(b)
        row.addStretch(1)
        row.addWidget(b_close)
        layout.addLayout(row)

        def fill():
            table.setRowCount(len(items))
            today = date.today()
            for r, f in enumerate(items):
                vals = [f"{f['due']:%m/%d/%Y}" + ("" if f["due"] <= today else " (soon)"), f["code"], f["customer"],
                        f["email"] or "no e-mail", f["label"], f"{f['finished']:%m/%d/%Y}"]
                for c, v in enumerate(vals):
                    table.setItem(r, c, QTableWidgetItem(v))
            empty.setVisible(not items)

        def current():
            r = table.currentRow()
            if r < 0 or r >= len(items):
                QMessageBox.information(dialog, "Follow-ups", "Click a line first.")
                return None, None
            return r, items[r]

        def finish(r, f, result):
            try:
                self._mark_followup(f["pid"], f["kind"], result)
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", str(e))
                return
            items.pop(r)
            fill()

        def mail():
            r, f = current()
            if f is None:
                return
            body = self._fill(FOLLOWUP_TEXT[f["kind"]], name=(f["customer"] or "there").split(" ")[0],
                              address=f["address"] or "your home", code=f["code"])
            subject = ("How is your new floor? — " if f["kind"] == "REVIEW_30" else "1-year floor check — ") + \
                company_settings.COMPANY_NAME
            if self._compose_dialog(dialog, f"Follow-up {f['code']}", f["email"], subject, body):
                finish(r, f, "SENT")

        def done():
            r, f = current()
            if f is not None:
                finish(r, f, "DONE")

        def skip():
            r, f = current()
            if f is not None:
                finish(r, f, "SKIPPED")

        b_mail.clicked.connect(mail)
        b_done.clicked.connect(done)
        b_skip.clicked.connect(skip)
        b_close.clicked.connect(dialog.accept)
        fill()
        dialog._items, dialog._done, dialog._table = items, done, table  # testes
        dialog.exec()

    # ═════════════════════════ HOME ═════════════════════════
    def _extra_attention_items(self):
        """Itens novos do 'Needs your attention' (chamado por sessao.py)."""
        items = []
        if hasattr(self, "_weekly_invoice_attention_items"):
            items += self._weekly_invoice_attention_items()
        for maker in ("_statement_attention_item", "_tax_attention_item", "_data_check_attention_item"):
            fn = getattr(self, maker, None)
            item = fn() if fn else None
            if item:
                items.append(item)
        try:
            low = self._low_stock()
            if low:
                names = ", ".join(r[2] for r in low[:2]) + ("…" if len(low) > 2 else "")
                items.append(("package", "#C62828", f"Low stock: {names}", self.open_stock_alerts_dialog))
        except (MySQLError, RuntimeError):
            pass
        try:
            # só os que venceram há pouco — os antigos ficam no cartão Follow-ups, sem lotar a Home
            recent = date.today() - timedelta(days=30)
            due = [f for f in self._followups_due(ahead=0) if f["due"] >= recent]
            if due:
                items.append(("send", "#1565C0",
                              f"{len(due)} follow-up{'s' if len(due) != 1 else ''} with past customers",
                              self.open_followups_dialog))
        except (MySQLError, RuntimeError):
            pass
        return items
