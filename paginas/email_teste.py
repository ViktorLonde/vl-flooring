# -*- coding: utf-8 -*-
"""
Botão "Send test e-mail" em Settings → Email.

Testa a conta de envio passo a passo, com os valores que estão digitados na
tela (mesmo antes de salvar): conectar no servidor → conexão segura (TLS) →
login → enviar um e-mail de teste para o e-mail do resumo semanal. Mostra
em qual passo falhou e o que fazer (em português).

Métodos da MainWindow (mixin) — veja main_.py.
"""

import smtplib
import ssl
from datetime import datetime

from app_common import *  # noqa: F401,F403
from paginas.visual import tabler_icon

_SMALL_BTN = ("QPushButton { background-color: #EEF2F7; color: #37474F; border: 1px solid #D0D7DE; "
              "border-radius: 6px; padding: 8px 14px; font-size: 12px; font-weight: 600; } "
              "QPushButton:hover { background-color: #E1E8F0; }")

_APP_PASSWORD_TIP = ("Use uma App Password (16 letras), não a senha normal: myaccount.google.com → Security → "
                     "2-Step Verification (ligar) → App passwords → criar \"VL Flooring\" → copiar as 16 letras "
                     "para o campo Password e clicar em Save.")


def smtp_diagnose(host, port, user, password, to, company="VL Flooring", send=True, smtp_module=smtplib):
    """[(passo, ok, detalhe)] — para no primeiro passo que falhar."""
    steps = []
    host = (host or "").strip()
    port = int(port or 0)
    if not host or not port:
        return [("Server", False, "Preencha o SMTP Host e a porta (Gmail: smtp.gmail.com, 587).")]
    if not user or "your-email" in user:
        return [("Account", False, "Preencha o SMTP User com o seu e-mail.")]
    if not password or password == "your-app-password":
        return [("Password", False, "Falta a senha. " + _APP_PASSWORD_TIP)]
    server = None
    try:
        if port == 465:
            server = smtp_module.SMTP_SSL(host, port, timeout=20, context=ssl.create_default_context())
        else:
            server = smtp_module.SMTP(host, port, timeout=20)
        server.ehlo()
        steps.append(("Connect to " + host, True, f"porta {port}"))
    except Exception as e:  # noqa: BLE001
        steps.append(("Connect to " + host, False,
                      f"Não conectou ({type(e).__name__}: {e}). Confira o servidor e a porta, a internet, ou se "
                      "o antivírus/firewall bloqueia o envio de e-mail."))
        return steps
    try:
        if port != 465:
            server.starttls(context=ssl.create_default_context())
            server.ehlo()
        steps.append(("Secure connection (TLS)", True, ""))
    except Exception as e:  # noqa: BLE001
        steps.append(("Secure connection (TLS)", False, f"{type(e).__name__}: {e}. Tente a porta 587 (ou 465)."))
        return steps
    try:
        server.login(user, password)
        steps.append(("Login", True, user))
    except smtplib.SMTPAuthenticationError as e:
        code = getattr(e, "smtp_code", "")
        steps.append(("Login", False, f"Usuário ou senha recusados ({code}). " + _APP_PASSWORD_TIP))
        return steps
    except smtplib.SMTPServerDisconnected:
        steps.append(("Login", False,
                      "O servidor fechou a conexão no login — normalmente é senha errada ou a senha normal da "
                      "conta em vez da App Password. " + _APP_PASSWORD_TIP + " Se o seu e-mail não abre em "
                      "mail.google.com, ele não é do Google: me diga o provedor para trocar o servidor."))
        return steps
    except Exception as e:  # noqa: BLE001
        steps.append(("Login", False, f"{type(e).__name__}: {e}"))
        return steps
    if send:
        try:
            m = EmailMessage()
            m["Subject"] = f"{company} — test e-mail"
            m["From"] = f"{company} <{user}>"
            m["To"] = to or user
            m.set_content(f"This is a test from the VL Flooring app ({datetime.now():%m/%d/%Y %H:%M}).\n"
                          "If you got it, invoices, reminders and the weekly summary can be e-mailed.")
            server.send_message(m)
            steps.append(("Send test e-mail", True, f"enviado para {to or user} — confira a caixa de entrada (e o spam)"))
        except Exception as e:  # noqa: BLE001
            steps.append(("Send test e-mail", False, f"{type(e).__name__}: {e}"))
    try:
        server.quit()
    except Exception:  # noqa: BLE001
        pass
    return steps


class EmailTestMixin:
    def _setup_email_test_button(self):
        grid = getattr(self.ui, "grid_settings_email", None)
        if grid is None:
            return
        btn = QPushButton("  Send test e-mail")
        btn.setObjectName("btn_send_test_email")
        btn.setIcon(tabler_icon("send", "#37474F", 16))
        btn.setStyleSheet(_SMALL_BTN)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip("Tests the account typed above (connect → login → send) and says what is wrong")
        btn.clicked.connect(self.run_email_test)
        grid.addWidget(btn, 5, 0, 1, 1, Qt.AlignmentFlag.AlignLeft)
        self.ui.btn_send_test_email = btn

    def run_email_test(self):
        ui = self.ui
        user = ui.txt_settings_smtp_user.text().strip()
        to = (self._summary_recipient() if hasattr(self, "_summary_recipient") else "") or user
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            steps = smtp_diagnose(ui.txt_settings_smtp_host.text(), ui.spn_settings_smtp_port.value(), user,
                                  ui.txt_settings_smtp_password.text(), to,
                                  company=company_settings.COMPANY_NAME)
        finally:
            QApplication.restoreOverrideCursor()
        ok = all(s[1] for s in steps) and steps[-1][0] == "Send test e-mail"
        lines = [f"{'✅' if good else '❌'}  {name}" + (f" — {detail}" if detail else "") for name, good, detail in steps]
        logging.getLogger("vl_flooring").info("e-mail test: %s", " | ".join(f"{n}={'ok' if g else 'FAIL'}"
                                                                            for n, g, _d in steps))
        box = QMessageBox(self)
        box.setWindowTitle("E-mail test")
        box.setIcon(QMessageBox.Icon.Information if ok else QMessageBox.Icon.Warning)
        box.setText("E-mail is working! ✔" if ok else "E-mail is not working yet")
        box.setInformativeText("\n\n".join(lines) +
                               ("" if ok or ui.txt_settings_smtp_password.text() == company_settings.EMAIL_SMTP_PASSWORD
                                else "\n\nLembre de clicar em Save depois de corrigir."))
        box.setStandardButtons(QMessageBox.StandardButton.Ok)
        box.exec()
        return steps
