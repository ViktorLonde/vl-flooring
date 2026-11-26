"""Testa (numa CÓPIA temporária do banco, sem enviar e-mail):
despesas ligadas às invoices, invoice da semana na Home, aviso de pagamento
repetido, abas novas do Data check e o resumo diário por e-mail."""
import sys, os, subprocess, tempfile, traceback, shutil
from datetime import date, datetime, timedelta
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); os.chdir(ROOT)
import config, mysql.connector
from PySide6.QtWidgets import (QApplication, QMessageBox, QDialog, QPushButton, QDoubleSpinBox, QTableWidget,
                               QLabel, QCheckBox)
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import Qt

REAL = config.load_db_config()
TEST_DB = "vl_control_test_tmp"
BIN = r"C:\Program Files\MySQL\MySQL Server 8.0\bin"
cnf = tempfile.NamedTemporaryFile("w", suffix=".cnf", delete=False)
cnf.write(f"[client]\nhost={REAL['host']}\nuser={REAL['user']}\npassword=\"{REAL['password']}\"\n"); cnf.close()
admin = mysql.connector.connect(**REAL); acur = admin.cursor()
acur.execute(f"DROP DATABASE IF EXISTS {TEST_DB}"); acur.execute(f"CREATE DATABASE {TEST_DB}")
dump = subprocess.run([os.path.join(BIN, "mysqldump.exe"), f"--defaults-extra-file={cnf.name}", "--single-transaction",
                       REAL["database"]], capture_output=True, check=True).stdout
subprocess.run([os.path.join(BIN, "mysql.exe"), f"--defaults-extra-file={cnf.name}", TEST_DB], input=dump, check=True)
TEST = {**REAL, "database": TEST_DB}
tmpdir = tempfile.mkdtemp()
import arquivos
arquivos.files_root = lambda: os.path.join(tmpdir, "files")

msgs = []
answers = {"question": QMessageBox.StandardButton.Yes}
QMessageBox.information = staticmethod(lambda *a, **k: msgs.append(str(a[2])) or QMessageBox.StandardButton.Ok)
QMessageBox.warning = staticmethod(lambda *a, **k: msgs.append("WARN " + str(a[2])) or QMessageBox.StandardButton.Ok)
QMessageBox.critical = staticmethod(lambda *a, **k: msgs.append("CRIT " + str(a[2])) or QMessageBox.StandardButton.Ok)
QMessageBox.question = staticmethod(lambda *a, **k: msgs.append("Q " + str(a[1])) or answers["question"])
QDesktopServices.openUrl = staticmethod(lambda *a: True)
actions = []


def fake_exec(d):
    if actions:
        result = actions.pop(0)(d)
        return 1 if result is None else result
    return 0


QDialog.exec = fake_exec
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
    from paginas import controle
    a = QApplication(sys.argv)
    w = MainWindow(db_config=TEST); w.resize(1536, 900); w.show(); a.processEvents()
    w.set_current_user("viktorlonde")
    w.offer_payment_receipt = lambda *a_, **k: False
    w._confirm_bank_info_ready = lambda *a_, **k: True

    # ── semana de cobrança: domingo a sábado ──
    s_, e_ = w._last_full_week(date(2026, 11, 25))
    check("billing week is Sunday to Saturday", (s_, e_) == (date(2026, 11, 15), date(2026, 11, 21)), (s_, e_))
    s_, e_ = w._last_full_week(date(2026, 11, 22))  # num domingo: a semana que acabou ontem
    check("on a Sunday it suggests the week that just ended", (s_, e_) == (date(2026, 11, 15), date(2026, 11, 21)),
          (s_, e_))

    # ── semana passada: um dia e uma despesa novos, fora de invoice ──
    monday, sunday = w._last_full_week()
    wed = monday + timedelta(days=2)
    cur.execute("INSERT INTO work_days (WORK_DATE, CONTRACTOR_ID, STATUS, PAYMENT_METHOD, VALUE, JOB_ADDRESS, "
                "DEMOLITION, INSTALLATION, PREPARATION, DAY_FRACTION) "
                "VALUES (%s, 1, 'COMPLETED', 'Receivable', 250, '1 Test St', 'not', 'not', 'not', 1)", (wed,))
    new_day = cur.lastrowid
    cur.execute("INSERT INTO expenses (EXPENSE_DATE, CATEGORY, DESCRIPTION, AMOUNT, ENTITY_TYPE, CONTRACTOR_ID) "
                "VALUES (%s, 'GAS', 'Test gas', 41.50, 'Contractor', 1)", (wed,))
    new_exp = cur.lastrowid
    exp_before = w._unbilled_expenses_total()

    items = w._weekly_invoice_attention_items()
    check("Home suggests invoicing last week", items and "Invoice last week" in items[0][2], [i[2] for i in items])
    sugg = w._weekly_invoice_suggestions()[0]
    week_days = len(sugg[0]["days"]) if sugg else 0
    state = {}

    def gen(d):
        lbl = next(l for l in d.findChildren(QLabel) if "job(s) selected" in l.text())
        state["status"] = lbl.text()
        next(b for b in d.findChildren(QPushButton) if b.text() == "Generate PDFs").click()
    actions[:] = [gen]
    before = q("SELECT COALESCE(MAX(ID),0) FROM contractor_invoices")[0][0]
    items[0][3](False); a.processEvents()  # o botão manda "checked" junto
    check("weekly suggestion opens Generate with the week's days", state.get("status", "").startswith(
        f"{week_days} job(s) selected"), state.get("status"))
    inv = q("SELECT ID, EXPENSES_TOTAL FROM contractor_invoices WHERE ID > %s", (before,))
    check("invoice created", bool(inv), inv)
    if inv:
        linked_exp = {r[0] for r in q("SELECT EXPENSE_ID FROM invoice_expenses WHERE INVOICE_ID=%s", (inv[0][0],))}
        check("the week's expense is linked to the invoice", new_exp in linked_exp, linked_exp)
        exp_after = w._unbilled_expenses_total()
        check("unbilled expenses went down", abs((exp_before[0] - exp_after[0]) - float(inv[0][1])) < 0.01,
              (exp_before, exp_after))
        check("weekly suggestion gone after invoicing", not w._weekly_invoice_attention_items())

        def regen(d):
            t = next(t for t in d.findChildren(QTableWidget)
                     if t.horizontalHeaderItem(2) and t.horizontalHeaderItem(2).text() == "Description")
            rows = [r for r in range(t.rowCount()) if "(invoiced #" in t.item(r, 2).text()]
            state["exp_marked"] = len(rows)
            state["exp_checked"] = sum(t.item(r, 0).checkState() == Qt.CheckState.Checked for r in rows)
        actions[:] = [regen]
        w.open_generate_invoices_dialog(prefill_bill_to="Contractor", prefill_from=monday, prefill_to=sunday)
        check("billed expenses show '(invoiced #N)' unchecked", state.get("exp_marked", 0) >= 1
              and state.get("exp_checked") == 0, (state.get("exp_marked"), state.get("exp_checked")))

        # apagar a invoice solta as despesas
        cur.execute("DELETE FROM invoice_expenses WHERE INVOICE_ID=%s", (inv[0][0],))

    # ── pagamento repetido ──
    open_inv = q("SELECT ID, TOTAL_AMOUNT FROM contractor_invoices WHERE STATUS='PENDING' ORDER BY ID LIMIT 1")
    if open_inv:
        iid = open_inv[0][0]

        def pay(amount):
            def act(d):
                d.findChildren(QDoubleSpinBox)[0].setValue(amount)
                next(b for b in d.findChildren(QPushButton) if b.text() == "Record Payment").click()
            return act
        answers["question"] = QMessageBox.StandardButton.No
        actions[:] = [pay(100)]
        w.open_record_payment_dialog(preselect=("Contractor", iid)); a.processEvents()
        actions[:] = [pay(100)]
        msgs.clear()
        w.open_record_payment_dialog(preselect=("Contractor", iid)); a.processEvents()
        n = q("SELECT COUNT(*) FROM payments WHERE INVOICE_TYPE='Contractor' AND INVOICE_ID=%s AND AMOUNT=100", (iid,))[0][0]
        check("same payment again asks first (answered No → not recorded)",
              any(m.startswith("Q Same payment again") for m in msgs) and n == 1, (msgs, n))
        answers["question"] = QMessageBox.StandardButton.Yes

    # ── Data check ──
    state = {}

    def look(d):
        state["tables"] = {k: t.rowCount() for k, t in d._check_tables.items()}
        state["titles"] = [d.findChild(type(d), None) and "" or ""]
        from PySide6.QtWidgets import QTabWidget
        tabs = d.findChild(QTabWidget, "tabs_data_cleanup")
        state["titles"] = [tabs.tabText(i) for i in range(tabs.count())]
        t = d._check_tables["cancelled"]
        if t.rowCount():
            t.selectAll()
            d._check_buttons["zero"].click(); a.processEvents()
        t = d._check_tables["duplicates"]
        state["dups"] = t.rowCount()
        if t.rowCount():
            t.selectRow(0)
            d._check_buttons["delete_dup"].click(); a.processEvents()
        state["after"] = {k: tt.rowCount() for k, tt in d._check_tables.items()}
    actions[:] = [look]
    w.open_data_cleanup_dialog(); a.processEvents()
    tbl = state.get("tables", {})
    check("Data check has the new tabs", all(any(x in t for t in state.get("titles", []))
                                            for x in ("Who pays?", "Dates far ahead", "Cancelled with value",
                                                      "Job Codes missing info", "Repeated payments")),
          state.get("titles"))
    check("far-ahead date found (2027)", tbl.get("future", 0) >= 1, tbl)
    check("who-pays rows found", tbl.get("whopays", 0) >= 1, tbl)
    check("job codes missing info found", tbl.get("jobcodes", 0) >= 1, tbl)
    check("cancelled with value fixed", state.get("after", {}).get("cancelled") == 0, state.get("after"))
    if state.get("dups"):
        check("repeated payment deleted and invoice recalculated",
              state["after"]["duplicates"] == state["dups"] - 1, state.get("after"))
        r14 = q("SELECT AMOUNT_PAID, TOTAL_AMOUNT, STATUS FROM contractor_invoices WHERE ID=14")
        check("invoice #14 paid total now matches its payments",
              r14 and abs(float(r14[0][0]) - float(q("SELECT COALESCE(SUM(AMOUNT),0) FROM payments WHERE "
                                                    "INVOICE_TYPE='Contractor' AND INVOICE_ID=14")[0][0])) < 0.01, r14)
    check("Home shows 'things to check in your data'", w._data_check_attention_item() is not None)

    # ── resumo diário ──
    tomorrow = date.today() + timedelta(days=1)
    cur.execute("INSERT INTO work_days (WORK_DATE, CONTRACTOR_ID, STATUS, PAYMENT_METHOD, VALUE, JOB_ADDRESS, "
                "DEMOLITION, INSTALLATION, PREPARATION, DAY_FRACTION) "
                "VALUES (%s, 1, 'PENDING', 'Receivable', 250, '77 Tomorrow Ave', 'not', 'not', 'not', 1)", (tomorrow,))
    data = w._daily_summary_data()
    html_ = w._daily_summary_html(data)
    check("daily summary lists tomorrow's job", "77 Tomorrow Ave" in html_)
    check("daily summary shows money to follow", "Expected this week" in html_ and "Received today" in html_)
    sent = []
    w._send_daily_summary = lambda d, r: sent.append(r)
    controle.correio.smtp_ready = lambda: True
    w._summary_recipient = lambda: "test@example.com"
    cur.execute("UPDATE app_settings SET DAILY_LAST_SENT=NULL, DAILY_SUMMARY=1 WHERE ID=1")
    check("not sent before 5 PM", w._auto_send_daily_summary(datetime.now().replace(hour=9)) is False)
    check("sent after 5 PM", w._auto_send_daily_summary(datetime.now().replace(hour=18)) is True)
    import time; time.sleep(0.5)
    check("e-mail went to the summary address", sent == ["test@example.com"], sent)
    check("only once a day", w._auto_send_daily_summary(datetime.now().replace(hour=19)) is False)
    cur.execute("UPDATE app_settings SET DAILY_LAST_SENT=NULL, DAILY_SUMMARY=0 WHERE ID=1")
    check("turned off → not sent", w._auto_send_daily_summary(datetime.now().replace(hour=18)) is False)
    tabs = w.ui.tabs_settings
    system = tabs.widget(tabs.count() - 1)
    check("Settings → System has the daily summary option",
          system.findChild(QCheckBox, "chk_daily_summary") is not None)

    # ── invoice paga (PDF para mandar) ──
    paid_id = q("SELECT ID FROM contractor_invoices WHERE STATUS='RECEIVED' ORDER BY ID DESC LIMIT 1")[0][0]
    path = w._build_paid_invoice_pdf("Contractor", paid_id)
    check("paid invoice PDF created", os.path.exists(path) and os.path.getsize(path) > 3000
          and path.endswith("_PAID.pdf"), path)
    data = open(path, "rb").read()
    check("paid PDF is inside the files folder (Invoices)", "Invoices" in path)
    composed = {}
    w._compose_dialog = lambda parent, title, to, subject, body, attachments=(), note="": (
        composed.update(to=to, subject=subject, att=attachments) or False)
    w._go_to_page(5, w.ui.btn_nav_receivables); w.ui.tabWidget_receivables.setCurrentIndex(1)
    w._invoice_quick_buttons["all"].click(); a.processEvents()
    t = w.ui.table_contractor_invoices
    row = next(r for r in range(t.rowCount()) if t.item(r, 0).text() == str(paid_id))
    t.selectRow(row); a.processEvents()
    check("'Paid invoice' button enabled for a paid invoice", w._invoice_action_buttons[4].isEnabled())
    w.invoice_action_paid_pdf(); a.processEvents()
    check("paid invoice offered by e-mail with the PDF attached",
          composed.get("att") and composed["att"][0].endswith("_PAID.pdf") and "paid in full" in composed.get("subject", ""),
          composed)
    # recibo depois do último pagamento anexa a invoice paga
    controle.correio.smtp_ready = lambda: True
    import paginas.emails_clientes as ec
    ec.correio.smtp_ready = lambda: True
    composed.clear()
    MainWindow.offer_payment_receipt(w, None, "Contractor", paid_id, 10, date.today().isoformat(), "Zelle")
    check("payment receipt attaches the PAID invoice", composed.get("att") and
          composed["att"][0].endswith("_PAID.pdf"), composed)

    # ── Home cabe na tela (sem rolagem para o lado) ──
    from PySide6.QtWidgets import QScrollArea
    w._go_to_page(0, w.ui.btn_home)
    w.show_attention_summary()
    for width in (1366, 1920):
        w.showNormal(); w.resize(width, 900); a.processEvents(); a.processEvents()
        areas = [s for s in w.ui.pg_home.findChildren(QScrollArea)] + \
                [p for p in [w.ui.pg_home.parentWidget()] if isinstance(p, QScrollArea)]
        page_w = w.ui.pg_home.minimumSizeHint().width()
        visible_w = w.ui.Pages.width()
        check(f"Home fits at {width}px wide", page_w <= visible_w, (page_w, visible_w))
        if width == 1366:
            w.grab().save(os.path.join(os.environ.get("TEMP", "."), "home_1366.png"))

    check("no error dialogs", not [m for m in msgs if m.startswith("CRIT")], [m for m in msgs if m.startswith("CRIT")])
    db.close()
except Exception:
    traceback.print_exc(); ok = False
finally:
    acur.execute("SET SESSION lock_wait_timeout = 15")
    acur.execute(f"DROP DATABASE IF EXISTS {TEST_DB}"); admin.close(); os.remove(cnf.name)
    shutil.rmtree(tmpdir, ignore_errors=True)
    print("temp db dropped", flush=True)
print("RESULT:", "ALL OK" if ok else "FAILED", flush=True)
sys.exit(0 if ok else 1)
