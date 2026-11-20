"""Testa o diagnóstico do botão "Send test e-mail" com um servidor falso
(não conecta em nada, não usa senha de verdade) e o botão em Settings."""
import sys, os, smtplib, traceback
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); os.chdir(ROOT)
from paginas.email_teste import smtp_diagnose

ok = True


def check(name, cond, extra=""):
    global ok
    ok &= bool(cond)
    print(("PASS " if cond else "FAIL ") + name, extra, flush=True)


class FakeSMTP:
    mode = "ok"
    sent = []

    def __init__(self, host, port, timeout=None, context=None):
        if FakeSMTP.mode == "noconnect":
            raise OSError("no route")

    def ehlo(self):
        return (250, b"ok")

    def starttls(self, context=None):
        return (220, b"ok")

    def login(self, user, password):
        if FakeSMTP.mode == "disconnect":
            raise smtplib.SMTPServerDisconnected("Connection unexpectedly closed")
        if FakeSMTP.mode == "auth":
            raise smtplib.SMTPAuthenticationError(535, b"Username and Password not accepted")

    def send_message(self, m):
        FakeSMTP.sent.append(m["To"])

    def quit(self):
        pass


class FakeModule:
    SMTP = FakeSMTP
    SMTP_SSL = FakeSMTP


try:
    args = ("smtp.example.com", 587, "me@example.com", "abcdefghijklmnop", "me@example.com")
    FakeSMTP.mode = "ok"
    steps = smtp_diagnose(*args, smtp_module=FakeModule)
    check("all steps pass and the test e-mail is sent", all(s[1] for s in steps) and FakeSMTP.sent == ["me@example.com"],
          [s[0] for s in steps])
    FakeSMTP.mode = "disconnect"
    steps = smtp_diagnose(*args, smtp_module=FakeModule)
    check("closed connection at login explains the App Password", steps[-1][0] == "Login" and not steps[-1][1]
          and "App Password" in steps[-1][2], steps[-1])
    FakeSMTP.mode = "auth"
    steps = smtp_diagnose(*args, smtp_module=FakeModule)
    check("rejected password explains the App Password", not steps[-1][1] and "535" in steps[-1][2], steps[-1][2][:60])
    FakeSMTP.mode = "noconnect"
    steps = smtp_diagnose(*args, smtp_module=FakeModule)
    check("no connection points to server/port", steps[-1][0].startswith("Connect") and not steps[-1][1])
    steps = smtp_diagnose("smtp.example.com", 587, "me@example.com", "your-app-password", "x", smtp_module=FakeModule)
    check("placeholder password is caught before connecting", steps == [steps[0]] and steps[0][0] == "Password")

    from PySide6.QtWidgets import QApplication
    import app as appmod
    from main_ import MainWindow
    a = QApplication(sys.argv)
    w = MainWindow(db_config=appmod.DB_CONFIG)
    check("test button in Settings → Email", hasattr(w.ui, "btn_send_test_email"))
    w._job_form_dirty = False
except Exception:
    traceback.print_exc(); ok = False
print("RESULT:", "ALL OK" if ok else "FAILED", flush=True)
sys.exit(0 if ok else 1)
