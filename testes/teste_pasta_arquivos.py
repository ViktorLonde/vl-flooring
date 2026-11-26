"""Testa a pasta de arquivos (arquivos.py): detectar Google Drive, criar as
subpastas, gravar/resolver caminhos "files:" e mover arquivos antigos
atualizando o banco (banco falso em memória — o banco real não é tocado).
Também abre o app para conferir o bloco "Files folder" em Settings → System."""
import sys, os, tempfile, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); os.chdir(ROOT)
import arquivos

ok = True


def check(name, cond, extra=""):
    global ok
    ok &= bool(cond)
    print(("PASS " if cond else "FAIL ") + name, extra, flush=True)


class FakeCursor:
    def __init__(self, db):
        self.db, self.rows = db, []

    def execute(self, sql, params=()):
        s = " ".join(sql.split())
        if s.startswith("SELECT"):
            table = s.split(" FROM ")[1].split()[0]
            col = s.split("SELECT ID, ")[1].split(" FROM")[0]
            self.rows = [(i, r[col]) for i, r in self.db.get(table, {}).items() if r.get(col)]
        elif s.startswith("UPDATE"):
            table = s.split()[1]
            col = s.split(" SET ")[1].split("=")[0]
            self.db[table][params[1]][col] = params[0]

    def fetchall(self):
        return self.rows

    def close(self):
        pass


class FakeConn:
    def __init__(self, db):
        self.db = db

    def cursor(self):
        return FakeCursor(self.db)

    def commit(self):
        pass


tmp = tempfile.mkdtemp()
saved = (arquivos.PROJECT_DIR, arquivos.CONFIG_FILE, arquivos.LOCAL_FALLBACK, dict(arquivos.LEGACY_DIRS),
         arquivos.find_google_drive, arquivos.DEFAULT_PARENT)
try:
    app_dir = os.path.join(tmp, "app")
    os.makedirs(app_dir)
    arquivos.PROJECT_DIR = app_dir
    arquivos.CONFIG_FILE = os.path.join(app_dir, "files_location.json")
    arquivos.LOCAL_FALLBACK = os.path.join(app_dir, "Files")
    docs = os.path.join(tmp, "Documents")
    arquivos.DEFAULT_PARENT = docs
    arquivos.find_google_drive = lambda: None
    arquivos.LEGACY_DIRS.clear()
    arquivos.LEGACY_DIRS.update({os.path.join(app_dir, "job_photos"): "photos",
                                 os.path.join(app_dir, "receipts_received"): "receipts"})

    # pasta antiga D:\VL_Flooring\Files (usada em 25/11) com um invoice e uma foto "files:"
    old_root = arquivos.LOCAL_FALLBACK
    arquivos.set_root(old_root)
    check("chosen old local folder in use", arquivos.files_root() == old_root, arquivos.files_root())
    arquivos.ensure_structure()
    check("subfolders created", all(os.path.isdir(os.path.join(old_root, s)) for s in arquivos.SUBFOLDERS.values()))
    os.makedirs(os.path.join(app_dir, "job_photos", "JB-0041"))
    open(os.path.join(app_dir, "job_photos", "JB-0041", "Before_1.jpg"), "w").write("x")
    os.makedirs(os.path.join(app_dir, "receipts_received"))
    open(os.path.join(app_dir, "receipts_received", "21_scan.jpg"), "w").write("x")
    inv = os.path.join(arquivos.folder("invoices", "2026"), "Invoice_Carpet_One.pdf")
    open(inv, "w").write("x")
    new_photo = os.path.join(arquivos.folder("photos", "JB-0040"), "After_1.jpg")
    open(new_photo, "w").write("x")
    stored_new = arquivos.to_stored(new_photo)
    check("new photo stored relative to the files folder", stored_new == "files:Job Photos/JB-0040/After_1.jpg", stored_new)
    check("resolve gives the file back", os.path.exists(arquivos.resolve(stored_new)))
    check("legacy relative path still resolves",
          os.path.exists(arquivos.resolve(os.path.join("job_photos", "JB-0041", "Before_1.jpg"))))

    db = {
        "documents": {1: {"FILE_PATH": os.path.join("job_photos", "JB-0041", "Before_1.jpg")},
                      2: {"FILE_PATH": stored_new},
                      3: {"FILE_PATH": r"C:\somewhere\else\contract.pdf"}},
        "company_invoices": {7: {"PDF_PATH": inv}},
        "expenses": {9: {"RECEIPT_PATH": os.path.join(app_dir, "receipts_received", "21_scan.jpg")}},
    }

    # sem escolha → Documents\VL Flooring Files; move tudo para lá
    arquivos.set_root("")
    new_root = arquivos.files_root()
    check("default is Documents/VL Flooring Files", new_root == os.path.join(docs, arquivos.ROOT_NAME), new_root)
    check("not reported as Google Drive", not arquivos.using_google_drive())
    check("pending files detected", arquivos.pending_moves() == 4, arquivos.pending_moves())
    files, rows = arquivos.move_everything(FakeConn(db), old_root=old_root)
    check("all 4 files moved", files == 4, files)
    check("old folders removed", not os.path.exists(os.path.join(app_dir, "job_photos"))
          and not os.path.exists(old_root))
    p1 = db["documents"][1]["FILE_PATH"]
    check("legacy photo now in Documents", p1 == "files:Job Photos/JB-0041/Before_1.jpg" and os.path.exists(arquivos.resolve(p1)), p1)
    check("files: path unchanged and still valid", db["documents"][2]["FILE_PATH"] == stored_new
          and os.path.exists(arquivos.resolve(stored_new)))
    check("outside file untouched", db["documents"][3]["FILE_PATH"] == r"C:\somewhere\else\contract.pdf")
    pdf = db["company_invoices"][7]["PDF_PATH"]
    check("invoice PDF path updated", pdf == os.path.join(new_root, "Invoices", "2026", "Invoice_Carpet_One.pdf")
          and os.path.exists(pdf), pdf)
    rec = db["expenses"][9]["RECEIPT_PATH"]
    check("expense receipt path updated", os.path.exists(rec) and arquivos.is_inside(rec), rec)
    check("nothing left to move", arquivos.pending_moves() == 0, arquivos.pending_moves())

    # Google Drive "My Drive" reconhecido
    drive = os.path.join(tmp, "G", "My Drive")
    check("My Drive path counts as Google Drive", arquivos.using_google_drive(os.path.join(drive, arquivos.ROOT_NAME)))

    # escolha manual da pasta
    custom = os.path.join(tmp, "Other", arquivos.ROOT_NAME)
    os.makedirs(os.path.dirname(custom))
    arquivos.set_root(custom)
    check("chosen folder wins", arquivos.files_root() == custom)
finally:
    (arquivos.PROJECT_DIR, arquivos.CONFIG_FILE, arquivos.LOCAL_FALLBACK, legacy, arquivos.find_google_drive,
     arquivos.DEFAULT_PARENT) = saved
    arquivos.LEGACY_DIRS.clear(); arquivos.LEGACY_DIRS.update(legacy)
    shutil.rmtree(tmp, ignore_errors=True)

# ── app: bloco Files folder em Settings → System ──
from PySide6.QtWidgets import QApplication, QMessageBox, QLabel
QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.No)
import app as appmod
from paginas.visual import install_icon_theme
from paginas.moderno import install_modern_ui
a = QApplication(sys.argv)
install_icon_theme(a); install_modern_ui(a)
appmod.start_session()
main, login = appmod._session["main"], appmod._session["login"]
login.login_successful.emit("viktorlonde"); a.processEvents()
tabs = main.ui.tabs_settings
system = tabs.widget(tabs.count() - 1)
boxes = [l.text() for l in system.findChildren(QLabel) if l.text() in ('Files folder', 'Database backup')]
check("Settings → System has 'Files folder'", "Files folder" in boxes, boxes)
check("label shows the current folder", arquivos.files_root() == main._txt_files_root.text())
tabs.setCurrentIndex(tabs.count() - 1); main.resize(1400, 800); main.show(); a.processEvents()
system.grab().save(os.path.join(os.environ.get('TEMP', '.'), 'system_tab.png'))
check("files folder exists after start", os.path.isdir(os.path.join(arquivos.files_root(), "Invoices")))
main._closing_for_sign_out = True; main.close(); login.close()
print("RESULT:", "ALL OK" if ok else "FAILED", flush=True)
sys.exit(0 if ok else 1)
