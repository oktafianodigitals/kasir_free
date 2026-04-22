"""
main.py - Controller Utama Aplikasi Kasir v4
Routing antar dashboard, load UI modules, integrasi database
"""

import sys
import os
import logging
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout,
    QVBoxLayout, QLabel, QPushButton, QStackedWidget,
    QFrame, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger('main')

# ── Database modules ──
from database import Database
from db_gudang import DatabaseGudang

# ── UI modules ──
from ui.styles import DARK_THEME
from ui.dashboard import MainDashboard
from ui.transaction_ui import TransactionTab, DetailTransaksiTab
from ui.product_ui import ProductTab
from ui.warehouse_dashboard import WarehouseDashboard
from ui.settings_ui import SettingsTab

# ── Legacy modules ──
from invoice import InvoiceGenerator
from excel import ExcelExporter, ExcelExporterGudang


class NavButton(QPushButton):
    def __init__(self, icon_text: str, label: str, parent=None):
        super().__init__(f"  {icon_text}  {label}", parent)
        self.setObjectName("nav_btn")
        self.setCheckable(False)
        self.setMinimumHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setProperty("active", "false")

    def set_active(self, active: bool):
        self.setProperty("active", "true" if active else "false")
        self.style().unpolish(self)
        self.style().polish(self)


class KasirApp(QMainWindow):
    def __init__(self):
        super().__init__()
        logger.info("Memulai Kasir v4...")

        # ── Init databases ──
        self.db = Database()
        self.db_gudang = DatabaseGudang()
        pengaturan = self.db.get_pengaturan()
        if pengaturan:
            self.nama_toko = pengaturan.get('nama_toko')
            self.alamat_toko = pengaturan.get('alamat_toko')

        # ── Init legacy modules ──
        self.invoice_gen = InvoiceGenerator()
        self.excel_export = ExcelExporter()
        self.excel_export_gudang = ExcelExporterGudang(self.db_gudang)

        # ── Window setup ──
        self.setWindowTitle(self.nama_toko + " - Sistem Kasir v4")
        self.setWindowIcon(QIcon("database/icon.ico"))
        self.setGeometry(80, 60, 1280, 820)
        self.setMinimumSize(1100, 700)
        self.setStyleSheet(DARK_THEME)

        self._init_ui()
        self._load_initial_data()
        logger.info("Aplikasi siap.")

    def _init_ui(self):
        """Bangun layout utama: sidebar + content area."""
        root_widget = QWidget()
        self.setCentralWidget(root_widget)
        root_layout = QHBoxLayout(root_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Sidebar ──
        sidebar = self._build_sidebar()
        root_layout.addWidget(sidebar)

        # ── Content Stack ──
        self.stack = QStackedWidget()
        root_layout.addWidget(self.stack, 1)

        # ── Pages ──
        self.page_dashboard = MainDashboard(self.db, self.db_gudang)
        self.page_transaksi = TransactionTab(self.db, self.invoice_gen)
        self.page_detail = DetailTransaksiTab(self.db, self.invoice_gen, self.excel_export)
        self.page_produk = ProductTab(self.db, on_changed=self._on_produk_changed)
        self.page_gudang = WarehouseDashboard(self.db_gudang, self.db, self.excel_export_gudang)
        self.page_settings = SettingsTab(self.db)

        for page in [self.page_dashboard, self.page_transaksi, self.page_detail, 
                    self.page_produk, self.page_gudang, self.page_settings]:
            self.stack.addWidget(page)

        # Tampilkan dashboard awal
        self._navigate(0)

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(210)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(4)

        # App title
        title_lbl = QLabel(self.nama_toko)
        title_lbl.setObjectName("app_title")
        sub_lbl = QLabel(self.alamat_toko)
        sub_lbl.setObjectName("app_subtitle")
        layout.addWidget(title_lbl)
        layout.addWidget(sub_lbl)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("background-color: #313244; max-height: 1px; border: none;")
        layout.addWidget(div)
        layout.addSpacing(8)

        # Nav items: (icon, label, page_index)
        nav_items = [
            ("📊", "Dashboard", 0),
            ("🛒", "Transaksi", 1),
            ("📋", "Riwayat", 2),
            ("📦", "Produk", 3),
            ("🏭", "Gudang", 4),
            ("⚙️", "Pengaturan", 5),
        ]

        self.nav_buttons = []
        for icon, label, idx in nav_items:
            btn = NavButton(icon, label)
            btn.clicked.connect(lambda _, i=idx: self._navigate(i))
            layout.addWidget(btn)
            self.nav_buttons.append(btn)

        layout.addStretch()

        # Version label
        ver_lbl = QLabel("v4.0 — 2026")
        ver_lbl.setStyleSheet("color: #45475a; font-size: 9px; padding: 4px;")
        layout.addWidget(ver_lbl)

        return sidebar

    def _on_produk_changed(self):
        """Dipanggil setiap kali data produk berubah."""
        try:
            self.page_transaksi.load_combo_data()
        except Exception as e:
            logger.warning(f"Gagal refresh combo transaksi: {e}")
        try:
            self.page_gudang.refresh_all()
        except Exception as e:
            logger.warning(f"Gagal refresh gudang: {e}")
        logger.info("Produk berubah — combo transaksi & gudang di-refresh.")

    def _navigate(self, index: int):
        """Pindah ke halaman berdasarkan index."""
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.set_active(i == index)
        try:
            page = self.stack.currentWidget()
            if hasattr(page, 'refresh'):
                page.refresh()
            elif hasattr(page, 'refresh_all'):
                page.refresh_all()
            elif hasattr(page, 'load_data'):
                page.load_data()
        except Exception as e:
            logger.warning(f"Gagal refresh halaman {index}: {e}")
        logger.debug(f"Navigasi ke halaman {index}")

    def _load_initial_data(self):
        """Load data awal ke semua page yang membutuhkannya."""
        try:
            self.page_transaksi.load_combo_data()
            self.page_detail.load_data()
        except Exception as e:
            logger.error(f"Gagal load initial data: {e}")


def main():
    
    app = QApplication(sys.argv)
    app.setApplicationVersion("2.1")
    app.setStyle('Fusion')
    try:
        app.setWindowIcon(QIcon("database/icon.ico"))
    except Exception:
        pass
    window = KasirApp()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()