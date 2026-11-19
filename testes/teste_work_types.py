"""Testa a lista de Work Types sem limite: 6 serviços de Installation num dia
(antes cabiam 4), salvar, carregar, colunas antigas, invoice, Duplicate,
agenda e New Job — numa CÓPIA temporária do banco."""
import sys, os, subprocess, tempfile, traceback
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); os.chdir(ROOT)
import config, mysql.connector
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog, QPushButton, QSpinBox

REAL = config.load_db_config()
TEST_DB = "vl_wt_test_tmp"
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

    check("existing work types were migrated", q("SELECT COUNT(*) FROM work_day_work_types")[0][0] > 0)
    inst = [r[0] for r in q("SELECT ID FROM work_types WHERE CATEGORY='INSTALLATION' ORDER BY ID LIMIT 6")]
    prep = q("SELECT ID FROM work_types WHERE CATEGORY='PREPARATION' ORDER BY ID LIMIT 1")[0][0]
    wid, wdate, pid = q("SELECT ID, WORK_DATE, JOB_PROJECT_ID FROM work_days WHERE JOB_PROJECT_ID IS NOT NULL "
                        "ORDER BY ID DESC LIMIT 1")[0]

    from main_ import MainWindow
    a = QApplication(sys.argv)
    w = MainWindow(db_config=TEST); w.resize(1536, 816); w.show(); a.processEvents()
    w.set_current_user("viktorlonde")
    w._go_to_page(1, w.ui.btn_jobs); w._open_job_by_id(wid, wdate); a.processEvents()
    check("old fixed fields are hidden", not w.ui.cmb_demolition.isVisible() and w.ui.txt_note.isVisible())

    # 6 instalações + 1 preparação (antes: máximo 4 por categoria)
    w._set_work_type_list([])
    for i, t in enumerate(inst):
        w._add_work_type_row("INSTALLATION", t, 100.5 + i)
    w._add_work_type_row("PREPARATION", prep, 2.25)
    w._job_form_dirty = True
    items = w._get_work_type_list()
    check("7 lines in the form", len(items) == 7, len(items))
    msgs.clear(); w.save_job_record(); a.processEvents()
    saved = q("SELECT CATEGORY, WORK_TYPE_ID, QTY FROM work_day_work_types WHERE WORK_DAY_ID=%s ORDER BY SORT_ORDER", (wid,))
    check("all 7 saved in the list table", len(saved) == 7 and float(saved[5][2]) == 105.5, saved[-2:])
    cols = q("SELECT INSTALLATION_1_ID, INSTALLATION_4_ID, INSTALLATION_4_QTY, PREPARATION_1_QTY, DEMOLITION_1_ID "
             "FROM work_days WHERE ID=%s", (wid,))[0]
    check("old columns keep the first 4 per category", cols[0] == inst[0] and cols[1] == inst[3]
          and float(cols[2]) == 103.5 and float(cols[3]) == 2.25 and cols[4] is None, cols)

    w._current_job_id = None
    w._open_job_by_id(wid, wdate); a.processEvents()
    check("reload shows the 7 lines with decimals", len(w._get_work_type_list()) == 7
          and w._get_work_type_list()[6][2] == 2.25, w._get_work_type_list()[-1])
    w._job_form_dirty = False

    # invoice mostra os 7 (inclui o 5º e 6º de Installation)
    rows = w._fetch_invoice_jobs(cur, "ID", wid, wdate, wdate, "clients", "CLIENT_ID", "FULL_NAME")
    item_rows, _total = w._prepare_invoice_item_rows(rows, w._get_work_type_lookup(cur),
                                                     {"show_qty": True, "group_same_date": False}, None) \
        if False else (None, None)
    full = w._invoice_work_type_lists.get(wid, [])
    lines = w._describe_work_type_list(full, w._get_work_type_lookup(cur), True)
    check("invoice description has all 7 services", len(lines) == 7, lines[4:6])

    # agenda da semana usa a lista completa
    from datetime import timedelta
    monday = wdate - timedelta(days=wdate.weekday())
    sched = {r["ID"]: r["WORK_TYPES"] for r in w._week_schedule_rows(monday)}
    names = {r[0] for r in q(f"SELECT NAME FROM work_types WHERE ID IN ({','.join(map(str, inst))})")}
    check("week schedule lists the extra services", all(n in sched.get(wid, "") for n in names), sched.get(wid, "")[:90])

    # Duplicate leva a lista completa
    def dup(d):
        d.findChild(QSpinBox).setValue(1)
        next(b for b in d.findChildren(QPushButton) if b.objectName() == "btn_save_duplicate").click()
    actions.append(dup)
    w._current_job_id = wid
    w.open_duplicate_job_dialog(); a.processEvents()
    new_id = q("SELECT MAX(ID) FROM work_days")[0][0]
    check("duplicate copies all 7 work types", q("SELECT COUNT(*) FROM work_day_work_types WHERE WORK_DAY_ID=%s",
                                                  (new_id,))[0][0] == 7)

    # New Job começa sem linhas; dia novo do mesmo Job Code sugere a lista do último dia
    w.new_job_record(); a.processEvents()
    check("new job starts with an empty list", w._get_work_type_list() == [])
    w._load_work_types_from_latest_day(pid)
    latest = q("SELECT ID FROM work_days WHERE JOB_PROJECT_ID=%s ORDER BY WORK_DATE DESC, ID DESC LIMIT 1", (pid,))[0][0]
    expected = q("SELECT COUNT(*) FROM work_day_work_types WHERE WORK_DAY_ID=%s", (latest,))[0][0]
    check("new day of the code suggests last day's services", len(w._get_work_type_list()) == expected > 0,
          (len(w._get_work_type_list()), expected))
    w._job_form_dirty = False

    # remover uma linha
    before = len(w._get_work_type_list())
    w._wt_rows[0]["widget"].findChildren(QPushButton)[-1].click(); a.processEvents()
    check("remove button drops a line", len(w._get_work_type_list()) == before - 1)
    w._job_form_dirty = False

    # categoria Delivery: aparece na lista, salva só na tabela nova, sai na invoice
    delivery = q("SELECT ID FROM work_types WHERE CATEGORY='DELIVERY' ORDER BY ID LIMIT 1")
    check("Delivery work types exist", bool(delivery))
    if delivery:
        w._current_job_id = None
        w._open_job_by_id(wid, wdate); a.processEvents()
        row = w._add_work_type_row("DELIVERY", delivery[0][0], 3)
        cats = [row["cat"].itemData(i) for i in range(row["cat"].count())]
        check("Delivery is in the category list", "DELIVERY" in cats, cats)
        w.save_job_record(); a.processEvents()
        saved = q("SELECT CATEGORY, QTY FROM work_day_work_types WHERE WORK_DAY_ID=%s AND WORK_TYPE_ID=%s",
                  (wid, delivery[0][0]))
        check("Delivery line saved", saved and saved[0][0] == "DELIVERY" and float(saved[0][1]) == 3, saved)
        rows = w._fetch_invoice_jobs(cur, "ID", wid, wdate, wdate, "clients", "CLIENT_ID", "FULL_NAME")
        lines = w._describe_work_type_list(w._invoice_work_type_lists.get(wid, []), w._get_work_type_lookup(cur), True)
        check("invoice shows the Delivery line", any(l.startswith("Delivery:") for l in lines), lines[-1:])
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
