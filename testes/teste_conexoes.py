import sys, os, gc
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); os.chdir(ROOT)
import logging
fallbacks = []
class H(logging.Handler):
    def emit(self, r):
        if "pool" in r.getMessage(): fallbacks.append(r.getMessage())
logging.getLogger().addHandler(H()); logging.getLogger().setLevel(logging.INFO)
from PySide6.QtWidgets import QApplication
import app as appmod
from main_ import MainWindow
a = QApplication(sys.argv)
w = MainWindow(db_config=appmod.DB_CONFIG); w.showMaximized(); a.processEvents()
w.set_current_user("viktorlonde")
btns = [w.ui.btn_home, w.ui.btn_jobs, w.ui.btn_reg_companies, w.ui.btn_reg_contractors, w.ui.btn_reg_work_types,
        w.ui.btn_nav_receivables, w.ui.btn_customer, w.ui.btn_user, w.ui.btn_reg_products, w.ui.btn_settings]
t = w.ui.table_work_days
for rnd in range(15):
    for i, b in enumerate(btns):
        w._go_to_page(i, b); a.processEvents()
        if i == 1:
            for r in range(min(t.rowCount(), 5)):
                t.selectRow(r); a.processEvents()
            w._job_form_dirty = False
            w.ui.tabWidget_jobs.setCurrentIndex(1); a.processEvents(); w.ui.tabWidget_jobs.setCurrentIndex(0)
        if i == 5:
            for k in range(w.ui.tabWidget_receivables.count()):
                w.ui.tabWidget_receivables.setCurrentIndex(k); a.processEvents()
    gc.collect()
print("free in pool:", w._db_pool._cnx_queue.qsize(), "of", w._DB_POOL_SIZE, "| fallbacks:", len(fallbacks), fallbacks[:2], flush=True)
ok = w._db_pool._cnx_queue.qsize() == w._DB_POOL_SIZE and not fallbacks
print("RESULT:", "ALL OK" if ok else "FAILED", flush=True)
sys.exit(0 if ok else 1)
