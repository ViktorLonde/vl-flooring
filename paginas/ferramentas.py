# -*- coding: utf-8 -*-
"""
Ferramentas novas:

• Material Calculator — área (SF) + perda (%) → quantas caixas/baldes de
  cada produto e o custo; pode lançar direto nos materiais do job aberto.
• Job Photos — fotos de antes / durante / depois por Job Code. As fotos são
  copiadas (reduzidas) para job_photos/<JOB CODE>/ dentro da pasta do app
  (fica no disco D:, visível nos dois computadores) e registradas na tabela
  documents (ENTITY_TYPE = 'JOB_PROJECT').
• Mileage — registro de milhas rodadas, total do ano e valor estimado de
  dedução (taxa por milha ajustável — confira a taxa do IRS do ano).
• Estimates — orçamento com serviços e materiais, PDF com a marca da
  empresa e "Convert to Job" (cria o Job Code, o primeiro dia e os
  materiais).

Métodos da MainWindow (mixin) — veja main_.py.
"""

import math
import os
import shutil
from datetime import timedelta

from PySide6.QtCore import QSettings
from PySide6.QtGui import QImage, QIcon
from PySide6.QtWidgets import QInputDialog, QListWidget, QListWidgetItem

from app_common import *  # noqa: F401,F403
from paginas.visual import tabler_icon
from paginas.moderno import show_toast

PHOTOS_DIR = os.path.join(PROJECT_DIR, "job_photos")
PHOTO_CATEGORIES = ["Before", "Progress", "After"]
ESTIMATE_STATUSES = ["DRAFT", "SENT", "APPROVED", "DECLINED", "CONVERTED"]
DEFAULT_MILEAGE_RATE = 0.70  # US$ por milha — confira a taxa do IRS do ano em Mileage

_SMALL_BTN = ("QPushButton { background-color: #EEF2F7; color: #37474F; border: 1px solid #D0D7DE; "
              "border-radius: 6px; padding: 6px 12px; font-size: 12px; font-weight: 600; } "
              "QPushButton:hover { background-color: #E1E8F0; }")
_PRIMARY_BTN = ("QPushButton { background-color: #1565C0; color: #FFFFFF; border: none; border-radius: 6px; "
                "padding: 8px 16px; font-weight: 700; } QPushButton:hover { background-color: #1E88E5; }")


def _money(v):
    return f"${float(v or 0):,.2f}"


class ToolsMixin:
    def _setup_tools(self):
        """Botões escondidos que os cartões da página Registrations acionam,
        e os botões Photos / Calculator no formulário de Job."""
        ui = self.ui
        for attr, handler in (("btn_tool_estimates", self.open_estimates_dialog),
                              ("btn_tool_calculator", lambda: self.open_material_calculator_dialog()),
                              ("btn_tool_mileage", self.open_mileage_dialog)):
            btn = QPushButton()
            btn.setObjectName(attr)
            btn.clicked.connect(handler)
            setattr(ui, attr, btn)

        photos = QPushButton("  Photos")
        photos.setObjectName("btn_job_photos")
        photos.setIcon(tabler_icon("folder-open", "#37474F", 16))
        photos.setCursor(Qt.CursorShape.PointingHandCursor)
        photos.setToolTip("Before / progress / after photos of this Job Code")
        photos.setStyleSheet(_SMALL_BTN)
        photos.clicked.connect(self.open_job_photos_dialog)
        header = ui.hboxLayout
        header.insertWidget(header.indexOf(getattr(self, "_btn_duplicate_job", ui.btn_job_go_to_expense)) + 1, photos)
        ui.btn_job_photos = photos

        calc = QPushButton("  Calculator")
        calc.setObjectName("btn_material_calculator")
        calc.setIcon(tabler_icon("calculator", "#37474F", 16))
        calc.setCursor(Qt.CursorShape.PointingHandCursor)
        calc.setToolTip("How many boxes / buckets for an area")
        calc.setStyleSheet(_SMALL_BTN)
        calc.clicked.connect(lambda: self.open_material_calculator_dialog(from_job=True))
        if hasattr(ui, "hboxLayout4"):
            ui.hboxLayout4.addWidget(calc)  # cabeçalho do quadro "Materials Used"

    def _current_project(self):
        code = self.ui.cmb_job_code.currentText().strip().upper()
        return code, self._job_code_to_id.get(code)

    def _products(self):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT ID, TYPE, NAME, BRAND, PRICE, UNIT, COVERAGE_QTY, COVERAGE_UNIT FROM products ORDER BY TYPE, NAME")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows

    # ══ calculadora de material ══════════════════════════════════════
    def open_material_calculator_dialog(self, from_job=False):
        try:
            products = self._products()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not load products:\n{e}")
            return
        by_id = {p[0]: p for p in products}
        code, project_id = self._current_project() if from_job else ("", None)

        dialog = QDialog(self)
        dialog.setWindowTitle("Material Calculator")
        dialog.resize(820, 520)
        layout = QVBoxLayout(dialog)
        top = QHBoxLayout()
        top.addWidget(QLabel("Area (SF):"))
        spin_area = QDoubleSpinBox()
        spin_area.setRange(0, 1_000_000)
        spin_area.setDecimals(0)
        spin_area.setGroupSeparatorShown(True)
        spin_area.setValue(1000)
        top.addWidget(spin_area)
        top.addSpacing(16)
        top.addWidget(QLabel("Waste (%):"))
        spin_waste = QDoubleSpinBox()
        spin_waste.setRange(0, 50)
        spin_waste.setDecimals(0)
        spin_waste.setValue(10)
        top.addWidget(spin_waste)
        top.addStretch(1)
        layout.addLayout(top)
        layout.addWidget(QLabel("Pick the products — the coverage comes from Products (e.g. SF per box)."))

        table = QTableWidget(0, 6)
        table.setHorizontalHeaderLabels(["Product", "Covers", "Needed", "Unit price", "Cost", ""])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col, width in ((1, 150), (2, 110), (3, 100), (4, 110), (5, 44)):
            table.setColumnWidth(col, width)
        table.verticalHeader().setVisible(False)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        table.setStyleSheet("QComboBox { min-height: 20px; padding: 4px 8px; margin: 4px; }")
        layout.addWidget(table, 1)
        lbl_total = QLabel()
        lbl_total.setStyleSheet("font-size:15px; font-weight:700;")
        layout.addWidget(lbl_total)
        results = {}

        def recalc():
            area = spin_area.value() * (1 + spin_waste.value() / 100)
            total = 0.0
            results.clear()
            missing = []
            for r in range(table.rowCount()):
                pid = table.cellWidget(r, 0).currentData()
                p = by_id.get(pid)
                if not p:
                    for c in range(1, 5):
                        table.setItem(r, c, QTableWidgetItem(""))
                    continue
                _id, _t, name, _b, price, unit, cov, cov_unit = p
                price, cov = float(price or 0), float(cov or 0)
                if cov <= 0:
                    needed, covers = None, "set coverage in Products"
                    missing.append(name)
                else:
                    needed = math.ceil(area / cov)
                    covers = f"{cov:g} {cov_unit or 'SF'} / {unit or 'unit'}"
                cost = (needed or 0) * price
                total += cost
                results[r] = (pid, needed, price)
                for c, text in enumerate([covers, f"{needed} {unit or ''}" if needed else "—",
                                          _money(price) if price else "no price", _money(cost)], start=1):
                    table.setItem(r, c, QTableWidgetItem(text))
            lbl_total.setText(f"Area with waste: {area:,.0f} SF   ·   Estimated material cost: {_money(total)}")

        def add_row(product_id=None):
            r = table.rowCount()
            table.insertRow(r)
            combo = QComboBox()
            combo.addItem("— Select a product —", None)
            for pid, ptype, name, brand, price, unit, cov, cov_unit in products:
                combo.addItem(f"{name}" + (f" ({brand})" if brand else "") + f"  ·  {ptype or ''}", pid)
            idx = combo.findData(product_id)
            combo.setCurrentIndex(idx if idx >= 0 else 0)
            combo.currentIndexChanged.connect(lambda *_a: recalc())
            remove = QPushButton()
            remove.setIcon(tabler_icon("x", "#C62828", 16))

            def do_remove():
                for row in range(table.rowCount()):
                    if table.cellWidget(row, 5) is remove:
                        table.removeRow(row)
                        break
                recalc()
            remove.clicked.connect(do_remove)
            table.setCellWidget(r, 0, combo)
            table.setCellWidget(r, 5, remove)
            table.setRowHeight(r, 48)
            recalc()

        # começa com o piso e o adesivo mais comuns (os que têm cobertura)
        def first_with_area(ptype):
            return next((p[0] for p in products if p[1] == ptype and float(p[6] or 0) > 0
                         and (p[7] or "SF").upper().startswith("SF")), None)
        starters = [pid for pid in (first_with_area("Flooring"), first_with_area("Adhesive")) if pid]
        for pid in starters or [None]:
            add_row(pid)
        spin_area.valueChanged.connect(lambda *_a: recalc())
        spin_waste.valueChanged.connect(lambda *_a: recalc())

        row = QHBoxLayout()
        btn_add = QPushButton("  Add product")
        btn_add.setIcon(tabler_icon("plus", "#37474F", 16))
        btn_add.clicked.connect(lambda: add_row())
        row.addWidget(btn_add)
        row.addStretch(1)
        btn_to_job = QPushButton(f"  Add to {code} materials" if project_id else "  Add to job materials")
        btn_to_job.setObjectName("btn_add_calc_to_job")
        btn_to_job.setIcon(tabler_icon("check", "#FFFFFF", 16))
        btn_to_job.setStyleSheet(_PRIMARY_BTN)
        btn_to_job.setVisible(bool(project_id))
        btn_close = QPushButton("Close")
        row.addWidget(btn_to_job)
        row.addWidget(btn_close)
        layout.addLayout(row)
        btn_close.clicked.connect(dialog.reject)

        def add_to_job():
            lines = [v for v in results.values() if v[1]]
            if not lines:
                QMessageBox.information(dialog, "Nothing to add", "Pick at least one product with coverage.")
                return
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                for pid, qty, price in lines:
                    cur.execute("INSERT INTO job_materials (JOB_PROJECT_ID, PRODUCT_ID, QUANTITY, UNIT_PRICE) "
                                "VALUES (%s, %s, %s, %s)", (project_id, pid, qty, price))
                conn.commit()
                cur.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not add the materials:\n{e}")
                return
            dialog.accept()
            if hasattr(self, "_load_job_materials"):
                self._load_job_materials()
            show_toast(f"{len(lines)} material line(s) added to {code}.", "success", self)

        btn_to_job.clicked.connect(add_to_job)
        dialog.exec()

    # ══ fotos do job ═════════════════════════════════════════════════
    def _photo_rows(self, project_id):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT ID, CATEGORY, NAME, FILE_PATH, UPLOADED_AT FROM documents "
                    "WHERE ENTITY_TYPE = 'JOB_PROJECT' AND ENTITY_ID = %s AND CATEGORY LIKE 'Job Photo%%' "
                    "ORDER BY UPLOADED_AT, ID", (project_id,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows

    @staticmethod
    def _photo_abs_path(path):
        return path if os.path.isabs(path) else os.path.join(PROJECT_DIR, path)

    def open_job_photos_dialog(self):
        code, project_id = self._current_project()
        if not project_id:
            QMessageBox.information(self, "Choose a job", "Open a job with a Job Code first, then click Photos.")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Photos — {code}")
        dialog.resize(900, 620)
        layout = QVBoxLayout(dialog)
        top = QHBoxLayout()
        top.addWidget(QLabel("Show:"))
        cmb_filter = QComboBox()
        cmb_filter.addItems(["All"] + PHOTO_CATEGORIES)
        top.addWidget(cmb_filter)
        top.addStretch(1)
        top.addWidget(QLabel("Add as:"))
        cmb_cat = QComboBox()
        cmb_cat.addItems(PHOTO_CATEGORIES)
        top.addWidget(cmb_cat)
        btn_add = QPushButton("  Add photos…")
        btn_add.setIcon(tabler_icon("upload", "#FFFFFF", 16))
        btn_add.setStyleSheet(_PRIMARY_BTN)
        top.addWidget(btn_add)
        layout.addLayout(top)

        grid = QListWidget()
        grid.setViewMode(QListWidget.ViewMode.IconMode)
        grid.setIconSize(QSize(200, 150))
        grid.setGridSize(QSize(220, 190))
        grid.setResizeMode(QListWidget.ResizeMode.Adjust)
        grid.setMovement(QListWidget.Movement.Static)
        grid.setSpacing(8)
        grid.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        layout.addWidget(grid, 1)
        bottom = QHBoxLayout()
        lbl_info = QLabel("Double-click a photo to open it.")
        lbl_info.setStyleSheet("color:#6B7C93;")
        bottom.addWidget(lbl_info)
        bottom.addStretch(1)
        btn_folder = QPushButton("  Open folder")
        btn_folder.setIcon(tabler_icon("folder", "#37474F", 16))
        btn_remove = QPushButton("  Remove selected")
        btn_remove.setIcon(tabler_icon("trash", "#C62828", 16))
        btn_close = QPushButton("Close")
        for b in (btn_folder, btn_remove, btn_close):
            bottom.addWidget(b)
        layout.addLayout(bottom)

        def reload():
            grid.clear()
            try:
                rows = self._photo_rows(project_id)
            except (MySQLError, RuntimeError) as e:
                lbl_info.setText(f"Could not load photos: {e}")
                return
            wanted = cmb_filter.currentText()
            shown = 0
            for did, category, name, path, uploaded in rows:
                cat = (category or "").replace("Job Photo - ", "")
                if wanted != "All" and cat != wanted:
                    continue
                full = self._photo_abs_path(path or "")
                pix = QPixmap(full)
                icon = QIcon(pix.scaled(200, 150, Qt.AspectRatioMode.KeepAspectRatio,
                                        Qt.TransformationMode.SmoothTransformation)) if not pix.isNull() \
                    else tabler_icon("x", "#C62828", 48)
                when = uploaded.strftime("%m/%d/%Y") if uploaded else ""
                item = QListWidgetItem(icon, f"{cat} · {when}")
                item.setData(Qt.ItemDataRole.UserRole, (did, full))
                item.setToolTip(name or "")
                grid.addItem(item)
                shown += 1
            lbl_info.setText(f"{shown} photo(s). Double-click a photo to open it.")
            self._refresh_photos_button()

        def add_photos():
            files, _ = QFileDialog.getOpenFileNames(dialog, "Choose photos", os.path.expanduser("~"),
                                                    "Images (*.jpg *.jpeg *.png *.heic *.webp *.bmp)")
            if not files:
                return
            folder = os.path.join(PHOTOS_DIR, code)
            os.makedirs(folder, exist_ok=True)
            category = cmb_cat.currentText()
            added, failed = 0, []
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                for i, src in enumerate(files):
                    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    target = os.path.join(folder, f"{category}_{stamp}_{i + 1}.jpg")
                    img = QImage(src)
                    if img.isNull():
                        # formato que o Qt não lê (ex.: HEIC): guarda o arquivo como veio
                        target = os.path.join(folder, f"{category}_{stamp}_{i + 1}{os.path.splitext(src)[1].lower()}")
                        try:
                            shutil.copy2(src, target)
                        except OSError as e:
                            failed.append(f"{os.path.basename(src)}: {e}")
                            continue
                    else:
                        if max(img.width(), img.height()) > 2000:  # economiza espaço no disco D:
                            img = img.scaled(2000, 2000, Qt.AspectRatioMode.KeepAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation)
                        if not img.save(target, "JPG", 85):
                            failed.append(os.path.basename(src))
                            continue
                    rel = os.path.relpath(target, PROJECT_DIR)
                    cur.execute("INSERT INTO documents (CATEGORY, ENTITY_TYPE, ENTITY_ID, NAME, FILE_PATH, NOTES) "
                                "VALUES (%s, 'JOB_PROJECT', %s, %s, %s, %s)",
                                (f"Job Photo - {category}", project_id, os.path.basename(src), rel, ""))
                    added += 1
                conn.commit()
                cur.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                failed.append(str(e))
            finally:
                QApplication.restoreOverrideCursor()
            reload()
            if failed:
                QMessageBox.warning(dialog, "Some photos were not added", "\n".join(failed[:8]))
            elif added:
                show_toast(f"{added} photo(s) added to {code} ({category}).", "success", self)

        def open_photo(item):
            _did, full = item.data(Qt.ItemDataRole.UserRole)
            if os.path.exists(full):
                QDesktopServices.openUrl(QUrl.fromLocalFile(full))
            else:
                QMessageBox.information(dialog, "Not found", f"The file was not found:\n{full}")

        def remove_selected():
            items = grid.selectedItems()
            if not items:
                return
            answer = QMessageBox.question(dialog, "Remove photos",
                                          f"Remove {len(items)} photo(s) from {code}? The files are deleted too.",
                                          QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                          QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                return
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                for item in items:
                    did, full = item.data(Qt.ItemDataRole.UserRole)
                    cur.execute("DELETE FROM documents WHERE ID = %s", (did,))
                    if full.startswith(PHOTOS_DIR) and os.path.exists(full):
                        os.remove(full)
                conn.commit()
                cur.close()
                conn.close()
            except (MySQLError, RuntimeError, OSError) as e:
                QMessageBox.critical(dialog, "Error", f"Could not remove:\n{e}")
            reload()

        def open_folder():
            folder = os.path.join(PHOTOS_DIR, code)
            os.makedirs(folder, exist_ok=True)
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

        cmb_filter.currentIndexChanged.connect(lambda *_a: reload())
        btn_add.clicked.connect(add_photos)
        grid.itemDoubleClicked.connect(open_photo)
        btn_remove.clicked.connect(remove_selected)
        btn_folder.clicked.connect(open_folder)
        btn_close.clicked.connect(dialog.accept)
        reload()
        dialog.exec()

    def _refresh_photos_button(self):
        btn = getattr(self.ui, "btn_job_photos", None)
        if btn is None:
            return
        _code, project_id = self._current_project()
        n = 0
        if project_id:
            try:
                n = len(self._photo_rows(project_id))
            except (MySQLError, RuntimeError):
                n = 0
        btn.setText(f"  Photos ({n})" if n else "  Photos")

    # ══ quilometragem ════════════════════════════════════════════════
    def open_mileage_dialog(self):
        settings = QSettings("VL Flooring", "app")
        dialog = QDialog(self)
        dialog.setWindowTitle("Mileage log")
        dialog.resize(940, 640)
        layout = QVBoxLayout(dialog)

        top = QHBoxLayout()
        top.addWidget(QLabel("Year:"))
        cmb_year = QComboBox()
        this_year = date.today().year
        for y in range(this_year, this_year - 6, -1):
            cmb_year.addItem(str(y), y)
        top.addWidget(cmb_year)
        top.addSpacing(16)
        top.addWidget(QLabel("Rate per mile:"))
        spin_rate = QDoubleSpinBox()
        spin_rate.setRange(0, 5)
        spin_rate.setDecimals(3)
        spin_rate.setPrefix("$ ")
        spin_rate.setValue(settings.value("mileage/rate", DEFAULT_MILEAGE_RATE, type=float))
        spin_rate.setToolTip("Standard mileage rate of the IRS for the year — check irs.gov and adjust")
        top.addWidget(spin_rate)
        top.addStretch(1)
        btn_excel = QPushButton("  Excel")
        btn_excel.setIcon(tabler_icon("download", "#37474F", 16))
        top.addWidget(btn_excel)
        layout.addLayout(top)
        lbl_summary = QLabel()
        lbl_summary.setStyleSheet("font-size:15px; font-weight:700;")
        layout.addWidget(lbl_summary)

        form = QHBoxLayout()
        d_trip = QDateEdit()
        d_trip.setCalendarPopup(True)
        d_trip.setDisplayFormat("MM/dd/yyyy")
        d_trip.setDate(QDate.currentDate())
        d_trip.setMinimumWidth(130)
        s_miles = QDoubleSpinBox()
        s_miles.setRange(0, 5000)
        s_miles.setDecimals(1)
        s_miles.setSuffix(" mi")
        t_purpose = QLineEdit()
        t_purpose.setPlaceholderText("Purpose (e.g. job site, supplier)")
        t_from = QLineEdit()
        t_from.setPlaceholderText("From")
        t_to = QLineEdit()
        t_to.setPlaceholderText("To")
        cmb_code = QComboBox()
        cmb_code.addItem("— Job Code —", None)
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT ID, CODE FROM job_projects WHERE CODE IS NOT NULL ORDER BY ID DESC")
            for pid, c in cur.fetchall():
                cmb_code.addItem(c, pid)
            cur.close()
            conn.close()
        except (MySQLError, RuntimeError):
            pass
        btn_add = QPushButton("  Add trip")
        btn_add.setObjectName("btn_add_mileage")
        btn_add.setIcon(tabler_icon("plus", "#FFFFFF", 16))
        btn_add.setStyleSheet(_PRIMARY_BTN)
        for w, stretch in ((d_trip, 0), (s_miles, 0), (t_purpose, 2), (t_from, 1), (t_to, 1), (cmb_code, 1), (btn_add, 0)):
            form.addWidget(w, stretch)
        layout.addLayout(form)

        table = QTableWidget(0, 6)
        table.setHorizontalHeaderLabels(["Date", "Miles", "Purpose", "From", "To", "Job Code"])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(table, 1)
        bottom = QHBoxLayout()
        note = QLabel("Keep a log of business trips (job sites, suppliers). Commuting from home to a regular "
                      "office usually does not count — ask your accountant.")
        note.setWordWrap(True)
        note.setStyleSheet("color:#6B7C93; font-size:11px;")
        bottom.addWidget(note, 1)
        btn_delete = QPushButton("  Delete selected")
        btn_delete.setIcon(tabler_icon("trash", "#C62828", 16))
        btn_close = QPushButton("Close")
        bottom.addWidget(btn_delete)
        bottom.addWidget(btn_close)
        layout.addLayout(bottom)

        def reload():
            year = cmb_year.currentData()
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                cur.execute("""SELECT m.ID, m.TRIP_DATE, m.MILES, m.PURPOSE, m.FROM_PLACE, m.TO_PLACE, jp.CODE
                               FROM mileage m LEFT JOIN job_projects jp ON jp.ID = m.JOB_PROJECT_ID
                               WHERE YEAR(m.TRIP_DATE) = %s ORDER BY m.TRIP_DATE DESC, m.ID DESC""", (year,))
                rows = cur.fetchall()
                cur.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                lbl_summary.setText(f"Could not load the log: {e}")
                return
            table.setRowCount(len(rows))
            total = 0.0
            for r, (mid, d, miles, purpose, f, t, c) in enumerate(rows):
                total += float(miles or 0)
                for col, text in enumerate([d.strftime("%m/%d/%Y") if d else "", f"{float(miles or 0):,.1f}",
                                            purpose or "", f or "", t or "", c or ""]):
                    item = QTableWidgetItem(text)
                    if col == 0:
                        item.setData(Qt.ItemDataRole.UserRole, mid)
                    table.setItem(r, col, item)
            rate = spin_rate.value()
            lbl_summary.setText(f"{year}: {len(rows)} trip(s) · {total:,.1f} miles × ${rate:.3f} = "
                                f"{_money(total * rate)} estimated deduction")

        def add_trip():
            if s_miles.value() <= 0:
                QMessageBox.information(dialog, "Miles", "Enter the miles of the trip.")
                return
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                cur.execute("INSERT INTO mileage (TRIP_DATE, MILES, PURPOSE, FROM_PLACE, TO_PLACE, JOB_PROJECT_ID) "
                            "VALUES (%s, %s, %s, %s, %s, %s)",
                            (d_trip.date().toPython(), s_miles.value(), t_purpose.text().strip() or None,
                             t_from.text().strip() or None, t_to.text().strip() or None, cmb_code.currentData()))
                conn.commit()
                cur.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not save the trip:\n{e}")
                return
            s_miles.setValue(0)
            t_purpose.clear()
            idx = cmb_year.findData(d_trip.date().year())
            if idx >= 0:
                cmb_year.setCurrentIndex(idx)
            reload()

        def delete_selected():
            ids = sorted({table.item(i.row(), 0).data(Qt.ItemDataRole.UserRole) for i in table.selectedIndexes()})
            if not ids:
                return
            answer = QMessageBox.question(dialog, "Delete trips", f"Delete {len(ids)} trip(s)?",
                                          QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                          QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                return
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                cur.execute(f"DELETE FROM mileage WHERE ID IN ({','.join(['%s'] * len(ids))})", ids)
                conn.commit()
                cur.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", str(e))
            reload()

        def save_rate():
            settings.setValue("mileage/rate", spin_rate.value())
            reload()

        cmb_year.currentIndexChanged.connect(lambda *_a: reload())
        spin_rate.valueChanged.connect(lambda *_a: save_rate())
        btn_add.clicked.connect(add_trip)
        btn_delete.clicked.connect(delete_selected)
        btn_close.clicked.connect(dialog.accept)
        btn_excel.clicked.connect(lambda: self._export_table_to_excel(table, f"Mileage_{cmb_year.currentData()}.xlsx"))
        reload()
        dialog.exec()

    # ══ orçamentos ═══════════════════════════════════════════════════
    def open_estimates_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Estimates")
        dialog.resize(900, 560)
        layout = QVBoxLayout(dialog)
        top = QHBoxLayout()
        txt_search = QLineEdit()
        txt_search.setPlaceholderText("Search client, address or estimate number…")
        cmb_status = QComboBox()
        cmb_status.addItem("All statuses", None)
        for s in ESTIMATE_STATUSES:
            cmb_status.addItem(s.title(), s)
        btn_new = QPushButton("  New estimate")
        btn_new.setObjectName("btn_new_estimate")
        btn_new.setIcon(tabler_icon("plus", "#FFFFFF", 16))
        btn_new.setStyleSheet(_PRIMARY_BTN)
        top.addWidget(txt_search, 1)
        top.addWidget(cmb_status)
        top.addWidget(btn_new)
        layout.addLayout(top)
        table = QTableWidget(0, 6)
        table.setHorizontalHeaderLabels(["Estimate", "Date", "Client", "Address", "Total", "Status"])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(table, 1)
        hint = QLabel("Double-click an estimate to open it.")
        hint.setStyleSheet("color:#6B7C93;")
        layout.addWidget(hint)

        def reload():
            sql = "SELECT ID, CODE, CREATED_AT, CLIENT_NAME, JOB_ADDRESS, TOTAL, STATUS FROM estimates WHERE 1=1"
            params = []
            if txt_search.text().strip():
                like = f"%{txt_search.text().strip()}%"
                sql += " AND (CODE LIKE %s OR CLIENT_NAME LIKE %s OR JOB_ADDRESS LIKE %s)"
                params += [like, like, like]
            if cmb_status.currentData():
                sql += " AND STATUS = %s"
                params.append(cmb_status.currentData())
            sql += " ORDER BY ID DESC"
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                cur.execute(sql, params)
                rows = cur.fetchall()
                cur.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                hint.setText(f"Could not load estimates: {e}")
                return
            table.setRowCount(len(rows))
            for r, (eid, code, created, client, address, total, status) in enumerate(rows):
                for c, text in enumerate([code, created.strftime("%m/%d/%Y") if created else "", client or "",
                                          address or "", _money(total), (status or "").title()]):
                    item = QTableWidgetItem(text)
                    if c == 0:
                        item.setData(Qt.ItemDataRole.UserRole, eid)
                    table.setItem(r, c, item)

        def open_row(row, _col):
            self.open_estimate_editor(table.item(row, 0).data(Qt.ItemDataRole.UserRole), parent=dialog)
            reload()

        txt_search.textChanged.connect(lambda *_a: reload())
        cmb_status.currentIndexChanged.connect(lambda *_a: reload())
        btn_new.clicked.connect(lambda: (self.open_estimate_editor(None, parent=dialog), reload()))
        table.cellDoubleClicked.connect(open_row)
        reload()
        dialog.exec()

    def _next_code(self, cur, table, prefix):
        cur.execute(f"SELECT CODE FROM {table} WHERE CODE LIKE %s", (f"{prefix}-%",))
        n = 0
        for (code,) in cur.fetchall():
            try:
                n = max(n, int(code.split("-")[1]))
            except (IndexError, ValueError):
                continue
        return f"{prefix}-{n + 1:04d}"

    def open_estimate_editor(self, estimate_id=None, parent=None):
        try:
            products = self._products()
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT ID, FULL_NAME, EMAIL, PHONE_NUMBER FROM clients ORDER BY FULL_NAME")
            clients = cur.fetchall()
            cur.execute("SELECT ID, CATEGORY, NAME, UNIT FROM work_types ORDER BY CATEGORY, NAME")
            work_types = cur.fetchall()
            est, items = None, []
            if estimate_id:
                cur.execute("SELECT * FROM estimates WHERE ID=%s", (estimate_id,))
                est = cur.fetchone()
                cur.execute("SELECT * FROM estimate_items WHERE ESTIMATE_ID=%s ORDER BY ID", (estimate_id,))
                items = cur.fetchall()
            cur.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(self, "Database Error", f"Could not load the estimate:\n{e}")
            return
        state = {"id": estimate_id, "code": est["CODE"] if est else None}

        dialog = QDialog(parent or self)
        dialog.setWindowTitle(f"Estimate {state['code']}" if est else "New estimate")
        dialog.resize(980, 720)
        layout = QVBoxLayout(dialog)

        grid = QGridLayout()
        cmb_client = QComboBox()
        cmb_client.setEditable(True)
        cmb_client.addItem("", None)
        for c in clients:
            cmb_client.addItem(c["FULL_NAME"], c["ID"])
        txt_email, txt_phone = QLineEdit(), QLineEdit()
        txt_email.setPlaceholderText("client@email.com")
        txt_phone.setPlaceholderText("(941) 000-0000")
        txt_address, txt_city = QLineEdit(), QLineEdit()
        txt_address.setPlaceholderText("Job address")
        txt_city.setPlaceholderText("City")
        d_valid = QDateEdit()
        d_valid.setCalendarPopup(True)
        d_valid.setDisplayFormat("MM/dd/yyyy")
        cmb_status = QComboBox()
        cmb_status.addItems(ESTIMATE_STATUSES)
        for r, (label, w) in enumerate((("Client", cmb_client), ("E-mail", txt_email), ("Phone", txt_phone))):
            grid.addWidget(QLabel(label), r, 0)
            grid.addWidget(w, r, 1)
        for r, (label, w) in enumerate((("Address", txt_address), ("City", txt_city), ("Valid until", d_valid))):
            grid.addWidget(QLabel(label), r, 2)
            grid.addWidget(w, r, 3)
        grid.addWidget(QLabel("Status"), 3, 0)
        grid.addWidget(cmb_status, 3, 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        layout.addLayout(grid)

        def fill_client(*_a):
            cid = cmb_client.currentData()
            c = next((x for x in clients if x["ID"] == cid), None)
            if c:
                if not txt_email.text():
                    txt_email.setText(c["EMAIL"] or "")
                if not txt_phone.text():
                    txt_phone.setText(c["PHONE_NUMBER"] or "")
        cmb_client.currentIndexChanged.connect(fill_client)
        from paginas.padrao_texto import attach_title_case
        for _w in (cmb_client.lineEdit(), txt_address, txt_city):
            attach_title_case(_w)

        table = QTableWidget(0, 7)
        table.setHorizontalHeaderLabels(["Type", "Description", "Qty", "Unit", "Unit price", "Total", ""])
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for col, width in ((0, 90), (2, 120), (3, 90), (4, 130), (5, 110), (6, 44)):
            table.setColumnWidth(col, width)
        table.setStyleSheet("QLineEdit, QDoubleSpinBox { min-height: 20px; padding: 4px 8px; margin: 4px 3px; }")
        table.verticalHeader().setVisible(False)
        layout.addWidget(table, 1)
        lbl_total = QLabel()
        lbl_total.setStyleSheet("font-size:16px; font-weight:700;")
        layout.addWidget(lbl_total, 0, Qt.AlignmentFlag.AlignRight)
        txt_notes = QTextEdit()
        txt_notes.setPlaceholderText("Notes shown on the estimate (scope, what is not included, payment terms…)")
        txt_notes.setMaximumHeight(90)
        layout.addWidget(txt_notes)
        updating = {"on": False}

        def total():
            t = 0.0
            for r in range(table.rowCount()):
                t += table.cellWidget(r, 2).value() * table.cellWidget(r, 4).value()
            return round(t, 2)

        def recalc():
            for r in range(table.rowCount()):
                line = table.cellWidget(r, 2).value() * table.cellWidget(r, 4).value()
                table.setItem(r, 5, QTableWidgetItem(_money(line)))
            lbl_total.setText(f"Total: {_money(total())}")

        def add_line(kind="SERVICE", description="", qty=1.0, unit="", price=0.0, product_id=None):
            r = table.rowCount()
            table.insertRow(r)
            kind_item = QTableWidgetItem("Material" if kind == "MATERIAL" else "Service")
            kind_item.setData(Qt.ItemDataRole.UserRole, (kind, product_id))
            kind_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            table.setItem(r, 0, kind_item)
            txt = QLineEdit(description)
            s_qty = QDoubleSpinBox()
            s_qty.setRange(0, 1_000_000)
            s_qty.setDecimals(2)
            s_qty.setGroupSeparatorShown(True)
            s_qty.setValue(float(qty or 0))
            t_unit = QLineEdit(unit or "")
            s_price = QDoubleSpinBox()
            s_price.setRange(0, 1_000_000)
            s_price.setDecimals(2)
            s_price.setPrefix("$ ")
            s_price.setGroupSeparatorShown(True)
            s_price.setValue(float(price or 0))
            btn_rm = QPushButton()
            btn_rm.setIcon(tabler_icon("x", "#C62828", 16))

            def remove():
                for row in range(table.rowCount()):
                    if table.cellWidget(row, 6) is btn_rm:
                        table.removeRow(row)
                        break
                recalc()
            btn_rm.clicked.connect(remove)
            s_qty.valueChanged.connect(lambda *_a: recalc())
            s_price.valueChanged.connect(lambda *_a: recalc())
            for c, w in ((1, txt), (2, s_qty), (3, t_unit), (4, s_price), (6, btn_rm)):
                table.setCellWidget(r, c, w)
            table.setRowHeight(r, 50)
            recalc()

        line_row = QHBoxLayout()
        btn_service = QPushButton("  Add service")
        btn_service.setIcon(tabler_icon("tool", "#37474F", 16))
        btn_material = QPushButton("  Add material")
        btn_material.setIcon(tabler_icon("package", "#37474F", 16))
        btn_custom = QPushButton("  Add custom line")
        btn_custom.setIcon(tabler_icon("plus", "#37474F", 16))
        for b in (btn_service, btn_material, btn_custom):
            line_row.addWidget(b)
        line_row.addStretch(1)
        layout.insertLayout(layout.indexOf(table), line_row)

        def pick_service():
            names = [f"{w['CATEGORY'] or ''} — {w['NAME']}" for w in work_types]
            if not names:
                add_line()
                return
            choice, ok = QInputDialog.getItem(dialog, "Add service", "Work type:", names, 0, False)
            if ok:
                w = work_types[names.index(choice)]
                add_line("SERVICE", w["NAME"], 1, w["UNIT"] or "SF", 0)

        def pick_material():
            names = [f"{p[2]}" + (f" ({p[3]})" if p[3] else "") for p in products]
            if not names:
                return
            choice, ok = QInputDialog.getItem(dialog, "Add material", "Product:", names, 0, False)
            if ok:
                p = products[names.index(choice)]
                add_line("MATERIAL", choice, 1, p[5] or "", float(p[4] or 0), p[0])

        btn_service.clicked.connect(pick_service)
        btn_material.clicked.connect(pick_material)
        btn_custom.clicked.connect(lambda: add_line())

        # dados existentes
        if est:
            idx = cmb_client.findData(est["CLIENT_ID"]) if est["CLIENT_ID"] else -1
            if idx >= 0:
                cmb_client.setCurrentIndex(idx)
            else:
                cmb_client.setEditText(est["CLIENT_NAME"] or "")
            txt_email.setText(est["CLIENT_EMAIL"] or "")
            txt_phone.setText(est["CLIENT_PHONE"] or "")
            txt_address.setText(est["JOB_ADDRESS"] or "")
            txt_city.setText(est["CITY"] or "")
            vu = est["VALID_UNTIL"] or (date.today() + timedelta(days=30))
            d_valid.setDate(QDate(vu.year, vu.month, vu.day))
            cmb_status.setCurrentText(est["STATUS"] or "DRAFT")
            txt_notes.setPlainText(est["NOTES"] or "")
            for it in items:
                add_line(it["KIND"], it["DESCRIPTION"], it["QTY"], it["UNIT"], it["UNIT_PRICE"], it["PRODUCT_ID"])
        else:
            vu = date.today() + timedelta(days=30)
            d_valid.setDate(QDate(vu.year, vu.month, vu.day))
            add_line()
        recalc()

        buttons = QHBoxLayout()
        btn_pdf = QPushButton("  PDF")
        btn_pdf.setIcon(tabler_icon("download", "#37474F", 16))
        btn_convert = QPushButton("  Convert to Job")
        btn_convert.setObjectName("btn_convert_estimate")
        btn_convert.setIcon(tabler_icon("clipboard-list", "#37474F", 16))
        btn_save = QPushButton("  Save")
        btn_save.setObjectName("btn_save_estimate")
        btn_save.setIcon(tabler_icon("device-floppy", "#FFFFFF", 16))
        btn_save.setStyleSheet(_PRIMARY_BTN)
        btn_close = QPushButton("Close")
        btn_email = QPushButton("  Send by e-mail")
        btn_email.setObjectName("btn_email_estimate")
        btn_email.setIcon(tabler_icon("send", "#37474F", 16))
        btn_suggest = QPushButton("  Suggest prices")
        btn_suggest.setObjectName("btn_suggest_estimate_prices")
        btn_suggest.setIcon(tabler_icon("cash", "#37474F", 16))
        btn_suggest.setToolTip("Fill $0 services with your Service Rates or the average $/SF of past jobs")
        buttons.addWidget(btn_pdf)
        buttons.addWidget(btn_email)
        buttons.addWidget(btn_convert)
        buttons.addWidget(btn_suggest)
        buttons.addStretch(1)
        buttons.addWidget(btn_close)
        buttons.addWidget(btn_save)
        layout.addLayout(buttons)

        def collect_items():
            out = []
            for r in range(table.rowCount()):
                kind, product_id = table.item(r, 0).data(Qt.ItemDataRole.UserRole)
                desc = table.cellWidget(r, 1).text().strip()
                if not desc:
                    continue
                out.append((kind, desc, table.cellWidget(r, 2).value(), table.cellWidget(r, 3).text().strip(),
                            table.cellWidget(r, 4).value(), product_id))
            return out

        def save(silent=False):
            client_name = cmb_client.currentText().strip()
            if not client_name:
                QMessageBox.information(dialog, "Client", "Enter the client's name.")
                return False
            lines = collect_items()
            if not lines:
                QMessageBox.information(dialog, "Items", "Add at least one line with a description.")
                return False
            idx = cmb_client.findText(client_name)
            client_id = cmb_client.itemData(idx) if idx >= 0 else None
            values = (client_id, client_name, txt_email.text().strip() or None, txt_phone.text().strip() or None,
                      txt_address.text().strip() or None, txt_city.text().strip() or None,
                      cmb_status.currentText(), d_valid.date().toPython(), txt_notes.toPlainText().strip() or None,
                      total())
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                if state["id"]:
                    cur.execute("UPDATE estimates SET CLIENT_ID=%s, CLIENT_NAME=%s, CLIENT_EMAIL=%s, CLIENT_PHONE=%s, "
                                "JOB_ADDRESS=%s, CITY=%s, STATUS=%s, VALID_UNTIL=%s, NOTES=%s, TOTAL=%s WHERE ID=%s",
                                values + (state["id"],))
                    cur.execute("DELETE FROM estimate_items WHERE ESTIMATE_ID=%s", (state["id"],))
                else:
                    state["code"] = self._next_code(cur, "estimates", "EST")
                    cur.execute("INSERT INTO estimates (CLIENT_ID, CLIENT_NAME, CLIENT_EMAIL, CLIENT_PHONE, JOB_ADDRESS, "
                                "CITY, STATUS, VALID_UNTIL, NOTES, TOTAL, CODE) "
                                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", values + (state["code"],))
                    state["id"] = cur.lastrowid
                for kind, desc, qty, unit, price, product_id in lines:
                    cur.execute("INSERT INTO estimate_items (ESTIMATE_ID, KIND, DESCRIPTION, QTY, UNIT, UNIT_PRICE, PRODUCT_ID) "
                                "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                                (state["id"], kind, desc, qty, unit or None, price, product_id))
                conn.commit()
                cur.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not save the estimate:\n{e}")
                return False
            dialog.setWindowTitle(f"Estimate {state['code']}")
            if not silent:
                show_toast(f"Estimate {state['code']} saved.", "success", self)
            return True

        def make_pdf():
            if not REPORTLAB_AVAILABLE:
                QMessageBox.critical(dialog, "Missing Dependency", "The 'reportlab' package is not installed.")
                return
            if not save(silent=True):
                return
            path, _ = QFileDialog.getSaveFileName(dialog, "Save estimate PDF", f"Estimate_{state['code']}.pdf",
                                                  "PDF Files (*.pdf)")
            if not path:
                return
            if not path.lower().endswith(".pdf"):
                path += ".pdf"
            try:
                self._build_estimate_pdf(path, state["code"], cmb_client.currentText().strip(), txt_email.text(),
                                         txt_phone.text(), txt_address.text(), txt_city.text(),
                                         d_valid.date().toPython(), collect_items(), total(), txt_notes.toPlainText())
            except Exception as e:
                logging.getLogger("vl_flooring").exception("estimate PDF failed")
                QMessageBox.critical(dialog, "PDF Error", f"Could not create the PDF:\n{e}")
                return
            if cmb_status.currentText() == "DRAFT":
                cmb_status.setCurrentText("SENT")
                save(silent=True)
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))

        def send_email():
            if not REPORTLAB_AVAILABLE:
                QMessageBox.critical(dialog, "Missing Dependency", "The 'reportlab' package is not installed.")
                return
            if not save(silent=True):
                return
            args = (state["code"], cmb_client.currentText().strip(), txt_email.text(), txt_phone.text(),
                    txt_address.text(), txt_city.text(), d_valid.date().toPython(), collect_items(), total(),
                    txt_notes.toPlainText())
            sent = self.email_estimate(dialog, state["id"], state["code"], args[1], txt_email.text().strip(),
                                       ", ".join(x for x in (txt_address.text().strip(), txt_city.text().strip()) if x),
                                       total(), args[6], lambda p: self._build_estimate_pdf(p, *args))
            if sent and cmb_status.currentText() == "DRAFT":
                cmb_status.setCurrentText("SENT")

        def suggest():
            rows = []
            for r in range(table.rowCount()):
                kind, _pid = table.item(r, 0).data(Qt.ItemDataRole.UserRole)
                if kind == "SERVICE":
                    rows.append((table.cellWidget(r, 1).text().strip(), table.cellWidget(r, 3).text().strip(),
                                 table.cellWidget(r, 4)))
            self.suggest_estimate_prices(dialog, rows, cmb_client.currentData())

        def convert():
            if not save(silent=True):
                return
            if cmb_status.currentText() == "CONVERTED":
                QMessageBox.information(dialog, "Already converted", "This estimate was already converted to a job.")
                return
            start = QDialog(dialog)
            start.setWindowTitle("Convert to Job")
            sl = QVBoxLayout(start)
            sl.addWidget(QLabel(f"Create a new Job Code from {state['code']}.\nFirst work day:"))
            d_start = QDateEdit()
            d_start.setCalendarPopup(True)
            d_start.setDisplayFormat("MM/dd/yyyy")
            d_start.setDate(QDate.currentDate())
            sl.addWidget(d_start)
            row = QHBoxLayout()
            b_cancel, b_ok = QPushButton("Cancel"), QPushButton("Create job")
            b_ok.setObjectName("btn_convert_confirm")
            row.addWidget(b_cancel)
            row.addWidget(b_ok)
            sl.addLayout(row)
            b_cancel.clicked.connect(start.reject)
            b_ok.clicked.connect(start.accept)
            if start.exec() != 1:  # 1 = Accepted
                return
            first_day = d_start.date().toPython()
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                client_name = cmb_client.currentText().strip()
                idx = cmb_client.findText(client_name)
                client_id = cmb_client.itemData(idx) if idx >= 0 else None
                if not client_id:
                    cur.execute("INSERT INTO clients (FULL_NAME, EMAIL, PHONE_NUMBER) VALUES (%s, %s, %s)",
                                (client_name, txt_email.text().strip() or None, txt_phone.text().strip() or None))
                    client_id = cur.lastrowid
                code = self._next_code(cur, "job_projects", "JB")
                has_budget = self._table_column_exists("job_projects", "BUDGET_AMOUNT")
                cols = "CODE, PROJECT_TYPE, STATUS, CLIENT_ID, JOB_ADDRESS" + (", BUDGET_AMOUNT" if has_budget else "")
                vals = [code, "DAY_WORK", "ACTIVE", client_id, txt_address.text().strip() or None]
                if has_budget:
                    vals.append(total())
                cur.execute(f"INSERT INTO job_projects ({cols}) VALUES ({', '.join(['%s'] * len(vals))})", vals)
                project_id = cur.lastrowid
                cur.execute("INSERT INTO work_days (WORK_DATE, CLIENT_ID, JOB_PROJECT_ID, JOB_ADDRESS, STATUS, VALUE, NOTE) "
                            "VALUES (%s, %s, %s, %s, 'PENDING', 0, %s)",
                            (first_day, client_id, project_id, txt_address.text().strip() or None,
                             f"From estimate {state['code']} ({_money(total())})"))
                work_day_id = cur.lastrowid
                for kind, desc, qty, unit, price, product_id in collect_items():
                    if kind == "MATERIAL" and product_id:
                        cur.execute("INSERT INTO job_materials (JOB_PROJECT_ID, PRODUCT_ID, QUANTITY, UNIT_PRICE) "
                                    "VALUES (%s, %s, %s, %s)", (project_id, product_id, qty, price))
                cur.execute("UPDATE estimates SET STATUS='CONVERTED', JOB_PROJECT_ID=%s, CLIENT_ID=%s WHERE ID=%s",
                            (project_id, client_id, state["id"]))
                conn.commit()
                cur.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not create the job:\n{e}")
                return
            cmb_status.setCurrentText("CONVERTED")
            self._last_converted = (code, work_day_id)
            dialog.accept()
            if hasattr(self, "_refresh_job_code_completer"):
                self._refresh_job_code_completer()
            show_toast(f"{state['code']} → job {code} created (first day {first_day:%m/%d/%Y}).", "success", self)
            try:
                if dialog.parent() is not None and dialog.parent() is not self:
                    dialog.parent().accept()
                self._open_job_by_id(work_day_id, first_day)
            except Exception:
                logging.getLogger("vl_flooring").exception("could not open the new job")

        btn_save.clicked.connect(lambda: save())
        btn_pdf.clicked.connect(make_pdf)
        btn_email.clicked.connect(send_email)
        btn_suggest.clicked.connect(suggest)
        dialog._send_email, dialog._suggest, dialog._add_line = send_email, suggest, add_line  # testes
        btn_convert.clicked.connect(convert)
        btn_close.clicked.connect(dialog.reject)
        dialog.exec()

    def _build_estimate_pdf(self, path, code, client, email, phone, address, city, valid_until, items, total, notes):
        styles = getSampleStyleSheet()
        small = ParagraphStyle("small", parent=styles["Normal"], fontSize=9, leading=12)
        right = ParagraphStyle("right", parent=styles["Normal"], alignment=TA_RIGHT, fontSize=10)
        story = []
        # Ícone do logo + nome atual da empresa (o logo horizontal antigo ainda
        # traz o texto "CONSTRUCTION")
        logo = os.path.join(PROJECT_DIR, "icons_", "logo_icon_only_256.png")
        name_style = ParagraphStyle("company", parent=styles["Normal"], fontSize=15, leading=18,
                                    textColor=colors.HexColor(BRAND_NAVY))
        name = Paragraph(f"<b>{company_settings.COMPANY_NAME}</b>", name_style)
        if os.path.exists(logo):
            img = Image(logo, width=0.62 * inch, height=0.62 * inch)
            brand = Table([[img, name]], colWidths=[0.75 * inch, 3.0 * inch])
            brand.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                       ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
            head_left = [brand]
        else:
            head_left = [name]
        head_left.append(Spacer(1, 6))
        head_left.append(Paragraph(f"{company_settings.COMPANY_PHONE}<br/>{company_settings.COMPANY_EMAIL}"
                                   f"<br/>{company_settings.COMPANY_WEBSITE}", small))
        head_right = Paragraph(f"<font size=20 color='{BRAND_ORANGE}'><b>ESTIMATE</b></font><br/><br/>"
                               f"<b>{code}</b><br/>Date: {date.today():%m/%d/%Y}<br/>"
                               f"Valid until: {valid_until:%m/%d/%Y}", right)
        header = Table([[head_left, head_right]], colWidths=[3.8 * inch, 3.2 * inch])
        header.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        story += [header, Spacer(1, 14), HRFlowable(width="100%", color=colors.HexColor(BRAND_ORANGE), thickness=2),
                  Spacer(1, 10)]
        client_lines = [f"<b>Prepared for:</b> {client}"]
        if address or city:
            client_lines.append(", ".join(x for x in (address, city) if x))
        if phone or email:
            client_lines.append(" · ".join(x for x in (phone, email) if x))
        story.append(Paragraph("<br/>".join(client_lines), styles["Normal"]))
        story.append(Spacer(1, 14))
        data = [["Description", "Qty", "Unit", "Unit price", "Total"]]
        for kind, desc, qty, unit, price, _pid in items:
            data.append([Paragraph(desc, small), f"{qty:,.2f}".rstrip("0").rstrip("."), unit or "",
                         _money(price), _money(qty * price)])
        data.append(["", "", "", "TOTAL", _money(total)])
        t = Table(data, colWidths=[3.4 * inch, 0.8 * inch, 0.7 * inch, 1.0 * inch, 1.1 * inch], repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(BRAND_NAVY)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -2), 0.4, colors.HexColor("#DDDDDD")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#F7F9FC")]),
            ("FONTNAME", (3, -1), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (3, -1), (-1, -1), 11),
            ("LINEABOVE", (3, -1), (-1, -1), 1.2, colors.HexColor(BRAND_ORANGE)),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(t)
        if notes and notes.strip():
            story += [Spacer(1, 14), Paragraph("<b>Notes</b>", styles["Normal"]),
                      Paragraph(notes.replace("&", "&amp;").replace("<", "&lt;").replace("\n", "<br/>"), small)]
        story += [Spacer(1, 36),
                  Paragraph("Accepted by: _______________________________ &nbsp;&nbsp; Date: ______________", small)]
        SimpleDocTemplate(path, pagesize=letter, leftMargin=0.6 * inch, rightMargin=0.6 * inch,
                          topMargin=0.6 * inch, bottomMargin=0.6 * inch).build(story)
