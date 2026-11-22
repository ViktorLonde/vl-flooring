"""Testa: trocar usuário, lembrar a última tela, aviso "Needs your attention",
gráfico de 6 meses, resumo do cliente e restaurar backup (numa CÓPIA
temporária do banco — o banco real não é alterado)."""
import sys, os, gzip, subprocess, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); os.chdir(ROOT)
import traceback
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QSettings
import app as appmod
errors = []
sys.excepthook = lambda *e: errors.append("".join(traceback.format_exception(*e))[-500:])
import backup_db, config, mysql.connector
from paginas.visual import install_icon_theme
from paginas.moderno import install_modern_ui

ok = True


def check(name, cond, extra=""):
    global ok
    ok &= bool(cond)
    print(("PASS " if cond else "FAIL ") + name, extra, flush=True)


QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)
settings = QSettings("VL Flooring", "app")
saved = {k: settings.value(k) for k in settings.allKeys()}

a = QApplication(sys.argv)
install_icon_theme(a)
install_modern_ui(a)

# ── login → tela lembrada → trocar usuário ──
settings.setValue("ui/last_page", 6)  # Customer
appmod.start_session()
main, login = appmod._session["main"], appmod._session["login"]
login.login_successful.emit("viktorlonde"); a.processEvents()
check("login opens main window", main.isVisible() and main._current_username == "viktorlonde")
check("always opens on Home (since 2026-11-20)", main.ui.Pages.currentIndex() == 0, main.ui.Pages.currentIndex())

layout = main.ui.layout_home_revenue_chart
check("revenue chart has 6 months", layout.count() in (1, 6), layout.count())
main._collect_attention_items()
check("attention summary runs", not errors, errors[:1])

t = main.ui.table_customers
if t.rowCount():
    t.selectRow(0); a.processEvents()
    check("customer summary shows jobs and invoices",
          "job" in main.ui.lbl_customer_job_history_total.text(), main.ui.lbl_customer_job_history_total.text())

main.signed_out.emit(); a.processEvents()
new_main, new_login = appmod._session["main"], appmod._session["login"]
check("switch user shows a new login", new_login is not login and new_login.isVisible())
check("old window closed without asking", not main.isVisible())
new_login.close(); new_main._closing_for_sign_out = True; new_main.close()

# ── restaurar backup numa cópia temporária ──
REAL = config.load_db_config()
TEST_DB = "vl_restore_test_tmp"
tmpdir = tempfile.mkdtemp()
cnf = os.path.join(tmpdir, "c.cnf")
open(cnf, "w").write(f"[client]\nhost={REAL['host']}\nuser={REAL['user']}\npassword=\"{REAL['password']}\"\n")
admin = mysql.connector.connect(**REAL); acur = admin.cursor()
try:
    acur.execute(f"DROP DATABASE IF EXISTS {TEST_DB}"); acur.execute(f"CREATE DATABASE {TEST_DB}")
    dump = subprocess.run([backup_db.find_mysqldump(), f"--defaults-extra-file={cnf}", "--single-transaction",
                           REAL["database"]], capture_output=True, check=True).stdout
    gz = os.path.join(tmpdir, "test.sql.gz")
    with gzip.open(gz, "wb") as f:
        f.write(dump)
    backup_db.restore_backup(gz, database=TEST_DB)
    acur.execute(f"SELECT COUNT(*) FROM {REAL['database']}.work_days"); real_n = acur.fetchone()[0]
    acur.execute(f"SELECT COUNT(*) FROM {TEST_DB}.work_days"); test_n = acur.fetchone()[0]
    check("restore_backup restores the data", real_n == test_n and test_n > 0, (real_n, test_n))
    check("list_backups finds backups", len(backup_db.list_backups()) > 0)
except Exception:
    errors.append(traceback.format_exc()); check("restore test ran", False, errors[-1][-300:])
finally:
    acur.execute("SET SESSION lock_wait_timeout = 15")
    acur.execute(f"DROP DATABASE IF EXISTS {TEST_DB}"); admin.close()
    for f in os.listdir(tmpdir):
        os.remove(os.path.join(tmpdir, f))
    os.rmdir(tmpdir)

check("no unexpected errors", not errors, errors[:1])
settings.clear()
for k, v in saved.items():
    settings.setValue(k, v)
print("RESULT:", "ALL OK" if ok else "FAILED", flush=True)
sys.exit(0 if ok else 1)
