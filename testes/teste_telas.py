import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); os.chdir(ROOT)
from PySide6.QtWidgets import QApplication, QMessageBox
errs = []
QMessageBox.critical = staticmethod(lambda *a, **k: errs.append(str(a[2])) or QMessageBox.StandardButton.Ok)
QMessageBox.warning = staticmethod(lambda *a, **k: errs.append(str(a[2])) or QMessageBox.StandardButton.Ok)
old_hook = sys.excepthook
sys.excepthook = lambda *e: errs.append(repr(e[1]))
import app as appmod
from main_ import MainWindow
a = QApplication(sys.argv)
w = MainWindow(db_config=appmod.DB_CONFIG); w.showMaximized(); a.processEvents()
w.set_current_user("viktorlonde")
btns = [w.ui.btn_home, w.ui.btn_jobs, w.ui.btn_reg_companies, w.ui.btn_reg_contractors, w.ui.btn_reg_work_types,
        w.ui.btn_nav_receivables, w.ui.btn_customer, w.ui.btn_user, w.ui.btn_reg_products, w.ui.btn_settings]
for i, b in enumerate(btns):
    w._go_to_page(i, b); a.processEvents()
    if i == 5:
        for t in range(w.ui.tabWidget_receivables.count()):
            w.ui.tabWidget_receivables.setCurrentIndex(t); a.processEvents()
print("pages visited, errors:", errs, flush=True)
print("RESULT:", "ALL OK" if not errs else "FAILED", flush=True)
sys.exit(0 if not errs else 1)
