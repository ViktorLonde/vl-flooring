"""Testa apagar Work Type em uso (troca por outro e apaga) numa CÓPIA do banco."""
import sys, os, subprocess, tempfile, traceback, time
from datetime import date, datetime, timedelta
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); os.chdir(ROOT)
import config, mysql.connector, smtplib
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog

REAL = config.load_db_config()
TEST_DB = "vl_wtdel_test_tmp"
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
    w = MainWindow(db_config=TEST); w.show(); a.processEvents()
    w.set_current_user("viktorlonde")
    old, new = 4, 33  # Installation Vinyl → Vinyl Plank (Floating/Click)
    # um dia com os dois, para testar a soma
    day = q("SELECT WORK_DAY_ID, QTY FROM work_day_work_types WHERE WORK_TYPE_ID=%s LIMIT 1", (old,))[0]
    q("INSERT INTO work_day_work_types (WORK_DAY_ID, CATEGORY, WORK_TYPE_ID, QTY, SORT_ORDER) VALUES (%s,'INSTALLATION',%s,10,9)",
      (day[0], new))
    usage = w._work_type_usage(old)
    check("usage found", usage["days"] > 0, usage)
    total_before = float(q("SELECT SUM(QTY) FROM work_day_work_types WHERE WORK_TYPE_ID IN (%s,%s)", (old, new))[0][0])
    # 1) cancelar não apaga
    w._current_work_type_id = old
    actions.append(lambda d: None)
    w.delete_work_type_record()
    check("cancel keeps it", q("SELECT COUNT(*) FROM work_types WHERE ID=%s", (old,))[0][0] == 1)
    # 2) trocar e apagar
    w._current_work_type_id = old

    def choose(d):
        d._combo.setCurrentIndex(d._combo.findData(new)); d._accept()
    actions.append(choose)
    w.delete_work_type_record()
    check("old work type deleted", q("SELECT COUNT(*) FROM work_types WHERE ID=%s", (old,))[0][0] == 0)
    cols = " OR ".join(f"{c} = {old}" for c in w._WT_DAY_COLUMNS)
    check("no day points to it anymore", q(f"SELECT COUNT(*) FROM work_days WHERE {cols}")[0][0] == 0 and
          q("SELECT COUNT(*) FROM work_day_work_types WHERE WORK_TYPE_ID=%s", (old,))[0][0] == 0)
    check("quantities kept (merged in the same day)",
          abs(float(q("SELECT SUM(QTY) FROM work_day_work_types WHERE WORK_TYPE_ID=%s", (new,))[0][0]) - total_before) < 0.001
          and q("SELECT COUNT(*) FROM work_day_work_types WHERE WORK_DAY_ID=%s AND WORK_TYPE_ID=%s", (day[0], new))[0][0] == 1)
    # 3) sem uso: apaga direto
    q("INSERT INTO work_types (CATEGORY, NAME, UNIT) VALUES ('OTHERS','Unused test','EA')")
    w._current_work_type_id = q("SELECT ID FROM work_types WHERE NAME='Unused test'")[0][0]
    w.delete_work_type_record()
    check("unused deleted directly", q("SELECT COUNT(*) FROM work_types WHERE NAME='Unused test'")[0][0] == 0)
    crit = [m for m in msgs if m.startswith("CRIT")]
    check("no database errors", not crit, crit[:2])
    db.close()
except Exception:
    traceback.print_exc(); ok = False
finally:
    acur.execute(f"DROP DATABASE IF EXISTS {TEST_DB}"); admin.close(); os.remove(cnf.name)
    print("temp db dropped", flush=True)
print("RESULT:", "ALL OK" if ok else "FAILED", flush=True)
sys.exit(0 if ok else 1)
