"""Testa o menu Projects (trabalhos particulares e subcontratos) numa CÓPIA
temporária do banco: criar projeto, plano de pagamento 50/50, cobrar parcela
(invoice + PDF), receber, invoice PAGA, subcontratado (combinado e pagamento →
despesa), lucro, projeto de Company e dias fora do "Not invoiced yet"."""
import sys, os, subprocess, tempfile, traceback, shutil
from datetime import date
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); os.chdir(ROOT)
import config, mysql.connector
from PySide6.QtWidgets import (QApplication, QMessageBox, QDialog, QPushButton, QDoubleSpinBox, QComboBox,
                               QLineEdit)
from PySide6.QtGui import QDesktopServices

REAL = config.load_db_config()
TEST_DB = "vl_projects_test_tmp"
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
QMessageBox.information = staticmethod(lambda *a, **k: msgs.append(str(a[2])) or QMessageBox.StandardButton.Ok)
QMessageBox.warning = staticmethod(lambda *a, **k: msgs.append("WARN " + str(a[2])) or QMessageBox.StandardButton.Ok)
QMessageBox.critical = staticmethod(lambda *a, **k: msgs.append("CRIT " + str(a[2])) or QMessageBox.StandardButton.Ok)
QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)
QDesktopServices.openUrl = staticmethod(lambda *a: True)
actions = []


def fake_exec(d):
    if actions:
        result = actions.pop(0)(d)
        return QDialog.DialogCode.Accepted if result is None else result
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
    a = QApplication(sys.argv)
    w = MainWindow(db_config=TEST); w.resize(1536, 900); w.show(); a.processEvents()
    w.set_current_user("viktorlonde")
    w.offer_payment_receipt = lambda *a_, **k: False
    w._confirm_bank_info_ready = lambda *a_, **k: True
    sent = []
    w._compose_dialog = lambda parent, title, to, subject, body, attachments=(), note="": (
        sent.append((title, subject, attachments)) or False)
    ui = w.ui

    check("Projects button in the sidebar", getattr(ui, "btn_projects", None) is not None)
    ui.btn_projects.click(); a.processEvents()
    check("Projects page opens", ui.Pages.currentIndex() == w._projects_index and ui.Top_label.text() == "Projects",
          ui.Top_label.text())

    st = {}

    def pay(amount):
        def act(d):
            d.findChildren(QDoubleSpinBox)[0].setValue(amount)
            next(b for b in d.findChildren(QPushButton) if b.text() == "Record Payment").click()
        return act

    def project(d):
        wg, act = d._widgets, d._actions
        wg["name"].setText("Smith kitchen LVP")
        wg["kind"].setCurrentIndex(0)
        wg["payer"].setEditText("Test Private Client")
        wg["address"].setText("100 Test Ave")
        wg["price"].setValue(10000)
        check("plan / subs / profit tabs locked before saving",
              not wg["tabs"].isTabEnabled(1) and not wg["tabs"].isTabEnabled(3))
        d._save(silent=True)
        st["id"] = d._state["id"]
        st["code"] = d._state["code"]
        wg["template"].setCurrentIndex(0)  # 50/50
        act["template"]()
        st["plan_rows"] = wg["plan"].rowCount()
        wg["plan"].selectRow(0)
        act["bill"]()
        wg["plan"].selectRow(0)
        actions[:] = [pay(5000)]
        act["record"]()
        # subcontratado
        def add_sub(dd):
            cmb, trade, phone, scope, sp = dd._fields
            cmb.setEditText("Test Carpet Guy")
            trade.setText("Carpet")
            scope.setText("Carpet in 2 bedrooms")
            sp.setValue(1500)
        actions[:] = [add_sub]
        act["add_sub"]()
        wg["subs"].selectRow(0)

        def pay_sub(dd):
            dd._fields[0].setValue(1000)
        actions[:] = [pay_sub]
        act["pay_sub"]()
        st["subs_text"] = [wg["subs"].item(0, c).text() for c in range(5)] if wg["subs"].rowCount() else []
        st["profit"] = wg["profit"].text()
        d.grab().save(os.path.join(os.environ.get("TEMP", "."), "project_dialog.png"))
        # segunda parcela: cobra e recebe → etapa Paid
        wg["plan"].selectRow(1)
        act["bill"]()
        wg["plan"].selectRow(1)
        actions[:] = [pay(5000)]
        act["record"]()
        st["stage"] = wg["stage"].currentData()

    actions[:] = [project]
    w.open_project_dialog(None); a.processEvents()
    pid = st.get("id")
    check("project saved as PRIVATE with a Job Code",
          pid and q("SELECT PROJECT_TYPE, CONTRACT_PRICE FROM job_projects WHERE ID=%s", (pid,))[0] == ("PRIVATE", 10000),
          (pid, st.get("code")))
    check("new client created", q("SELECT COUNT(*) FROM clients WHERE FULL_NAME='Test Private Client'")[0][0] == 1)
    check("50/50 plan created", st.get("plan_rows") == 2, st.get("plan_rows"))
    plan = q("SELECT NAME, AMOUNT, INVOICE_TYPE, INVOICE_ID FROM project_payment_plan WHERE JOB_PROJECT_ID=%s "
             "ORDER BY SORT_ORDER", (pid,))
    check("both payments billed as client invoices", len(plan) == 2 and all(p[2] == "Client" and p[3] for p in plan), plan)
    inv1 = plan[0][3] if plan else None
    r1 = q("SELECT TOTAL_AMOUNT, AMOUNT_PAID, STATUS, PDF_PATH FROM client_invoices WHERE ID=%s", (inv1,))
    check("deposit invoice paid", r1 and float(r1[0][1]) == 5000 and r1[0][2] == "RECEIVED", r1)
    check("invoice PDF saved", r1 and os.path.exists(r1[0][3]) and os.path.getsize(r1[0][3]) > 3000, r1 and r1[0][3])
    check("invoice offered by e-mail with the PDF", any(t == "Send invoice" and att for t, _s, att in sent), sent)
    paid_pdf = w._build_paid_invoice_pdf("Client", inv1)
    check("paid project invoice PDF", paid_pdf.endswith("_PAID.pdf") and os.path.exists(paid_pdf), paid_pdf)
    check("stage goes to Paid when everything is paid", st.get("stage") == "PAID", st.get("stage"))
    check("subcontractor row: agreed 1500, paid 1000, owed 500",
          st.get("subs_text", [])[2:] == ["$1,500.00", "$1,000.00", "$500.00"], st.get("subs_text"))
    exp = q("SELECT CATEGORY, AMOUNT, JOB_PROJECT_ID FROM expenses WHERE CATEGORY='SUBCONTRACTOR'")
    check("sub payment saved as a project expense (P&L)", exp and float(exp[0][1]) == 1000 and exp[0][2] == pid, exp)
    f = w._project_financials(pid)
    check("profit = price − subcontractor", abs(f["profit"] - (10000 - 1500)) < 0.01 and f["received"] == 10000, f)
    check("profit shown in the project", "$8,500.00" in st.get("profit", ""), st.get("profit"))

    # dias do projeto não aparecem em "Not invoiced yet"
    cur.execute("INSERT INTO work_days (WORK_DATE, CLIENT_ID, JOB_PROJECT_ID, STATUS, PAYMENT_METHOD, VALUE, JOB_ADDRESS, "
                "DEMOLITION, INSTALLATION, PREPARATION, DAY_FRACTION) SELECT CURDATE() - INTERVAL 1 DAY, CLIENT_ID, ID, "
                "'COMPLETED', 'Receivable', 250, JOB_ADDRESS, 'not', 'not', 'not', 1 FROM job_projects WHERE ID=%s", (pid,))
    day_id = cur.lastrowid
    groups = w._not_invoiced_groups()
    check("project work days are not in 'Not invoiced yet'", all(day_id not in g["days"] for g in groups))

    # projeto de Company (você é o subcontratado)
    def company_project(d):
        wg, act = d._widgets, d._actions
        wg["name"].setText("Carpet One — condo 305")
        wg["kind"].setCurrentIndex(1)
        idx = wg["payer"].findText("Carpet One")
        wg["payer"].setCurrentIndex(idx)
        wg["address"].setText("1135 Gulf of Mexico Dr")
        wg["price"].setValue(4200)
        d._save(silent=True)
        st["cid"] = d._state["id"]
        wg["template"].setCurrentIndex(3)  # 100% at the end
        act["template"]()
        wg["plan"].selectRow(0)
        act["bill"]()
    actions[:] = [company_project]
    w.open_project_dialog(None); a.processEvents()
    cp = q("SELECT INVOICE_TYPE, INVOICE_ID, AMOUNT FROM project_payment_plan WHERE JOB_PROJECT_ID=%s", (st.get("cid"),))
    check("company project bills a company invoice", cp and cp[0][0] == "Company" and float(cp[0][2]) == 4200, cp)
    check("company invoice in Receivables",
          cp and q("SELECT TOTAL_AMOUNT FROM company_invoices WHERE ID=%s", (cp[0][1],))[0][0] == 4200)

    # lista
    w.load_projects_page(); a.processEvents()
    w._cmb_project_stage.setCurrentIndex(w._cmb_project_stage.findData("ALL")); a.processEvents()
    t = w._table_projects
    codes = [t.item(r, 0).text() for r in range(t.rowCount())]
    check("projects listed", st.get("code") in codes, codes)
    open_value = float(q("SELECT COALESCE(SUM(CONTRACT_PRICE), 0) FROM job_projects WHERE PROJECT_TYPE='PRIVATE' "
                         "AND COALESCE(PROJECT_STAGE, 'ESTIMATE') NOT IN ('PAID', 'CANCELLED')")[0][0])
    check("cards show open contract value", w._project_card_values["contract"].text() == f"${open_value:,.2f}",
          (w._project_card_values["contract"].text(), open_value))
    check("cards show owed to subcontractors", w._project_card_values["subs_owed"].text() == "$500.00",
          w._project_card_values["subs_owed"].text())

    def subs_dialog(d):
        st["subs_rows"] = d._table.rowCount()
    actions[:] = [subs_dialog]
    w.open_subcontractors_dialog()
    check("subcontractors list", st.get("subs_rows") == 1, st.get("subs_rows"))
    w.grab().save(os.path.join(os.environ.get("TEMP", "."), "projects_page.png"))
    # nome de cliente que já existe (maiúsculas/espaços diferentes) não cria cliente repetido
    before = q("SELECT COUNT(*) FROM clients")[0][0]

    def same_client(d):
        wg = d._widgets
        wg["name"].setText("Second job same client")
        wg["kind"].setCurrentIndex(0)
        wg["payer"].setCurrentIndex(-1)
        wg["payer"].setEditText("  test   private CLIENT ")
        wg["address"].setText("100 Test Ave")
        d._save(silent=True)
        st["same_client_project"] = d._state["id"]
    actions[:] = [same_client]
    w.open_project_dialog(None); a.processEvents()
    check("project with an existing client's name reuses that client",
          q("SELECT COUNT(*) FROM clients")[0][0] == before and
          q("SELECT c.FULL_NAME FROM job_projects jp JOIN clients c ON c.ID = jp.CLIENT_ID WHERE jp.ID=%s",
            (st.get("same_client_project"),))[0][0] == "Test Private Client")

    # tela Customer: cadastrar de novo o mesmo cliente pergunta antes (resposta No → não cria)
    QMessageBox.question = staticmethod(lambda *a_, **k: msgs.append("Q " + str(a_[1])) or QMessageBox.StandardButton.No)
    w._go_to_page(6, ui.btn_customer); a.processEvents()
    w.new_customer_record() if hasattr(w, "new_customer_record") else None
    w._current_customer_id = None
    ui.txt_customer_name.setText("Test Private Client")
    before = q("SELECT COUNT(*) FROM clients")[0][0]
    w.save_customer_record(); a.processEvents()
    check("Customer: same name asks before creating a duplicate",
          any(m == "Q Customer already exists" for m in msgs) and q("SELECT COUNT(*) FROM clients")[0][0] == before)
    QMessageBox.question = staticmethod(lambda *a_, **k: QMessageBox.StandardButton.Yes)

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
