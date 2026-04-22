"""
ui/dashboard.py - Dashboard Utama (Beranda)
Menampilkan statistik ringkas transaksi & stok hari ini.
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QSizePolicy, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QGroupBox
)
from PyQt6.QtCore import Qt
from ui.styles import BADGE_LUNAS, BADGE_BELUM, BADGE_MENIPIS, BADGE_HABIS
from utils.helpers import format_rupiah

logger = logging.getLogger('dashboard_ui')


def _stat_card(icon, value, label, color="#a6e3a1"):
    card = QFrame()
    card.setObjectName("stat_card")
    card.setMinimumWidth(160)
    card.setMinimumHeight(100)
    card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    layout = QVBoxLayout(card)
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(4)

    icon_lbl = QLabel(icon)
    icon_lbl.setObjectName("stat_icon")

    val_lbl = QLabel(value)
    val_lbl.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold;")

    lab_lbl = QLabel(label)
    lab_lbl.setObjectName("stat_label")

    layout.addWidget(icon_lbl)
    layout.addWidget(val_lbl)
    layout.addWidget(lab_lbl)
    return card, val_lbl


class MainDashboard(QWidget):
    """Halaman beranda dashboard utama."""

    def __init__(self, db_utama, db_gudang, parent=None):
        super().__init__(parent)
        self.db = db_utama
        self.db_gudang = db_gudang
        self._init_ui()
        self.refresh()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(20)

        # ── Header ──
        hdr = QHBoxLayout()
        title = QLabel("📊  Dashboard Utama")
        title.setObjectName("section_title")
        sub = QLabel("Ringkasan performa penjualan dan kondisi stok")
        sub.setObjectName("section_sub")
        btn_refresh = QPushButton("🔄  Refresh")
        btn_refresh.setProperty("class", "secondary")
        btn_refresh.setFixedWidth(120)
        btn_refresh.clicked.connect(self.refresh)
        hdr.addWidget(title)
        hdr.addWidget(sub, 1)
        hdr.addWidget(btn_refresh)
        root.addLayout(hdr)

        # ── Stat Cards ──
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)

        card1, self.lbl_total_trx = _stat_card("🧾", "0", "Total Transaksi")
        card2, self.lbl_trx_hari_ini = _stat_card("📅", "0", "Transaksi Hari Ini", "#89dceb")
        card3, self.lbl_pendapatan_hari_ini = _stat_card("💵", "Rp 0", "Pendapatan Hari Ini", "#f9e2af")
        card4, self.lbl_total_pendapatan = _stat_card("💰", "Rp 0", "Total Pendapatan Lunas", "#a6e3a1")
        card5, self.lbl_stok_alert = _stat_card("⚠️", "0", "Stok Perlu Perhatian", "#f38ba8")

        for card in [card1, card2, card3, card4, card5]:
            stats_row.addWidget(card)
        root.addLayout(stats_row)

        # ── Bawah: Transaksi Terbaru + Stok Alert ──
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(16)

        # Transaksi terbaru
        trx_group = QGroupBox("🧾  Transaksi Terbaru")
        trx_layout = QVBoxLayout(trx_group)
        self.tbl_recent_trx = QTableWidget()
        self.tbl_recent_trx.setColumnCount(5)
        self.tbl_recent_trx.setHorizontalHeaderLabels([
            "Invoice", "Nama Pembeli", "Total", "Status", "Tanggal"
        ])
        self.tbl_recent_trx.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_recent_trx.setMaximumHeight(250)
        self.tbl_recent_trx.setAlternatingRowColors(True)
        trx_layout.addWidget(self.tbl_recent_trx)

        # Stok menipis/habis
        stok_group = QGroupBox("⚠️  Stok Perlu Perhatian")
        stok_layout = QVBoxLayout(stok_group)
        self.tbl_stok_alert = QTableWidget()
        self.tbl_stok_alert.setColumnCount(5)
        self.tbl_stok_alert.setHorizontalHeaderLabels([
            "Kategori", "Warna", "Ukuran", "Jumlah", "Status"
        ])
        self.tbl_stok_alert.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_stok_alert.setMaximumHeight(250)
        self.tbl_stok_alert.setAlternatingRowColors(True)
        stok_layout.addWidget(self.tbl_stok_alert)

        bottom_row.addWidget(trx_group, 6)
        bottom_row.addWidget(stok_group, 4)
        root.addLayout(bottom_row)

    def refresh(self):
        """Refresh semua data dashboard."""
        try:
            stats = self.db.get_statistik_dashboard()
            self.lbl_total_trx.setText(str(stats['total_transaksi']))
            self.lbl_trx_hari_ini.setText(str(stats['transaksi_hari_ini']))
            self.lbl_pendapatan_hari_ini.setText(format_rupiah(stats['pendapatan_hari_ini']))
            self.lbl_total_pendapatan.setText(format_rupiah(stats['total_pendapatan']))
        except Exception as e:
            logger.error(f"Gagal load statistik dashboard: {e}")

        try:
            stok_stats = self.db_gudang.get_statistik_gudang()
            alert_count = stok_stats['stok_habis'] + stok_stats['stok_menipis']
            self.lbl_stok_alert.setText(str(alert_count))
        except Exception as e:
            logger.warning(f"Gagal load stok stats: {e}")

        self._load_recent_trx()
        self._load_stok_alerts()

    def _load_recent_trx(self):
        try:
            data = self.db.get_all_transaksi()
            recent = list(data)[:10]
            self.tbl_recent_trx.setRowCount(len(recent))
            for i, row in enumerate(recent):
                id_, nama, subtotal, pembayaran, status, tanggal, no_invoice = row
                vals = [no_invoice, nama, format_rupiah(subtotal), status, tanggal]
                for j, v in enumerate(vals):
                    cell = QTableWidgetItem(v)
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.tbl_recent_trx.setItem(i, j, cell)

                badge = QLabel(status)
                badge.setStyleSheet(BADGE_LUNAS if status == 'LUNAS' else BADGE_BELUM)
                badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tbl_recent_trx.setCellWidget(i, 3, badge)
        except Exception as e:
            logger.error(f"Gagal load recent trx: {e}")

    def _load_stok_alerts(self):
        try:
            habis = self.db_gudang.get_stok_habis()
            menipis = self.db_gudang.get_stok_menipis()
            # Tuple: (kategori, warna, ukuran, jumlah, status) - sesuai header tabel
            all_alerts = (
                [(i['kategori'], i['warna'], i['ukuran'], 0, "HABIS") for i in habis] +
                [(i['kategori'], i['warna'], i['ukuran'], i['jumlah'], "MENIPIS") for i in menipis]
            )
            self.tbl_stok_alert.setRowCount(len(all_alerts))
            for i, (kategori, warna, ukuran, jumlah, status) in enumerate(all_alerts):
                for j, v in enumerate([kategori, warna, ukuran, str(jumlah)]):
                    cell = QTableWidgetItem(v)
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.tbl_stok_alert.setItem(i, j, cell)

                badge = QLabel(status)
                badge.setStyleSheet(BADGE_HABIS if status == "HABIS" else BADGE_MENIPIS)
                badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tbl_stok_alert.setCellWidget(i, 4, badge)
        except Exception as e:
            logger.error(f"Gagal load stok alert: {e}")
