"""Testa: Expense do job já ligado ao Job Code, filtro de produtos sem preço,
calculadora de material, fotos do job, quilometragem e orçamentos (salvar,
PDF, converter em job) — numa CÓPIA temporária do banco."""
import sys, os, subprocess, tempfile, traceback, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); os.chdir(ROOT)
import config, mysql.connector
from PySide6.QtWidgets import (QApplication, QMessageBox, QDialog, QPushButton, QDoubleSpinBox, QComboBox,
                               QTableWidget, QLineEdit, QFileDialog, QInputDialog, QListWidget)
from PySide6.QtGui import QImage, QColor, QDesktopServices

REAL = config.load_db_config()
TEST_DB = "vl_tools_test_tmp"
BIN = r"C:\Program Files\MySQL\MySQL Server 8.0\bin"
cnf = tempfile.NamedTemporaryFile("w", suffix=".cnf", delete=False)
cnf.write(f"[client]\nhost={REAL['host']}\nuser={REAL['user']}\npassword=\"{REAL['password']}\"\n"); cnf.close()
admin = mysql.connector.connect(**REAL); acur = admin.cursor()
acur.execute(f"DROP DATABASE IF EXISTS {TEST_DB}"); acur.execute(f"CREATE DATABASE {TEST_DB}")
dump = subprocess.run([os.path.join(BIN, "mysqldump.exe"), f"--defaults-extra-file={cnf.name}", "--single-transaction",
                       REAL["database"]], capture_output=True, check=True).stdout
subprocess.run([os.path.join(BIN, "mysql.exe"), f"--defaults-extra-file={cnf.name}", TEST_DB], input=dump, check=True)
TEST = {**REAL, "database": TEST_DB}
tmpdir = tempfile.mkdtemp()

msgs = []
QMessageBox.information = staticmethod(lambda *a, **k: msgs.append(str(a[2])) or QMessageBox.StandardButton.Ok)
QMessageBox.warning = staticmethod(lambda *a, **k: msgs.append("WARN " + str(a[2])) or QMessageBox.StandardButton.Ok)
QMessageBox.critical = staticmethod(lambda *a, **k: msgs.append("CRIT " + str(a[2])) or QMessageBox.StandardButton.Ok)
QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)
QDesktopServices.openUrl = staticmethod(lambda *a: True)
actions = []


def fake_exec(d):
    if actions:
        result = actions.pop(0)(d)
        return 1 if result is None else result
    return 0


QDialog.exec = fake_exec
ok = True


def check(name, cond, extra=""):
    global ok
    ok &= bool(cond)
    print(("PASS " if cond else "FAIL ") + name, extra, flush=True)


photo_folder = None
try:
    db = mysql.connector.connect(**TEST); db.autocommit = True; cur = db.cursor()

    def q(sql, p=()):
        cur.execute(sql, p); return cur.fetchall()

    from main_ import MainWindow
    a = QApplication(sys.argv)
    w = MainWindow(db_config=TEST); w.resize(1536, 816); w.show(); a.processEvents()
    w.set_current_user("viktorlonde")
    ui = w.ui

    # ── Expense do job ──
    pid, wid, code, wdate = q("SELECT jp.ID, wd.ID, jp.CODE, wd.WORK_DATE FROM work_days wd JOIN job_projects jp "
                              "ON jp.ID = wd.JOB_PROJECT_ID ORDER BY wd.ID DESC LIMIT 1")[0]
    w._go_to_page(1, ui.btn_jobs); w._open_job_by_id(wid, wdate); a.processEvents(); w._job_form_dirty = False
    w._go_to_new_expense_from_job(); a.processEvents()
    check("Expense from job comes linked to the Job Code", ui.cmb_expense_job_code.currentData() == pid,
          ui.cmb_expense_job_code.currentText())

    # ── produtos sem preço ──
    w._go_to_page(8, ui.btn_reg_products); a.processEvents()
    w._chk_products_no_price.setChecked(True); a.processEvents()
    zero = q("SELECT COUNT(*) FROM products WHERE COALESCE(PRICE,0)=0")[0][0]
    check("filter shows only products without price", ui.table_products.rowCount() == zero, (ui.table_products.rowCount(), zero))
    check("hint counts products without price", str(zero) in w._lbl_products_no_price.text(), w._lbl_products_no_price.text())
    w._chk_products_no_price.setChecked(False)

    # ── calculadora ──
    cur.execute("INSERT INTO products (TYPE, NAME, PRICE, UNIT, COVERAGE_QTY, COVERAGE_UNIT) "
                "VALUES ('Flooring', 'Calc Test Floor', 50, 'BOX', 20, 'SF')"); floor_id = cur.lastrowid
    w._go_to_page(1, ui.btn_jobs); w._open_job_by_id(wid, wdate); a.processEvents(); w._job_form_dirty = False
    before = q("SELECT COUNT(*) FROM job_materials WHERE JOB_PROJECT_ID=%s", (pid,))[0][0]

    def calc(d):
        spins = d.findChildren(QDoubleSpinBox)
        spins[0].setValue(1000); spins[1].setValue(10)
        t = d.findChild(QTableWidget)
        while t.rowCount() > 1:
            t.removeRow(t.rowCount() - 1)
        combo = t.cellWidget(0, 0); combo.setCurrentIndex(combo.findData(floor_id)); a.processEvents()
        state["needed"] = t.item(0, 2).text()
        next(b for b in d.findChildren(QPushButton) if b.objectName() == "btn_add_calc_to_job").click()
    state = {}
    actions.append(calc)
    w.open_material_calculator_dialog(from_job=True); a.processEvents()
    check("calculator: 1000 SF + 10% / 20 SF per box = 55 boxes", state.get("needed", "").startswith("55"), state)
    mat = q("SELECT QUANTITY, UNIT_PRICE FROM job_materials WHERE JOB_PROJECT_ID=%s AND PRODUCT_ID=%s", (pid, floor_id))
    check("calculator adds to job materials", mat and float(mat[0][0]) == 55 and float(mat[0][1]) == 50, mat)

    # ── fotos ──
    img_path = os.path.join(tmpdir, "test.jpg")
    img = QImage(3000, 2000, QImage.Format.Format_RGB32); img.fill(QColor("#336699")); img.save(img_path, "JPG")
    QFileDialog.getOpenFileNames = staticmethod(lambda *a_, **k: ([img_path], ""))

    def photos(d):
        next(b for b in d.findChildren(QPushButton) if "Add photos" in b.text()).click(); a.processEvents()
        state["photos"] = d.findChild(QListWidget).count()
    actions.append(photos)
    w.open_job_photos_dialog(); a.processEvents()
    rows = q("SELECT FILE_PATH FROM documents WHERE ENTITY_TYPE='JOB_PROJECT' AND ENTITY_ID=%s", (pid,))
    check("photo saved and listed", state.get("photos") == 1 and len(rows) == 1, (state.get("photos"), rows))
    if rows:
        full = os.path.join(ROOT, rows[0][0]); photo_folder = os.path.dirname(full)
        saved = QImage(full)
        check("photo stored resized in job_photos/<code>", os.path.exists(full) and max(saved.width(), saved.height()) <= 2000,
              rows[0][0])
    check("Photos button shows the count", "Photos (1)" in ui.btn_job_photos.text(), ui.btn_job_photos.text())

    # ── quilometragem ──
    def miles(d):
        spins = [s for s in d.findChildren(QDoubleSpinBox)]
        rate, miles_spin = spins[0], spins[1]
        rate.setValue(0.70); miles_spin.setValue(42.5)
        next(e for e in d.findChildren(QLineEdit) if "Purpose" in e.placeholderText()).setText("Supplier run")
        next(b for b in d.findChildren(QPushButton) if b.objectName() == "btn_add_mileage").click(); a.processEvents()
        state["summary"] = next(l for l in d.findChildren(type(ui.Top_label)) if "miles" in l.text()).text()
    actions.append(miles)
    w.open_mileage_dialog(); a.processEvents()
    check("mileage trip saved", q("SELECT MILES FROM mileage WHERE PURPOSE='Supplier run'"), state.get("summary"))
    check("mileage deduction shown", "$29.75" in state.get("summary", ""), state.get("summary"))

    # ── orçamento: salvar, PDF, converter ──
    QInputDialog.getItem = staticmethod(lambda *a_, **k: (a_[3][0], True))
    pdf_path = os.path.join(tmpdir, "est.pdf")
    QFileDialog.getSaveFileName = staticmethod(lambda *a_, **k: (pdf_path, ""))

    def estimate(d):
        d.findChildren(QComboBox)[0].setEditText("Test Estimate Client")
        next(e for e in d.findChildren(QLineEdit) if e.placeholderText() == "Job address").setText("1 Test St")
        t = d.findChild(QTableWidget)
        t.cellWidget(0, 1).setText("Install hardwood"); t.cellWidget(0, 2).setValue(500); t.cellWidget(0, 4).setValue(3.5)
        next(b for b in d.findChildren(QPushButton) if "Add material" in b.text()).click()
        t.cellWidget(1, 2).setValue(10)
        next(b for b in d.findChildren(QPushButton) if b.objectName() == "btn_save_estimate").click()
        next(b for b in d.findChildren(QPushButton) if b.text().strip() == "PDF").click()

        def confirm(sd):
            return 1
        actions.insert(0, confirm)
        next(b for b in d.findChildren(QPushButton) if b.objectName() == "btn_convert_estimate").click()
    actions.append(estimate)
    w.open_estimate_editor(None); a.processEvents()
    est = q("SELECT CODE, TOTAL, STATUS, JOB_PROJECT_ID FROM estimates ORDER BY ID DESC LIMIT 1")
    check("estimate saved with total", est and float(est[0][1]) >= 1750, est)
    check("estimate PDF created", os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 1000)
    check("estimate converted", est and est[0][2] == "CONVERTED" and est[0][3], est)
    if est and est[0][3]:
        job = q("SELECT jp.CODE, wd.STATUS, wd.NOTE, c.FULL_NAME FROM job_projects jp JOIN work_days wd ON wd.JOB_PROJECT_ID=jp.ID "
                "JOIN clients c ON c.ID=wd.CLIENT_ID WHERE jp.ID=%s", (est[0][3],))
        check("new job has first day, client and note", job and job[0][1] == "PENDING" and "From estimate" in job[0][2]
              and job[0][3] == "Test Estimate Client", job)
        check("estimate materials went to the job", q("SELECT COUNT(*) FROM job_materials WHERE JOB_PROJECT_ID=%s",
                                                      (est[0][3],))[0][0] == 1)
    w._job_form_dirty = False
    db.close()
except Exception:
    traceback.print_exc(); ok = False
finally:
    acur.execute("SET SESSION lock_wait_timeout = 15")
    acur.execute(f"DROP DATABASE IF EXISTS {TEST_DB}"); admin.close(); os.remove(cnf.name)
    shutil.rmtree(tmpdir, ignore_errors=True)
    if photo_folder and os.path.isdir(photo_folder):
        for f in os.listdir(photo_folder):
            if f.startswith(("Before_", "Progress_", "After_")):
                os.remove(os.path.join(photo_folder, f))
        if not os.listdir(photo_folder):
            os.rmdir(photo_folder)
    print("temp db dropped", flush=True)
print("RESULT:", "ALL OK" if ok else "FAILED", flush=True)
sys.exit(0 if ok else 1)
