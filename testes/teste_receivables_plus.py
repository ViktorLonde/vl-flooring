"""Testa as melhorias de Receivables (25/11/2026) numa CÓPIA temporária do banco:
card "Not invoiced yet" + gerar invoice já com os dias marcados, previsão de
recebimento, aviso de pagamento a mais (guardar como extra), atalhos de
período, filtros rápidos e ações na lista de Invoices, e a pergunta quando o
pagamento passa do saldo. Nenhum e-mail é enviado."""
import sys, os, subprocess, tempfile, traceback, shutil
from datetime import date
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); os.chdir(ROOT)
import config, mysql.connector
from PySide6.QtWidgets import (QApplication, QMessageBox, QDialog, QPushButton, QDoubleSpinBox, QTableWidget,
                               QLabel, QListWidget)
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import Qt

REAL = config.load_db_config()
TEST_DB = "vl_recv_plus_test_tmp"
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
FILES_TMP = os.path.join(tmpdir, "files")
arquivos.files_root = lambda: FILES_TMP

msgs = []
QMessageBox.information = staticmethod(lambda *a, **k: msgs.append(str(a[2])) or QMessageBox.StandardButton.Ok)
QMessageBox.warning = staticmethod(lambda *a, **k: msgs.append("WARN " + str(a[2])) or QMessageBox.StandardButton.Ok)
QMessageBox.critical = staticmethod(lambda *a, **k: msgs.append("CRIT " + str(a[2])) or QMessageBox.StandardButton.Ok)
QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)
QDesktopServices.openUrl = staticmethod(lambda *a: True)
overpay_choice = {"text": "Record only"}


def fake_box_exec(box):
    """QMessageBox montado à mão (pagamento a mais): clica o botão escolhido."""
    for b in box.buttons():
        if b.text().startswith(overpay_choice["text"]):
            b.click()
            return 0
    return 0


QMessageBox.exec = fake_box_exec
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
    a = QApplication(sys.argv)
    w = MainWindow(db_config=TEST); w.resize(1536, 900); w.show(); a.processEvents()
    w.set_current_user("viktorlonde")
    w.offer_payment_receipt = lambda *a_, **k: False  # nunca manda recibo por e-mail no teste
    w._confirm_bank_info_ready = lambda *a_, **k: True
    ui = w.ui

    # ── Dashboard ──
    w._go_to_page(5, ui.btn_nav_receivables); ui.tabWidget_receivables.setCurrentIndex(0)
    w.load_receivables_dashboard(); a.processEvents()
    expected_not_inv = float(q("""SELECT COALESCE(SUM(VALUE),0) FROM work_days wd WHERE WORK_DATE <= CURDATE()
        AND COALESCE(STATUS,'') <> 'CANCELLED' AND COALESCE(VALUE,0) > 0
        AND COALESCE(PAYMENT_METHOD,'Receivable')='Receivable'
        AND NOT EXISTS (SELECT 1 FROM invoice_work_days i WHERE i.WORK_DAY_ID = wd.ID)""")[0][0])
    check("Not invoiced card shows the right total", w._lbl_not_invoiced_value.text() == f"${expected_not_inv:,.2f}",
          (w._lbl_not_invoiced_value.text(), expected_not_inv))
    open_now = float(q("SELECT COALESCE(SUM(TOTAL_AMOUNT-AMOUNT_PAID),0) FROM contractor_invoices "
                       "WHERE STATUS IN ('PENDING','PARTIAL')")[0][0])
    exp_sum = sum(float(l.text().replace("$", "").replace(",", "")) for l in w._lbl_expected.values())
    check("Expected buckets add up to what is open", abs(exp_sum - open_now) < 0.01, (exp_sum, open_now))
    overpaid = q("SELECT ID FROM contractor_invoices WHERE AMOUNT_PAID > TOTAL_AMOUNT + 0.005")
    check("overpaid banner shown", w._frame_overpaid.isVisible() == bool(overpaid) and
          (not overpaid or f"#{overpaid[0][0]}" in w._lbl_overpaid.text()), w._lbl_overpaid.text())

    # período: atalhos e "Custom"
    preset = w._cmb_dashboard_preset
    preset.setCurrentText("Last year"); a.processEvents()
    check("Last year preset sets the combos", ui.cmb_dashboard_month.currentData() == 0
          and ui.cmb_dashboard_year.currentData() == date.today().year - 1,
          (ui.cmb_dashboard_month.currentData(), ui.cmb_dashboard_year.currentData()))
    check("Total Receivable ignores the period (open now)",
          ui.lbl_receivables_total_value.text() == f"${open_now:,.2f}", ui.lbl_receivables_total_value.text())
    ui.cmb_dashboard_month.setCurrentIndex(3); a.processEvents()
    check("changing month by hand shows Custom", preset.currentText() == "Custom", preset.currentText())
    preset.setCurrentText("This month"); a.processEvents()
    check("This month preset", ui.cmb_dashboard_month.currentData() == date.today().month)

    # ── Not invoiced → Generate invoice com os dias marcados ──
    groups = w._not_invoiced_groups()
    g = groups[0]
    state = {}

    def pick_group(d):
        t = d.findChild(QTableWidget, "table_not_invoiced")
        state["rows"] = t.rowCount()
        t.selectRow(0)
        next(b for b in d.findChildren(QPushButton) if b.text() == "Generate invoice").click()

    def gen_dialog(d):
        lbl = next(l for l in d.findChildren(QLabel) if "job(s) selected" in l.text())
        state["status"] = lbl.text()
        next(b for b in d.findChildren(QPushButton) if b.text() == "Generate PDFs").click()

    actions[:] = [pick_group, gen_dialog]
    before_inv = q("SELECT COALESCE(MAX(ID),0) FROM contractor_invoices")[0][0]
    w.open_not_invoiced_dialog(); a.processEvents()
    check("not-invoiced dialog lists the groups", state.get("rows") == len(groups), state.get("rows"))
    check("generate dialog opens with only those days selected",
          state.get("status", "").startswith(f"{len(g['days'])} job(s) selected — total ${g['total']:,.2f}")
          and "0 expense(s) selected" in state.get("status", ""),
          (state.get("status"), len(g["days"]), g["total"]))
    new_inv = q("SELECT ID, TOTAL_AMOUNT FROM contractor_invoices WHERE ID > %s", (before_inv,))
    linked = {r[0] for r in q("SELECT WORK_DAY_ID FROM invoice_work_days WHERE INVOICE_TYPE='Contractor' "
                              "AND INVOICE_ID=%s", (new_inv[0][0],))} if new_inv else set()
    check("invoice created with exactly those days", new_inv and linked == set(g["days"]),
          (new_inv, len(linked), len(g["days"])))
    w.load_receivables_dashboard(); a.processEvents()
    left = sum(x["total"] for x in w._not_invoiced_groups())
    check("not invoiced total went down", abs(left - (expected_not_inv - g["total"])) < 0.01, left)

    # gerar de novo o mesmo período: dias já faturados aparecem desmarcados
    def regen(d):
        jobs = [t for t in d.findChildren(QTableWidget) if t.horizontalHeaderItem(2) and t.horizontalHeaderItem(2).text() == "Address"][0]
        marked = [r for r in range(jobs.rowCount())
                  if "(invoiced #" in (jobs.item(r, 2).text() if jobs.item(r, 2) else "")]
        state["marked"] = len(marked)
        state["marked_checked"] = sum(jobs.item(r, 0).checkState() == Qt.CheckState.Checked for r in marked)
    actions[:] = [regen]
    w.open_generate_invoices_dialog(prefill_bill_to="Contractor", prefill_from=g["first"], prefill_to=g["last"])
    check("already-invoiced days are marked and start unchecked", state.get("marked", 0) >= len(g["days"])
          and state.get("marked_checked") == 0, (state.get("marked"), state.get("marked_checked")))

    # ── pagamento a mais: revisar e guardar como extra ──
    if overpaid:
        def keep(d):
            d.findChild(QPushButton, "btn_keep_extra").click()
        actions[:] = [keep]
        w.open_overpaid_review_dialog(); a.processEvents()
        note = q("SELECT ADJUSTMENT_NOTE FROM contractor_invoices WHERE ID=%s", (overpaid[0][0],))[0][0] or ""
        check("kept as extra/tip → note saved", "Extra/tip received: $" in note, note)
        w.load_receivables_dashboard(); a.processEvents()
        check("banner gone after review", not w._frame_overpaid.isVisible())

    # ── Invoices: filtros rápidos, status com vencimento, ações ──
    ui.tabWidget_receivables.setCurrentIndex(1); ui.cmb_invoice_entity_type.setCurrentText("Contractor")
    w._invoice_quick_buttons["all"].click(); a.processEvents()
    t = ui.table_contractor_invoices
    statuses = [t.item(r, 7).text() for r in range(t.rowCount())]
    pend = [s for s in statuses if s.startswith(("Payment Due", "Partially Paid"))]
    check("open invoices show due date or days late", pend and all(("due" in s or "late" in s) for s in pend), pend)
    w._invoice_quick_buttons["RECEIVED"].click(); a.processEvents()
    check("Paid button filters by status", ui.cmb_filter_invoice_status.currentText() == "RECEIVED"
          and all(t.item(r, 7).text().startswith("Paid in Full") for r in range(t.rowCount())))
    w._invoice_quick_buttons["overdue"].click(); a.processEvents()
    visible = [t.item(r, 7).text() for r in range(t.rowCount()) if not t.isRowHidden(r)]
    check("Overdue button shows only late ones", all("late" in s for s in visible), visible)
    w._invoice_quick_buttons["all"].click(); a.processEvents()
    check("action buttons disabled with no selection", not any(b.isEnabled() for b in w._invoice_action_buttons))

    open_id = q("SELECT ID, TOTAL_AMOUNT - AMOUNT_PAID FROM contractor_invoices WHERE STATUS IN ('PENDING','PARTIAL') "
                "ORDER BY ID LIMIT 1")
    if open_id:
        iid, bal = open_id[0][0], float(open_id[0][1])
        row = next(r for r in range(t.rowCount()) if t.item(r, 0).text() == str(iid))
        t.selectRow(row); a.processEvents()
        check("action buttons enabled on an open invoice", all(b.isEnabled() for b in w._invoice_action_buttons))
        check("reminder for one invoice finds it", len(w._overdue_invoices(only=("Contractor", iid))) == 1)

        def pay_too_much(d):
            lst = d.findChild(QListWidget)
            state["preselected"] = lst.currentItem().text() if lst.currentItem() else ""
            d.findChildren(QDoubleSpinBox)[0].setValue(bal + 100)
            next(b for b in d.findChildren(QPushButton) if b.text() == "Record Payment").click()
        overpay_choice["text"] = "Record only"
        actions[:] = [pay_too_much]
        w.invoice_action_record_payment(); a.processEvents()
        check("Record payment opens with the invoice selected", state.get("preselected", "").startswith(f"#{iid} —"),
              state.get("preselected"))
        paid = q("SELECT AMOUNT_PAID, TOTAL_AMOUNT, STATUS FROM contractor_invoices WHERE ID=%s", (iid,))[0]
        check("overpayment → recorded only the balance", abs(float(paid[0]) - float(paid[1])) < 0.01
              and paid[2] == "RECEIVED", paid)

        w.load_contractor_invoices(); a.processEvents()
        row = next(r for r in range(t.rowCount()) if t.item(r, 0).text() == str(iid))
        t.selectRow(row); a.processEvents()
        check("paid invoice: Record payment / reminder disabled",
              not w._invoice_action_buttons[0].isEnabled() and not w._invoice_action_buttons[3].isEnabled()
              and w._invoice_action_buttons[2].isEnabled())
        w.invoice_action_open_pdf()  # não pode dar erro (arquivo pode não existir na cópia)

    check("no error dialogs", not [m for m in msgs if m.startswith("CRIT")], [m for m in msgs if m.startswith("CRIT")])
    w.ui.tabWidget_receivables.setCurrentIndex(0); a.processEvents()
    w.grab().save(os.path.join(os.environ.get("TEMP", "."), "receivables_dashboard.png"))
    ui.tabWidget_receivables.setCurrentIndex(1); a.processEvents()
    w.grab().save(os.path.join(os.environ.get("TEMP", "."), "receivables_invoices.png"))
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
