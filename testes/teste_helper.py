"""Testa o campo Helper do job: salva, carrega de volta, NÃO é copiado para
os outros dias do mesmo Job Code e aparece na agenda da semana — numa CÓPIA
temporária do banco (o banco real não é alterado)."""
import sys, os, subprocess, tempfile, traceback
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); os.chdir(ROOT)
import config, mysql.connector
from PySide6.QtWidgets import QApplication, QMessageBox

REAL = config.load_db_config()
TEST_DB = "vl_helper_test_tmp"
BIN = r"C:\Program Files\MySQL\MySQL Server 8.0\bin"
cnf = tempfile.NamedTemporaryFile("w", suffix=".cnf", delete=False)
cnf.write(f"[client]\nhost={REAL['host']}\nuser={REAL['user']}\npassword=\"{REAL['password']}\"\n"); cnf.close()
admin = mysql.connector.connect(**REAL); acur = admin.cursor()
acur.execute(f"DROP DATABASE IF EXISTS {TEST_DB}"); acur.execute(f"CREATE DATABASE {TEST_DB}")
dump = subprocess.run([os.path.join(BIN, "mysqldump.exe"), f"--defaults-extra-file={cnf.name}", "--single-transaction",
                       REAL["database"]], capture_output=True, check=True).stdout
subprocess.run([os.path.join(BIN, "mysql.exe"), f"--defaults-extra-file={cnf.name}", TEST_DB], input=dump, check=True)
TEST = {**REAL, "database": TEST_DB}

msgs = []
QMessageBox.information = staticmethod(lambda *a, **k: msgs.append(str(a[2])) or QMessageBox.StandardButton.Ok)
QMessageBox.warning = staticmethod(lambda *a, **k: msgs.append("WARN " + str(a[2])) or QMessageBox.StandardButton.Ok)
QMessageBox.critical = staticmethod(lambda *a, **k: msgs.append("CRIT " + str(a[2])) or QMessageBox.StandardButton.Ok)
QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)
ok = True


def check(name, cond, extra=""):
    global ok
    ok &= bool(cond)
    print(("PASS " if cond else "FAIL ") + name, extra, flush=True)


try:
    db = mysql.connector.connect(**TEST); db.autocommit = True; cur = db.cursor()

    def q(sql, p=()):
        cur.execute(sql, p); return cur.fetchall()

    check("HELPER_ID column exists", q("SHOW COLUMNS FROM work_days LIKE 'HELPER_ID'"))
    cur.execute("INSERT INTO helpers (FULL_NAME, PHONE_NUMBER, PAYMENT_ZELLE) VALUES ('Test Helper', '941', 'zelle@x')")
    helper_id = cur.lastrowid
    check("helper payment column saves", q("SELECT PAYMENT_ZELLE FROM helpers WHERE ID=%s", (helper_id,))[0][0] == "zelle@x")
    pid = q("SELECT JOB_PROJECT_ID FROM work_days WHERE JOB_PROJECT_ID IS NOT NULL GROUP BY JOB_PROJECT_ID "
            "HAVING COUNT(*) >= 2 ORDER BY MAX(WORK_DATE) DESC LIMIT 1")[0][0]
    days = [r[0] for r in q("SELECT ID FROM work_days WHERE JOB_PROJECT_ID=%s ORDER BY ID", (pid,))]
    target, other = days[0], days[1]
    work_date = q("SELECT WORK_DATE FROM work_days WHERE ID=%s", (target,))[0][0]

    from main_ import MainWindow
    a = QApplication(sys.argv)
    w = MainWindow(db_config=TEST); w.resize(1536, 816); w.show(); a.processEvents()
    w.set_current_user("viktorlonde")
    w._go_to_page(1, w.ui.btn_jobs); a.processEvents()
    w._open_job_by_id(target, work_date); a.processEvents()
    check("job opened", str(w._current_job_id) == str(target), w._current_job_id)
    idx = w.ui.cmb_helper.findData(helper_id)
    check("helper appears in the Helper list", idx >= 0)
    w.ui.cmb_helper.setCurrentIndex(idx)
    w.ui.dspn_helper_pay.setValue(150)
    msgs.clear(); w.save_job_record(); a.processEvents()
    saved, pay = q("SELECT HELPER_ID, HELPER_PAY FROM work_days WHERE ID=%s", (target,))[0]
    check("helper saved on the job", saved == helper_id, (saved, msgs[-1:]))
    check("helper pay saved", float(pay or 0) == 150.0, pay)
    check("helper NOT copied to other days of the code",
          q("SELECT HELPER_ID FROM work_days WHERE ID=%s", (other,))[0][0] in (None, 0))

    w._current_job_id = None
    w._open_job_by_id(target, work_date); a.processEvents()
    check("helper loads back into the form", w.ui.cmb_helper.currentData() == helper_id, w.ui.cmb_helper.currentText())
    check("helper pay loads back", w.ui.dspn_helper_pay.value() == 150.0, w.ui.dspn_helper_pay.value())
    w._job_form_dirty = False

    # lucro do Job Code desconta o pagamento do helper
    code = q("SELECT CODE FROM job_projects WHERE ID=%s", (pid,))[0][0]
    w._profit_widgets[0].setCurrentIndex(3)  # All time
    w.load_job_profit()
    t = w._profit_widgets[2]
    row = next(r for r in range(t.rowCount()) if t.item(r, 0).text() == code)
    revenue = float(t.item(row, 3).data(256)); helper_col = float(t.item(row, 6).data(256))
    profit = float(t.item(row, 7).data(256))
    check("profit subtracts helper pay", helper_col == 150.0 and abs(profit - (revenue - 150.0)) < 0.01,
          (revenue, helper_col, profit))

    # New Job zera o pagamento
    w.new_job_record(); a.processEvents()
    check("new job starts with helper pay 0", w.ui.dspn_helper_pay.value() == 0)
    w._job_form_dirty = False

    from datetime import timedelta
    monday = work_date - timedelta(days=work_date.weekday())
    text = w._week_schedule_text(monday, w._week_schedule_rows(monday))
    check("week schedule shows the helper", "Helper: Test Helper" in text)
    db.close()
except Exception:
    traceback.print_exc(); ok = False
finally:
    acur.execute("SET SESSION lock_wait_timeout = 15")
    acur.execute(f"DROP DATABASE IF EXISTS {TEST_DB}"); admin.close(); os.remove(cnf.name)
    print("temp db dropped", flush=True)
print("RESULT:", "ALL OK" if ok else "FAILED", flush=True)
sys.exit(0 if ok else 1)
