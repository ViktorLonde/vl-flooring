"""Testa perfis, histórico, Generate Code e jobs incompletos num banco TEMPORÁRIO."""
import sys, os, subprocess, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); os.chdir(ROOT)
import config, mysql.connector
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog, QTableWidget

REAL = config.load_db_config()
TEST_DB = "vl_jobs_test_tmp"
BIN = r"C:\Program Files\MySQL\MySQL Server 8.0\bin"
cnf = tempfile.NamedTemporaryFile("w", suffix=".cnf", delete=False)
cnf.write(f"[client]\nhost={REAL['host']}\nuser={REAL['user']}\npassword=\"{REAL['password']}\"\n"); cnf.close()
admin = mysql.connector.connect(**REAL); acur = admin.cursor()
acur.execute(f"DROP DATABASE IF EXISTS {TEST_DB}"); acur.execute(f"CREATE DATABASE {TEST_DB}")
dump = subprocess.run([os.path.join(BIN, "mysqldump.exe"), f"--defaults-extra-file={cnf.name}", "--single-transaction",
                       "--routines", "--triggers", REAL["database"]], capture_output=True, check=True).stdout
subprocess.run([os.path.join(BIN, "mysql.exe"), f"--defaults-extra-file={cnf.name}", TEST_DB], input=dump, check=True)
print("restored", flush=True)
TEST = {**REAL, "database": TEST_DB}
msgs = []
QMessageBox.information = staticmethod(lambda *a, **k: msgs.append(str(a[2])) or QMessageBox.StandardButton.Ok)
QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)
QMessageBox.warning = staticmethod(lambda *a, **k: msgs.append("WARN " + str(a[2])) or QMessageBox.StandardButton.Ok)
QMessageBox.critical = staticmethod(lambda *a, **k: msgs.append("CRIT " + str(a[2])) or QMessageBox.StandardButton.Ok)
dialog_rows = []
QDialog.exec = lambda self: dialog_rows.append(self.findChild(QTableWidget).rowCount()) or 0
ok = True
try:
    import registro
    from main_ import MainWindow
    app = QApplication(sys.argv)
    registro.install_default_save_folder()
    db = mysql.connector.connect(**TEST); db.autocommit = True; cur = db.cursor()

    def q(sql, p=()):
        cur.execute(sql, p); return cur.fetchall()

    def check(name, cond, extra=""):
        global ok
        ok &= bool(cond); print(("PASS " if cond else "FAIL ") + name, extra, flush=True)

    # ── ADMIN ──
    w = MainWindow(db_config=TEST); w.showMaximized(); app.processEvents()
    w.set_current_user("viktorlonde")
    check("admin label", "Admin" in w.ui.lbl_user.text(), w.ui.lbl_user.text())
    check("admin sees Users/Settings", w.ui.btn_user.isVisibleTo(w) and w.ui.btn_settings.isVisibleTo(w))
    check("admin delete enabled", w.ui.btn_delete_job.isEnabled())
    check("audit_log table created", q("SHOW TABLES LIKE 'audit_log'"))

    n_before = q("SELECT COUNT(*) FROM job_projects")[0][0]
    w._go_to_page(1, w.ui.btn_jobs); w.new_job_record(); app.processEvents()
    w.ui.cmb_contractor.setCurrentIndex(1)
    w._generate_job_code(); code = w.ui.cmb_job_code.currentText()
    check("generate code does not insert", q("SELECT COUNT(*) FROM job_projects")[0][0] == n_before, code)
    w.ui.dspn_value.setValue(123.45)
    msgs.clear(); w.save_job_record(); app.processEvents()
    proj = q("SELECT ID FROM job_projects WHERE CODE=%s", (code,))
    check("saving creates the code", proj, str(msgs[-1:])[:120])
    audit = q("SELECT username, action, table_name, record_id FROM audit_log ORDER BY id")
    check("history recorded save", any(a[0] == "viktorlonde" and a[2] == "work_days" and a[1] == "INSERT" for a in audit), audit[-3:])
    new_job_id = max(int(a[3]) for a in audit if a[2] == "work_days" and a[1] == "INSERT")

    w.open_change_history_dialog()
    check("history dialog lists rows", dialog_rows and dialog_rows[-1] >= 2, dialog_rows[-1:])
    w.open_incomplete_jobs_dialog()
    check("incomplete jobs dialog lists rows", dialog_rows[-1] > 0, dialog_rows[-1:])
    w._open_job_by_id(new_job_id, __import__("datetime").date.today())
    check("open job by id", str(w._current_job_id) == str(new_job_id), w._current_job_id)
    w._job_form_dirty = False

    # pasta padrão de exportação
    from PySide6.QtWidgets import QFileDialog
    import registro as r
    seen = {}
    orig = QFileDialog.getSaveFileName
    check("exports dir", r.EXPORTS_DIR.endswith(os.path.join("Documents", "VL Flooring")))
    w.close(); w.deleteLater(); app.processEvents()

    # ── VIEWER ──
    w = MainWindow(db_config=TEST); w.showMaximized(); app.processEvents()
    w.set_current_user("Nana")
    check("viewer label", "Viewer" in w.ui.lbl_user.text(), w.ui.lbl_user.text())
    check("viewer no Users/Settings", not w.ui.btn_user.isVisibleTo(w) and not w.ui.btn_settings.isVisibleTo(w))
    check("viewer buttons disabled", not w.ui.btn_save_job.isEnabled() and not w.ui.btn_new_customer.isEnabled()
          and not w.ui.btn_delete_job.isEnabled(), "")
    check("viewer export still enabled", w.ui.btn_export_pdf_jobs.isEnabled() and w.ui.btn_refresh_jobs.isEnabled())
    check("viewer P&L hidden", not w.ui.tabWidget_receivables.isTabVisible(w.ui.tabWidget_receivables.indexOf(w.ui.tab_pnl)))
    w._go_to_page(9, w.ui.btn_settings); check("viewer cannot open Settings", w.ui.Pages.currentIndex() != 9)
    cnt = q("SELECT COUNT(*) FROM work_days")[0][0]
    w._go_to_page(1, w.ui.btn_jobs); w.new_job_record(); w.ui.cmb_contractor.setCurrentIndex(1)
    msgs.clear(); w.save_job_record(); app.processEvents()
    check("viewer save refused by MySQL", q("SELECT COUNT(*) FROM work_days")[0][0] == cnt, str(msgs)[:160])
    w._job_form_dirty = False
    w.close(); w.deleteLater(); app.processEvents()

    # ── MANAGER ──
    w = MainWindow(db_config=TEST); w.showMaximized(); app.processEvents()
    w.set_current_user("Lia")
    check("manager can save, cannot delete", w.ui.btn_save_job.isEnabled() and not w.ui.btn_delete_job.isEnabled())
    check("manager no Users", not w.ui.btn_user.isVisibleTo(w))
    w._go_to_page(1, w.ui.btn_jobs); w.ui.dspn_value.setValue(10)
    w._open_job_by_id(new_job_id, __import__("datetime").date.today())
    w.ui.dspn_value.setValue(99); msgs.clear(); w.save_job_record(); app.processEvents()
    a = q("SELECT username, action, record_id FROM audit_log WHERE username='Lia' AND table_name='work_days'")
    check("manager change recorded with record id", any(x[1] == "UPDATE" and x[2] == str(new_job_id) for x in a), a[-2:])
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
