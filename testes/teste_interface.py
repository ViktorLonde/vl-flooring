"""Testa as melhorias de interface: atalhos, busca geral, avisos (toasts),
modo escuro, tabelas e o rótulo P&L. Só lê o banco real."""
import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); os.chdir(ROOT)
from PySide6.QtWidgets import QApplication, QMessageBox, QTableWidget
from PySide6.QtCore import QSettings
import app as appmod
import traceback
sys.excepthook = lambda *e: errors.append("".join(traceback.format_exception(*e))[-400:])
from main_ import MainWindow
from paginas.visual import install_icon_theme
from paginas.moderno import install_modern_ui, Toast
from paginas import tema

errors = []
ok = True


def check(name, cond, extra=""):
    global ok
    ok &= bool(cond)
    print(("PASS " if cond else "FAIL ") + name, extra, flush=True)


settings = QSettings("VL Flooring", "app")
saved_dark = settings.value("dark_mode", False, type=bool)
settings.setValue("dark_mode", False)

a = QApplication(sys.argv)
install_icon_theme(a)
install_modern_ui(a)
w = MainWindow(db_config=appmod.DB_CONFIG)
w.resize(1536, 816); w.show(); a.processEvents()
w.set_current_user("viktorlonde")
ui = w.ui

# P&L e data
pnl = ui.tabWidget_receivables.tabText(ui.tabWidget_receivables.indexOf(ui.tab_pnl))
check("P&L tab text", pnl == "P&&L", pnl)
from PySide6.QtCore import QDate
check("work date starts today", ui.date_work_date.date() == QDate.currentDate())

# atalhos: acham os botões certos na tela de Jobs
w._go_to_page(1, ui.btn_jobs); a.processEvents()
names = [b.objectName() for b in w._page_widgets(type(ui.btn_save_job))]
check("Ctrl+S/Ctrl+N find job buttons", "btn_save_job" in names and "btn_new_job" in names)
w._focus_page_search(); a.processEvents()
check("Ctrl+F focuses page search", a.focusWidget() is ui.txt_search_jobs or ui.txt_search_jobs.hasFocus())

# tabelas
t = ui.table_work_days
check("tables: no row-number column", not t.verticalHeader().isVisible())
check("tables: status delegate", t.itemDelegate().__class__.__name__ == "StatusPillDelegate")

# busca geral → contractor
w._global_search.setText("qual"); w._run_global_search(); a.processEvents()
items = [w._global_popup.item(i) for i in range(w._global_popup.count())]
contractor = next((i for i in items if i.data(256) and i.data(256)[0] == "contractor"), None)
check("global search finds a contractor", contractor is not None, [i.text() for i in items][:4])
if contractor:
    w._open_global_result(contractor); a.processEvents()
    check("opening result goes to Contractors", ui.Pages.currentIndex() == 3
          and ui.table_contractors.currentRow() >= 0)
job = next((i for i in items if i.data(256) and i.data(256)[0] == "job"), None)
if job is None:
    w._global_search.setText("JB-00"); w._run_global_search(); a.processEvents()
    job = next((w._global_popup.item(i) for i in range(w._global_popup.count())
                if w._global_popup.item(i).data(256) and w._global_popup.item(i).data(256)[0] == "job"), None)
check("global search finds a job", job is not None)
if job:
    w._open_global_result(job); a.processEvents()
    check("opening job loads the form", ui.Pages.currentIndex() == 1 and w._current_job_id is not None)
w._job_form_dirty = False

# toast
result = QMessageBox.information(w, "Saved", "Job record saved successfully.")
a.processEvents()
check("information became a toast", result == QMessageBox.StandardButton.Ok and len(Toast._active) >= 1)

# modo escuro liga e desliga sem perder o estilo original
light_qss = w.styleSheet()
w._toggle_dark_mode(); a.processEvents()
check("dark mode on", tema.is_dark() and w.styleSheet() != light_qss and "#1B2533" in w.styleSheet())
w._go_to_page(5, ui.btn_nav_receivables); a.processEvents()
w._toggle_dark_mode(); a.processEvents()
check("dark mode off restores light style", not tema.is_dark() and w.styleSheet() == light_qss)

check("no unexpected errors", not errors, errors[:1])
settings.setValue("dark_mode", saved_dark)
print("RESULT:", "ALL OK" if ok else "FAILED", flush=True)
sys.exit(0 if ok else 1)
