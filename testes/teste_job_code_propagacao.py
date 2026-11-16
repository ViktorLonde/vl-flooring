"""Testa a propagação por Job Code e o limpar ao desmarcar categoria, num banco TEMPORÁRIO."""
import sys, os, subprocess, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); os.chdir(ROOT)
import config, mysql.connector
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

REAL = config.load_db_config()
TEST_DB = "vl_jobs_test_tmp"
BIN = r"C:\Program Files\MySQL\MySQL Server 8.0\bin"
cnf = tempfile.NamedTemporaryFile("w", suffix=".cnf", delete=False)
cnf.write(f"[client]\nhost={REAL['host']}\nuser={REAL['user']}\npassword=\"{REAL['password']}\"\n"); cnf.close()
admin = mysql.connector.connect(**REAL); acur = admin.cursor()
print("stage: create db", flush=True); acur.execute(f"DROP DATABASE IF EXISTS {TEST_DB}"); acur.execute(f"CREATE DATABASE {TEST_DB}"); print("stage: dump", flush=True)
dump = subprocess.run([os.path.join(BIN, "mysqldump.exe"), f"--defaults-extra-file={cnf.name}", "--single-transaction",
                       "--routines", "--triggers", REAL["database"]], capture_output=True, check=True).stdout
subprocess.run([os.path.join(BIN, "mysql.exe"), f"--defaults-extra-file={cnf.name}", TEST_DB], input=dump, check=True)
print("stage: restored", flush=True)
TEST = {**REAL, "database": TEST_DB}
msgs = []
QMessageBox.information = staticmethod(lambda *a, **k: msgs.append(str(a[2])) or QMessageBox.StandardButton.Ok)
QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)
QMessageBox.warning = staticmethod(lambda *a, **k: msgs.append("WARN " + str(a[2])) or QMessageBox.StandardButton.Ok)
QMessageBox.critical = staticmethod(lambda *a, **k: msgs.append("CRIT " + str(a[2])) or QMessageBox.StandardButton.Ok)
ok = True
db = None
try:
    from main_ import MainWindow
    app = QApplication(sys.argv)
    w = MainWindow(db_config=TEST)
    w.showMaximized(); app.processEvents(); w.set_current_user("viktorlonde"); print("stage: window up", flush=True)
    db = mysql.connector.connect(**TEST); cur = db.cursor(dictionary=True)

    def days(pid):
        cur.execute("SELECT ID, WORK_DATE, VALUE, STATUS, JOB_ADDRESS, ZIP_CODE, COMPANY_ID FROM work_days "
                    "WHERE JOB_PROJECT_ID=%s ORDER BY ID", (pid,))
        rows = cur.fetchall(); db.commit()
        return rows

    cur.execute("SELECT JOB_PROJECT_ID pid, COUNT(*) n FROM work_days WHERE JOB_PROJECT_ID IS NOT NULL "
                "GROUP BY JOB_PROJECT_ID HAVING n >= 2 ORDER BY n LIMIT 1")
    pid = cur.fetchone()["pid"]
    before = days(pid)
    target = before[0]["ID"]

    def load(job_id):
        w._go_to_page(1, w.ui.btn_jobs)
        w.ui.txt_search_jobs.clear(); w.load_work_days()
        t = w.ui.table_work_days
        for r in range(t.rowCount()):
            if t.item(r, 0) and t.item(r, 0).text() == str(job_id):
                t.selectRow(r); w.load_job_into_form(); app.processEvents(); return True
        return False

    print("stage: tests start", flush=True)
    # 1) muda o endereço de um dia -> todos os dias do código mudam; o resto não
    assert load(target), "job not found in table"
    w.ui.cmb_client_address.setCurrentText("123 TEST NEW ADDRESS")
    msgs.clear(); w.save_job_record()
    after = days(pid)
    addr_ok = all(d["JOB_ADDRESS"] == "123 TEST NEW ADDRESS" for d in after)
    other_ok = all((a["WORK_DATE"], a["VALUE"], a["STATUS"]) == (b["WORK_DATE"], b["VALUE"], b["STATUS"]) for a, b in zip(before, after))
    print(f"[1] {len(after)} days of project {pid}: address on all = {addr_ok} | date/value/status kept = {other_ok}")
    print("    message:", [m for m in msgs if "Also updated" in m] or msgs)
    ok &= addr_ok and other_ok

    # 2) salva outro dia SEM mexer -> não pode desfazer nada
    assert load(after[1]["ID"])
    msgs.clear(); w.save_job_record()
    again = days(pid)
    noop_ok = all(d["JOB_ADDRESS"] == "123 TEST NEW ADDRESS" for d in again) and not any("Also updated" in m for m in msgs)
    print(f"[2] saving another day unchanged keeps address and propagates nothing = {noop_ok}")
    ok &= noop_ok

    # 3) desmarcar categoria limpa as escolhas dela
    w.new_job_record(); app.processEvents()
    QTest.mouseClick(w.ui.chk_demolition, Qt.MouseButton.LeftButton); app.processEvents()
    w.ui.cmb_demolition.setCurrentIndex(1); w.ui.dspn_demolition.setValue(5)
    picked = (w.ui.cmb_demolition.currentIndex(), w.ui.dspn_demolition.value())
    QTest.mouseClick(w.ui.chk_demolition, Qt.MouseButton.LeftButton); app.processEvents()
    cleared = (w.ui.cmb_demolition.currentIndex(), w.ui.dspn_demolition.value(), w.ui.chk_demolition.isChecked())
    clear_ok = picked == (1, 5.0) and cleared == (0, 1.0, False)
    print(f"[3] demolition picked={picked} -> after uncheck={cleared} ok={clear_ok}")
    ok &= clear_ok

    # 4) carregar um job com work types não apaga nada (só clique do usuário apaga)
    cur.execute("SELECT ID FROM work_days WHERE INSTALLATION_1_ID IS NOT NULL AND WORK_DATE <= CURDATE() AND WORK_DATE >= CURDATE() - INTERVAL 120 DAY ORDER BY ID DESC LIMIT 1")
    jid = cur.fetchone()["ID"]
    found = load(jid)
    print("    found in table:", found, "| install idx", w.ui.cmb_installation.currentIndex(), "| chk", w.ui.chk_installation.isChecked(), "| filter", w.ui.date_filter_from.date().toString("MM/dd/yyyy") if hasattr(w.ui, "date_filter_from") else "?")
    cur.execute("SELECT WORK_DATE, INSTALLATION_1_ID FROM work_days WHERE ID=%s", (jid,)); print("    db:", cur.fetchone())
    load_ok = w.ui.cmb_installation.currentIndex() > 0 and w.ui.chk_installation.isChecked()
    print(f"[4] loading job {jid} keeps its work types = {load_ok}")
    ok &= load_ok
    w._job_form_dirty = False
except Exception:
    import traceback; traceback.print_exc(); ok = False
finally:
    try: db.close()
    except Exception: pass
    acur.execute("SET SESSION lock_wait_timeout = 15")
    acur.execute(f"DROP DATABASE IF EXISTS {TEST_DB}"); admin.close(); os.remove(cnf.name)
    print("temp db dropped", flush=True)
print("RESULT:", "ALL OK" if ok else "FAILED", flush=True)
sys.exit(0 if ok else 1)
