"""Testa: entrar num campo de valor seleciona o número (é só digitar por
cima) e o ZIP sugere os códigos já usados na cidade escolhida. Só lê o banco."""
import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); os.chdir(ROOT)
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
import app as appmod
from main_ import MainWindow
from paginas.digitacao import install_select_all_on_focus
import config, mysql.connector

ok = True


def check(name, cond, extra=""):
    global ok
    ok &= bool(cond)
    print(("PASS " if cond else "FAIL ") + name, extra, flush=True)


a = QApplication(sys.argv)
install_select_all_on_focus(a)
w = MainWindow(db_config=appmod.DB_CONFIG); w.resize(1536, 816); w.show(); a.processEvents()
w.set_current_user("viktorlonde"); w._go_to_page(1, w.ui.btn_jobs); a.processEvents()
w.activateWindow(); a.processEvents()

# campo Value: ao entrar, o número fica selecionado; digitar substitui
spin = w.ui.dspn_value
spin.setValue(250)
w.ui.txt_note.setFocus(); a.processEvents()
QTest.mouseClick(spin.lineEdit(), Qt.MouseButton.LeftButton); a.processEvents(); QTest.qWait(50); a.processEvents()
check("clicking Value selects the whole number", spin.lineEdit().selectedText() == spin.cleanText(),
      repr(spin.lineEdit().selectedText()))
QTest.keyClicks(spin.lineEdit(), "375"); a.processEvents()
spin.interpretText()
check("typing replaces the old value", abs(spin.value() - 375) < 0.001, spin.value())
w.ui.txt_note.setFocus(); a.processEvents()
spin.setFocus(Qt.FocusReason.TabFocusReason); a.processEvents(); QTest.qWait(50); a.processEvents()
check("entering with Tab also selects", spin.lineEdit().selectedText() == spin.cleanText(),
      repr(spin.lineEdit().selectedText()))

# ZIP sugerido pela cidade (pega do banco uma cidade que já tem ZIP salvo)
c = mysql.connector.connect(**config.load_db_config()); cur = c.cursor()
cur.execute("""SELECT ci.CITY, s.ID, wd.ZIP_CODE FROM work_days wd JOIN cities ci ON ci.ID = wd.CITY_ID
               JOIN states s ON s.ID = wd.STATE_ID WHERE COALESCE(wd.ZIP_CODE,'') <> '' LIMIT 1""")
row = cur.fetchone(); c.close()
if row:
    city_name, state_id, zip_code = row
    w._set_combo_by_data(w.ui.cmb_client_state, state_id); a.processEvents()
    idx = w.ui.cmb_client_city.findText(city_name)
    w.ui.cmb_client_city.setCurrentIndex(idx); a.processEvents()
    model = w.ui.txt_client_zip.completer().model()
    zips = [model.index(i, 0).data() for i in range(model.rowCount())]
    check("ZIP suggests the codes saved for the city", w._format_zip(zip_code) in zips, (city_name, zips[:5]))
else:
    print("SKIP no saved ZIP in the database")
w._job_form_dirty = False
print("RESULT:", "ALL OK" if ok else "FAILED", flush=True)
sys.exit(0 if ok else 1)
