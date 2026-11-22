# -*- coding: utf-8 -*-
"""
E-mails para clientes, helpers e para você (conta de Settings → Email):

• Recibo de pagamento — depois de registrar um pagamento, oferece mandar
  "Payment received, thank you" (valor, data, forma, total e saldo). Você
  vê e pode editar o texto antes; nada sai sem clicar Send.
• Statement mensal — PDF por empresa/contractor/cliente com os invoices em
  aberto e o atraso (0–30, 31–60, 61–90, 90+ dias). Salvo em
  Documents\\VL Flooring\\Statements\\<ano-mês>\\ e enviado por e-mail com
  um clique (você escolhe quem). Do dia 1º ao 7, a Home lembra.
• Estimate por e-mail — botão no orçamento: PDF anexado, status vira SENT
  e guarda a data de envio (estimates.SENT_AT).
• Agenda da semana por helper — no "Share week": cada helper recebe só os
  dias e endereços dele (precisa do e-mail no cadastro do helper).
• Vencimentos de Compliance — e-mail PARA VOCÊ (mesmo destino do Weekly
  Summary) 30 e 7 dias antes de vencer seguro, licença etc. Uma vez por
  vencimento, nos dois computadores (compliance_items.REMINDED_30_FOR /
  REMINDED_7_FOR guardam para qual data já avisou).

Métodos da MainWindow (mixin) — veja main_.py.
"""

import threading
from datetime import date, timedelta
from urllib.parse import quote

from PySide6.QtCore import QSettings

from app_common import *  # noqa: F401,F403
import registro
from paginas import correio
from paginas.correio import esc
from paginas.moderno import show_toast
from paginas.visual import tabler_icon

STATEMENTS_DIR = os.path.join(registro.EXPORTS_DIR, "Statements")
ESTIMATES_DIR = os.path.join(registro.EXPORTS_DIR, "Estimates")
BUCKETS = ["0–30", "31–60", "61–90", "90+"]

_PRIMARY_BTN = ("QPushButton { background-color: #1565C0; color: #FFFFFF; border: none; border-radius: 6px; "
                "padding: 8px 16px; font-weight: 700; } QPushButton:hover { background-color: #1E88E5; }")
_WARN_QSS = "background:#FFF3CD; color:#8A6D00; padding:8px; border-radius:6px;"

RECEIPT_TEMPLATE = """Hi {name},

We received your payment of {amount} on {date} ({method}) for invoice #{invoice}. Thank you!

Invoice total: {total}
Paid so far: {paid}
Balance: {balance}

{company}
{phone}"""

STATEMENT_TEMPLATE = """Hi {name},

Attached is your statement for {month}: {count} open invoice(s), {total} in total.

If any payment is already on its way, please disregard this message. Thank you for your business!

{company}
{phone}"""

ESTIMATE_TEMPLATE = """Hi {name},

Thank you for the opportunity. Attached is estimate {code} for {address} — total {total}, valid until {valid}.

Let us know if you have any questions or would like to schedule the work.

{company}
{phone}"""


def _money(v):
    return f"${float(v or 0):,.2f}"


def _bucket(days):
    days = int(days or 0)
    return 0 if days <= 30 else 1 if days <= 60 else 2 if days <= 90 else 3


class CustomerEmailsMixin:
    # ═════════════════════════ janela de envio ═════════════════════════
    def _compose_dialog(self, parent, title, to, subject, body, attachments=(), note=""):
        """Mostra o e-mail pronto (Para, Assunto, Texto, anexos) e envia ao
        confirmar. Devolve True se enviou."""
        d = QDialog(parent)
        d.setWindowTitle(title)
        d.resize(640, 560)
        lay = QVBoxLayout(d)
        if not correio.smtp_ready():
            w = QLabel("⚠ The e-mail account is not set up yet (Settings → Email).")
            w.setStyleSheet(_WARN_QSS)
            lay.addWidget(w)
        if note:
            n = QLabel(note)
            n.setWordWrap(True)
            n.setStyleSheet("color:#6B7C93;")
            lay.addWidget(n)
        g = QGridLayout()
        txt_to, txt_subject = QLineEdit(to or ""), QLineEdit(subject)
        txt_to.setPlaceholderText("customer@email.com")
        g.addWidget(QLabel("To"), 0, 0)
        g.addWidget(txt_to, 0, 1)
        g.addWidget(QLabel("Subject"), 1, 0)
        g.addWidget(txt_subject, 1, 1)
        lay.addLayout(g)
        txt = QTextEdit()
        txt.setPlainText(body)
        lay.addWidget(txt, 1)
        if attachments:
            lay.addWidget(QLabel("📎 " + ", ".join(os.path.basename(a) for a in attachments)))
        row = QHBoxLayout()
        row.addStretch(1)
        cancel, send = QPushButton("Not now"), QPushButton("  Send")
        send.setIcon(tabler_icon("send", "#FFFFFF", 16))
        send.setStyleSheet(_PRIMARY_BTN)
        row.addWidget(cancel)
        row.addWidget(send)
        lay.addLayout(row)
        result = {"sent": False}

        def do_send():
            to_addr = txt_to.text().strip()
            if "@" not in to_addr:
                QMessageBox.information(d, "E-mail", "Enter the e-mail address.")
                return
            if not correio.smtp_ready():
                QMessageBox.warning(d, "E-mail not set up", "Set up the e-mail account in Settings → Email first.")
                return
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                correio.send_mail(to_addr, txt_subject.text().strip(), txt.toPlainText(), attachments=attachments)
            except Exception as e:
                QApplication.restoreOverrideCursor()
                QMessageBox.critical(d, "Not sent", f"The e-mail could not be sent:\n{e}")
                return
            QApplication.restoreOverrideCursor()
            logging.getLogger("vl_flooring").info("e-mail sent to %s: %s", to_addr, txt_subject.text())
            result["sent"], result["to"] = True, to_addr
            d.accept()

        send.clicked.connect(do_send)
        cancel.clicked.connect(d.reject)
        d._fields = (txt_to, txt_subject, txt, do_send)  # testes
        d.exec()
        self._last_compose = result
        return result["sent"]

    def _fill(self, template, **values):
        values.setdefault("company", company_settings.COMPANY_NAME)
        values.setdefault("phone", company_settings.COMPANY_PHONE)
        try:
            return template.format(**values)
        except (KeyError, IndexError, ValueError):
            return template

    # ═════════════════════════ recibo de pagamento ═════════════════════════
    def _invoice_partner(self, kind, invoice_id):
        src = next((s for s in correio.PARTNER_SOURCES if s[0] == kind), None)
        if not src:
            return None
        _k, table, fk, partner, name_sql, email_sql = src
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute(f"SELECT {name_sql}, {email_sql}, COALESCE(i.TOTAL_AMOUNT, 0), COALESCE(i.AMOUNT_PAID, 0) "
                    f"FROM {table} i LEFT JOIN {partner} p ON p.ID = i.{fk} WHERE i.ID = %s", (invoice_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if not row:
            return None
        name, email, total, paid = row
        return {"name": name or "", "email": (email or "").strip(), "total": float(total), "paid": float(paid)}

    def offer_payment_receipt(self, parent, kind, invoice_id, amount, paid_date, method):
        """Chamado depois de gravar um pagamento. Só pergunta se o e-mail
        está configurado; sem e-mail do cliente, deixa digitar."""
        if not correio.smtp_ready():
            return False
        try:
            info = self._invoice_partner(kind, invoice_id)
        except (MySQLError, RuntimeError):
            return False
        if not info:
            return False
        if isinstance(paid_date, str):
            try:
                paid_date = date.fromisoformat(paid_date)
            except ValueError:
                paid_date = date.today()
        body = self._fill(RECEIPT_TEMPLATE, name=info["name"] or "there", amount=_money(amount),
                          date=f"{paid_date:%m/%d/%Y}", method=method or "payment", invoice=invoice_id,
                          total=_money(info["total"]), paid=_money(info["paid"]),
                          balance=_money(max(info["total"] - info["paid"], 0)))
        subject = f"Payment received — invoice #{invoice_id} — {company_settings.COMPANY_NAME}"
        note = "Send a thank-you receipt for this payment?" + ("" if info["email"] else
                                                                "  (No e-mail on file for this customer.)")
        sent = self._compose_dialog(parent or self, "Payment receipt", info["email"], subject, body, note=note)
        if sent:
            show_toast(f"Receipt sent to {self._last_compose.get('to')}.", "success", self)
        return sent

    # ═════════════════════════ statement mensal ═════════════════════════
    def _statement_data(self):
        """[{kind, partner_id, name, email, invoices: [(id, date, total, paid, open, days)], buckets, total}]"""
        out = []
        conn = self._get_connection()
        cur = conn.cursor()
        for kind, table, fk, partner, name_sql, email_sql in correio.PARTNER_SOURCES:
            cur.execute(f"""
                SELECT i.{fk}, {name_sql}, {email_sql}, i.ID, i.GENERATED_AT, COALESCE(i.TOTAL_AMOUNT, 0),
                       COALESCE(i.AMOUNT_PAID, 0), DATEDIFF(CURDATE(), i.GENERATED_AT), i.PERIOD_FROM, i.PERIOD_TO
                FROM {table} i LEFT JOIN {partner} p ON p.ID = i.{fk}
                WHERE i.STATUS IN ('PENDING', 'PARTIAL') AND COALESCE(i.TOTAL_AMOUNT, 0) - COALESCE(i.AMOUNT_PAID, 0) > 0.009
                ORDER BY i.{fk}, i.GENERATED_AT""")
            groups = {}
            for pid, name, email, iid, gen, total, paid, days, pfrom, pto in cur.fetchall():
                g = groups.setdefault(pid, {"kind": kind, "partner_id": pid, "name": name or "(no name)",
                                            "email": (email or "").strip(), "invoices": [],
                                            "buckets": [0.0] * 4, "total": 0.0})
                open_amt = float(total) - float(paid)
                g["invoices"].append((iid, gen, float(total), float(paid), open_amt, int(days or 0), pfrom, pto))
                g["buckets"][_bucket(days)] += open_amt
                g["total"] += open_amt
            out += list(groups.values())
        cur.close()
        conn.close()
        out.sort(key=lambda g: -g["total"])
        return out

    def _build_statement_pdf(self, path, g):
        styles = getSampleStyleSheet()
        small = ParagraphStyle("st_small", parent=styles["Normal"], fontSize=9, leading=12)
        story = correio.brand_header("STATEMENT", [f"Date: {date.today():%m/%d/%Y}", f"{g['kind']}: {esc(g['name'])}"])
        story.append(Paragraph(f"<b>Statement for:</b> {esc(g['name'])}" +
                               (f"<br/>{esc(g['email'])}" if g["email"] else ""), styles["Normal"]))
        story.append(Spacer(1, 12))
        data = [["Invoice", "Date", "Period", "Total", "Paid", "Open", "Days"]]
        for iid, gen, total, paid, open_amt, days, pfrom, pto in g["invoices"]:
            period = f"{pfrom:%m/%d}–{pto:%m/%d/%y}" if pfrom and pto else ""
            data.append([f"#{iid}", f"{gen:%m/%d/%Y}" if gen else "", period, _money(total), _money(paid),
                         _money(open_amt), str(days)])
        t = Table(data, colWidths=[0.8 * inch, 0.95 * inch, 1.35 * inch, 1.05 * inch, 1.0 * inch, 1.05 * inch, 0.6 * inch],
                  repeatRows=1)
        t.setStyle(correio.table_style([("ALIGN", (3, 0), (-1, -1), "RIGHT")]))
        story += [t, Spacer(1, 14)]
        aging = Table([["Current (0–30)", "31–60 days", "61–90 days", "Over 90 days", "TOTAL DUE"],
                       [_money(x) for x in g["buckets"]] + [_money(g["total"])]],
                      colWidths=[1.36 * inch] * 5)
        aging.setStyle(correio.table_style([("ALIGN", (0, 0), (-1, -1), "CENTER"),
                                            ("FONTNAME", (-1, 1), (-1, 1), "Helvetica-Bold"),
                                            ("FONTSIZE", (0, 1), (-1, 1), 11)]))
        story += [aging, Spacer(1, 16)]
        pay = []
        if hasattr(self, "_invoice_payment_info_lines"):
            try:
                pay = list(self._invoice_payment_info_lines())  # já vem escapado
            except Exception:
                pay = []
        if pay:
            story += [Paragraph("<b>How to pay</b>", styles["Normal"]), Paragraph("<br/>".join(pay), small)]
        story += [Spacer(1, 10), Paragraph("Thank you for your business!", small)]
        os.makedirs(os.path.dirname(path), exist_ok=True)
        SimpleDocTemplate(path, pagesize=letter, leftMargin=0.6 * inch, rightMargin=0.6 * inch,
                          topMargin=0.6 * inch, bottomMargin=0.6 * inch).build(story)
        return path

    def _statement_path(self, g):
        safe = "".join(ch for ch in g["name"] if ch.isalnum() or ch in " -_").strip().replace(" ", "_") or "customer"
        return os.path.join(STATEMENTS_DIR, f"{date.today():%Y-%m}", f"Statement_{safe}_{date.today():%Y-%m-%d}.pdf")

    def open_statements_dialog(self):
        if not REPORTLAB_AVAILABLE:
            QMessageBox.critical(self, "Missing Dependency", "The 'reportlab' package is not installed.")
            return
        try:
            groups = self._statement_data()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not load the invoices:\n{e}")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Customer statements")
        dialog.resize(1060, 600)
        layout = QVBoxLayout(dialog)
        intro = QLabel("One statement per customer with all open invoices and how late they are. "
                       "Tick who should get it by e-mail; PDFs are saved in Documents\\VL Flooring\\Statements.")
        intro.setWordWrap(True)
        layout.addWidget(intro)
        if not correio.smtp_ready():
            w = QLabel("⚠ The e-mail account is not set up yet — you can still save the PDFs.")
            w.setStyleSheet(_WARN_QSS)
            layout.addWidget(w)
        table = QTableWidget(len(groups), 10)
        table.setObjectName("table_statements")
        table.setHorizontalHeaderLabels(["Send", "Type", "Name", "E-mail", "Invoices"] + BUCKETS + ["Total open"])
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        for r, g in enumerate(groups):
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            chk.setCheckState(Qt.CheckState.Checked if g["email"] else Qt.CheckState.Unchecked)
            table.setItem(r, 0, chk)
            vals = [g["kind"], g["name"], g["email"] or "no e-mail", str(len(g["invoices"]))] + \
                   [_money(x) if x else "—" for x in g["buckets"]] + [_money(g["total"])]
            for c, v in enumerate(vals, start=1):
                it = QTableWidgetItem(v)
                if c >= 5:
                    it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if c in (7, 8) and g["buckets"][c - 5] > 0:
                    it.setForeground(QColor("#C62828"))
                table.setItem(r, c, it)
        layout.addWidget(table, 1)
        total = sum(g["total"] for g in groups)
        summary = QLabel(f"{len(groups)} customer(s) with open invoices · {_money(total)} to receive" if groups
                         else "No open invoices — nothing to send. 🎉")
        summary.setStyleSheet("font-weight:700; color:#334155;")
        layout.addWidget(summary)
        layout.addWidget(QLabel("Message ({name}, {month}, {count}, {total} are filled in):"))
        msg = QTextEdit()
        msg.setPlainText(STATEMENT_TEMPLATE)
        msg.setMaximumHeight(140)
        layout.addWidget(msg)
        row = QHBoxLayout()
        btn_pdf = QPushButton("  Open PDF of selected line")
        btn_pdf.setIcon(tabler_icon("download", "#37474F", 16))
        btn_folder = QPushButton("  Save all PDFs")
        btn_folder.setIcon(tabler_icon("folder", "#37474F", 16))
        btn_close = QPushButton("Close")
        btn_send = QPushButton("  Send to ticked")
        btn_send.setObjectName("btn_send_statements")
        btn_send.setIcon(tabler_icon("send", "#FFFFFF", 16))
        btn_send.setStyleSheet(_PRIMARY_BTN)
        for b in (btn_pdf, btn_folder):
            row.addWidget(b)
        row.addStretch(1)
        row.addWidget(btn_close)
        row.addWidget(btn_send)
        layout.addLayout(row)

        def open_pdf():
            r = table.currentRow()
            if r < 0:
                QMessageBox.information(dialog, "Statement", "Click a customer first.")
                return
            try:
                path = self._build_statement_pdf(self._statement_path(groups[r]), groups[r])
            except Exception as e:
                QMessageBox.critical(dialog, "PDF Error", f"Could not create the PDF:\n{e}")
                return
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))

        def save_all():
            paths = []
            try:
                for g in groups:
                    paths.append(self._build_statement_pdf(self._statement_path(g), g))
            except Exception as e:
                QMessageBox.critical(dialog, "PDF Error", f"Could not create the PDF:\n{e}")
                return
            if paths:
                QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(paths[0])))

        def send():
            chosen = [g for r, g in enumerate(groups)
                      if table.item(r, 0).checkState() == Qt.CheckState.Checked and g["email"]]
            if not chosen:
                QMessageBox.information(dialog, "Nothing selected", "Tick at least one customer that has an e-mail.")
                return
            if not correio.smtp_ready():
                QMessageBox.warning(dialog, "E-mail not set up", "Set up the e-mail account in Settings → Email first.")
                return
            names = ", ".join(g["name"] for g in chosen[:6]) + ("…" if len(chosen) > 6 else "")
            if QMessageBox.question(dialog, "Send statements", f"Send {len(chosen)} statement(s) now?\n\n{names}",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                    QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
                return
            month = f"{date.today():%B %Y}"
            messages, failed = [], []
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                for g in chosen:
                    try:
                        pdf = self._build_statement_pdf(self._statement_path(g), g)
                    except Exception as e:
                        failed.append(f"{g['name']}: PDF — {e}")
                        continue
                    body = self._fill(msg.toPlainText(), name=g["name"], month=month, count=len(g["invoices"]),
                                      total=_money(g["total"]))
                    m = correio.build_message(g["email"], f"Statement {month} — {company_settings.COMPANY_NAME}",
                                              body, attachments=[pdf])
                    m._vl_name = g["name"]
                    messages.append(m)
                results = correio.send_messages(messages) if messages else []
                failed += [f"{m._vl_name}: {err}" for m, err in results if err]
                sent = sum(1 for _m, err in results if not err)
            except Exception as e:
                sent = 0
                failed.append(f"Could not connect to the e-mail server: {e}")
            finally:
                QApplication.restoreOverrideCursor()
            if sent:
                QSettings("VL Flooring", "app").setValue("statements/last_sent", f"{date.today():%Y-%m}")
                logging.getLogger("vl_flooring").info("statements sent: %s", sent)
            if failed:
                QMessageBox.warning(dialog, "Statements", f"{sent} sent.\n\nNot sent:\n" + "\n".join(failed[:10]))
            else:
                show_toast(f"{sent} statement(s) sent.", "success", self)
                dialog.accept()

        btn_pdf.clicked.connect(open_pdf)
        btn_folder.clicked.connect(save_all)
        btn_send.clicked.connect(send)
        btn_close.clicked.connect(dialog.reject)
        dialog._groups, dialog._send = groups, send  # testes
        dialog.exec()

    def _statement_attention_item(self):
        today = date.today()
        if today.day > 7 or not self._role_rule("finance"):
            return None
        if QSettings("VL Flooring", "app").value("statements/last_sent", "") == f"{today:%Y-%m}":
            return None
        try:
            if not self._statement_data():
                return None
        except (MySQLError, RuntimeError):
            return None
        return ("file-type-pdf", "#1565C0", f"{today:%B} statements are ready to send", self.open_statements_dialog)

    # ═════════════════════════ estimate por e-mail ═════════════════════════
    def email_estimate(self, parent, estimate_id, code, client, email, address, total, valid_until, build_pdf):
        """build_pdf(path) cria o PDF. Devolve True se enviou (e marca SENT)."""
        path = os.path.join(ESTIMATES_DIR, f"Estimate_{code}.pdf")
        try:
            os.makedirs(ESTIMATES_DIR, exist_ok=True)
            build_pdf(path)
        except Exception as e:
            logging.getLogger("vl_flooring").exception("estimate PDF failed")
            QMessageBox.critical(parent, "PDF Error", f"Could not create the PDF:\n{e}")
            return False
        body = self._fill(ESTIMATE_TEMPLATE, name=(client or "there").split(" ")[0], code=code,
                          address=address or "your project", total=_money(total),
                          valid=f"{valid_until:%m/%d/%Y}" if valid_until else "30 days")
        sent = self._compose_dialog(parent, f"Send estimate {code}", email,
                                    f"Estimate {code} — {company_settings.COMPANY_NAME}", body, attachments=[path])
        if sent:
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                cur.execute("UPDATE estimates SET STATUS = IF(STATUS='DRAFT', 'SENT', STATUS), SENT_AT = NOW() "
                            "WHERE ID = %s", (estimate_id,))
                conn.commit()
                cur.close()
                conn.close()
            except (MySQLError, RuntimeError):
                logging.getLogger("vl_flooring").exception("estimate SENT_AT not saved")
            show_toast(f"Estimate {code} sent to {self._last_compose.get('to')}.", "success", self)
        return sent

    # ═════════════════════════ agenda por helper ═════════════════════════
    def _week_crew_by_day(self, day_ids):
        if not day_ids:
            return {}, {}
        conn = self._get_connection()
        cur = conn.cursor()
        marks = ",".join(["%s"] * len(day_ids))
        cur.execute(f"SELECT x.WORK_DAY_ID, h.ID FROM work_day_helpers x JOIN helpers h ON h.ID = x.HELPER_ID "
                    f"WHERE x.WORK_DAY_ID IN ({marks})", tuple(day_ids))
        by_day = {}
        for wid, hid in cur.fetchall():
            by_day.setdefault(wid, set()).add(hid)
        cur.execute("SELECT ID, COALESCE(NULLIF(FULL_NAME, ''), COMPANY_NAME), COALESCE(EMAIL, '') FROM helpers")
        helpers = {hid: (name or "", (email or "").strip()) for hid, name, email in cur.fetchall()}
        cur.close()
        conn.close()
        return by_day, helpers

    def _helper_week_text(self, name, monday, rows):
        sunday = monday + timedelta(days=6)
        lines = [f"Hi {name.split(' ')[0]},", "", f"Your schedule for {monday:%m/%d} – {sunday:%m/%d/%Y}:", ""]
        for r in rows:
            place = ", ".join(x for x in (r.get("JOB_ADDRESS"), r.get("JOB_ADDRESS2"), r.get("CITY_NAME")) if x) \
                or "address to be confirmed"
            code = f" ({r['JOB_CODE']})" if r.get("JOB_CODE") else ""
            lines.append(f"{r['WORK_DATE']:%a %m/%d} — {place}{code}")
            if r.get("WORK_TYPES"):
                lines.append(f"    {r['WORK_TYPES']}")
            maps = "https://maps.google.com/?q=" + quote(place) if place != "address to be confirmed" else ""
            if maps:
                lines.append(f"    Map: {maps}")
        lines += ["", "Any question, call me.", company_settings.COMPANY_NAME, company_settings.COMPANY_PHONE]
        return "\n".join(lines)

    def email_week_to_helpers(self, parent, monday, rows):
        try:
            by_day, helpers = self._week_crew_by_day([r["ID"] for r in rows])
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(parent, "Database Error", str(e))
            return
        per_helper = {}
        for r in rows:
            for hid in by_day.get(r["ID"], ()):
                per_helper.setdefault(hid, []).append(r)
        if not per_helper:
            QMessageBox.information(parent, "No helpers", "No helper is scheduled in this week's days.")
            return
        d = QDialog(parent)
        d.setWindowTitle("E-mail each helper their week")
        d.resize(760, 560)
        lay = QVBoxLayout(d)
        if not correio.smtp_ready():
            w = QLabel("⚠ The e-mail account is not set up yet (Settings → Email).")
            w.setStyleSheet(_WARN_QSS)
            lay.addWidget(w)
        table = QTableWidget(len(per_helper), 4)
        table.setHorizontalHeaderLabels(["Send", "Helper", "E-mail", "Days"])
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        order = sorted(per_helper, key=lambda h: helpers.get(h, ("",))[0])
        preview = QTextEdit()
        preview.setReadOnly(True)
        for r, hid in enumerate(order):
            name, email = helpers.get(hid, ("?", ""))
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            chk.setCheckState(Qt.CheckState.Checked if email else Qt.CheckState.Unchecked)
            table.setItem(r, 0, chk)
            table.setItem(r, 1, QTableWidgetItem(name))
            table.setItem(r, 2, QTableWidgetItem(email or "no e-mail — add it in Helpers"))
            table.setItem(r, 3, QTableWidgetItem(", ".join(f"{x['WORK_DATE']:%a %m/%d}" for x in per_helper[hid])))
        lay.addWidget(table)
        lay.addWidget(QLabel("Preview (click a helper):"))
        lay.addWidget(preview, 1)
        table.currentCellChanged.connect(lambda r, *_a: 0 <= r < len(order) and preview.setPlainText(
            self._helper_week_text(helpers[order[r]][0], monday, per_helper[order[r]])))
        if order:
            preview.setPlainText(self._helper_week_text(helpers[order[0]][0], monday, per_helper[order[0]]))
        row = QHBoxLayout()
        row.addStretch(1)
        cancel, send = QPushButton("Close"), QPushButton("  Send to ticked")
        send.setIcon(tabler_icon("send", "#FFFFFF", 16))
        send.setStyleSheet(_PRIMARY_BTN)
        row.addWidget(cancel)
        row.addWidget(send)
        lay.addLayout(row)

        def do_send():
            chosen = [hid for r, hid in enumerate(order)
                      if table.item(r, 0).checkState() == Qt.CheckState.Checked and helpers[hid][1]]
            if not chosen:
                QMessageBox.information(d, "Nothing selected", "Tick at least one helper that has an e-mail.")
                return
            if not correio.smtp_ready():
                QMessageBox.warning(d, "E-mail not set up", "Set up the e-mail account in Settings → Email first.")
                return
            if QMessageBox.question(d, "Send", f"Send the schedule to {len(chosen)} helper(s)?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                    QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
                return
            msgs = [correio.build_message(helpers[h][1], f"Your schedule {monday:%m/%d} — {company_settings.COMPANY_NAME}",
                                          self._helper_week_text(helpers[h][0], monday, per_helper[h])) for h in chosen]
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                results = correio.send_messages(msgs)
            except Exception as e:
                QApplication.restoreOverrideCursor()
                QMessageBox.critical(d, "Not sent", f"Could not connect to the e-mail server:\n{e}")
                return
            QApplication.restoreOverrideCursor()
            bad = [f"{m['To']}: {err}" for m, err in results if err]
            if bad:
                QMessageBox.warning(d, "Schedule", "Not sent:\n" + "\n".join(bad))
            else:
                show_toast(f"Schedule sent to {len(results)} helper(s).", "success", self)
                d.accept()

        send.clicked.connect(do_send)
        cancel.clicked.connect(d.reject)
        d._send = do_send  # testes
        d.exec()

    # ═════════════════════════ vencimentos de compliance ═════════════════════════
    def _compliance_reminders_due(self, today=None):
        """[(id, nome, tipo, vencimento, dias, coluna)] que ainda não foram avisados."""
        today = today or date.today()
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT ID, NAME, ITEM_TYPE, DUE_DATE, REMINDED_30_FOR, REMINDED_7_FOR FROM compliance_items "
                    "WHERE STATUS = 'ACTIVE' AND DUE_DATE BETWEEN %s AND %s", (today, today + timedelta(days=30)))
        out = []
        for iid, name, itype, due, r30, r7 in cur.fetchall():
            days = (due - today).days
            if days <= 7 and r7 != due:
                out.append((iid, name, itype, due, days, "REMINDED_7_FOR"))
            elif days > 7 and r30 != due:
                out.append((iid, name, itype, due, days, "REMINDED_30_FOR"))
        cur.close()
        conn.close()
        return out

    def _auto_send_compliance_reminders(self):
        """Uma vez por vencimento: e-mail para você (destino do Weekly Summary).
        Reserva no banco antes de enviar — o outro computador não repete."""
        if not correio.smtp_ready() or getattr(self, "_db_read_only", False):
            return
        try:
            recipient = self._summary_recipient()
            if "@" not in recipient:
                return
            due = self._compliance_reminders_due()
            if not due:
                return
            conn = self._get_connection()
            cur = conn.cursor()
            claimed = []
            for iid, name, itype, ddate, days, col in due:
                cur.execute(f"UPDATE compliance_items SET {col}=%s WHERE ID=%s AND ({col} IS NULL OR {col} <> %s)",
                            (ddate, iid, ddate))
                if cur.rowcount:
                    claimed.append((iid, name, itype, ddate, days, col))
            conn.commit()
            cur.close()
            conn.close()
        except (MySQLError, RuntimeError):
            logging.getLogger("vl_flooring").exception("compliance reminders: could not prepare")
            return
        if not claimed:
            return
        lines = ["These items are due soon:", ""]
        for _i, name, itype, ddate, days, _c in sorted(claimed, key=lambda x: x[3]):
            when = "TODAY" if days == 0 else ("OVERDUE" if days < 0 else f"in {days} day{'s' if days != 1 else ''}")
            lines.append(f"• {name} ({itype or 'item'}) — due {ddate:%m/%d/%Y}, {when}")
        lines += ["", "Open VL Flooring → Registrations → Compliance to renew or mark them done."]
        subject = f"Due soon: {len(claimed)} compliance item(s) — {company_settings.COMPANY_NAME}"
        db_config = dict(self.db_config)
        log = logging.getLogger("vl_flooring")

        def worker():
            try:
                correio.send_mail(recipient, subject, "\n".join(lines))
                log.info("compliance reminders sent: %s", [c[0] for c in claimed])
            except Exception:
                log.exception("compliance reminders could not be sent")
                try:  # libera para tentar de novo
                    import mysql.connector as _m
                    c = _m.connect(**db_config)
                    cc = c.cursor()
                    for iid, _n, _t, ddate, _d, col in claimed:
                        cc.execute(f"UPDATE compliance_items SET {col}=NULL WHERE ID=%s AND {col}=%s", (iid, ddate))
                    c.commit()
                    c.close()
                except Exception:
                    pass
        threading.Thread(target=worker, daemon=True).start()
