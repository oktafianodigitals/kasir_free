"""
ui/styles.py - Stylesheet terpusat untuk seluruh aplikasi
"""

DARK_THEME = """
QMainWindow, QDialog {
    background-color: #1e1e2e;
    color: #cdd6f4;
}

QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 11px;
}

/* ── Sidebar ── */
QFrame#sidebar {
    background-color: #181825;
    border-right: 2px solid #313244;
    border-radius: 0px;
}

QLabel#app_title {
    color: #cba6f7;
    font-size: 14px;
    font-weight: bold;
    padding: 8px 4px;
}

QLabel#app_subtitle {
    color: #6c7086;
    font-size: 10px;
    padding: 0px 4px 12px 4px;
}

QPushButton#nav_btn {
    background-color: transparent;
    color: #a6adc8;
    border: none;
    border-radius: 8px;
    padding: 12px 16px;
    text-align: left;
    font-size: 12px;
    font-weight: normal;
}

QPushButton#nav_btn:hover {
    background-color: #313244;
    color: #cdd6f4;
}

QPushButton#nav_btn[active="true"] {
    background-color: #45475a;
    color: #cba6f7;
    font-weight: bold;
    border-left: 3px solid #cba6f7;
}

/* ── Content Area ── */
QStackedWidget {
    background-color: #1e1e2e;
}

/* ── Cards / Group Boxes ── */
QGroupBox {
    font-weight: bold;
    font-size: 12px;
    color: #cdd6f4;
    border: 1px solid #313244;
    border-radius: 8px;
    margin-top: 14px;
    padding: 12px 8px 8px 8px;
    background-color: #24273a;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #cba6f7;
}

/* ── Stat Cards ── */
QFrame#stat_card {
    background-color: #24273a;
    border: 1px solid #313244;
    border-radius: 10px;
    padding: 8px;
}

QLabel#stat_value {
    color: #a6e3a1;
    font-size: 22px;
    font-weight: bold;
}

QLabel#stat_label {
    color: #6c7086;
    font-size: 10px;
}

QLabel#stat_icon {
    font-size: 26px;
}

/* ── Inputs ── */
QLineEdit, QSpinBox, QComboBox, QTextEdit, QDateEdit {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 8px 10px;
    font-size: 11px;
    selection-background-color: #585b70;
}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 2px solid #cba6f7;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    selection-background-color: #585b70;
}

/* ── Buttons ── */
QPushButton {
    background-color: #cba6f7;
    color: #1e1e2e;
    border: none;
    border-radius: 6px;
    padding: 9px 18px;
    font-size: 11px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #d4b3fa;
}

QPushButton:pressed {
    background-color: #b491e4;
}

QPushButton:disabled {
    background-color: #45475a;
    color: #6c7086;
}

QPushButton[class="danger"] {
    background-color: #f38ba8;
    color: #1e1e2e;
}

QPushButton[class="danger"]:hover {
    background-color: #f5a0b5;
}

QPushButton[class="success"] {
    background-color: #a6e3a1;
    color: #1e1e2e;
}

QPushButton[class="success"]:hover {
    background-color: #b6f0b2;
}

QPushButton[class="warning"] {
    background-color: #f9e2af;
    color: #1e1e2e;
}

QPushButton[class="info"] {
    background-color: #89dceb;
    color: #1e1e2e;
}

QPushButton[class="secondary"] {
    background-color: #45475a;
    color: #cdd6f4;
}

QPushButton[class="secondary"]:hover {
    background-color: #585b70;
}

/* ── Tables ── */
QTableWidget {
    background-color: #24273a;
    alternate-background-color: #1e1e2e;
    gridline-color: #313244;
    selection-background-color: #585b70;
    selection-color: #cdd6f4;
    border: 1px solid #313244;
    border-radius: 6px;
    font-size: 11px;
}

QTableWidget::item {
    padding: 8px 10px;
    border-bottom: 1px solid #313244;
}

QTableWidget::item:selected {
    background-color: #45475a;
    color: #cdd6f4;
}

QHeaderView::section {
    background-color: #181825;
    color: #cba6f7;
    padding: 10px 10px;
    border: none;
    border-right: 1px solid #313244;
    font-weight: bold;
    font-size: 11px;
}

/* ── Scrollbars ── */
QScrollBar:vertical {
    background-color: #1e1e2e;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background-color: #45475a;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background-color: #585b70;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* ── Labels ── */
QLabel {
    color: #cdd6f4;
}

QLabel#section_title {
    font-size: 18px;
    font-weight: bold;
    color: #cdd6f4;
    padding-bottom: 4px;
}

QLabel#section_sub {
    color: #6c7086;
    font-size: 11px;
}

QLabel#total_label {
    font-size: 16px;
    font-weight: bold;
    color: #a6e3a1;
    padding: 8px;
    background-color: #24273a;
    border-radius: 6px;
}

QLabel#alert_menipis {
    color: #f9e2af;
    font-weight: bold;
}

QLabel#alert_habis {
    color: #f38ba8;
    font-weight: bold;
}

/* ── Divider Line ── */
QFrame[frameShape="4"], QFrame[frameShape="5"] {
    background-color: #313244;
    border: none;
    max-height: 1px;
}

/* ── Message Boxes ── */
QMessageBox {
    background-color: #24273a;
}
QMessageBox QLabel {
    color: #cdd6f4;
}

/* ── Dialog ── */
QDialog {
    background-color: #24273a;
}
"""

# Badge styles
BADGE_LUNAS = (
    "background-color: #a6e3a1; color: #1e1e2e; "
    "border-radius: 4px; padding: 3px 8px; font-weight: bold; font-size: 10px;"
)
BADGE_BELUM = (
    "background-color: #f38ba8; color: #1e1e2e; "
    "border-radius: 4px; padding: 3px 8px; font-weight: bold; font-size: 10px;"
)
BADGE_MENIPIS = (
    "background-color: #f9e2af; color: #1e1e2e; "
    "border-radius: 4px; padding: 3px 8px; font-weight: bold; font-size: 10px;"
)
BADGE_HABIS = (
    "background-color: #f38ba8; color: #1e1e2e; "
    "border-radius: 4px; padding: 3px 8px; font-weight: bold; font-size: 10px;"
)
BADGE_OK = (
    "background-color: #a6e3a1; color: #1e1e2e; "
    "border-radius: 4px; padding: 3px 8px; font-weight: bold; font-size: 10px;"
)

# Table button styles - Warna berbeda untuk setiap tombol
TABLE_BTN_VIEW = """
    QPushButton {
        background-color: #89dceb;
        color: #1e1e2e;
        border: none;
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 12px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #a5e7f0;
    }
    QPushButton:pressed {
        background-color: #6dd4e3;
    }
"""

TABLE_BTN_EDIT = """
    QPushButton {
        background-color: #f9e2af;
        color: #1e1e2e;
        border: none;
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 12px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #fae8c0;
    }
    QPushButton:pressed {
        background-color: #f5d89a;
    }
"""

TABLE_BTN_PRINT = """
    QPushButton {
        background-color: #a6e3a1;
        color: #1e1e2e;
        border: none;
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 12px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #b6f0b2;
    }
    QPushButton:pressed {
        background-color: #8fd689;
    }
"""

TABLE_BTN_DELETE = """
    QPushButton {
        background-color: #f38ba8;
        color: #1e1e2e;
        border: none;
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 12px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #f5a0b5;
    }
    QPushButton:pressed {
        background-color: #e06c8b;
    }
"""