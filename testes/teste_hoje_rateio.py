"""Testa: diária do helper (pagamento = diária × parte do dia), Log today
(cria os dias com a parte de cada job), Earnings per day / meta do mês e o
rateio de despesa entre jobs — numa CÓPIA temporária do banco."""
import sys, os, subprocess, tempfile, traceback
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); os.chdir(ROOT)
import config, mysql.connector
from datetime import date, timedelta
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog, QPushButton, QTableWidget
from PySide6.QtCore import QSettings

REAL = config.load_db_config()
TEST_DB = "vl_today_test_tmp"
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
fc.execute("DELETE FROM service_rates")
fix.commit(); fix.close()

msgs = []
QMessageBox.information = staticmethod(lambda *a, **k: msgs.append(str(a[2])) or QMessageBox.StandardButton.Ok)
QMessageBox.warning = staticmethod(lambda *a, **k: msgs.append("WARN " + str(a[2])) or QMessageBox.StandardButton.Ok)
QMessageBox.critical = staticmethod(lambda *a, **k: msgs.append("CRIT " + str(a[2])) or QMessageBox.StandardButton.Ok)
QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)
actions = []
QDialog.exec = lambda d: (actions.pop(0)(d) if actions else None, 0)[1]
settings = QSettings("VL Flooring", "app")
goal_before = settings.value("goal/monthly", None)
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

    # ── DIÁRIA DO HELPER ──
    helper = q("SELECT ID FROM helpers ORDER BY ID LIMIT 1")[0][0]
    cur.execute("UPDATE helpers SET DAILY_RATE=180 WHERE ID=%s", (helper,))
    day_id = q("SELECT ID FROM work_days WHERE JOB_PROJECT_ID IS NOT NULL ORDER BY WORK_DATE DESC, ID DESC LIMIT 1")[0][0]
    w._go_to_page(1, w.ui.btn_jobs); w._open_job_by_id(day_id, None); a.processEvents()
    w._job_form_dirty = False
    w._job_helpers = []
    got = {}

    def crew(d):
        t = d.findChild(QTableWidget)
        t.cellWidget(0, 0).setCurrentIndex(t.cellWidget(0, 0).findData(helper))
        got["full"] = t.cellWidget(0, 2).value()
        t.cellWidget(0, 1).setCurrentIndex(t.cellWidget(0, 1).findData(0.333))
        got["third"] = t.cellWidget(0, 2).value()
        next(b for b in d.findChildren(QPushButton) if b.objectName() == "btn_job_helpers_ok").click()
    actions.append(crew)
    w.open_job_helpers_dialog(); a.processEvents()
    check("daily rate × the day's part fills the pay", abs(got.get("full", 0) - round(180 * w._day_portion_value(), 2)) < 0.01,
          (got, w._day_portion_value()))
    check("⅓ day pays ⅓ of the rate", abs(got.get("third", 0) - 59.94) < 0.01, got)
    w._job_form_dirty = False

    # ── LOG TODAY ──
    recent = w._recent_job_codes()
    check("recent job codes listed", len(recent) >= 2, [r[1] for r in recent[:3]])
    (p1, c1, *_r1), (p2, c2, *_r2) = recent[0], recent[1]
    last1 = q("SELECT ID, VALUE, DAY_FRACTION FROM work_days WHERE JOB_PROJECT_ID=%s AND STATUS <> 'CANCELLED' "
              "ORDER BY WORK_DATE DESC, ID DESC LIMIT 1", (p1,))[0]
    wt_count = q("SELECT COUNT(*) FROM work_day_work_types WHERE WORK_DAY_ID=%s", (last1[0],))[0][0]
    target = date.today() + timedelta(days=3)

    def log(d):
        d._when.setDate(target)
        rows = {r["pid"]: r for r in d._rows}
        for r in d._rows:
            r["chk"].setChecked(r["pid"] in (p1, p2))
        rows[p1]["portion"].setCurrentIndex(rows[p1]["portion"].findData(0.333))
        rows[p2]["portion"].setCurrentIndex(rows[p2]["portion"].findData(0.667))
        next(b for b in d.findChildren(QPushButton) if b.objectName() == "btn_save_log_today").click()
    actions.append(log)
    w.open_log_today_dialog(); a.processEvents()
    new = q("SELECT JOB_PROJECT_ID, DAY_FRACTION, VALUE, STATUS, ID FROM work_days WHERE WORK_DATE=%s ORDER BY ID", (target,))
    by_pid = {r[0]: r for r in new}
    check("one new day per ticked job", set(by_pid) == {p1, p2}, new)
    check("each day keeps its part", float(by_pid[p1][1]) == 0.333 and float(by_pid[p2][1]) == 0.667)
    expected = round(float(last1[1] or 0) * 0.333 / float(last1[2] or 1), 2)
    check("value proportional to the last day", abs(float(by_pid[p1][2]) - expected) < 0.02, (by_pid[p1][2], expected))
    check("services copied from the last day",
          q("SELECT COUNT(*) FROM work_day_work_types WHERE WORK_DAY_ID=%s", (by_pid[p1][4],))[0][0] == wt_count)
    check("form opens the new day", str(w._current_job_id) in {str(by_pid[p1][4]), str(by_pid[p2][4])}, w._current_job_id)
    w._job_form_dirty = False

    # ── EARNINGS / META ──
    data = w._earnings(date(2000, 1, 1), date(2100, 1, 1))
    check("earnings by month/job/customer", data["month"] and data["job"] and data["customer"])
    seen = {}
    actions.append(lambda d: seen.update(summary=next(l.text() for l in d.findChildren(type(w.ui.lbl_user))
                                                      if "per full day" in l.text())))
    w.open_earnings_dialog()
    check("earnings dialog shows $ per full day", "per full day" in seen.get("summary", ""), seen.get("summary"))
    settings.setValue("goal/monthly", 1000.0)
    w._go_to_page(0, w.ui.btn_home); a.processEvents()
    w.refresh_today_card()
    card = w._today_card
    check("home card shows month and goal", "per day" in card["label"].text() and "Goal $1,000.00" in card["sub"].text(),
          (card["label"].text(), card["sub"].text()))

    # ── RATEIO ──
    monday = target - timedelta(days=target.weekday())
    cur.execute("INSERT INTO expenses (EXPENSE_DATE, CATEGORY, DESCRIPTION, AMOUNT, ENTITY_TYPE, SUBMITTED_BY) "
                "VALUES (%s, 'GAS', 'test gas', 90, 'Contractor', 'ME')", (target,))
    exp_id = cur.lastrowid
    seen = {}

    def split(d):
        seen["parts"] = {pid: s.value() for pid, s in d._spins}
        next(b for b in d.findChildren(QPushButton) if b.objectName() == "btn_save_split_confirm").click()
    actions.append(split)
    w.open_expense_split_dialog(exp_id); a.processEvents()
    alloc = dict((pid, float(v)) for pid, v in q("SELECT JOB_PROJECT_ID, AMOUNT FROM expense_allocations WHERE EXPENSE_ID=%s",
                                                  (exp_id,)))
    check("split saved and adds up", alloc and abs(sum(alloc.values()) - 90) < 0.01, alloc)
    week_days = {pid: float(d) for pid, d in q(
        "SELECT JOB_PROJECT_ID, SUM(DAY_FRACTION) FROM work_days WHERE WORK_DATE BETWEEN %s AND %s AND STATUS <> 'CANCELLED' "
        "AND JOB_PROJECT_ID IS NOT NULL GROUP BY JOB_PROJECT_ID", (monday, monday + timedelta(days=6)))}
    tot = sum(week_days.values())
    check("split is proportional to the days", all(abs(alloc.get(p, 0) - 90 * d / tot) < 0.02 for p, d in week_days.items()),
          (alloc, week_days))
    w._profit_widgets[0].setCurrentIndex(3); w.load_job_profit()
    t = w._profit_widgets[2]
    code1 = q("SELECT CODE FROM job_projects WHERE ID=%s", (p1,))[0][0]
    row = next((r for r in range(t.rowCount()) if t.item(r, 0).text() == code1), None)
    check("job profit shows the job", row is not None)

    check("hub has the Earnings card", "earnings" in w._hub_cards)
    crit = [m for m in msgs if m.startswith("CRIT")]
    check("no database errors", not crit, crit[:2])
    w._job_form_dirty = False
    db.close()
except Exception:
    traceback.print_exc(); ok = False
finally:
    if goal_before is None:
        settings.remove("goal/monthly")
    else:
        settings.setValue("goal/monthly", goal_before)
    acur.execute("SET SESSION lock_wait_timeout = 15")
    acur.execute(f"DROP DATABASE IF EXISTS {TEST_DB}"); admin.close(); os.remove(cnf.name)
    print("temp db dropped", flush=True)
print("RESULT:", "ALL OK" if ok else "FAILED", flush=True)
sys.exit(0 if ok else 1)
