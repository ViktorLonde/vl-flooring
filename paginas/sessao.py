# -*- coding: utf-8 -*-
"""
Sessão do usuário:

• Menu no nome do usuário (canto de cima): "Switch user" e "Exit".
• O app lembra a última tela aberta, o tamanho da janela e a aba de
  Receivables (por computador, em QSettings). Os filtros de data de Job
  Records NÃO são lembrados de propósito: uma data "até" antiga esconderia
  os jobs novos.
• Resumo "Needs your attention" no topo da Home depois do login (invoices
  atrasadas, compliance vencendo, jobs pendentes de dias anteriores e
  jobs sem dados), cada item com um clique para ir até lá.

Métodos da MainWindow (mixin) — veja main_.py.
"""

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QMenu

from app_common import *  # noqa: F401,F403
from paginas.visual import tabler_icon

_SETTINGS = ("VL Flooring", "app")

_ATTENTION_QSS = """
#frame_attention { background-color: #FFFFFF; border: 1px solid #E3E8EE; border-radius: 10px; }
#frame_attention QLabel { background: transparent; }
#lbl_attention_title { color: #1C2B3A; font-size: 14px; font-weight: 700; }
#frame_attention QPushButton {
    background-color: #F5F8FC; color: #1C2B3A; border: 1px solid #E3E8EE; border-radius: 8px;
    padding: 7px 12px; font-size: 13px; text-align: left;
}
#frame_attention QPushButton:hover { background-color: #EEF4FB; border-color: #90B8E0; }
#btn_attention_close { background: transparent; border: none; padding: 4px; }
"""


class SessionMixin:
    # ── menu do usuário ───────────────────────────────────────────────
    def _setup_user_menu(self):
        lbl = self.ui.lbl_user
        lbl.setCursor(Qt.CursorShape.PointingHandCursor)
        lbl.setToolTip("Switch user or exit")
        lbl.installEventFilter(self)
        lbl.setMaximumWidth(260)

    def _show_user_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu { background: #FFFFFF; border: 1px solid #D0D7DE; border-radius: 8px; padding: 6px; } "
            "QMenu::item { padding: 8px 18px 8px 10px; border-radius: 6px; color: #1C2B3A; } "
            "QMenu::item:selected { background: #EEF4FB; color: #0D47A1; } "
            "QMenu::separator { height: 1px; background: #E3E8EE; margin: 4px 6px; }")
        header = menu.addAction(self.ui.lbl_user.toolTip() if self._current_username else "")
        header.setEnabled(False)
        menu.addSeparator()
        switch = menu.addAction(tabler_icon("arrows-exchange", "#37474F", 16), "Switch user")
        leave = menu.addAction(tabler_icon("logout", "#37474F", 16), "Exit")
        lbl = self.ui.lbl_user
        chosen = menu.exec(lbl.mapToGlobal(lbl.rect().bottomLeft()))
        if chosen is switch:
            self._sign_out()
        elif chosen is leave:
            self.close()

    def _sign_out(self):
        if getattr(self, "_job_form_dirty", False):
            answer = QMessageBox.question(
                self, "Unsaved changes",
                "You have unsaved changes in the current Job. Discard them and switch user?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                return
            self._job_form_dirty = False
        self.save_ui_state()
        logging.getLogger("vl_flooring").info("sign out: %s", self._current_username)
        self.signed_out.emit()

    # ── lembrar onde parou ────────────────────────────────────────────
    def save_ui_state(self):
        if not self._current_username:
            return
        s = QSettings(*_SETTINGS)
        s.setValue("window/geometry", self.saveGeometry())
        s.setValue("window/maximized", self.isMaximized())
        s.setValue("ui/last_page", self.ui.Pages.currentIndex())
        s.setValue("ui/receivables_tab", self.ui.tabWidget_receivables.currentIndex())
        s.setValue("ui/jobs_tab", self.ui.tabWidget_jobs.currentIndex())

    def restore_ui_state(self):
        """Chamado depois do login. Volta pra última tela (se o perfil
        permitir) e devolve True se a janela deve abrir maximizada."""
        s = QSettings(*_SETTINGS)
        geometry = s.value("window/geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)
        page = s.value("ui/last_page", 0, type=int)
        buttons = {0: self.ui.btn_home, 1: self.ui.btn_jobs, 2: self.ui.btn_reg_companies,
                   3: self.ui.btn_reg_contractors, 4: self.ui.btn_reg_work_types, 5: self.ui.btn_nav_receivables,
                   6: self.ui.btn_customer, 7: self.ui.btn_user, 8: self.ui.btn_reg_products, 9: self.ui.btn_settings,
                   getattr(self, "_hub_index", -1): self.ui.btn_registrations}
        if page in buttons and page != 0:
            self._go_to_page(page, buttons[page])
        tab = s.value("ui/receivables_tab", 0, type=int)
        if 0 <= tab < self.ui.tabWidget_receivables.count() and self.ui.tabWidget_receivables.isTabVisible(tab):
            self.ui.tabWidget_receivables.setCurrentIndex(tab)
        jobs_tab = s.value("ui/jobs_tab", 0, type=int)
        if 0 <= jobs_tab < self.ui.tabWidget_jobs.count():
            self.ui.tabWidget_jobs.setCurrentIndex(jobs_tab)
        return s.value("window/maximized", True, type=bool) or geometry is None

    # ── precisa de atenção ────────────────────────────────────────────
    def _collect_attention_items(self):
        """Lista de (texto, ação) com o que precisa de atenção agora."""
        items = []
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            overdue = 0
            for table in ("contractor_invoices", "company_invoices", "client_invoices"):
                cur.execute(f"SELECT COUNT(*) FROM {table} WHERE STATUS IN ('PENDING','PARTIAL') "
                            "AND DATEDIFF(CURDATE(), GENERATED_AT) > 30")
                overdue += cur.fetchone()[0] or 0
            cur.execute("SELECT COUNT(*) FROM work_days WHERE STATUS = 'PENDING' AND WORK_DATE < CURDATE()")
            old_pending = cur.fetchone()[0] or 0
            cur.execute("SELECT COUNT(*) FROM work_days WHERE WORK_DATE >= CURDATE() - INTERVAL 30 DAY "
                        "AND (JOB_PROJECT_ID IS NULL OR COALESCE(JOB_ADDRESS,'') = '' OR COALESCE(VALUE,0) = 0)")
            incomplete = cur.fetchone()[0] or 0
            cur.close()
            conn.close()
        except (MySQLError, RuntimeError):
            logging.getLogger("vl_flooring").exception("attention summary failed")
            return items

        def plural(n, word):
            return f"{n} {word}{'' if n == 1 else 's'}"

        if overdue:
            items.append(("alert-triangle", "#C62828", f"{plural(overdue, 'invoice')} overdue (30+ days)",
                          lambda: self._go_to_page(5, self.ui.btn_nav_receivables)))
        due = getattr(self, "_compliance_due_soon", 0) or 0
        if due:
            items.append(("clipboard-check", "#B26A00", f"{plural(due, 'compliance item')} due in the next 30 days",
                          self.open_compliance_manager_dialog))
        if old_pending:
            items.append(("hourglass", "#B26A00", f"{plural(old_pending, 'job')} from past days still PENDING",
                          self._show_old_pending_jobs))
        backup_item = self._backup_attention_item()
        if backup_item:
            items.append(backup_item)
        if incomplete:
            items.append(("clipboard-list", "#1565C0",
                          f"{plural(incomplete, 'job')} from the last 30 days missing information",
                          self.open_incomplete_jobs_dialog))
        return items

    def _backup_attention_item(self):
        """Avisa se o último backup tem mais de 2 dias (o backup automático só
        roda com o disco D: ligado no notebook). Só para Admin."""
        if not self._role_rule("admin_pages"):
            return None
        try:
            import backup_db
            backups = backup_db.list_backups()
        except Exception:
            return None
        import socket
        server = (self.db_config.get("server_name") or "").lower()
        on_server = self.db_config.get("host") in ("127.0.0.1", "localhost") or socket.gethostname().lower() == server
        if not backups:
            if not on_server:
                return None  # este computador não guarda backups
            return ("database-import", "#C62828", "No database backup found on this computer",
                    self._run_backup_now)
        age = (datetime.now() - backups[0][1]).days
        if age < 2:
            return None
        return ("database-import", "#C62828", f"Last database backup was {age} days ago — back up now",
                self._run_backup_now if on_server else (lambda: None))

    def _run_backup_now(self):
        import backup_db
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            path = backup_db.run_backup()
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "Backup failed", f"The backup could not be made:\n{e}")
            return
        QApplication.restoreOverrideCursor()
        from paginas.moderno import show_toast
        show_toast(f"Backup saved: {os.path.basename(path)}", "success", self)
        self.show_attention_summary()

    def _show_old_pending_jobs(self):
        self._go_to_page(1, self.ui.btn_jobs)
        self.ui.tabWidget_jobs.setCurrentWidget(self.ui.tab_jobs_master)
        idx = self.ui.cmb_filter_status.findText("PENDING")
        if idx >= 0:
            self.ui.cmb_filter_status.setCurrentIndex(idx)
        self.load_work_days()

    def show_attention_summary(self):
        """Mostra o quadro "Needs your attention" no topo da Home."""
        old = getattr(self.ui, "frame_attention", None)
        if old is not None:
            old.deleteLater()
            self.ui.frame_attention = None
        items = self._collect_attention_items()
        if not items:
            return
        frame = QFrame(self.ui.pg_home)
        frame.setObjectName("frame_attention")
        frame.setStyleSheet(_ATTENTION_QSS)
        outer = QVBoxLayout(frame)
        outer.setContentsMargins(16, 12, 12, 14)
        outer.setSpacing(8)
        head = QHBoxLayout()
        bell = QLabel()
        bell.setPixmap(tabler_icon("bell", "#E8590C", 18).pixmap(18, 18))
        title = QLabel("Needs your attention")
        title.setObjectName("lbl_attention_title")
        close = QPushButton()
        close.setObjectName("btn_attention_close")
        close.setIcon(tabler_icon("x", "#6B7C93", 16))
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.setToolTip("Hide")
        close.clicked.connect(frame.hide)
        head.addWidget(bell)
        head.addWidget(title, 1)
        head.addWidget(close)
        outer.addLayout(head)
        row = QHBoxLayout()
        row.setSpacing(8)
        for icon, color, text, action in items:
            btn = QPushButton(f"  {text}")
            btn.setIcon(tabler_icon(icon, color, 16))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(action)
            row.addWidget(btn)
        row.addStretch(1)
        outer.addLayout(row)
        self.ui.layout_home_page.insertWidget(0, frame)
        self.ui.frame_attention = frame
        total = len(items)
        if self.ui.Pages.currentIndex() != 0:
            from paginas.moderno import show_toast
            show_toast(f"{total} thing{'s' if total > 1 else ''} need your attention — see Home.", "info", self)
