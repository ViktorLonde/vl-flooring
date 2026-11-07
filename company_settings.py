# -*- coding: utf-8 -*-
"""
Dados da empresa e do e-mail usados nos invoices e no envio por e-mail.

Os valores abaixo são só o padrão: ao abrir, o app carrega o que estiver salvo
na tabela app_settings (tela Settings) e sobrescreve aqui. Todo o código lê
daqui como company_settings.NOME, assim uma alteração feita na tela Settings
vale imediatamente em todas as telas.
"""

# ── MARCA / INVOICE ───────────────────────────────────────────────────
COMPANY_NAME = "Vertex Londe Flooring LLC"
COMPANY_TAGLINE = "FLOORING LLC"
COMPANY_PHONE = "+00 1234 5678 013"
COMPANY_EMAIL = "info@vertexlonde.com"
COMPANY_WEBSITE = "www.vertexlonde.com"

# Informações bancárias mostradas na área "Payment Info" do invoice.
COMPANY_BANK_INFO = {
    "account_no": "123456789",
    "account_name": "Vertex Londe Flooring LLC",
    "bank_details": "Your Bank Name — Routing 000000000",
}
# Formas de pagamento aceitas, mostradas no invoice.
COMPANY_PAYMENT_METHODS = ["Zelle", "Check", "Cash", "Bank Transfer"]

# ── ENVIO DE INVOICES POR E-MAIL ──────────────────────────────────────
# Preencha com os dados do seu provedor de e-mail (Gmail, Outlook, etc.)
# Para Gmail, use uma "App Password" (não a senha normal da conta) —
# gere em https://myaccount.google.com/apppasswords
EMAIL_SMTP_HOST = "smtp.gmail.com"
EMAIL_SMTP_PORT = 587
EMAIL_SMTP_USER = "your-email@gmail.com"
EMAIL_SMTP_PASSWORD = "your-app-password"
EMAIL_FROM_NAME = COMPANY_NAME
