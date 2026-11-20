"""Testa a equipe do dia (vários helpers por job): salva, carrega de volta,
NÃO é copiada para os outros dias do mesmo Job Code, entra no lucro, aparece
na agenda da semana, vai junto no Duplicate e no relatório Helper Pay —
numa CÓPIA temporária do banco (o banco real não é alterado)."""
import sys, os, subprocess, tempfile, traceback
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); os.chdir(ROOT)
import config, mysql.connector
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog, QPushButton, QSpinBox

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
dialog_actions = []
QDialog.exec = lambda d: (dialog_actions.pop(0)(d) if dialog_actions else None, 0)[1]
ok = True


def check(name, cond, extra=""):
    global ok
    ok &= bool(cond)
    print(("PASS " if cond else "FAIL ") + name, extra, flush=True)


try:
    db = mysql.connector.connect(**TEST); db.autocommit = True; cur = db.cursor()

    def q(sql, p=()):
        cur.execute(sql, p); return cur.fetchall()

    check("work_day_helpers table exists", q("SHOW TABLES LIKE 'work_day_helpers'"))
    cur.execute("INSERT INTO helpers (FULL_NAME, PAYMENT_ZELLE) VALUES ('Joao Test', 'joao@zelle')"); h1 = cur.lastrowid
    cur.execute("INSERT INTO helpers (FULL_NAME) VALUES ('Pedro Test')"); h2 = cur.lastrowid
    pid = q("SELECT JOB_PROJECT_ID FROM work_days WHERE JOB_PROJECT_ID IS NOT NULL GROUP BY JOB_PROJECT_ID "
            "HAVING COUNT(*) >= 2 ORDER BY MAX(WORK_DATE) DESC LIMIT 1")[0][0]
    days = [r[0] for r in q("SELECT ID FROM work_days WHERE JOB_PROJECT_ID=%s ORDER BY ID", (pid,))]
    target, other = days[0], days[1]
    # a cópia já pode ter equipe lançada pelo usuário: começa do zero nesses dias
    cur.execute(f"DELETE FROM work_day_helpers WHERE WORK_DAY_ID IN ({','.join(map(str, days))})")
    work_date = q("SELECT WORK_DATE FROM work_days WHERE ID=%s", (target,))[0][0]

    from main_ import MainWindow
    a = QApplication(sys.argv)
    w = MainWindow(db_config=TEST); w.resize(1536, 816); w.show(); a.processEvents()
    w.set_current_user("viktorlonde")
    w._go_to_page(1, w.ui.btn_jobs); a.processEvents()
    w._open_job_by_id(target, work_date); a.processEvents()
    check("job opened", str(w._current_job_id) == str(target), w._current_job_id)
    check("Helpers button shown", w.ui.btn_job_helpers.isVisible() and not w.ui.cmb_helper.isVisible(),
          w.ui.btn_job_helpers.text())

    # adiciona 2 helpers pela janela
    def fill(d):
        from PySide6.QtWidgets import QTableWidget
        t = d.findChild(QTableWidget)
        next(b for b in d.findChildren(QPushButton) if "Add helper" in b.text()).click()
        t.cellWidget(0, 0).setCurrentIndex(t.cellWidget(0, 0).findData(h1)); t.cellWidget(0, 2).setValue(150)
        t.cellWidget(1, 0).setCurrentIndex(t.cellWidget(1, 0).findData(h2)); t.cellWidget(1, 2).setValue(120)
        t.cellWidget(1, 1).setCurrentIndex(t.cellWidget(1, 1).findData(0.333))  # helper 2: 1/3 do dia
        next(b for b in d.findChildren(QPushButton) if b.objectName() == "btn_job_helpers_ok").click()
    dialog_actions.append(fill)
    w.open_job_helpers_dialog(); a.processEvents()
    check("button shows 2 helpers and total", "Helpers (2)" in w.ui.btn_job_helpers.text()
          and "270.00" in w.ui.btn_job_helpers.text(), w.ui.btn_job_helpers.text())
    w.ui.cmb_day_portion.setCurrentIndex(w.ui.cmb_day_portion.findData(0.333))  # o dia: 1/3 neste job
    msgs.clear(); w.save_job_record(); a.processEvents()
    crew = q("SELECT HELPER_ID, PAY, DAY_FRACTION FROM work_day_helpers WHERE WORK_DAY_ID=%s ORDER BY ID", (target,))
    check("crew saved (2 helpers)", [(c[0], float(c[1])) for c in crew] == [(h1, 150.0), (h2, 120.0)], crew)
    check("helper day portion saved", [float(c[2]) for c in crew] == [1.0, 0.333], crew)
    check("job day portion saved", float(q("SELECT DAY_FRACTION FROM work_days WHERE ID=%s", (target,))[0][0]) == 0.333)
    w._open_job_by_id(target, None); a.processEvents(); w._job_form_dirty = False
    w._update_days_worked_label(); a.processEvents()
    check("days worked label adds the fractions", "⅓" in w.ui.lbl_days_worked_value.text()
          or q("SELECT COUNT(*) FROM work_days WHERE JOB_PROJECT_ID=(SELECT JOB_PROJECT_ID FROM work_days WHERE ID=%s) "
               "AND STATUS <> 'CANCELLED'", (target,))[0][0] == 0, w.ui.lbl_days_worked_value.text())
    summ = q("SELECT HELPER_ID, HELPER_PAY FROM work_days WHERE ID=%s", (target,))[0]
    check("day summary = first helper + total pay", summ[0] == h1 and float(summ[1]) == 270.0, summ)
    check("crew NOT copied to other days of the code",
          not q("SELECT 1 FROM work_day_helpers WHERE WORK_DAY_ID=%s", (other,)))

    w._current_job_id = None
    w._open_job_by_id(target, work_date); a.processEvents()
    check("crew loads back", w._job_helpers == [[h1, 150.0, 1.0], [h2, 120.0, 0.333]], w._job_helpers)
    check("job day portion loads back", abs(w._day_portion_value() - 0.333) < 0.001)
    w._job_form_dirty = False

    # lucro e View Project descontam a soma
    code = q("SELECT CODE FROM job_projects WHERE ID=%s", (pid,))[0][0]
    w._profit_widgets[0].setCurrentIndex(3); w.load_job_profit()
    t = w._profit_widgets[2]
    row = next(r for r in range(t.rowCount()) if t.item(r, 0).text() == code)
    check("profit subtracts all helpers", float(t.item(row, 6).data(256)) == 270.0, t.item(row, 6).text())

    # agenda da semana
    from datetime import timedelta
    monday = work_date - timedelta(days=work_date.weekday())
    text = w._week_schedule_text(monday, w._week_schedule_rows(monday))
    check("week schedule lists both helpers", "Helpers: Joao Test, Pedro Test" in text)

    # Duplicate leva a equipe
    def dup(d):
        d.findChild(QSpinBox).setValue(1)
        next(b for b in d.findChildren(QPushButton) if b.objectName() == "btn_save_duplicate").click()
    dialog_actions.append(dup)
    w._current_job_id = target
    w.open_duplicate_job_dialog(); a.processEvents()
    new_id = q("SELECT MAX(ID) FROM work_days")[0][0]
    check("duplicate copies the crew", len(q("SELECT 1 FROM work_day_helpers WHERE WORK_DAY_ID=%s", (new_id,))) == 2)

    # relatório Helper Pay
    cmb, dfrom, dto, summary, table, detail, lbl = w._helper_pay_widgets
    from PySide6.QtCore import QDate
    cmb.setCurrentText("Custom")
    dfrom.setDate(QDate(work_date.year, 1, 1)); dto.setDate(QDate(work_date.year + 1, 12, 31))
    w.load_helper_pay_report()
    names = {table.item(r, 0).text(): table.item(r, 2).text() for r in range(table.rowCount())}
    check("report totals per helper", names.get("Joao Test") == "$300.00" and names.get("Pedro Test") == "$240.00", names)
    row = next(r for r in range(table.rowCount()) if table.item(r, 0).text() == "Joao Test")
    check("report shows how to pay", "Zelle: joao@zelle" in table.item(row, 3).text())
    table.selectRow(row); a.processEvents()
    check("report detail lists the days", detail.rowCount() == 2, detail.rowCount())

    # New Job começa sem equipe
    w.new_job_record(); a.processEvents()
    check("new job starts without helpers", w._job_helpers == [])
    w._job_form_dirty = False
    db.close()
except Exception:
    traceback.print_exc(); ok = False
finally:
    acur.execute("SET SESSION lock_wait_timeout = 15")
    acur.execute(f"DROP DATABASE IF EXISTS {TEST_DB}"); admin.close(); os.remove(cnf.name)
    print("temp db dropped", flush=True)
print("RESULT:", "ALL OK" if ok else "FAILED", flush=True)
sys.exit(0 if ok else 1)
