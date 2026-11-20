"""Testa Service Rates (Value calculado), invoice ligado aos dias (Board vai
sozinho para Invoiced / Paid), Accountant Package, Material Usage e o
arquivo de calendário (.ics) — numa CÓPIA temporária do banco."""
import sys, os, subprocess, tempfile, traceback, zipfile, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); os.chdir(ROOT)
import config, mysql.connector, smtplib
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog, QPushButton

REAL = config.load_db_config()
TEST_DB = "vl_rates_test_tmp"
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
smtplib.SMTP = lambda *a, **k: (_ for _ in ()).throw(AssertionError("tried to send e-mail"))
actions = []
QDialog.exec = lambda d: (actions.pop(0)(d) if actions else None, 0)[1]
os.startfile = lambda *a, **k: None
ok = True
tmpdir = tempfile.mkdtemp(prefix="vl_test_")


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

    # ── SERVICE RATES ──
    inst = q("SELECT ID FROM work_types WHERE CATEGORY='INSTALLATION' ORDER BY ID LIMIT 1")[0][0]
    prep = q("SELECT ID FROM work_types WHERE CATEGORY='PREPARATION' ORDER BY ID LIMIT 1")[0][0]
    contractor = q("SELECT ID FROM contractors ORDER BY ID LIMIT 1")[0][0]

    def rates(d):
        d._spins[inst].setValue(2.5)
        d._spins[prep].setValue(0.75)
        next(b for b in d.findChildren(QPushButton) if b.objectName() == "btn_save_service_rates").click()
        d._who.setCurrentIndex(d._who.findData(f"Contractor:{contractor}"))
        d._spins[inst].setValue(3.0)
        next(b for b in d.findChildren(QPushButton) if b.objectName() == "btn_save_service_rates").click()
    actions.append(rates)
    w.open_service_rates_dialog()
    saved = q("SELECT WORK_TYPE_ID, ENTITY_TYPE, ENTITY_ID, RATE FROM service_rates ORDER BY ID")
    check("rates saved (default + contractor)", len(saved) == 3, saved)
    items = [("INSTALLATION", inst, 100), ("PREPARATION", prep, 40)]
    total, priced, missing = w._calculate_value_from_rates(items, contractor, None)
    check("contractor rate wins over default", total == 100 * 3.0 + 40 * 0.75, total)
    total2, _p, _m = w._calculate_value_from_rates(items, None, None)
    check("default rate used without contractor", total2 == 100 * 2.5 + 40 * 0.75, total2)

    w._go_to_page(1, w.ui.btn_jobs); w.new_job_record(); a.processEvents()
    w._set_combo_by_data(w.ui.cmb_contractor, contractor); a.processEvents()
    w._add_work_type_row("INSTALLATION", inst, 100); w._add_work_type_row("PREPARATION", prep, 40); a.processEvents()
    check("new job Value filled from rates", abs(w.ui.dspn_value.value() - 330.0) < 0.01, w.ui.dspn_value.value())
    w.ui.dspn_value.setValue(500); a.processEvents()
    check("hint offers the calculated value", "330.00" in w.ui.btn_use_rate_value.text(), w.ui.btn_use_rate_value.text())
    w.ui.btn_use_rate_value.click(); a.processEvents()
    check("Use puts the calculated value back", abs(w.ui.dspn_value.value() - 330.0) < 0.01)
    w._job_form_dirty = False

    # ── INVOICE → BOARD ──
    check("old invoices were linked to their days", q("SELECT COUNT(*) FROM invoice_work_days")[0][0] > 0)
    pid, company, d_from, d_to = q("""
        SELECT wd.JOB_PROJECT_ID, MIN(wd.COMPANY_ID), MIN(wd.WORK_DATE), MAX(wd.WORK_DATE) FROM work_days wd
        WHERE wd.JOB_PROJECT_ID IS NOT NULL AND wd.COMPANY_ID IS NOT NULL AND COALESCE(wd.STATUS,'') <> 'CANCELLED'
          AND wd.ID NOT IN (SELECT WORK_DAY_ID FROM invoice_work_days)
        GROUP BY wd.JOB_PROJECT_ID HAVING COUNT(DISTINCT wd.COMPANY_ID) = 1 ORDER BY COUNT(*) DESC LIMIT 1""")[0]
    day_ids = [r[0] for r in q("SELECT ID FROM work_days WHERE JOB_PROJECT_ID=%s AND COALESCE(STATUS,'') <> 'CANCELLED'",
                               (pid,))]
    cur.execute("UPDATE work_days SET STATUS='COMPLETED' WHERE JOB_PROJECT_ID=%s AND STATUS <> 'CANCELLED'", (pid,))
    before = w._board_stage_of(pid)
    from PySide6.QtCore import QDate
    opts = {"show_qty": True, "group_same_date": False, "discount": 0, "addition": 0, "tax_percent": 0}
    name = q("SELECT COMPANY_NAME FROM companies WHERE ID=%s", (company,))[0][0]
    w._generate_single_company_invoice(company, name, d_from, d_to, QDate(d_from), QDate(d_to), tmpdir, opts,
                                       job_ids=day_ids)
    inv_id = q("SELECT MAX(ID) FROM company_invoices")[0][0]
    linked = {r[0] for r in q("SELECT WORK_DAY_ID FROM invoice_work_days WHERE INVOICE_TYPE='Company' AND INVOICE_ID=%s",
                              (inv_id,))}
    check("new invoice records its days", linked == set(day_ids), (len(linked), len(day_ids)))
    check("board moves the job to Invoiced by itself", w._board_stage_of(pid) == "INVOICED", (before, w._board_stage_of(pid)))
    cur.execute("UPDATE company_invoices SET STATUS='RECEIVED', AMOUNT_PAID=TOTAL_AMOUNT WHERE ID=%s", (inv_id,))
    check("received invoice moves the job to Paid", w._board_stage_of(pid) == "PAID")
    cur.execute("DELETE FROM company_invoices WHERE ID=%s", (inv_id,))
    check("deleted invoice no longer counts", w._board_stage_of(pid) == "COMPLETED", w._board_stage_of(pid))

    # ── ACCOUNTANT PACKAGE ──
    year = q("SELECT YEAR(MAX(WORK_DATE)) FROM work_days")[0][0]
    folder, zip_path, missing, data = w.build_accountant_package(year, base_dir=tmpdir)
    from openpyxl import load_workbook
    wb = load_workbook(os.path.join(folder, f"VL Flooring {year}.xlsx"))
    check("workbook has all the sheets", wb.sheetnames == ["Summary", "By month", "Payments received", "Expenses",
                                                          "Helper pay (1099)", "Mileage", "Invoices"], wb.sheetnames)
    check("summary has income and net", "Income received" in str(wb["Summary"]["A4"].value)
          and wb["Summary"]["B4"].value == round(data["received"], 2), (wb["Summary"]["A4"].value, wb["Summary"]["B4"].value))
    check("payments sheet lists the year's payments", wb["Payments received"].max_row - 1 == len(data["payments"]))
    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()
    check("zip has the workbook", any(n.endswith(".xlsx") for n in names), names[:3])

    # ── MATERIAL USAGE ──
    usage = w._material_usage_rows()
    check("material usage lists jobs with materials", usage and all("lines" in j for j in usage), len(usage))
    check("flooring SF calculated from coverage", any(j["floor_sf"] > 0 for j in usage))
    seen = {}
    actions.append(lambda d: seen.update(n=len(d._jobs)))
    w.open_material_usage_dialog()
    check("usage dialog opens", seen.get("n") == len(usage))

    # ── CALENDAR ──
    start = q("SELECT MIN(WORK_DATE) FROM work_days WHERE WORK_DATE >= (SELECT MAX(WORK_DATE) FROM work_days) - "
              "INTERVAL 20 DAY")[0][0]
    ics_path = os.path.join(tmpdir, "test.ics")
    w.export_schedule_ics(start, weeks=4, path=ics_path, quiet=True)
    text = open(ics_path, encoding="utf-8").read()
    n_events = text.count("BEGIN:VEVENT")
    check("ics has events and is a calendar", text.startswith("BEGIN:VCALENDAR") and n_events > 0
          and "DTSTART;VALUE=DATE:" in text, n_events)

    # ── HUB ──
    check("hub has the new cards", all(k in w._hub_cards for k in ("rates", "accountant", "usage", "calendar")))
    check("calendar button in Schedule", hasattr(w.ui, "btn_export_schedule_ics"))
    crit = [m for m in msgs if m.startswith("CRIT")]
    check("no database errors", not crit, crit[:2])
    w._job_form_dirty = False
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
