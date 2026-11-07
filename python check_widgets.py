# -*- coding: utf-8 -*-
"""
Verifica se ui_main_window_vl_flooring.py (gerado pelo pyside6-uic)
contem todos os widgets que main_.py espera encontrar em self.ui.<nome>

Uso:
    python check_widgets.py
Rode na pasta onde estao main_.py e ui_main_window_vl_flooring.py
"""
import re
import sys
import os

REQUIRED = [
    "Left_container","Pages","Top_label","btn_customer","btn_delete_company",
    "btn_delete_contractor","btn_delete_expense","btn_delete_job","btn_delete_user",
    "btn_delete_work_type","btn_expense_attach_receipt","btn_generate_invoices",
    "btn_home","btn_jobs","btn_nav_receivables","btn_new_company","btn_new_contractor",
    "btn_new_expense","btn_new_job","btn_new_user","btn_new_work_type",
    "btn_refresh_companies","btn_refresh_contractors","btn_refresh_expenses",
    "btn_refresh_invoices","btn_refresh_jobs","btn_refresh_users","btn_refresh_work_types",
    "btn_reg_companies","btn_reg_contractors",
]

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ui_path = os.path.join(here, "ui_main_window_vl_flooring.py")
    main_path = os.path.join(here, "main_.py")

    if not os.path.exists(ui_path):
        print(f"[ERRO] Nao encontrei {ui_path}")
        print("Gere primeiro com: pyside6-uic main_window_vl_flooring_6.ui -o ui_main_window_vl_flooring.py")
        sys.exit(1)

    if not os.path.exists(main_path):
        print(f"[AVISO] Nao encontrei {main_path} nesta pasta - usando apenas a lista embutida.")
        required = REQUIRED
    else:
        with open(main_path, "r", encoding="utf-8") as f:
            content = f.read()
        required = sorted(set(re.findall(r"self\.ui\.([a-zA-Z_][a-zA-Z0-9_]*)", content)))

    with open(ui_path, "r", encoding="utf-8") as f:
        ui_content = f.read()

    missing = []
    for name in required:
        # objectName aparece como self.<name> = Qt... dentro do setupUi gerado
        if re.search(rf"\bself\.{re.escape(name)}\b", ui_content) is None:
            missing.append(name)

    print(f"Total de widgets esperados por main_.py: {len(required)}")
    if missing:
        print(f"\n[FALTANDO] {len(missing)} widget(s) nao encontrados em ui_main_window_vl_flooring.py:\n")
        for m in missing:
            print(f"  - {m}")
        print("\nAdicione esses objetos no Qt Designer (mesmo objectName) e gere o .ui novamente.")
        sys.exit(1)
    else:
        print("\n[OK] Todos os widgets esperados existem no arquivo gerado.")

if __name__ == "__main__":
    main()
    