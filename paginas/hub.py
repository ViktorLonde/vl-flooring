# -*- coding: utf-8 -*-
"""
Página "Registrations" com cartões (no lugar da lista que abria na sidebar).

Dois grupos:
  • Registrations — Companies, Contractors, Helpers, Work Types, Products
  • Tools — Projects, Documents, Compliance, Bank Reconciliation,
            Receipt Inbox, Job Site Inbox

Cada cartão só "aperta" o botão antigo correspondente (que continua
existindo, escondido), então o que cada tela faz não mudou — muda só o
caminho até ela. Os números dos cartões são atualizados sempre que a
página abre.

Métodos da MainWindow (mixin) — veja main_.py.
"""

from app_common import *  # noqa: F401,F403
from paginas.visual import tabler_icon

_CARD_QSS = """
QPushButton#hub_card {
    background-color: #FFFFFF; border: 1px solid #E3E8EE; border-radius: 12px; text-align: left;
    padding: 0px;
}
QPushButton#hub_card:hover { border: 1px solid #1E88E5; background-color: #F8FAFD; }
QPushButton#hub_card:disabled { background-color: #F5F8FC; }
QLabel#hub_card_title { color: #1C2B3A; font-size: 15px; font-weight: 700; background: transparent; }
QLabel#hub_card_sub { color: #6B7C93; font-size: 12px; background: transparent; }
QLabel#hub_card_icon { background: transparent; }
QLabel#hub_section { color: #6B7C93; font-size: 12px; font-weight: 700; background: transparent; }
QLabel#hub_title { color: #1C2B3A; font-size: 20px; font-weight: 700; background: transparent; }
QLabel#hub_intro { color: #6B7C93; font-size: 13px; background: transparent; }
"""

# (chave, ícone, título, descrição, botão antigo, consulta do número)
_REGISTRATION_CARDS = [
    ("companies", "building", "Companies", "Companies you work for",
     "btn_reg_companies", "SELECT COUNT(*) FROM companies"),
    ("contractors", "briefcase", "Contractors", "Contractors (1099) and W-9",
     "btn_reg_contractors", "SELECT COUNT(*) FROM contractors"),
    ("helpers", "users", "Helpers", "Your crew and how to pay them",
     "btn_reg_helpers", "SELECT COUNT(*) FROM helpers"),
    ("work_types", "wall", "Work Types", "Services and units",
     "btn_reg_work_types", "SELECT COUNT(*) FROM work_types"),
    ("products", "package", "Products", "Materials, prices and coverage",
     "btn_reg_products", "SELECT COUNT(*) FROM products"),
    ("rates", "cash", "Service Rates", "What you charge per SF / unit — job Value is calculated",
     "btn_tool_service_rates", "SELECT COUNT(DISTINCT WORK_TYPE_ID) FROM service_rates WHERE RATE > 0"),
]
_TOOL_CARDS = [
    ("projects", "chart-bar", "Projects", "All Job Codes and their status",
     "btn_reg_projects_dashboard", "SELECT COUNT(*) FROM job_projects"),
    ("documents", "folder", "Documents", "Files, photos and contracts",
     "btn_reg_documents", "SELECT COUNT(*) FROM documents"),
    ("compliance", "clipboard-check", "Compliance", "Licenses, insurance and due dates",
     "btn_reg_compliance", None),
    ("bank", "building-bank", "Bank Reconciliation", "Match bank statements to payments",
     "btn_reg_bank_reconciliation", "SELECT COUNT(*) FROM bank_transactions WHERE STATUS <> 'MATCHED'"),
    ("receipts", "inbox", "Receipt Inbox", "Receipts received by e-mail",
     "btn_reg_receipt_inbox", None),
    ("job_site", "map-pin", "Job Site Inbox", "Job site visits from e-mail",
     "btn_reg_job_site_inbox", "SELECT COUNT(*) FROM job_site_visits"),
    ("estimates", "receipt", "Estimates", "Quotes with PDF — convert to a job",
     "btn_tool_estimates", "SELECT COUNT(*) FROM estimates WHERE STATUS IN ('DRAFT','SENT','APPROVED')"),
    ("calculator", "calculator", "Material Calculator", "Boxes and buckets for an area",
     "btn_tool_calculator", None),
    ("mileage", "car", "Mileage", "Business miles for the tax deduction",
     "btn_tool_mileage", "SELECT COALESCE(ROUND(SUM(MILES)), 0) FROM mileage WHERE YEAR(TRIP_DATE) = YEAR(CURDATE())"),
    ("purchases", "receipt-2", "Purchases", "Supplier orders — prices, job materials, expense",
     "btn_tool_purchases", "SELECT COUNT(*) FROM purchases WHERE PURCHASE_DATE >= DATE_FORMAT(CURDATE(), '%Y-%m-01')"),
    ("stock", "package", "Stock", "Leftover material for the next job",
     "btn_tool_stock", "SELECT COUNT(*) FROM (SELECT PRODUCT_ID FROM inventory_moves GROUP BY PRODUCT_ID "
                       "HAVING SUM(QUANTITY) > 0.001) s"),
    ("board", "layout-dashboard", "Projects Board", "Pending → In Progress → Completed → Invoiced → Paid",
     "btn_tool_board", "SELECT COUNT(*) FROM job_projects WHERE COALESCE(STATUS, 'ACTIVE') <> 'PAID'"),
    ("weekly", "calendar", "Weekly Summary", "Days, value, helper pay, invoices, expenses",
     "btn_tool_weekly_summary", None),
    ("earnings", "cash", "Earnings per Day", "What a full day of work brings in — by month, job, customer",
     "btn_tool_earnings", None),
    ("accountant", "file-spreadsheet", "Accountant Package", "Year in Excel + receipts + invoices (.zip)",
     "btn_tool_accountant", None),
    ("usage", "chart-bar", "Material Usage", "Installed SF × flooring launched = waste %",
     "btn_tool_material_usage", None),
    ("calendar", "calendar", "Calendar Export", "Next 8 weeks of jobs for Google Calendar / phone",
     "btn_tool_calendar", "SELECT COUNT(*) FROM work_days WHERE WORK_DATE BETWEEN CURDATE() AND CURDATE() + INTERVAL 56 DAY "
                          "AND COALESCE(STATUS, '') <> 'CANCELLED'"),
    ("cleanup", "eraser", "Data Cleanup", "Old open days, fake clients, products without price",
     "btn_tool_cleanup",
     "SELECT (SELECT COUNT(*) FROM work_days WHERE (STATUS = 'PENDING' AND WORK_DATE < CURDATE()) OR "
     "(STATUS IN ('IN_PROGRESS','STARTED') AND WORK_DATE < CURDATE() - INTERVAL 7 DAY)) + "
     "(SELECT COUNT(*) FROM clients WHERE FULL_NAME LIKE '%— Select%') + "
     "(SELECT COUNT(*) FROM products WHERE COALESCE(PRICE, 0) = 0)"),
]
_COUNT_LABELS = {
    "companies": "registered", "contractors": "registered", "helpers": "registered",
    "work_types": "registered", "products": "registered", "projects": "job codes",
    "documents": "files", "bank": "unmatched", "job_site": "visits",
    "estimates": "open", "mileage": "miles this year",
    "purchases": "this month", "stock": "products in stock", "board": "open job codes",
    "cleanup": "to fix", "rates": "services priced", "calendar": "days scheduled",
}


class _HubCard(QPushButton):
    def __init__(self, icon_name, color, title, subtitle):
        super().__init__()
        self.setObjectName("hub_card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumSize(220, 112)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(4)
        icon = QLabel()
        icon.setObjectName("hub_card_icon")
        icon.setPixmap(tabler_icon(icon_name, color, 24).pixmap(24, 24))
        self.lbl_title = QLabel(title)
        self.lbl_title.setObjectName("hub_card_title")
        self.lbl_sub = QLabel(subtitle)
        self.lbl_sub.setObjectName("hub_card_sub")
        self.lbl_sub.setWordWrap(True)
        self._subtitle = subtitle
        for w in (icon, self.lbl_title, self.lbl_sub):
            w.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(icon)
        layout.addSpacing(4)
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_sub)
        layout.addStretch(1)

    def set_info(self, text):
        self.lbl_sub.setText(f"{self._subtitle}  ·  {text}" if text else self._subtitle)


class RegistrationsHubMixin:
    def _setup_registrations_hub(self):
        ui = self.ui
        page = QWidget()
        page.setObjectName("pg_registrations_hub")
        page.setStyleSheet(_CARD_QSS)
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        content.setObjectName("hub_content")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(10)
        scroll.setWidget(content)
        outer.addWidget(scroll)

        self._hub_cards = {}

        def section(title, cards, color):
            lbl = QLabel(title.upper())
            lbl.setObjectName("hub_section")
            layout.addSpacing(8)
            layout.addWidget(lbl)
            grid = QGridLayout()
            grid.setSpacing(14)
            for i, (key, icon, name, sub, button_attr, _sql) in enumerate(cards):
                card = _HubCard(icon, color, name, sub)
                old_button = getattr(ui, button_attr, None)
                if old_button is not None:
                    card.clicked.connect(old_button.click)
                else:
                    card.setEnabled(False)
                grid.addWidget(card, i // 3, i % 3)
                self._hub_cards[key] = card
            for col in range(3):
                grid.setColumnStretch(col, 1)
            layout.addLayout(grid)

        title = QLabel("Registrations")
        title.setObjectName("hub_title")
        intro = QLabel("Everything you register once and use in the jobs, plus the office tools.")
        intro.setObjectName("hub_intro")
        layout.addWidget(title)
        layout.addWidget(intro)
        section("Registrations", _REGISTRATION_CARDS, "#1D4ED8")
        section("Tools", _TOOL_CARDS, "#C2410C")
        layout.addStretch(1)

        ui.Pages.addWidget(page)
        ui.pg_registrations_hub = page
        self._hub_index = ui.Pages.indexOf(page)

        # O botão da sidebar abre a página (antes abria/fechava uma lista)
        try:
            ui.btn_registrations.clicked.disconnect()
        except (RuntimeError, TypeError):
            pass
        ui.btn_registrations.clicked.connect(lambda: self._go_to_page(self._hub_index, ui.btn_registrations))
        ui.frame_registrations_submenu.setVisible(False)
        ui.frame_registrations_submenu.setMaximumHeight(0)

    def _apply_hub_role_rules(self):
        """Some com os cartões que o perfil não pode usar (ex.: conciliação
        bancária é só do Admin)."""
        card = getattr(self, "_hub_cards", {}).get("bank")
        if card is not None:
            card.setVisible(self._role_rule("admin_pages"))
        for key in ("weekly", "accountant", "earnings"):  # valores e helper pay — só quem vê as finanças
            card = getattr(self, "_hub_cards", {}).get(key)
            if card is not None:
                card.setVisible(self._role_rule("finance"))

    def refresh_registrations_hub(self):
        """Atualiza os números dos cartões (chamado ao abrir a página)."""
        self._apply_hub_role_rules()
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            for key, *_rest, sql in _REGISTRATION_CARDS + _TOOL_CARDS:
                card = self._hub_cards.get(key)
                if card is None:
                    continue
                if key == "compliance":
                    due = getattr(self, "_compliance_due_soon", 0) or 0
                    card.set_info(f"{due} due in 30 days" if due else "")
                    continue
                if not sql:
                    continue
                try:
                    cur.execute(sql)
                    n = cur.fetchone()[0] or 0
                    card.set_info(f"{n} {_COUNT_LABELS.get(key, '')}".strip())
                except MySQLError:
                    card.set_info("")
            cur.close()
            conn.close()
        except (MySQLError, RuntimeError):
            logging.getLogger("vl_flooring").exception("registrations hub counts failed")
