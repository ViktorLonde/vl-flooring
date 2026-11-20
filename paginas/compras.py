# -*- coding: utf-8 -*-
"""
Compras de fornecedor e estoque de sobras.

• Purchases — registra o pedido do fornecedor (ex.: Carpet One #1228897)
  com os itens, quantidades e preços. Ao salvar:
    – atualiza o preço do produto (e preenche linhas de material que
      estavam a $0 em qualquer job);
    – lança os itens no Job Code escolhido (se o material já estava lançado
      a $0, só coloca o preço — não duplica a quantidade);
    – itens marcados "Stock" vão para o estoque em vez do job;
    – cria UMA despesa (MATERIALS) com o total, o fornecedor e o recibo.
  No Job Profit a despesa da compra NÃO soma de novo (o material já conta
  pelos itens lançados); só o imposto (tax) da compra entra como despesa.

• Stock — sobras de material: "Leftover from a job" tira do job e põe no
  estoque; "Use in a job" tira do estoque e lança no job, pelo preço médio.
  Cada entrada/saída é uma linha em inventory_moves (+ entra, − sai).

Métodos da MainWindow (mixin) — veja main_.py.
"""

import os
from datetime import date

from PySide6.QtCore import QDate
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QCheckBox, QDateEdit, QFormLayout

from app_common import *  # noqa: F401,F403
from formatar_texto import smart_title
from paginas.visual import tabler_icon
from paginas.moderno import show_toast

_PRIMARY_BTN = ("QPushButton { background-color: #1565C0; color: #FFFFFF; border: none; border-radius: 6px; "
                "padding: 8px 16px; font-weight: 700; } QPushButton:hover { background-color: #1E88E5; }")
_SMALL_BTN = ("QPushButton { background-color: #EEF2F7; color: #37474F; border: 1px solid #D0D7DE; "
              "border-radius: 6px; padding: 6px 12px; font-size: 12px; font-weight: 600; } "
              "QPushButton:hover { background-color: #E1E8F0; }")


def _money(v):
    return f"${float(v or 0):,.2f}"


def _qty(v):
    return f"{float(v or 0):g}"


def _fill_product_combo(combo, rows, placeholder="— Select a product —"):
    """rows: (ID, NAME, UNIT, PRICE, TYPE, BRAND). Agrupa por tipo, com
    títulos desativados (criados pelo próprio combo — veja jobs.py)."""
    combo.clear()
    combo.addItem(placeholder, None)
    current = None
    model = combo.model()
    for pid, name, unit, price, ptype, brand in rows:
        if ptype != current:
            current = ptype
            combo.addItem(f"── {(ptype or 'Others').upper()} ──", None)
            header = model.item(combo.count() - 1)
            if header is not None:
                header.setFlags(Qt.ItemFlag.NoItemFlags)
            bold = QFont(combo.font())
            bold.setBold(True)
            combo.setItemData(combo.count() - 1, bold, Qt.ItemDataRole.FontRole)
        combo.addItem(f"   {name}" + (f" ({brand})" if brand else "") + (f"  ·  {unit}" if unit else ""), pid)


def _money_spin(maximum=999999.99):
    s = QDoubleSpinBox()
    s.setDecimals(2)
    s.setMaximum(maximum)
    s.setPrefix("$ ")
    return s


def _qty_spin(maximum=99999.0):
    s = QDoubleSpinBox()
    s.setDecimals(2)
    s.setMaximum(maximum)
    return s


class PurchasesStockMixin:
    # ── dados básicos ───────────────────────────────────────────────
    def _product_rows(self):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT ID, NAME, UNIT, PRICE, COALESCE(NULLIF(TYPE, ''), 'Others'), BRAND "
                    "FROM products ORDER BY 5, NAME")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows

    def _job_code_rows(self):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT ID, CODE FROM job_projects WHERE CODE IS NOT NULL ORDER BY ID DESC")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows

    def _current_form_job_project_id(self):
        try:
            typed = self.ui.cmb_job_code.currentText().strip().upper()
            return getattr(self, "_job_code_to_id", {}).get(typed)
        except AttributeError:
            return None

    @staticmethod
    def _add_to_job_materials(cur, job_project_id, product_id, qty, price):
        """Soma no material do job: se já existe a linha do produto, junta
        (preço = média ponderada; se a linha estava a $0, vale o novo preço)."""
        cur.execute("SELECT ID, QUANTITY, UNIT_PRICE FROM job_materials WHERE JOB_PROJECT_ID=%s AND PRODUCT_ID=%s "
                    "ORDER BY ID LIMIT 1", (job_project_id, product_id))
        row = cur.fetchone()
        if row:
            mid, old_q, old_p = row[0], float(row[1] or 0), float(row[2] or 0)
            new_q = old_q + qty
            if old_p <= 0:
                new_p = price
            elif price <= 0:
                new_p = old_p
            else:
                new_p = (old_q * old_p + qty * price) / new_q if new_q else price
            cur.execute("UPDATE job_materials SET QUANTITY=%s, UNIT_PRICE=%s WHERE ID=%s", (new_q, round(new_p, 2), mid))
        else:
            cur.execute("INSERT INTO job_materials (JOB_PROJECT_ID, PRODUCT_ID, QUANTITY, UNIT_PRICE) "
                        "VALUES (%s, %s, %s, %s)", (job_project_id, product_id, qty, price))

    # ═════════════════════════ PURCHASES ═════════════════════════
    def open_purchases_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Supplier purchases")
        dialog.resize(900, 560)
        layout = QVBoxLayout(dialog)
        intro = QLabel("Register the supplier order: product prices are updated, the items go into the Job Code "
                       "(or into Stock) and one Materials expense is created with the receipt.")
        intro.setWordWrap(True)
        intro.setStyleSheet("color:#475569;")
        layout.addWidget(intro)
        table = QTableWidget(0, 7)
        table.setObjectName("table_purchases")
        table.setHorizontalHeaderLabels(["Date", "Supplier", "Order #", "Job Code", "Items", "Total", "Receipt"])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        layout.addWidget(table, 1)
        buttons = QHBoxLayout()
        btn_new = QPushButton("  New purchase")
        btn_new.setObjectName("btn_new_purchase")
        btn_new.setIcon(tabler_icon("plus", "#FFFFFF", 16))
        btn_new.setStyleSheet(_PRIMARY_BTN)
        btn_view = QPushButton("  View items")
        btn_view.setStyleSheet(_SMALL_BTN)
        btn_del = QPushButton("  Delete")
        btn_del.setObjectName("btn_delete_purchase")
        btn_del.setStyleSheet(_SMALL_BTN)
        btn_close = QPushButton("Close")
        buttons.addWidget(btn_new)
        buttons.addWidget(btn_view)
        buttons.addWidget(btn_del)
        buttons.addStretch(1)
        buttons.addWidget(btn_close)
        layout.addLayout(buttons)
        if self._role_rule("read_only"):
            for b in (btn_new, btn_del):
                b.setEnabled(False)
                b.setToolTip("Your user has read-only access.")
        if not self._role_rule("can_delete"):
            btn_del.setEnabled(False)

        def reload():
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                cur.execute("""
                    SELECT p.ID, p.PURCHASE_DATE, p.SUPPLIER, p.ORDER_NUMBER, jp.CODE,
                           (SELECT COUNT(*) FROM purchase_items i WHERE i.PURCHASE_ID = p.ID), p.TOTAL_AMOUNT,
                           p.RECEIPT_PATH
                    FROM purchases p LEFT JOIN job_projects jp ON jp.ID = p.JOB_PROJECT_ID
                    ORDER BY p.PURCHASE_DATE DESC, p.ID DESC""")
                rows = cur.fetchall()
                cur.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not load the purchases:\n{e}")
                return
            table.setRowCount(len(rows))
            for r, (pid, d, sup, order, code, n, total, receipt) in enumerate(rows):
                cells = [d.strftime("%m/%d/%Y") if d else "", sup or "", order or "", code or "Stock",
                         str(n), _money(total), "📎" if receipt else ""]
                for c, v in enumerate(cells):
                    item = QTableWidgetItem(v)
                    if c == 0:
                        item.setData(Qt.ItemDataRole.UserRole, pid)
                    if c in (4, 5):
                        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    table.setItem(r, c, item)

        def selected_id():
            row = table.currentRow()
            item = table.item(row, 0) if row >= 0 else None
            return item.data(Qt.ItemDataRole.UserRole) if item else None

        def new():
            if self.open_new_purchase_dialog(parent=dialog):
                reload()

        def delete():
            pid = selected_id()
            if not pid:
                return
            answer = QMessageBox.question(
                dialog, "Delete purchase",
                "Delete this purchase and its Materials expense?\n\n"
                "Prices and materials already launched in the job are kept (edit them in the job if needed).",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                return
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                cur.execute("SELECT EXPENSE_ID FROM purchases WHERE ID=%s", (pid,))
                row = cur.fetchone()
                cur.execute("DELETE FROM purchases WHERE ID=%s", (pid,))
                if row and row[0]:
                    cur.execute("DELETE FROM expenses WHERE ID=%s", (row[0],))
                conn.commit()
                cur.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(dialog, "Database Error", f"Could not delete:\n{e}")
                return
            reload()
            show_toast("Purchase deleted.", "success", self)

        btn_new.clicked.connect(new)
        btn_view.clicked.connect(lambda: selected_id() and self._show_purchase_items(selected_id(), dialog))
        table.cellDoubleClicked.connect(lambda *_: selected_id() and self._show_purchase_items(selected_id(), dialog))
        btn_del.clicked.connect(delete)
        btn_close.clicked.connect(dialog.accept)
        reload()
        dialog.exec()

    def _show_purchase_items(self, purchase_id, parent=None):
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""SELECT pr.NAME, i.QUANTITY, pr.UNIT, i.UNIT_PRICE, i.TO_STOCK
                           FROM purchase_items i JOIN products pr ON pr.ID = i.PRODUCT_ID
                           WHERE i.PURCHASE_ID=%s ORDER BY i.ID""", (purchase_id,))
            items = cur.fetchall()
            cur.execute("SELECT SUPPLIER, ORDER_NUMBER, TAX_AMOUNT, TOTAL_AMOUNT, NOTES, RECEIPT_PATH "
                        "FROM purchases WHERE ID=%s", (purchase_id,))
            sup, order, tax, total, notes, receipt = cur.fetchone()
            cur.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(parent or self, "Database Error", str(e))
            return
        d = QDialog(parent or self)
        d.setWindowTitle(f"{sup} — order {order or ''}")
        d.resize(640, 420)
        lay = QVBoxLayout(d)
        t = QTableWidget(len(items), 5)
        t.setHorizontalHeaderLabels(["Product", "Qty", "Unit price", "Total", "Went to"])
        t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        t.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        t.verticalHeader().setVisible(False)
        for r, (name, q, unit, price, stock) in enumerate(items):
            for c, v in enumerate([name, f"{_qty(q)} {unit or ''}", _money(price),
                                   _money(float(q) * float(price)), "Stock" if stock else "Job"]):
                t.setItem(r, c, QTableWidgetItem(v))
        lay.addWidget(t, 1)
        info = f"Tax: {_money(tax)}   ·   Total: {_money(total)}"
        if notes:
            info += f"   ·   {notes}"
        lay.addWidget(QLabel(info))
        if receipt:
            open_btn = QPushButton("Open receipt")
            open_btn.clicked.connect(lambda: os.path.exists(receipt) and os.startfile(receipt))
            lay.addWidget(open_btn)
        d.exec()

    def open_new_purchase_dialog(self, parent=None, job_project_id=None):
        """Formulário de compra. Devolve True se salvou."""
        try:
            products = self._product_rows()
            codes = self._job_code_rows()
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT SUPPLIER FROM purchases UNION SELECT DISTINCT VENDOR FROM expenses "
                        "WHERE COALESCE(VENDOR, '') <> '' ORDER BY 1")
            suppliers = [r[0] for r in cur.fetchall() if r[0]]
            cur.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(parent or self, "Database Error", str(e))
            return False
        price_of = {p[0]: float(p[3] or 0) for p in products}

        dialog = QDialog(parent or self)
        dialog.setWindowTitle("New supplier purchase")
        dialog.resize(940, 640)
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        supplier = QComboBox()
        supplier.setEditable(True)
        supplier.setObjectName("cmb_purchase_supplier")
        supplier.addItems(suppliers)
        supplier.setCurrentText("")
        supplier.lineEdit().setPlaceholderText("e.g. Carpet One")
        order = QLineEdit()
        order.setObjectName("txt_purchase_order")
        order.setPlaceholderText("Order / invoice number")
        when = QDateEdit(QDate.currentDate())
        when.setCalendarPopup(True)
        when.setDisplayFormat("MM/dd/yyyy")
        job = QComboBox()
        job.setObjectName("cmb_purchase_job")
        job.addItem("— No job (everything to Stock) —", None)
        for pid, code in codes:
            job.addItem(code, pid)
        if job_project_id:
            job.setCurrentIndex(max(0, job.findData(job_project_id)))
        receipt_row = QHBoxLayout()
        receipt = QLineEdit()
        receipt.setObjectName("txt_purchase_receipt")
        receipt.setPlaceholderText("Photo or PDF of the receipt (optional)")
        browse = QPushButton("Browse…")
        receipt_row.addWidget(receipt, 1)
        receipt_row.addWidget(browse)
        notes = QLineEdit()
        form.addRow("Supplier:", supplier)
        form.addRow("Order #:", order)
        form.addRow("Date:", when)
        form.addRow("Job Code:", job)
        form.addRow("Receipt:", receipt_row)
        form.addRow("Notes:", notes)
        layout.addLayout(form)

        items = QTableWidget(0, 5)
        items.setObjectName("table_purchase_items")
        items.setHorizontalHeaderLabels(["Product", "Qty", "Unit price", "Line total", "Stock"])
        items.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        items.verticalHeader().setVisible(False)
        items.setColumnWidth(1, 100)
        items.setColumnWidth(2, 120)
        items.setColumnWidth(3, 110)
        items.setColumnWidth(4, 60)
        items.verticalHeader().setDefaultSectionSize(48)
        layout.addWidget(items, 1)
        add_row = QHBoxLayout()
        btn_add = QPushButton("  Add item")
        btn_add.setObjectName("btn_purchase_add_item")
        btn_add.setIcon(tabler_icon("plus", "#37474F", 16))
        btn_add.setStyleSheet(_SMALL_BTN)
        btn_remove = QPushButton("  Remove item")
        btn_remove.setStyleSheet(_SMALL_BTN)
        add_row.addWidget(btn_add)
        add_row.addWidget(btn_remove)
        add_row.addStretch(1)
        add_row.addWidget(QLabel("Tax:"))
        tax = _money_spin()
        tax.setObjectName("dspn_purchase_tax")
        add_row.addWidget(tax)
        total_lbl = QLabel()
        total_lbl.setStyleSheet("font-weight:700; font-size:15px; padding-left:12px;")
        add_row.addWidget(total_lbl)
        layout.addLayout(add_row)

        chk_prices = QCheckBox("Update the product prices with these prices")
        chk_prices.setChecked(True)
        chk_expense = QCheckBox("Create a Materials expense with the total (and the receipt)")
        chk_expense.setChecked(True)
        layout.addWidget(chk_prices)
        layout.addWidget(chk_expense)
        hint = QLabel("Tick “Stock” on items that are not for this job. If the material was already added to the "
                      "job without a price, only the price is filled in — the quantity is not doubled.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#64748B; font-size:12px;")
        layout.addWidget(hint)
        bottom = QHBoxLayout()
        bottom.addStretch(1)
        btn_cancel = QPushButton("Cancel")
        btn_save = QPushButton("  Save purchase")
        btn_save.setObjectName("btn_save_purchase")
        btn_save.setIcon(tabler_icon("check", "#FFFFFF", 16))
        btn_save.setStyleSheet(_PRIMARY_BTN)
        bottom.addWidget(btn_cancel)
        bottom.addWidget(btn_save)
        layout.addLayout(bottom)

        rows = []  # [{"product", "qty", "price", "stock"}]

        def subtotal():
            return sum(r["qty"].value() * r["price"].value() for r in rows)

        def refresh_totals():
            for i, r in enumerate(rows):
                cell = items.item(i, 3)
                if cell is None:
                    cell = QTableWidgetItem()
                    cell.setFlags(Qt.ItemFlag.ItemIsEnabled)
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    items.setItem(i, 3, cell)
                cell.setText(_money(r["qty"].value() * r["price"].value()))
            total_lbl.setText(f"Total: {_money(subtotal() + tax.value())}")

        def stock_default():
            return job.currentData() is None

        def add_item(product_id=None, qty=1.0, price=None, stock=None):
            r = items.rowCount()
            items.insertRow(r)
            combo = QComboBox()
            _fill_product_combo(combo, products)
            q = _qty_spin()
            q.setValue(qty)
            p = _money_spin()
            chk = QCheckBox()
            chk.setStyleSheet("QCheckBox::indicator { width: 18px; height: 18px; border: 2px solid #94A3B8; border-radius: 4px; background-color: #FFFFFF; } QCheckBox::indicator:checked { background-color: #1565C0; border-color: #1565C0; }")
            chk.setChecked(stock_default() if stock is None else stock)
            box = QWidget()
            bl = QHBoxLayout(box)
            bl.setContentsMargins(0, 0, 0, 0)
            bl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            bl.addWidget(chk)
            row = {"product": combo, "qty": q, "price": p, "stock": chk}
            rows.append(row)

            def product_changed(*_a):
                pid = combo.currentData()
                if pid and p.value() == 0:
                    p.setValue(price_of.get(pid, 0))
                refresh_totals()
            combo.currentIndexChanged.connect(product_changed)
            q.valueChanged.connect(lambda *_: refresh_totals())
            p.valueChanged.connect(lambda *_: refresh_totals())
            items.setCellWidget(r, 0, combo)
            items.setCellWidget(r, 1, q)
            items.setCellWidget(r, 2, p)
            items.setCellWidget(r, 4, box)
            if product_id:
                combo.setCurrentIndex(max(0, combo.findData(product_id)))
            if price is not None:
                p.setValue(price)
            refresh_totals()
            return row

        def remove_item():
            r = items.currentRow()
            if r < 0:
                r = items.rowCount() - 1
            if r < 0:
                return
            items.removeRow(r)
            rows.pop(r)
            refresh_totals()

        def browse_receipt():
            path, _ = QFileDialog.getOpenFileName(dialog, "Receipt", "", "Receipts (*.pdf *.png *.jpg *.jpeg *.heic);;All files (*)")
            if path:
                receipt.setText(path)

        def job_changed(*_a):
            for r in rows:
                if job.currentData() is None:
                    r["stock"].setChecked(True)
        job.currentIndexChanged.connect(job_changed)
        tax.valueChanged.connect(lambda *_: refresh_totals())
        btn_add.clicked.connect(lambda: add_item())
        btn_remove.clicked.connect(remove_item)
        browse.clicked.connect(browse_receipt)
        btn_cancel.clicked.connect(dialog.reject)
        dialog._add_item = add_item  # usado nos testes
        add_item()

        saved = {"ok": False}

        def save():
            sup = smart_title(supplier.currentText().strip())
            lines = [(r["product"].currentData(), r["qty"].value(), r["price"].value(), r["stock"].isChecked())
                     for r in rows]
            lines = [l for l in lines if l[0] and l[1] > 0]
            if not sup:
                QMessageBox.warning(dialog, "Supplier", "Type the supplier name.")
                return
            if not lines:
                QMessageBox.warning(dialog, "Items", "Add at least one product with a quantity.")
                return
            job_id = job.currentData()
            if job_id is None:
                lines = [(a, b, c, True) for a, b, c, _s in lines]
            total = round(sum(q * p for _pid, q, p, _s in lines) + tax.value(), 2)
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                # prévia do que acontece no job
                preview = []
                for pid, q, p, stock in lines:
                    name = next((x[1] for x in products if x[0] == pid), "?")
                    if stock:
                        preview.append(f"• {name}: {q:g} → Stock")
                        continue
                    cur.execute("SELECT QUANTITY, UNIT_PRICE FROM job_materials WHERE JOB_PROJECT_ID=%s "
                                "AND PRODUCT_ID=%s ORDER BY ID LIMIT 1", (job_id, pid))
                    ex = cur.fetchone()
                    if ex and float(ex[1] or 0) == 0:
                        preview.append(f"• {name}: already in the job ({float(ex[0]):g}) — price set to {_money(p)}")
                    elif ex:
                        preview.append(f"• {name}: +{q:g} added to the {float(ex[0]):g} in the job")
                    else:
                        preview.append(f"• {name}: {q:g} added to the job")
                answer = QMessageBox.question(
                    dialog, "Save purchase",
                    f"{sup} — {_money(total)}\n\n" + "\n".join(preview[:15]) +
                    ("\n\nA Materials expense will be created." if chk_expense.isChecked() else ""),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes)
                if answer != QMessageBox.StandardButton.Yes:
                    cur.close()
                    conn.close()
                    return
                d = when.date().toPython()
                cur.execute("INSERT INTO purchases (SUPPLIER, ORDER_NUMBER, PURCHASE_DATE, JOB_PROJECT_ID, "
                            "RECEIPT_PATH, TAX_AMOUNT, TOTAL_AMOUNT, NOTES) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                            (sup, order.text().strip() or None, d, job_id, receipt.text().strip() or None,
                             tax.value(), total, notes.text().strip() or None))
                purchase_id = cur.lastrowid
                for pid, q, p, stock in lines:
                    cur.execute("INSERT INTO purchase_items (PURCHASE_ID, PRODUCT_ID, QUANTITY, UNIT_PRICE, TO_STOCK) "
                                "VALUES (%s,%s,%s,%s,%s)", (purchase_id, pid, q, p, 1 if stock else 0))
                    if chk_prices.isChecked() and p > 0:
                        cur.execute("UPDATE products SET PRICE=%s WHERE ID=%s", (p, pid))
                        cur.execute("UPDATE job_materials SET UNIT_PRICE=%s WHERE PRODUCT_ID=%s "
                                    "AND COALESCE(UNIT_PRICE,0)=0 AND JOB_PROJECT_ID <> %s", (p, pid, job_id or 0))
                    if stock:
                        cur.execute("INSERT INTO inventory_moves (PRODUCT_ID, QUANTITY, UNIT_PRICE, JOB_PROJECT_ID, "
                                    "NOTE, CREATED_BY) VALUES (%s,%s,%s,NULL,%s,%s)",
                                    (pid, q, p, f"Purchase {sup} {order.text().strip()}".strip(),
                                     getattr(self, "_current_username", None)))
                        continue
                    cur.execute("SELECT ID, UNIT_PRICE FROM job_materials WHERE JOB_PROJECT_ID=%s AND PRODUCT_ID=%s "
                                "ORDER BY ID LIMIT 1", (job_id, pid))
                    ex = cur.fetchone()
                    if ex and float(ex[1] or 0) == 0:
                        cur.execute("UPDATE job_materials SET UNIT_PRICE=%s WHERE ID=%s", (p, ex[0]))
                    else:
                        self._add_to_job_materials(cur, job_id, pid, q, p)
                if chk_expense.isChecked():
                    desc = (f"Purchase {order.text().strip()} — " if order.text().strip() else "Purchase — ") + \
                           f"{len(lines)} item(s)"
                    cur.execute("INSERT INTO expenses (EXPENSE_DATE, CATEGORY, DESCRIPTION, VENDOR, AMOUNT, ENTITY_TYPE, "
                                "OTHER_NAME, JOB_PROJECT_ID, RECEIPT_PATH, SUBMITTED_BY) "
                                "VALUES (%s,'MATERIALS',%s,%s,%s,'Others',%s,%s,%s,'ME')",
                                (d, desc[:200], sup[:100], total, sup[:150], job_id, receipt.text().strip() or None))
                    cur.execute("UPDATE purchases SET EXPENSE_ID=%s WHERE ID=%s", (cur.lastrowid, purchase_id))
                conn.commit()
                cur.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                try:
                    conn.rollback()
                except Exception:
                    pass
                QMessageBox.critical(dialog, "Database Error", f"Could not save the purchase:\n{e}")
                return
            logging.getLogger("vl_flooring").info("purchase %s saved: %s %s", purchase_id, sup, total)
            saved["ok"] = True
            dialog.accept()
            show_toast(f"Purchase saved — {_money(total)}.", "success", self)
            if hasattr(self, "_refresh_material_product_combo"):
                self._refresh_material_product_combo()
            if job_id and job_id == self._current_form_job_project_id() and hasattr(self, "_load_job_materials"):
                self._load_job_materials()

        btn_save.clicked.connect(save)
        dialog.exec()
        return saved["ok"]

    # ═════════════════════════ STOCK ═════════════════════════
    def _stock_balance(self):
        """[(product_id, name, type, unit, qty, avg_price)] com saldo > 0."""
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT pr.ID, pr.NAME, COALESCE(NULLIF(pr.TYPE, ''), 'Others'), pr.UNIT, SUM(m.QUANTITY),
                   SUM(CASE WHEN m.QUANTITY > 0 THEN m.QUANTITY * m.UNIT_PRICE ELSE 0 END),
                   SUM(CASE WHEN m.QUANTITY > 0 THEN m.QUANTITY ELSE 0 END), MAX(m.CREATED_AT)
            FROM inventory_moves m JOIN products pr ON pr.ID = m.PRODUCT_ID
            GROUP BY pr.ID, pr.NAME, pr.TYPE, pr.UNIT
            HAVING SUM(m.QUANTITY) > 0.001
            ORDER BY 3, 2""")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        out = []
        for pid, name, ptype, unit, qty, value_in, qty_in, last in rows:
            avg = float(value_in or 0) / float(qty_in) if qty_in else 0.0
            out.append((pid, name, ptype, unit or "", float(qty), round(avg, 2), last))
        return out

    def open_stock_dialog(self, job_project_id=None):
        dialog = QDialog(self)
        dialog.setWindowTitle("Material stock (leftovers)")
        dialog.resize(860, 520)
        layout = QVBoxLayout(dialog)
        summary = QLabel()
        summary.setStyleSheet("font-weight:600; color:#334155;")
        layout.addWidget(summary)
        table = QTableWidget(0, 6)
        table.setObjectName("table_stock")
        table.setHorizontalHeaderLabels(["Type", "Product", "In stock", "Avg price", "Value", "Last move"])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        layout.addWidget(table, 1)
        buttons = QHBoxLayout()
        btn_left = QPushButton("  Leftover from a job")
        btn_left.setObjectName("btn_new_leftover")
        btn_left.setIcon(tabler_icon("package", "#FFFFFF", 16))
        btn_left.setStyleSheet(_PRIMARY_BTN)
        btn_use = QPushButton("  Use in a job")
        btn_use.setObjectName("btn_save_stock_use")
        btn_use.setIcon(tabler_icon("arrows-exchange", "#37474F", 16))
        btn_use.setStyleSheet(_SMALL_BTN)
        btn_hist = QPushButton("  History")
        btn_hist.setStyleSheet(_SMALL_BTN)
        btn_close = QPushButton("Close")
        for b in (btn_left, btn_use, btn_hist):
            buttons.addWidget(b)
        buttons.addStretch(1)
        buttons.addWidget(btn_close)
        layout.addLayout(buttons)
        if self._role_rule("read_only"):
            for b in (btn_left, btn_use):
                b.setEnabled(False)
                b.setToolTip("Your user has read-only access.")

        state = {"rows": []}

        def reload():
            try:
                state["rows"] = rows = self._stock_balance()
            except (MySQLError, RuntimeError) as e:
                summary.setText(f"Could not load the stock: {e}")
                return
            table.setRowCount(len(rows))
            value = 0.0
            for r, (pid, name, ptype, unit, qty, avg, last) in enumerate(rows):
                value += qty * avg
                cells = [ptype, name, f"{qty:g} {unit}", _money(avg), _money(qty * avg),
                         last.strftime("%m/%d/%Y") if last else ""]
                for c, v in enumerate(cells):
                    item = QTableWidgetItem(v)
                    if c == 0:
                        item.setData(Qt.ItemDataRole.UserRole, pid)
                    table.setItem(r, c, item)
            summary.setText(f"{len(rows)} product(s) in stock · value {_money(value)}" if rows else
                            "Nothing in stock yet. Use “Leftover from a job” when material is left over, "
                            "or tick “Stock” on a purchase item.")

        def selected_pid():
            row = table.currentRow()
            item = table.item(row, 0) if row >= 0 else None
            return item.data(Qt.ItemDataRole.UserRole) if item else None

        btn_left.clicked.connect(lambda: self.open_leftover_dialog(job_project_id, dialog) and reload())
        btn_use.clicked.connect(lambda: self.open_use_stock_dialog(selected_pid(), job_project_id, dialog) and reload())
        table.cellDoubleClicked.connect(
            lambda *_: self.open_use_stock_dialog(selected_pid(), job_project_id, dialog) and reload())
        btn_hist.clicked.connect(lambda: self._show_stock_history(dialog))
        btn_close.clicked.connect(dialog.accept)
        reload()
        dialog.exec()

    def open_leftover_dialog(self, job_project_id=None, parent=None):
        """Sobrou material: tira do job (opcional) e põe no estoque."""
        try:
            codes = self._job_code_rows()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(parent or self, "Database Error", str(e))
            return False
        d = QDialog(parent or self)
        d.setWindowTitle("Leftover material → Stock")
        d.resize(560, 300)
        lay = QVBoxLayout(d)
        form = QFormLayout()
        job = QComboBox()
        job.setObjectName("cmb_leftover_job")
        for pid, code in codes:
            job.addItem(code, pid)
        if job_project_id:
            job.setCurrentIndex(max(0, job.findData(job_project_id)))
        product = QComboBox()
        product.setObjectName("cmb_leftover_product")
        qty = _qty_spin()
        qty.setObjectName("dspn_leftover_qty")
        info = QLabel()
        info.setStyleSheet("color:#64748B;")
        chk = QCheckBox("Take it out of this job's materials (the job used less)")
        chk.setChecked(True)
        form.addRow("From Job Code:", job)
        form.addRow("Product:", product)
        form.addRow("Leftover qty:", qty)
        lay.addLayout(form)
        lay.addWidget(info)
        lay.addWidget(chk)
        lay.addStretch(1)
        bottom = QHBoxLayout()
        bottom.addStretch(1)
        cancel = QPushButton("Cancel")
        ok = QPushButton("  Move to Stock")
        ok.setObjectName("btn_save_leftover")
        ok.setStyleSheet(_PRIMARY_BTN)
        bottom.addWidget(cancel)
        bottom.addWidget(ok)
        lay.addLayout(bottom)
        lines = {}

        def load_lines(*_a):
            lines.clear()
            product.clear()
            jid = job.currentData()
            if not jid:
                return
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                cur.execute("""SELECT jm.ID, jm.PRODUCT_ID, pr.NAME, pr.UNIT, jm.QUANTITY, jm.UNIT_PRICE
                               FROM job_materials jm JOIN products pr ON pr.ID = jm.PRODUCT_ID
                               WHERE jm.JOB_PROJECT_ID=%s ORDER BY pr.TYPE, pr.NAME""", (jid,))
                for mid, pid, name, unit, q, p in cur.fetchall():
                    lines[mid] = (pid, name, unit or "", float(q or 0), float(p or 0))
                    product.addItem(f"{name}  ·  {float(q or 0):g} {unit or ''} in the job", mid)
                cur.close()
                conn.close()
            except (MySQLError, RuntimeError):
                pass
            line_changed()

        def line_changed(*_a):
            mid = product.currentData()
            if mid in lines:
                _pid, _n, unit, q, p = lines[mid]
                qty.setMaximum(q)
                qty.setSuffix(f" {unit}")
                info.setText(f"Launched in the job: {q:g} {unit} at {_money(p)}. It goes to Stock at the same price.")
            else:
                info.setText("This Job Code has no materials." if job.currentData() else "")
        job.currentIndexChanged.connect(load_lines)
        product.currentIndexChanged.connect(line_changed)
        cancel.clicked.connect(d.reject)
        done = {"ok": False}

        def save():
            mid = product.currentData()
            q = qty.value()
            if mid not in lines or q <= 0:
                QMessageBox.warning(d, "Leftover", "Pick a product and the quantity left over.")
                return
            pid, name, unit, launched, price = lines[mid]
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                cur.execute("INSERT INTO inventory_moves (PRODUCT_ID, QUANTITY, UNIT_PRICE, JOB_PROJECT_ID, NOTE, "
                            "CREATED_BY) VALUES (%s,%s,%s,%s,%s,%s)",
                            (pid, q, price, job.currentData(), f"Leftover from {job.currentText()}",
                             getattr(self, "_current_username", None)))
                if chk.isChecked():
                    remaining = round(launched - q, 2)
                    if remaining <= 0:
                        cur.execute("DELETE FROM job_materials WHERE ID=%s", (mid,))
                    else:
                        cur.execute("UPDATE job_materials SET QUANTITY=%s WHERE ID=%s", (remaining, mid))
                conn.commit()
                cur.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(d, "Database Error", str(e))
                return
            done["ok"] = True
            d.accept()
            show_toast(f"{q:g} {unit} of {name} moved to Stock.", "success", self)
            if job.currentData() == self._current_form_job_project_id() and hasattr(self, "_load_job_materials"):
                self._load_job_materials()

        ok.clicked.connect(save)
        load_lines()
        d._job, d._product, d._qty, d._chk = job, product, qty, chk  # usado nos testes
        d.exec()
        return done["ok"]

    def open_use_stock_dialog(self, product_id=None, job_project_id=None, parent=None):
        """Usa material do estoque num job (sai do estoque pelo preço médio)."""
        try:
            stock = self._stock_balance()
            codes = self._job_code_rows()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(parent or self, "Database Error", str(e))
            return False
        if not stock:
            QMessageBox.information(parent or self, "Stock", "Nothing in stock.")
            return False
        d = QDialog(parent or self)
        d.setWindowTitle("Use stock in a job")
        d.resize(520, 240)
        lay = QVBoxLayout(d)
        form = QFormLayout()
        product = QComboBox()
        product.setObjectName("cmb_stock_product")
        by_pid = {}
        for pid, name, ptype, unit, q, avg, _last in stock:
            by_pid[pid] = (name, unit, q, avg)
            product.addItem(f"{name}  ·  {q:g} {unit} in stock", pid)
        if product_id:
            product.setCurrentIndex(max(0, product.findData(product_id)))
        qty = _qty_spin()
        qty.setObjectName("dspn_stock_qty")
        job = QComboBox()
        job.setObjectName("cmb_stock_job")
        for pid, code in codes:
            job.addItem(code, pid)
        if job_project_id:
            job.setCurrentIndex(max(0, job.findData(job_project_id)))
        form.addRow("Product:", product)
        form.addRow("Qty:", qty)
        form.addRow("To Job Code:", job)
        lay.addLayout(form)
        info = QLabel()
        info.setStyleSheet("color:#64748B;")
        lay.addWidget(info)
        lay.addStretch(1)
        bottom = QHBoxLayout()
        bottom.addStretch(1)
        cancel = QPushButton("Cancel")
        ok = QPushButton("  Add to the job")
        ok.setObjectName("btn_save_use_stock")
        ok.setStyleSheet(_PRIMARY_BTN)
        bottom.addWidget(cancel)
        bottom.addWidget(ok)
        lay.addLayout(bottom)

        def changed(*_a):
            pid = product.currentData()
            if pid in by_pid:
                name, unit, q, avg = by_pid[pid]
                qty.setMaximum(q)
                qty.setSuffix(f" {unit}")
                if qty.value() == 0:
                    qty.setValue(q)
                info.setText(f"Goes into the job at the stock price {_money(avg)} per {unit or 'unit'}.")
        product.currentIndexChanged.connect(changed)
        changed()
        cancel.clicked.connect(d.reject)
        done = {"ok": False}

        def save():
            pid, q, jid = product.currentData(), qty.value(), job.currentData()
            if not pid or q <= 0 or not jid:
                QMessageBox.warning(d, "Use stock", "Pick the product, the quantity and the Job Code.")
                return
            name, unit, _avail, avg = by_pid[pid]
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                cur.execute("INSERT INTO inventory_moves (PRODUCT_ID, QUANTITY, UNIT_PRICE, JOB_PROJECT_ID, NOTE, "
                            "CREATED_BY) VALUES (%s,%s,%s,%s,%s,%s)",
                            (pid, -q, avg, jid, f"Used in {job.currentText()}", getattr(self, "_current_username", None)))
                self._add_to_job_materials(cur, jid, pid, q, avg)
                conn.commit()
                cur.close()
                conn.close()
            except (MySQLError, RuntimeError) as e:
                QMessageBox.critical(d, "Database Error", str(e))
                return
            done["ok"] = True
            d.accept()
            show_toast(f"{q:g} {unit} of {name} added to {job.currentText()}.", "success", self)
            if jid == self._current_form_job_project_id() and hasattr(self, "_load_job_materials"):
                self._load_job_materials()

        ok.clicked.connect(save)
        d._product, d._qty, d._job = product, qty, job  # usado nos testes
        d.exec()
        return done["ok"]

    def _show_stock_history(self, parent=None):
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""SELECT m.CREATED_AT, pr.NAME, m.QUANTITY, pr.UNIT, m.UNIT_PRICE, m.NOTE, m.CREATED_BY
                           FROM inventory_moves m JOIN products pr ON pr.ID = m.PRODUCT_ID
                           ORDER BY m.ID DESC LIMIT 300""")
            rows = cur.fetchall()
            cur.close()
            conn.close()
        except (MySQLError, RuntimeError) as e:
            QMessageBox.critical(parent or self, "Database Error", str(e))
            return
        d = QDialog(parent or self)
        d.setWindowTitle("Stock history")
        d.resize(780, 460)
        lay = QVBoxLayout(d)
        t = QTableWidget(len(rows), 6)
        t.setHorizontalHeaderLabels(["When", "Product", "In / Out", "Price", "Note", "By"])
        t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        t.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        t.verticalHeader().setVisible(False)
        for r, (when, name, q, unit, price, note, by) in enumerate(rows):
            q = float(q)
            cells = [when.strftime("%m/%d/%Y %H:%M") if when else "", name, f"{q:+g} {unit or ''}",
                     _money(price), note or "", by or ""]
            for c, v in enumerate(cells):
                item = QTableWidgetItem(v)
                if c == 2:
                    item.setForeground(QColor("#15803D" if q > 0 else "#B91C1C"))
                t.setItem(r, c, item)
        lay.addWidget(t)
        d.exec()

    def _setup_stock_button(self):
        """Botão "Leftover" junto dos materiais do job."""
        btn = QPushButton("  Leftover → Stock")
        btn.setObjectName("btn_new_job_leftover")
        btn.setIcon(tabler_icon("package", "#37474F", 16))
        btn.setStyleSheet(_SMALL_BTN)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip("Material left over from this Job Code goes to Stock for the next job")
        btn.clicked.connect(lambda: self.open_leftover_dialog(self._current_form_job_project_id()))
        row = getattr(self, "_materials_btn_row", None)
        if row is not None:
            row.addWidget(btn, 1)
        else:
            btn.setVisible(False)
        self.ui.btn_new_job_leftover = btn
