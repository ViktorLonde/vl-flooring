"""Testa a ordem do Tab nos formulários (só leitura — não grava nada no banco)."""
import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); os.chdir(ROOT)
import config
from PySide6.QtWidgets import QApplication, QMessageBox

QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.No)
ok = True


def check(name, cond, extra=""):
    global ok
    ok &= bool(cond)
    print(("PASS " if cond else "FAIL ") + name, extra, flush=True)


def walk(start, n):
    """Segue o Tab a partir de 'start' (n passos) — nomes dos widgets."""
    out, w = [start.objectName()], start
    for _ in range(n):
        w = w.nextInFocusChain()
        while w is not None and (not w.isVisible() or not (w.focusPolicy() & Qt.FocusPolicy.TabFocus)
                                 or w.parentWidget().__class__.__name__ in ("QComboBox",)
                                 or w.objectName() in ("", "qt_spinbox_lineedit")):
            w = w.nextInFocusChain()
        out.append(w.objectName())
    return out


from PySide6.QtCore import Qt
from main_ import MainWindow
a = QApplication(sys.argv)
w = MainWindow(db_config=config.load_db_config()); w.resize(1536, 900); w.show(); a.processEvents()
w.set_current_user("viktorlonde")
ui = w.ui

w._go_to_page(6, ui.btn_customer); a.processEvents(); a.processEvents()
expected = ["txt_customer_name", "txt_customer_email", "txt_customer_phone", "txt_customer_phone2",
            "txt_customer_address", "txt_customer_address2", "cmb_customer_state", "cmb_customer_city",
            "txt_customer_zip", "btn_save_customer"]
got = walk(ui.txt_customer_name, len(expected) - 1)
check("Customer: Tab follows the screen", got == expected, got)
check("Customer: Tab after Phone 2 goes to Address", walk(ui.txt_customer_phone2, 1)[1] == "txt_customer_address")

w._go_to_page(2, ui.btn_reg_companies); a.processEvents(); a.processEvents()
got = walk(ui.txt_company_name, 6)
check("Companies: name → email → phone → phone 2 → address…", got[:6] == [
    "txt_company_name", got[1], "txt_company_email", "txt_company_phone", "txt_company_phone2", "txt_company_address"]
      or got[:5] == ["txt_company_name", "txt_company_email", "txt_company_phone", "txt_company_phone2",
                     "txt_company_address"], got)

w._go_to_page(3, ui.btn_reg_contractors); a.processEvents(); a.processEvents()
got = walk(ui.txt_contractor_full_name, 5)
check("Contractors: name → position → email → phone → phone 2 → company",
      got == ["txt_contractor_full_name", "txt_contractor_position", "txt_contractor_email", "txt_contractor_phone",
              "txt_contractor_phone2", "txt_contractor_company_name"], got)

w._go_to_page(1, ui.btn_jobs); ui.tabWidget_jobs.setCurrentWidget(ui.tab_jobs_master); a.processEvents(); a.processEvents()
chain = __import__("paginas.ordem_tab", fromlist=["screen_order"]).screen_order(ui.tab_jobs_master)
check("Job form has a tab order", len(chain) > 10, len(chain))
ys = [c.mapTo(ui.tab_jobs_master, c.rect().topLeft()).y() for c in chain]
check("Job form: Tab never jumps back up the screen", all(b >= a_ - 14 for a_, b in zip(ys, ys[1:])))
w._job_form_dirty = False
print("RESULT:", "ALL OK" if ok else "FAILED", flush=True)
sys.exit(0 if ok else 1)
