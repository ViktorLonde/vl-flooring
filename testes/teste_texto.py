"""Testa o padrão de escrita (formatar_texto.smart_title) e que os campos de
nome/endereço do formulário aplicam o padrão ao sair do campo."""
import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); os.chdir(ROOT)
from formatar_texto import smart_title

CASES = {
    "3331 FOUNDERS CLUB DR": "3331 Founders Club Dr",
    "3331 founders club dr": "3331 Founders Club Dr",
    "QUALYTI FLOORING": "Qualyti Flooring",
    "Carpet one": "Carpet One",
    "fabiana": "Fabiana",
    "flooring options by carpet one": "Flooring Options by Carpet One",
    "vertex londe flooring llc": "Vertex Londe Flooring LLC",
    "Hardwood Oak Wedding Day (TruBalance)": "Hardwood Oak Wedding Day (TruBalance)",
    "771-STEP Advanced Polymer Wood Flooring Adhesive": "771-STEP Advanced Polymer Wood Flooring Adhesive",
    "123 NE 4TH ST": "123 NE 4th St",
    "o'neil construction": "O'Neil Construction",
    "Rigid LVT 7 x 48": "Rigid LVT 7 x 48",
    "Cardboard 36x42": "Cardboard 36x42",
    "PL Premium Max Construction Adhesive": "PL Premium Max Construction Adhesive",
    "apt 2b": "Apt 2B",
    "info@vertexlonde.com": "info@vertexlonde.com",
    "Self-leveling": "Self-Leveling",
    "": "",
}
ok = True
for given, expected in CASES.items():
    got = smart_title(given)
    good = got == expected
    ok &= good
    print(("PASS " if good else "FAIL ") + repr(given), "->", repr(got), "" if good else f"(expected {expected!r})", flush=True)

from PySide6.QtWidgets import QApplication
import app as appmod
from main_ import MainWindow
a = QApplication(sys.argv)
w = MainWindow(db_config=appmod.DB_CONFIG)
w.ui.txt_client_name.setText("JOHN DOE")
w.ui.txt_client_name.editingFinished.emit()
addr = w.ui.cmb_client_address.lineEdit()
addr.setText("100 main st"); addr.editingFinished.emit()
good = w.ui.txt_client_name.text() == "John Doe" and addr.text() == "100 Main St"
ok &= good
print(("PASS " if good else "FAIL ") + "form fields apply the standard on leaving the field",
      w.ui.txt_client_name.text(), "|", addr.text(), flush=True)
w.ui.txt_client_email.setText("JOHN@MAIL.COM"); w.ui.txt_client_email.editingFinished.emit()
good = w.ui.txt_client_email.text() == "JOHN@MAIL.COM"
ok &= good
print(("PASS " if good else "FAIL ") + "e-mail is not touched", flush=True)
w._job_form_dirty = False
print("RESULT:", "ALL OK" if ok else "FAILED", flush=True)
sys.exit(0 if ok else 1)
