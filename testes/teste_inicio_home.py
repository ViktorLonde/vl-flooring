import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); os.chdir(ROOT)
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication
import app as appmod
from main_ import MainWindow
from paginas.sessao import _SETTINGS
a = QApplication(sys.argv)
s = QSettings(*_SETTINGS); old = s.value("ui/last_page")
s.setValue("ui/last_page", 9)  # última tela usada = Settings
w = MainWindow(db_config=appmod.DB_CONFIG)
w.restore_ui_state()
ok = w.ui.stackedWidget.currentIndex() == 0 if hasattr(w.ui, "stackedWidget") else None
if ok is None:
    ok = w.ui.btn_home.isChecked()
if old is None: s.remove("ui/last_page")
else: s.setValue("ui/last_page", old)
print("opens on Home even if last page was Settings:", ok, flush=True)
print("RESULT:", "ALL OK" if ok else "FAILED", flush=True)
sys.exit(0 if ok else 1)
