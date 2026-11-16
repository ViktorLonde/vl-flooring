import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); os.chdir(ROOT)
from PySide6.QtWidgets import QApplication, QMessageBox
import app as appmod, company_settings
from main_ import MainWindow
a = QApplication(sys.argv)
w = MainWindow(db_config=appmod.DB_CONFIG)
shown = []
def fake_exec(box):
    shown.append(box.informativeText()); box_btns = box.buttons()
    # simula clicar no botão escolhido
    target = next(b for b in box_btns if b.text() == CHOICE)
    target.click(); return 0
QMessageBox.exec = fake_exec
print("current DB bank info:", company_settings.COMPANY_BANK_INFO, flush=True)
CHOICE = "Cancel"; r1 = w._confirm_bank_info_ready()
CHOICE = "Continue anyway"; r2 = w._confirm_bank_info_ready()
company_settings.COMPANY_BANK_INFO = {"account_no": "987654", "account_name": "X", "bank_details": "Chase — Routing 021000021"}
n = len(shown); r3 = w._confirm_bank_info_ready()
ok = (r1, r2, r3) == (False, True, True) and len(shown) == n
print("cancel->", r1, "| continue->", r2, "| real data->", r3, "no dialog:", len(shown) == n, flush=True)
print("RESULT:", "ALL OK" if ok else "FAILED", flush=True)
sys.exit(0 if ok else 1)
