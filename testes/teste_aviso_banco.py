import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); os.chdir(ROOT)
from PySide6.QtWidgets import QApplication, QMessageBox
import app as appmod, company_settings
from main_ import MainWindow
a = QApplication(sys.argv)
w = MainWindow(db_config=appmod.DB_CONFIG)
shown = []
QMessageBox.exec = lambda box: shown.append(box.text()) or 0

# Dados de exemplo: sem aviso, sem bloco de banco, sem "Bank Transfer"
company_settings.COMPANY_BANK_INFO = {"account_no": "123456789", "account_name": "X",
                                      "bank_details": "Your Bank Name — Routing 000000000"}
company_settings.COMPANY_PAYMENT_METHODS = ["Zelle", "Check", "Cash", "Bank Transfer"]
r1 = w._confirm_bank_info_ready()
t1 = " ".join(w._invoice_payment_info_lines())
ok1 = r1 and not shown and "123456789" not in t1 and "Bank Transfer" not in t1 and "Zelle" in t1

# Dados reais: bloco aparece com Bank Transfer
company_settings.COMPANY_BANK_INFO = {"account_no": "987654", "account_name": "X", "bank_details": "Chase — Routing 021000021"}
t2 = " ".join(w._invoice_payment_info_lines())
ok2 = "987654" in t2 and "021000021" in t2 and "Bank Transfer" in t2

# Settings em abas
tabs = w.ui.tabs_settings
names = [tabs.tabText(i) for i in range(tabs.count())]
ok3 = names == ["Company", "Invoices", "Email", "System"]
tabs.setCurrentIndex(3); hidden_on_system = w.ui.btn_settings_save.isHidden()
tabs.setCurrentIndex(1); shown_on_invoices = not w.ui.btn_settings_save.isHidden()
ok4 = hidden_on_system and shown_on_invoices

# Detalhe de cada forma de pagamento
company_settings.COMPANY_PAYMENT_METHODS = ["Zelle", "Venmo", "Cash"]
company_settings.COMPANY_PAYMENT_DETAILS = {"Zelle": "941-000-0000", "Venmo": "@teste & co"}
t5 = w._invoice_payment_info_lines()
ok5 = "Zelle: 941-000-0000" in t5 and "Venmo: @teste &amp; co" in t5 and "Cash" in t5
pm = w._settings_payment_widgets()
ok6 = list(pm) == ["Zelle", "Venmo", "Cash App", "PayPal", "Check", "Cash", "Bank Transfer", "Credit Card"]
pm["Venmo"][0].setChecked(False); off = not pm["Venmo"][1].isEnabled()
pm["Venmo"][0].setChecked(True); on = pm["Venmo"][1].isEnabled()
ok6 = ok6 and off and on and pm["Bank Transfer"][1] is None

# Preview em Settings acompanha o que é digitado (sem salvar)
pm["Venmo"][1].setText("@preview_test")
prev = w.ui.lbl_settings_invoice_preview.text()
ok6 = ok6 and "Venmo: @preview_test" in prev
w.load_settings_form()  # volta o formulário ao que está salvo

print("placeholder:", ok1, "| real:", ok2, "| tabs:", names, "| save btn:", ok4,
      "| details on invoice:", ok5, "| settings rows:", ok6, flush=True)
ok = ok1 and ok2 and ok3 and ok4 and ok5 and ok6
print("RESULT:", "ALL OK" if ok else "FAILED", flush=True)
sys.exit(0 if ok else 1)
