# ============================================================
# VL FLOORING — TeamViewer-Inspired StyleSheet
# Para aplicar: cole este QSS no MainWindow.setStyleSheet()
# ============================================================

TEAMVIEWER_QSS = """

/* ── BASE ───────────────────────────────────────────────── */
QMainWindow, QWidget {
    background-color: #F0F4F8;
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
    color: #1C2B3A;
}

* {
    border: none;
    outline: none;
}

/* ── SIDEBAR (Left_container) ───────────────────────────── */
#Left_container {
    background-color: #1C2B3A;
    border-right: none;
    min-width: 200px;
    max-width: 220px;
}

/* Logo label dentro da sidebar */
#Left_container QLabel {
    color: #FFFFFF;
    font-size: 15px;
    font-weight: bold;
    padding: 14px 8px 10px 8px;
    background-color: #1C2B3A;
    border-bottom: 1px solid #263849;
}

/* ── BOTÕES DE NAVEGAÇÃO (sidebar) ─────────────────────── */
#Left_container QPushButton {
    background-color: transparent;
    color: #8AAEC8;
    text-align: left;
    padding: 10px 16px;
    font-size: 13px;
    font-weight: 500;
    border-left: 3px solid transparent;
    border-radius: 0px;
    margin: 1px 0px;
}

#Left_container QPushButton:hover {
    background-color: #263849;
    color: #FFFFFF;
    border-left: 3px solid #5B8DB8;
    border-radius: 0px;
}

#Left_container QPushButton:checked,
#Left_container QPushButton:pressed {
    background-color: #1A4A7A;
    color: #FFFFFF;
    border-left: 3px solid #1E88E5;
    border-radius: 0px;
    font-weight: 600;
}

/* Botão toggle (menu) */
#btn_toggle {
    padding: 8px 12px;
    color: #8AAEC8;
}

#btn_toggle:hover {
    color: #FFFFFF;
    background-color: #263849;
}

/* ── CONTAINER PRINCIPAL ────────────────────────────────── */
#Main_container {
    background-color: #F0F4F8;
}

/* ── TOPBAR (Top_frame) ─────────────────────────────────── */
#Top_frame {
    background-color: #FFFFFF;
    border-bottom: 1px solid #DDE4EE;
    min-height: 50px;
    max-height: 50px;
}

#Top_frame QLabel {
    color: #1C2B3A;
    font-size: 16px;
    font-weight: 600;
    padding: 0px 8px;
    background-color: transparent;
    border: none;
}

/* Label do usuário logado */
#lbl_user {
    color: #FFFFFF;
    background-color: #1565C0;
    font-size: 12px;
    font-weight: 600;
    padding: 4px 12px;
    border-radius: 20px;
}

/* ── STACKED WIDGET / PÁGINAS ───────────────────────────── */
QStackedWidget {
    background-color: #F0F4F8;
}

/* ── TABS ────────────────────────────────────────────────── */
QTabWidget::pane {
    border: none;
    background-color: #F0F4F8;
}

QTabBar {
    background-color: #FFFFFF;
    border-bottom: 1px solid #DDE4EE;
}

QTabBar::tab {
    background-color: transparent;
    color: #6B7C93;
    padding: 12px 20px;
    font-size: 13px;
    font-weight: 500;
    border-bottom: 2px solid transparent;
    border-radius: 0px;
    margin-bottom: 0px;
}

QTabBar::tab:hover {
    color: #1C2B3A;
    background-color: #F5F8FC;
}

QTabBar::tab:selected {
    color: #1565C0;
    border-bottom: 2px solid #1E88E5;
    font-weight: 600;
    background-color: #FFFFFF;
}

/* ── FRAMES INTERNOS (cards de formulário) ──────────────── */
QFrame {
    background-color: #FFFFFF;
    border-radius: 8px;
}

/* Frame do cabeçalho do card (frame_2, frame_7) */
#frame_2, #frame_7 {
    background-color: #1565C0;
    border-radius: 0px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
}

#frame_7 {
    border-top-left-radius: 0px;
    border-top-right-radius: 0px;
    border-bottom-left-radius: 8px;
    border-bottom-right-radius: 8px;
}

/* Card principal de registro */
#frame {
    background-color: #FFFFFF;
    border-radius: 8px;
    border: 1px solid #DDE4EE;
    max-width: 520px;
}

/* Divisores internos */
#frame_3, #frame_4 {
    background-color: #EEF2F7;
    border-radius: 0px;
    max-height: 1px;
}

/* Frame da tabela de usuários */
#frame_5 {
    background-color: #FFFFFF;
    border-radius: 8px;
    border: 1px solid #DDE4EE;
}

/* Frame de edição/update */
#frame_user_management_update {
    background-color: #FFFFFF;
    border-radius: 8px;
    border: 1px solid #DDE4EE;
    margin-top: 12px;
}

/* ── LABELS NO FORMULÁRIO ───────────────────────────────── */
QLabel {
    color: #6B7C93;
    font-size: 11px;
    font-weight: 600;
    background-color: transparent;
}

/* Labels dentro do card azul */
#frame_2 QLabel, #frame_7 QLabel {
    color: #FFFFFF;
    font-size: 16px;
    font-weight: 700;
    background-color: transparent;
}

/* Labels de campos (estilo ALL-CAPS pequeno) */
#frame QLabel {
    color: #6B7C93;
    font-size: 11px;
    font-weight: 600;
    background-color: transparent;
}

/* ── INPUTS ─────────────────────────────────────────────── */
QLineEdit {
    background-color: #F5F8FC;
    color: #1C2B3A;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    selection-background-color: #BBDEFB;
}

QLineEdit:focus {
    border: 1px solid #1E88E5;
    background-color: #FFFFFF;
}

QLineEdit:disabled {
    background-color: #EEF2F7;
    color: #9BADBF;
    border: 1px solid #E0E7EF;
}

QLineEdit::placeholder {
    color: #9BADBF;
}

/* ── COMBOBOX ───────────────────────────────────────────── */
QComboBox {
    background-color: #F5F8FC;
    color: #1C2B3A;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 7px 12px;
    font-size: 13px;
    min-height: 30px;
}

QComboBox:focus, QComboBox:on {
    border: 1px solid #1E88E5;
    background-color: #FFFFFF;
}

QComboBox::drop-down {
    border: none;
    width: 22px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #6B7C93;
    width: 0;
    height: 0;
    margin-right: 6px;
}

QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    selection-background-color: #E3F2FD;
    selection-color: #1565C0;
    padding: 4px;
}

/* ── BOTÃO PRINCIPAL (Create User / Save) ───────────────── */
#btn_user_create_user {
    background-color: #1565C0;
    color: #FFFFFF;
    border-radius: 6px;
    padding: 10px 24px;
    font-size: 14px;
    font-weight: 700;
    min-height: 42px;
}

#btn_user_create_user:hover {
    background-color: #1E88E5;
}

#btn_user_create_user:pressed {
    background-color: #0D47A1;
}

/* ── BOTÕES DE AÇÃO (Save, Delete, Update, Refresh, Print) */
#btn_save_user_3, #btn_save_user_6 {
    background-color: #1565C0;
    color: #FFFFFF;
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 600;
    min-height: 32px;
}

#btn_save_user_3:hover, #btn_save_user_6:hover {
    background-color: #1E88E5;
}

#btn_delete_user_3 {
    background-color: #C62828;
    color: #FFFFFF;
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 600;
    min-height: 32px;
}

#btn_delete_user_3:hover {
    background-color: #E53935;
}

#btn_delete_user_6 {
    background-color: #2E7D32;
    color: #FFFFFF;
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 600;
    min-height: 32px;
}

#btn_delete_user_6:hover {
    background-color: #43A047;
}

#btn_refresh_users_3 {
    background-color: #37474F;
    color: #FFFFFF;
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 600;
    min-height: 32px;
}

#btn_refresh_users_3:hover {
    background-color: #546E7A;
}

/* ── TABELA ─────────────────────────────────────────────── */
QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #DDE4EE;
    border-radius: 6px;
    gridline-color: #EEF2F7;
    selection-background-color: #E3F2FD;
    selection-color: #1C2B3A;
    font-size: 13px;
}

QTableWidget::item {
    padding: 8px 10px;
    border-bottom: 1px solid #EEF2F7;
}

QTableWidget::item:selected {
    background-color: #E3F2FD;
    color: #1565C0;
}

QHeaderView::section {
    background-color: #F5F8FC;
    color: #6B7C93;
    font-size: 11px;
    font-weight: 700;
    padding: 10px;
    border: none;
    border-bottom: 2px solid #DDE4EE;
    border-right: 1px solid #EEF2F7;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

QHeaderView::section:first {
    border-top-left-radius: 6px;
}

QHeaderView::section:last {
    border-right: none;
    border-top-right-radius: 6px;
}

/* ── SCROLLBARS ─────────────────────────────────────────── */
QScrollBar:vertical {
    background: #F0F4F8;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #CBD5E1;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #90A4AE;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background: #F0F4F8;
    height: 8px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background: #CBD5E1;
    border-radius: 4px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background: #90A4AE;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* ── STATUS BAR ─────────────────────────────────────────── */
QStatusBar {
    background-color: #1C2B3A;
    color: #8AAEC8;
    font-size: 12px;
    padding: 2px 10px;
}

"""

# ============================================================
# COMO USAR:
#
# No seu arquivo main.py (ou onde cria a MainWindow):
#
#   from teamviewer_style import TEAMVIEWER_QSS
#
#   app = QApplication(sys.argv)
#   window = MainWindow()
#   window.setStyleSheet(TEAMVIEWER_QSS)   # <- aplica aqui
#   window.show()
#   sys.exit(app.exec())
#
# OU no setupUi, substitua o MainWindow.setStyleSheet(...) por:
#   MainWindow.setStyleSheet(TEAMVIEWER_QSS)
# ============================================================
