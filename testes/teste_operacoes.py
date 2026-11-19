"""Testa editar vários jobs, duplicar job, agenda da semana, lucro por job,
lembretes (sem enviar e-mail) e o aviso de backup — numa CÓPIA temporária
do banco (o banco real não é alterado)."""
import sys, os, subprocess, tempfile, traceback
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); os.chdir(ROOT)
import config, mysql.connector, smtplib
from PySide6.QtWidgets import (QApplication, QMessageBox, QDialog, QCheckBox, QComboBox, QPushButton, QSpinBox)

REAL = config.load_db_config()
TEST_DB = "vl_ops_test_tmp"
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
fc.execute("UPDATE users SET role='ADMIN', status='Active' WHERE username='viktorlonde'"); fix.commit(); fix.close()

msgs = []
QMessageBox.information = staticmethod(lambda *a, **k: msgs.append(str(a[2])) or QMessageBox.StandardButton.Ok)
QMessageBox.warning = staticmethod(lambda *a, **k: msgs.append("WARN " + str(a[2])) or QMessageBox.StandardButton.Ok)
QMessageBox.critical = staticmethod(lambda *a, **k: msgs.append("CRIT " + str(a[2])) or QMessageBox.StandardButton.Ok)
QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)


def no_email(*a, **k):
    raise AssertionError("tried to send e-mail")


smtplib.SMTP = no_email
ok = True
errors = []


def check(name, cond, extra=""):
    global ok
    ok &= bool(cond)
    print(("PASS " if cond else "FAIL ") + name, extra, flush=True)


dialog_actions = []
QDialog.exec = lambda d: (dialog_actions.pop(0)(d) if dialog_actions else None, 0)[1]

try:
    from main_ import MainWindow
    a = QApplication(sys.argv)
    w = MainWindow(db_config=TEST); w.resize(1536, 816); w.show(); a.processEvents()
    w.set_current_user("viktorlonde")
    db = mysql.connector.connect(**TEST); db.autocommit = True; cur = db.cursor()

    def q(sql, p=()):
        cur.execute(sql, p); return cur.fetchall()

    # ── editar vários ──
    w._go_to_page(1, w.ui.btn_jobs); w.ui.cmb_filter_status.setCurrentIndex(0); w.load_work_days()
    t = w.ui.table_work_days
    t.clearSelection()
    t.selectRow(0); t.selectRow(1)
    from PySide6.QtCore import QItemSelectionModel
    sm = t.selectionModel()
    sm.select(t.model().index(0, 0), QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows)
    a.processEvents()
    ids = w._selected_job_ids()
    check("multi-select picks 2 jobs", len(ids) == 2, ids)
    check("bulk edit button visible", w._btn_bulk_edit.isVisible(), w._btn_bulk_edit.text())

    def bulk(d):
        chk = next(c for c in d.findChildren(QCheckBox) if c.text() == "Status")
        chk.setChecked(True)
        combo = [c for c in d.findChildren(QComboBox)][0]
        combo.setCurrentText("COMPLETED")
        next(b for b in d.findChildren(QPushButton) if b.objectName() == "btn_save_bulk_edit").click()
    dialog_actions.append(bulk)
    w.open_bulk_edit_dialog(); a.processEvents()
    st = q(f"SELECT STATUS FROM work_days WHERE ID IN ({ids[0]},{ids[1]})")
    check("bulk edit changed status", all(s[0] == "COMPLETED" for s in st), st)
    w._job_form_dirty = False

    # ── duplicar ──
    job = ids[0]
    w._open_job_by_id(job, None); a.processEvents()
    w._job_form_dirty = False
    before = q("SELECT COUNT(*) FROM work_days")[0][0]
    pid = q("SELECT JOB_PROJECT_ID FROM work_days WHERE ID=%s", (job,))[0][0]

    def dup(d):
        d.findChild(QSpinBox).setValue(3)
        next(b for b in d.findChildren(QPushButton) if b.objectName() == "btn_save_duplicate").click()
    dialog_actions.append(dup)
    w._current_job_id = job
    w.open_duplicate_job_dialog(); a.processEvents()
    after = q("SELECT COUNT(*) FROM work_days")[0][0]
    new = q("SELECT JOB_PROJECT_ID, STATUS FROM work_days ORDER BY ID DESC LIMIT 3")
    check("duplicate created 3 copies", after == before + 3, (before, after))
    check("copies keep Job Code and start PENDING", all(n[0] == pid and n[1] == "PENDING" for n in new), new)

    # ── agenda da semana ──
    from datetime import date, timedelta
    d0 = q("SELECT WORK_DATE FROM work_days ORDER BY WORK_DATE DESC LIMIT 1 OFFSET 3")[0][0]
    monday = d0 - timedelta(days=d0.weekday())
    rows = w._week_schedule_rows(monday)
    text = w._week_schedule_text(monday, rows)
    check("week schedule lists jobs", rows and "Mon" in text and "•" in text, text[:120].replace("\n", " | "))

    # ── lucro ──
    w._profit_widgets[0].setCurrentIndex(3)  # All time
    w.load_job_profit()
    check("profit report has rows", w._profit_widgets[2].rowCount() > 0, w._profit_widgets[1].text())

    # ── lembretes (sem enviar) ──
    inv = w._overdue_invoices()
    check("overdue invoices listed", isinstance(inv, list), len(inv))
    check("smtp placeholder detected", not w._smtp_ready())

    # ── aviso de backup ──
    item = w._backup_attention_item()
    check("backup check runs", item is None or len(item) == 4, item[2] if item else "up to date")

    # ── concluir o trabalho (todos os dias do Job Code) ──
    code_pid = q("SELECT JOB_PROJECT_ID FROM work_days WHERE JOB_PROJECT_ID IS NOT NULL GROUP BY JOB_PROJECT_ID "
                 "HAVING SUM(STATUS <> 'COMPLETED') >= 2 ORDER BY COUNT(*) DESC LIMIT 1")[0][0]
    code_ids = [r[0] for r in q("SELECT ID FROM work_days WHERE JOB_PROJECT_ID=%s ORDER BY ID", (code_pid,))]
    future_id = code_ids[-1]
    cur.execute("UPDATE work_days SET WORK_DATE = CURDATE() + INTERVAL 20 DAY, STATUS='PENDING' WHERE ID=%s", (future_id,))
    w._go_to_page(1, w.ui.btn_jobs)
    w._open_job_by_id(code_ids[0], None); a.processEvents()
    w._job_form_dirty = False
    w._update_days_worked_label(); a.processEvents()
    check("Complete job button visible", w._btn_complete_job.isVisible())
    check("days tooltip lists the days", "#" in w.ui.lbl_days_worked_value.toolTip())

    def complete(d):
        next(b for b in d.findChildren(QPushButton) if b.objectName() == "btn_complete_job_confirm").click()
    dialog_actions.append(complete)
    w.open_complete_job_dialog(); a.processEvents()
    statuses = dict(q("SELECT ID, STATUS FROM work_days WHERE JOB_PROJECT_ID=%s", (code_pid,)))
    past_ok = all(statuses[i] in ("COMPLETED", "CANCELLED") for i in code_ids if i != future_id)
    check("past days marked COMPLETED", past_ok, statuses)
    check("future day left untouched", statuses[future_id] == "PENDING")

    # ── preço preenchido depois: materiais lançados a $0 recebem o preço ──
    pid_m, prod = q("SELECT JOB_PROJECT_ID, PRODUCT_ID FROM job_materials LIMIT 1")[0] if q(
        "SELECT COUNT(*) FROM job_materials")[0][0] else (None, None)
    if prod:
        cur.execute("UPDATE job_materials SET UNIT_PRICE=0 WHERE PRODUCT_ID=%s", (prod,))
        w._fill_unpriced_job_materials(prod, 42.5)
        prices = {float(p[0]) for p in q("SELECT UNIT_PRICE FROM job_materials WHERE PRODUCT_ID=%s", (prod,))}
        check("unpriced materials get the new price", prices == {42.5}, prices)

    # ── materiais: produto repetido soma; edição de quantidade/preço ──
    w._go_to_page(1, w.ui.btn_jobs)
    w._open_job_by_id(code_ids[0], None); a.processEvents(); w._job_form_dirty = False
    prod = q("SELECT ID FROM products WHERE ID NOT IN (SELECT PRODUCT_ID FROM job_materials WHERE JOB_PROJECT_ID=%s) "
             "ORDER BY ID LIMIT 1", (code_pid,))[0][0]
    combo = w.ui.cmb_material_product
    combo.setCurrentIndex(combo.findData(prod)); w.ui.dspn_material_qty.setValue(5)
    w.add_job_material(); a.processEvents()
    combo.setCurrentIndex(combo.findData(prod)); w.ui.dspn_material_qty.setValue(3)

    def merge(d):
        next(b for b in d.findChildren(QPushButton) if b.text().startswith("Add to it")).click()
    dialog_actions.append(merge)
    w.add_job_material(); a.processEvents()
    lines = q("SELECT ID, QUANTITY FROM job_materials WHERE JOB_PROJECT_ID=%s AND PRODUCT_ID=%s", (code_pid, prod))
    check("same product is added to the existing line", len(lines) == 1 and float(lines[0][1]) == 8, lines)

    def edit(d):
        from PySide6.QtWidgets import QDoubleSpinBox as _S
        spins = d.findChildren(_S); spins[0].setValue(6.5); spins[1].setValue(12.25)
        next(b for b in d.findChildren(QPushButton) if b.objectName() == "btn_save_material_edit").click()
    dialog_actions.append(edit)
    w.edit_job_material(lines[0][0]); a.processEvents()
    after = q("SELECT QUANTITY, UNIT_PRICE FROM job_materials WHERE ID=%s", (lines[0][0],))[0]
    check("material quantity and price can be edited", float(after[0]) == 6.5 and float(after[1]) == 12.25, after)
except Exception:
    traceback.print_exc(); ok = False
finally:
    try: db.close()
    except Exception: pass
    acur.execute("SET SESSION lock_wait_timeout = 15")
    acur.execute(f"DROP DATABASE IF EXISTS {TEST_DB}"); admin.close(); os.remove(cnf.name)
    print("temp db dropped", flush=True)
print("RESULT:", "ALL OK" if ok else "FAILED", flush=True)
sys.exit(0 if ok else 1)
