"""Testa Purchases (preço, materiais do job sem duplicar, estoque, despesa),
Stock (sobra e uso), Projects Board, Weekly Summary (sem enviar e-mail) e
Data Cleanup — numa CÓPIA temporária do banco (o banco real não muda)."""
import sys, os, subprocess, tempfile, traceback
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); os.chdir(ROOT)
import config, mysql.connector, smtplib
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog, QPushButton, QComboBox, QLineEdit

REAL = config.load_db_config()
TEST_DB = "vl_buy_test_tmp"
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
fc.execute("UPDATE app_settings SET SMTP_USER='your-email@gmail.com', SMTP_PASSWORD='your-app-password'")
fix.commit(); fix.close()

msgs = []
QMessageBox.information = staticmethod(lambda *a, **k: msgs.append(str(a[2])) or QMessageBox.StandardButton.Ok)
QMessageBox.warning = staticmethod(lambda *a, **k: msgs.append("WARN " + str(a[2])) or QMessageBox.StandardButton.Ok)
QMessageBox.critical = staticmethod(lambda *a, **k: msgs.append("CRIT " + str(a[2])) or QMessageBox.StandardButton.Ok)
QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)


def no_email(*a, **k):
    raise AssertionError("tried to send e-mail")


smtplib.SMTP = no_email
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

    # ── PURCHASE ──
    job_id, prod_old, qty_old = q("SELECT JOB_PROJECT_ID, PRODUCT_ID, QUANTITY FROM job_materials ORDER BY ID LIMIT 1")[0]
    cur.execute("UPDATE job_materials SET UNIT_PRICE=0 WHERE JOB_PROJECT_ID=%s AND PRODUCT_ID=%s", (job_id, prod_old))
    prod_new, prod_stock = [r[0] for r in q(
        "SELECT ID FROM products WHERE ID NOT IN (SELECT PRODUCT_ID FROM job_materials WHERE JOB_PROJECT_ID=%s) "
        "ORDER BY ID LIMIT 2", (job_id,))]
    w.load_job_profit()
    exp_before = q("SELECT COALESCE(SUM(AMOUNT),0) FROM expenses WHERE JOB_PROJECT_ID=%s", (job_id,))[0][0]

    def fill_purchase(d):
        d.findChild(QComboBox, "cmb_purchase_supplier").setCurrentText("carpet one")
        d.findChild(QLineEdit, "txt_purchase_order").setText("1228897")
        job = d.findChild(QComboBox, "cmb_purchase_job"); job.setCurrentIndex(job.findData(job_id))
        rows = [d._add_item(prod_old, float(qty_old), 31.5)]
        rows[0]  # a primeira linha vazia (criada ao abrir) é ignorada por não ter produto
        d._add_item(prod_new, 4, 12.0)
        d._add_item(prod_stock, 6, 9.25, stock=True)
        from PySide6.QtWidgets import QDoubleSpinBox
        d.findChild(QDoubleSpinBox, "dspn_purchase_tax").setValue(5.0)
        next(b for b in d.findChildren(QPushButton) if b.objectName() == "btn_save_purchase").click()
    actions.append(fill_purchase)
    saved = w.open_new_purchase_dialog()
    check("purchase saved", saved, msgs[-1:] if msgs else "")
    pur = q("SELECT ID, SUPPLIER, ORDER_NUMBER, TOTAL_AMOUNT, EXPENSE_ID FROM purchases ORDER BY ID DESC LIMIT 1")[0]
    expected_total = round(float(qty_old) * 31.5 + 4 * 12 + 6 * 9.25 + 5, 2)
    check("purchase header and total", pur[1] == "Carpet One" and pur[2] == "1228897"
          and abs(float(pur[3]) - expected_total) < 0.01, pur)
    check("3 items saved", q("SELECT COUNT(*) FROM purchase_items WHERE PURCHASE_ID=%s", (pur[0],))[0][0] == 3)
    line = q("SELECT QUANTITY, UNIT_PRICE FROM job_materials WHERE JOB_PROJECT_ID=%s AND PRODUCT_ID=%s", (job_id, prod_old))
    check("existing $0 material gets the price, qty not doubled",
          len(line) == 1 and float(line[0][0]) == float(qty_old) and float(line[0][1]) == 31.5, line)
    line = q("SELECT QUANTITY, UNIT_PRICE FROM job_materials WHERE JOB_PROJECT_ID=%s AND PRODUCT_ID=%s", (job_id, prod_new))
    check("new product added to the job", line and float(line[0][0]) == 4 and float(line[0][1]) == 12, line)
    check("stock item not in the job", not q("SELECT 1 FROM job_materials WHERE JOB_PROJECT_ID=%s AND PRODUCT_ID=%s",
                                             (job_id, prod_stock)))
    check("product price updated", float(q("SELECT PRICE FROM products WHERE ID=%s", (prod_new,))[0][0]) == 12)
    exp = q("SELECT CATEGORY, VENDOR, AMOUNT, JOB_PROJECT_ID FROM expenses WHERE ID=%s", (pur[4],))
    check("materials expense created and linked", exp and exp[0][0] == "MATERIALS" and exp[0][1] == "Carpet One"
          and abs(float(exp[0][2]) - expected_total) < 0.01 and exp[0][3] == job_id, exp)

    # Job Profit não conta a compra duas vezes (só o imposto entra como despesa)
    w._profit_widgets[0].setCurrentIndex(3); w.load_job_profit()
    t = w._profit_widgets[2]
    code = q("SELECT CODE FROM job_projects WHERE ID=%s", (job_id,))[0][0]
    row = next((r for r in range(t.rowCount()) if t.item(r, 0).text() == code), None)
    if row is not None:
        shown = t.item(row, 4).data(0x0100)
        check("job profit counts only the purchase tax as expense", abs(float(shown) - (float(exp_before) + 5)) < 0.01,
              (shown, exp_before))

    # ── STOCK ──
    bal = {r[0]: r[4] for r in w._stock_balance()}
    check("stock item is in the stock", bal.get(prod_stock) == 6, bal)

    def leftover(d):
        d._job.setCurrentIndex(d._job.findData(job_id))
        d._product.setCurrentIndex(next(i for i in range(d._product.count())
                                        if q("SELECT PRODUCT_ID FROM job_materials WHERE ID=%s",
                                             (d._product.itemData(i),))[0][0] == prod_new))
        d._qty.setValue(1.5)
        next(b for b in d.findChildren(QPushButton) if b.objectName() == "btn_save_leftover").click()
    actions.append(leftover)
    check("leftover saved", w.open_leftover_dialog(job_id))
    left = q("SELECT QUANTITY FROM job_materials WHERE JOB_PROJECT_ID=%s AND PRODUCT_ID=%s", (job_id, prod_new))
    check("leftover taken out of the job", left and float(left[0][0]) == 2.5, left)
    check("leftover is in stock", {r[0]: r[4] for r in w._stock_balance()}.get(prod_new) == 1.5)

    other_job = q("SELECT ID FROM job_projects WHERE ID <> %s AND CODE IS NOT NULL ORDER BY ID DESC LIMIT 1", (job_id,))[0][0]

    def use(d):
        d._product.setCurrentIndex(d._product.findData(prod_stock))
        d._qty.setValue(4)
        d._job.setCurrentIndex(d._job.findData(other_job))
        next(b for b in d.findChildren(QPushButton) if b.objectName() == "btn_save_use_stock").click()
    actions.append(use)
    check("use stock saved", w.open_use_stock_dialog(prod_stock))
    used = q("SELECT QUANTITY, UNIT_PRICE FROM job_materials WHERE JOB_PROJECT_ID=%s AND PRODUCT_ID=%s",
             (other_job, prod_stock))
    check("stock goes into the other job at stock price", used and float(used[0][0]) >= 4
          and float(used[0][1]) > 0, used)
    check("stock reduced", {r[0]: r[4] for r in w._stock_balance()}.get(prod_stock) == 2)
    actions.append(lambda d: None)
    w.open_stock_dialog()  # abre sem erro

    # ── BOARD ──
    projects = w._board_projects()
    check("board has projects in stages", projects and all(p["stage"] in
          ("PENDING", "IN_PROGRESS", "COMPLETED", "INVOICED", "PAID") for p in projects), len(projects))
    target = next(p for p in projects if p["stage"] in ("IN_PROGRESS", "PENDING") and p["days"])
    final = w._board_move(target["id"], target["stage"], "COMPLETED")
    still_open = q("SELECT COUNT(*) FROM work_days WHERE JOB_PROJECT_ID=%s AND WORK_DATE <= CURDATE() "
                   "AND STATUS NOT IN ('COMPLETED','CANCELLED')", (target["id"],))[0][0]
    check("drag to Completed completes the past days", still_open == 0, (final, still_open))
    check("move to Invoiced", w._board_move(target["id"], final, "INVOICED") == "INVOICED")
    check("move to Paid", w._board_move(target["id"], "INVOICED", "PAID") == "PAID")
    check("Job Code status stored", q("SELECT STATUS FROM job_projects WHERE ID=%s", (target["id"],))[0][0] == "PAID")
    back = w._board_move(target["id"], "PAID", "IN_PROGRESS")
    check("moving back clears the manual stage", q("SELECT STATUS FROM job_projects WHERE ID=%s",
                                                   (target["id"],))[0][0] == "ACTIVE", back)
    seen = {}

    def board(d):
        d._reload()
        seen.update({k: lst.count() for k, lst in d._lists.items()})
    actions.append(board)
    w.open_projects_board()
    check("board dialog shows cards", sum(seen.values()) > 0, seen)

    # ── WEEKLY SUMMARY ──
    from datetime import timedelta
    last = q("SELECT MAX(WORK_DATE) FROM work_days")[0][0]
    monday = last - timedelta(days=last.weekday())
    data = w._weekly_summary_data(monday)
    html_text = w._weekly_summary_html(data)
    check("summary has days and value", data["days"] and "Value produced" in html_text and "Helper pay" in html_text,
          (len(data["days"]), data["value"]))
    check("summary recipient from settings", w._summary_recipient().endswith("@vertexlondeflooring.com"))
    shown = {}

    def weekly(d):
        shown["html"] = d._view.toPlainText()
    actions.append(weekly)
    w.open_weekly_summary_dialog(monday)
    check("summary dialog shows the week", "Weekly summary" in shown.get("html", ""))
    w._auto_send_weekly_summary()  # SMTP não configurado → não envia (smtplib levantaria erro)
    check("no auto e-mail without SMTP", q("SELECT SUMMARY_LAST_SENT FROM app_settings")[0][0] is None)

    # ── CLEANUP ──
    counts = w._cleanup_counts()
    check("cleanup finds the fake clients", counts["clients"] >= 1, counts)
    result = {}

    def cleanup(d):
        t = d._tables
        result["before"] = {k: v.rowCount() for k, v in t.items()}
        t["days"].selectAll()
        d._buttons["done"].click()
        d._buttons["fix_clients"].click()
        if t["products"].rowCount():
            t["products"].cellWidget(0, 4).setValue(7.77)
            result["pid"] = t["products"].item(0, 0).data(0x0100)
            d._buttons["prices"].click()
        result["after"] = {k: v.rowCount() for k, v in t.items()}
    actions.append(cleanup)
    w.open_data_cleanup_dialog()
    check("old open days fixed", result["after"]["days"] == 0, result)
    check("fake clients removed", result["after"]["clients"] == 0 and
          q("SELECT COUNT(*) FROM clients WHERE FULL_NAME LIKE '%— Select%'")[0][0] == 0)
    if "pid" in result:
        check("price saved from cleanup", float(q("SELECT PRICE FROM products WHERE ID=%s", (result["pid"],))[0][0]) == 7.77)

    # ── HUB ──
    w._go_to_page(w._hub_index, w.ui.btn_registrations); a.processEvents()
    check("hub has the new cards", all(k in w._hub_cards for k in ("purchases", "stock", "board", "weekly", "cleanup")))
    check("leftover button in job form", hasattr(w.ui, "btn_new_job_leftover"))
    crit = [m for m in msgs if m.startswith("CRIT")]
    check("no database errors", not crit, crit[:2])
    db.close()
except Exception:
    traceback.print_exc(); ok = False
finally:
    acur.execute("SET SESSION lock_wait_timeout = 15")
    acur.execute(f"DROP DATABASE IF EXISTS {TEST_DB}"); admin.close(); os.remove(cnf.name)
    print("temp db dropped", flush=True)
print("RESULT:", "ALL OK" if ok else "FAILED", flush=True)
sys.exit(0 if ok else 1)
