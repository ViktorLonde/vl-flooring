"""Testa Work Day Inbox, Material Inbox, recibo de pagamento, statements,
estimate por e-mail, agenda por helper, avisos de compliance, price per SF,
sugestão de preço, cash forecast, tax reserve, estoque mínimo, sign-off PDF
e follow-ups — numa CÓPIA temporária do banco. Nenhum e-mail sai de verdade
(envio e caixa de entrada são simulados)."""
import sys, os, subprocess, tempfile, traceback, time
from datetime import date, datetime, timedelta
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); os.chdir(ROOT)
import config, mysql.connector, smtplib
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog

REAL = config.load_db_config()
TEST_DB = "vl_mail_test_tmp"
BIN = r"C:\Program Files\MySQL\MySQL Server 8.0\bin"
cnf = tempfile.NamedTemporaryFile("w", suffix=".cnf", delete=False)
cnf.write(f"[client]\nhost={REAL['host']}\nuser={REAL['user']}\npassword=\"{REAL['password']}\"\n"); cnf.close()
admin = mysql.connector.connect(**REAL); acur = admin.cursor()
acur.execute(f"DROP DATABASE IF EXISTS {TEST_DB}"); acur.execute(f"CREATE DATABASE {TEST_DB}")
dump = subprocess.run([os.path.join(BIN, "mysqldump.exe"), f"--defaults-extra-file={cnf.name}", "--single-transaction",
                       REAL["database"]], capture_output=True, check=True).stdout
subprocess.run([os.path.join(BIN, "mysql.exe"), f"--defaults-extra-file={cnf.name}", TEST_DB], input=dump, check=True)
TEST = {**REAL, "database": TEST_DB}
fix = mysql.connector.connect(**TEST); fc = fix.cursor()
fc.execute("UPDATE users SET role='ADMIN', status='Active' WHERE username='viktorlonde'")
fix.commit(); fix.close()

msgs = []
QMessageBox.information = staticmethod(lambda *a, **k: msgs.append(str(a[2])) or QMessageBox.StandardButton.Ok)
QMessageBox.warning = staticmethod(lambda *a, **k: msgs.append("WARN " + str(a[2])) or QMessageBox.StandardButton.Ok)
QMessageBox.critical = staticmethod(lambda *a, **k: msgs.append("CRIT " + str(a[2])) or QMessageBox.StandardButton.Ok)
QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)


def no_smtp(*a, **k):
    raise AssertionError("real SMTP used")


smtplib.SMTP = no_smtp
from paginas import correio
sent = []
correio.smtp_ready = lambda: True
correio.send_messages = lambda ms: [(sent.append(m) or (m, None)) for m in ms]
correio.send_mail = lambda to, subject, text, html=None, attachments=(), cc=None: sent.append(
    {"To": to, "Subject": subject, "text": text, "att": list(attachments)})
seen = []
correio.mark_seen = lambda uids: seen.extend(uids)
inbox = {"dia": [], "material": []}
correio.fetch_unseen = lambda kw: list(inbox["dia"] if "dia" in kw else inbox["material"])
QDesktopOpened = []
from PySide6.QtGui import QDesktopServices
QDesktopServices.openUrl = staticmethod(lambda url: QDesktopOpened.append(url.toLocalFile()) or True)

actions = []
QDialog.exec = lambda d: (actions.pop(0)(d) if actions else None, 0)[1]
ok = True


def check(name, cond, extra=""):
    global ok
    ok &= bool(cond)
    print(("PASS " if cond else "FAIL ") + name, extra, flush=True)


try:
    db = mysql.connector.connect(**TEST); db.autocommit = True; cur = db.cursor()

    def q(sql, p=()):
        cur.execute(sql, p); return cur.fetchall()

    from main_ import MainWindow
    a = QApplication(sys.argv)
    w = MainWindow(db_config=TEST); w.resize(1536, 816); w.show(); a.processEvents()
    w.set_current_user("viktorlonde")
    tmp = tempfile.mkdtemp()

    # ── WORK DAY INBOX ──
    code, pid = q("SELECT jp.CODE, jp.ID FROM job_projects jp WHERE EXISTS (SELECT 1 FROM work_days w "
                  "WHERE w.JOB_PROJECT_ID = jp.ID) ORDER BY jp.ID DESC LIMIT 1")[0]
    hid, hname = q("SELECT ID, FULL_NAME FROM helpers ORDER BY ID LIMIT 1")[0]
    q("UPDATE helpers SET DAILY_RATE=200 WHERE ID=%s", (hid,))
    day = date(2026, 12, 1)
    inbox["dia"] = [
        {"uid": b"11", "subject": f"dia {code}", "body": f"meio dia, {hname.split()[0]}\n\nSent from my iPhone",
         "date": datetime(2026, 12, 1, 17, 0), "attachments": []},
        {"uid": b"12", "subject": "dia JB-9999", "body": "", "date": datetime(2026, 12, 1, 17, 5), "attachments": []},
        {"uid": b"13", "subject": "diario de obra", "body": "", "date": datetime(2026, 12, 1, 17, 5), "attachments": []},
    ]
    state = {}

    def day_inbox(d):
        d._check()
        state["rows"] = [(r["code"], r["chk"].isChecked(), r["chk"].isEnabled()) for r in d._rows]
        d._create()
        d._rows[1]["chk"].setChecked(False)
        from PySide6.QtWidgets import QTableWidget
        d.findChild(QTableWidget, "table_work_day_inbox").setCurrentCell(1, 2)
        d._ignore()
    actions.append(day_inbox)
    w.open_work_day_inbox_dialog()
    check("only 'dia …' e-mails become rows", [r[0] for r in state.get("rows", [])] == [code, "JB-9999"], state)
    check("unknown code cannot be created", state["rows"][1][2] is False if state.get("rows") else False)
    new = q("SELECT ID, DAY_FRACTION, HELPER_ID, HELPER_PAY FROM work_days WHERE JOB_PROJECT_ID=%s AND WORK_DATE=%s",
            (pid, day))
    check("day created from e-mail with half day", len(new) == 1 and abs(float(new[0][1]) - 0.5) < 0.01, new)
    if new:
        crew = q("SELECT HELPER_ID, PAY FROM work_day_helpers WHERE WORK_DAY_ID=%s", (new[0][0],))
        check("crew = helper named in the e-mail, pay = daily rate × ½", crew == [(hid, 100)] or
              [(h, float(p)) for h, p in crew] == [(hid, 100.0)], crew)
    check("e-mails marked as read only after handled", sorted(seen) == [b"11", b"12"], seen)

    # ── MATERIAL INBOX ──
    seen.clear()
    before = q("SELECT COALESCE(SUM(QUANTITY), 0) FROM job_materials WHERE JOB_PROJECT_ID=%s AND PRODUCT_ID=24", (pid,))[0][0]
    inbox["material"] = [{"uid": b"21", "subject": f"material {code}", "body": "6 Bostik SL-100\n2 ProFlex primer\nthanks",
                          "date": datetime(2026, 12, 1, 18, 0),
                          "attachments": [("nota.jpg", b"\xff\xd8fakejpg", "image/jpeg"), ("sig.txt", b"x", "text/plain")]}]
    mat = {}

    def material_inbox(d):
        d._check()
        mat["rows"] = [(r["text"], r["combo"].currentData(), r["qty"].value()) for r in d._rows]
        d._launch()
    actions.append(material_inbox)
    w.open_material_inbox_dialog()
    check("material lines recognised", mat.get("rows") == [("Bostik SL-100", 24, 6.0), ("ProFlex primer", 25, 2.0)], mat)
    after = q("SELECT COALESCE(SUM(QUANTITY), 0) FROM job_materials WHERE JOB_PROJECT_ID=%s AND PRODUCT_ID=24", (pid,))[0][0]
    check("materials launched in the job", float(after) - float(before) == 6.0, (before, after))
    docs = q("SELECT FILE_PATH FROM documents WHERE ENTITY_ID=%s AND CATEGORY='Material Receipt'", (pid,))
    check("receipt photo saved (text attachment ignored)", len(docs) == 1, docs)
    for (p,) in docs:
        full = os.path.join(ROOT, p)
        if os.path.exists(full):
            os.remove(full)
    check("material e-mail marked as read", seen == [b"21"], seen)

    # quick product
    def quick(d):
        cmb_type, txt_name, txt_brand, txt_spec, cmb_unit, price, save = d._fields
        txt_brand.setText("TestBrand"); save()
    actions.append(quick)
    new_pid = w._quick_product_dialog(w, "Test Primer 9000")
    check("product registered inline", bool(new_pid) and q("SELECT NAME FROM products WHERE ID=%s", (new_pid,))[0][0]
          == "Test Primer 9000")

    # ── PAYMENT RECEIPT ──
    sent.clear()
    inv = q("SELECT ID FROM contractor_invoices ORDER BY ID LIMIT 1")
    if inv:
        q("UPDATE contractors c JOIN contractor_invoices i ON i.CONTRACTOR_ID=c.ID SET c.EMAIL='payer@example.com', "
          "c.COMPANY_EMAIL='' WHERE i.ID=%s", (inv[0][0],))
        actions.append(lambda d: d._fields[3]())
        r = w.offer_payment_receipt(w, "Contractor", inv[0][0], 150.0, "2026-12-01", "Zelle")
        check("payment receipt sent to the customer", r and sent and sent[-1]["To"] == "payer@example.com"
              and "$150.00" in sent[-1]["text"] and "Balance" in sent[-1]["text"], sent[-1:] )

    # ── STATEMENTS ──
    q("UPDATE contractor_invoices SET STATUS='PENDING', AMOUNT_PAID=0 ORDER BY ID LIMIT 2")
    groups = w._statement_data()
    check("statement groups built", groups and all(abs(sum(g["buckets"]) - g["total"]) < 0.01 for g in groups),
          [(g["name"], g["total"]) for g in groups][:3])
    path = w._build_statement_pdf(os.path.join(tmp, "st.pdf"), groups[0]) if groups else ""
    check("statement PDF created", path and os.path.getsize(path) > 1000)
    sent.clear()

    def stmts(d):
        d._send()
    actions.append(stmts)
    w.open_statements_dialog()
    with_mail = [g for g in groups if g["email"]]
    check("statements e-mailed with PDF", len(sent) == len(with_mail) and all(
        any(p.get_content_type() == "application/pdf" for p in m.iter_attachments()) for m in sent), len(sent))
    for g in groups:
        p = w._statement_path(g)
        if os.path.exists(p):
            os.remove(p)

    # ── ESTIMATE BY E-MAIL ──
    sent.clear()
    q("INSERT INTO estimates (CODE, CLIENT_NAME, CLIENT_EMAIL, STATUS, TOTAL) VALUES ('EST-T1','Test Client','c@example.com','DRAFT',1000)")
    est_id = q("SELECT ID FROM estimates WHERE CODE='EST-T1'")[0][0]
    actions.append(lambda d: d._fields[3]())
    okk = w.email_estimate(w, est_id, "EST-T1", "Test Client", "c@example.com", "1 Main St", 1000, date(2026, 12, 31),
                           lambda p: open(p, "wb").write(b"%PDF-1.4 test"))
    st = q("SELECT STATUS, SENT_AT FROM estimates WHERE ID=%s", (est_id,))[0]
    check("estimate e-mailed with PDF, status SENT + date", okk and st[0] == "SENT" and st[1] is not None and
          sent and sent[-1]["att"], st)
    from paginas.emails_clientes import ESTIMATES_DIR
    if os.path.exists(os.path.join(ESTIMATES_DIR, "Estimate_EST-T1.pdf")):
        os.remove(os.path.join(ESTIMATES_DIR, "Estimate_EST-T1.pdf"))

    # estimate editor has the new buttons
    from PySide6.QtWidgets import QPushButton
    ed = {}

    def editor(d):
        ed["buttons"] = {b.objectName() for b in d.findChildren(QPushButton)}
    actions.append(editor)
    w.open_estimate_editor(est_id)
    check("estimate editor shows Send by e-mail + Suggest prices",
          {"btn_email_estimate", "btn_suggest_estimate_prices"} <= ed.get("buttons", set()))

    # ── HELPER WEEK ──
    monday = day - timedelta(days=day.weekday())
    q("UPDATE helpers SET EMAIL='helper@example.com' WHERE ID=%s", (hid,))
    rows = w._week_schedule_rows(monday)
    sent.clear()
    actions.append(lambda d: d._send())
    w.email_week_to_helpers(w, monday, rows)
    check("each helper gets only their days", len(sent) == 1 and sent[0]["To"] == "helper@example.com" and
          code in sent[0].get_content(), [m["To"] for m in sent])

    # ── COMPLIANCE REMINDERS ──
    q("INSERT INTO compliance_items (ITEM_TYPE, ENTITY_TYPE, NAME, DUE_DATE, STATUS) VALUES "
      "('INSURANCE','COMPANY','GL Insurance test', CURDATE() + INTERVAL 5 DAY, 'ACTIVE'), "
      "('LICENSE','COMPANY','License test', CURDATE() + INTERVAL 25 DAY, 'ACTIVE')")
    q("UPDATE app_settings SET SUMMARY_EMAIL='me@example.com' WHERE ID=1")
    sent.clear()
    w._auto_send_compliance_reminders(); time.sleep(1.5)
    check("compliance reminder sent to me", len(sent) == 1 and sent[0]["To"] == "me@example.com" and
          "GL Insurance test" in sent[0]["text"] and "License test" in sent[0]["text"], sent)
    sent.clear()
    w._auto_send_compliance_reminders(); time.sleep(1.0)
    check("compliance reminder not repeated", not sent, sent)

    # ── PRICE PER SF / SUGGEST ──
    jobs, services = w._price_per_sf_data()
    check("price per SF data", jobs and all("sf" in j for j in jobs), len(jobs))
    actions.append(lambda d: None)
    w.open_price_per_sf_dialog()
    from PySide6.QtWidgets import QDoubleSpinBox
    spin = QDoubleSpinBox(); spin.setRange(0, 1e6)
    wt_id, wt_name = q("SELECT ID, NAME FROM work_types WHERE UNIT='SF' ORDER BY ID LIMIT 1")[0]
    q("INSERT INTO service_rates (WORK_TYPE_ID, ENTITY_TYPE, ENTITY_ID, RATE) VALUES (%s, 'Default', 0, 3.25)", (wt_id,))
    w._load_service_rates(force=True)
    w.suggest_estimate_prices(w, [(wt_name, "SF", spin)])
    check("suggest price uses the Service Rate", abs(spin.value() - 3.25) < 0.001, spin.value())

    # ── CASH FORECAST / TAX ──
    cf = w._cash_forecast_data()
    check("cash forecast adds up", abs(cf["net"] - (cf["in"] - cf["out"])) < 0.01, {k: cf[k] for k in ("in", "out", "net")})
    actions.append(lambda d: None)
    w.open_cash_forecast_dialog()
    tax = w._tax_reserve_data(2026)
    check("tax reserve = 25% of positive profit", len(tax) == 4 and all(
        abs(p["reserve"] - round(max(p["profit"], 0) * 0.25, 2)) < 0.01 for p in tax), [p["reserve"] for p in tax])
    actions.append(lambda d: None)
    w.open_tax_reserve_dialog()

    # ── STOCK ALERTS ──
    q("UPDATE products SET MIN_STOCK=5 WHERE ID=24")
    low = w._low_stock()
    check("low stock detected", any(r[0] == 24 for r in low), [r[0] for r in low])

    def stock(d):
        for p, s, _old in d._spins:
            if p == 24:
                s.setValue(0)
        d._save()
    actions.append(stock)
    w.open_stock_alerts_dialog()
    check("minimum saved from the dialog", float(q("SELECT MIN_STOCK FROM products WHERE ID=24")[0][0]) == 0)

    # ── SIGN-OFF PDF ──
    so = {}

    def signoff(d):
        so["path"] = d._build()
    actions.append(signoff)
    w.open_signoff_dialog(pid)
    check("sign-off PDF created and saved in the job documents", so.get("path") and os.path.getsize(so["path"]) > 1500 and
          q("SELECT COUNT(*) FROM documents WHERE ENTITY_ID=%s AND CATEGORY='Completion Sign-off'", (pid,))[0][0] == 1)
    if so.get("path") and os.path.exists(so["path"]):
        os.remove(so["path"])
    check("Sign-off button in the job form", hasattr(w.ui, "btn_job_signoff"))

    # ── FOLLOW-UPS ──
    q("UPDATE work_days SET STATUS='COMPLETED', WORK_DATE = CURDATE() - INTERVAL 40 DAY WHERE JOB_PROJECT_ID=%s", (pid,))
    due = [f for f in w._followups_due() if f["pid"] == pid]
    check("30-day follow-up due for a finished job", [f["kind"] for f in due] == ["REVIEW_30"], due)

    def follow(d):
        r = next(i for i, f in enumerate(d._items) if f["pid"] == pid)
        d._table.setCurrentCell(r, 0)
        d._done()
    actions.append(follow)
    w.open_followups_dialog()
    check("follow-up marked done", not [f for f in w._followups_due() if f["pid"] == pid] and
          q("SELECT RESULT FROM job_followups WHERE JOB_PROJECT_ID=%s", (pid,)) == [("DONE",)])

    # ── HOME + HUB ──
    items = w._extra_attention_items()
    check("extra attention items load", isinstance(items, list), items)
    w.show_attention_summary(); a.processEvents()
    w._go_to_page(w._hub_index, w.ui.btn_registrations); a.processEvents()
    check("hub has the new cards", all(k in w._hub_cards and w._hub_cards[k].isEnabled() for k in
                                       ("day_inbox", "material_inbox", "statements", "price_sf", "cash_forecast",
                                        "tax_reserve", "stock_alerts", "followups")))
    crit = [m for m in msgs if m.startswith("CRIT")]
    check("no database errors", not crit, crit[:3])
    db.close()
except Exception:
    traceback.print_exc(); ok = False
finally:
    acur.execute("SET SESSION lock_wait_timeout = 15")
    acur.execute(f"DROP DATABASE IF EXISTS {TEST_DB}"); admin.close(); os.remove(cnf.name)
    print("temp db dropped", flush=True)
print("RESULT:", "ALL OK" if ok else "FAILED", flush=True)
sys.exit(0 if ok else 1)
