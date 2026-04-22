"""
ui/warehouse_dashboard.py - Dashboard Gudang (Warehouse Management)
Fitur: Manajemen Stok, Log Stok, Backup Stok, Stok Alert
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget,
    QGroupBox, QSpinBox, QFormLayout, QDialog, QDialogButtonBox,
    QMessageBox, QComboBox, QFrame, QLineEdit, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from ui.styles import BADGE_OK, BADGE_MENIPIS, BADGE_HABIS

logger = logging.getLogger('warehouse_ui')


def _make_stat_card(icon: str, nilai: str, label: str, color: str = "#a6e3a1") -> QFrame:
    """Buat widget stat card kecil."""
    card = QFrame()
    card.setObjectName("stat_card")
    card.setMinimumWidth(160)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(14, 12, 14, 12)

    icon_lbl = QLabel(icon)
    icon_lbl.setObjectName("stat_icon")
    icon_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)

    val_lbl = QLabel(nilai)
    val_lbl.setObjectName("stat_value")
    val_lbl.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: bold;")
    val_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)

    lab_lbl = QLabel(label)
    lab_lbl.setObjectName("stat_label")
    lab_lbl.setStyleSheet("color: #6c7086; font-size: 10px;")

    layout.addWidget(icon_lbl)
    layout.addWidget(val_lbl)
    layout.addWidget(lab_lbl)
    return card, val_lbl


class WarehouseDashboard(QWidget):
    """Dashboard Gudang - tab utama warehouse management."""

    def __init__(self, db_gudang, db_utama, excel_exporter_gudang=None, parent=None):
        super().__init__(parent)
        self.db_gudang = db_gudang
        self.db_utama = db_utama
        self.excel_exporter_gudang = excel_exporter_gudang
        self._init_ui()
        self.refresh_all()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # ── Header ──
        hdr = QHBoxLayout()
        title = QLabel("🏭  Dashboard Gudang")
        title.setObjectName("section_title")
        sub = QLabel("Manajemen stok, log perubahan & backup otomatis")
        sub.setObjectName("section_sub")
        btn_refresh = QPushButton("🔄  Refresh")
        btn_refresh.setProperty("class", "secondary")
        btn_refresh.setFixedWidth(120)
        btn_refresh.clicked.connect(self.refresh_all)

        btn_export_gudang = QPushButton("📤  Export Excel")
        btn_export_gudang.setProperty("class", "success")
        btn_export_gudang.setFixedWidth(140)
        btn_export_gudang.clicked.connect(self._export_gudang)

        hdr.addWidget(title)
        hdr.addWidget(sub, 1)
        hdr.addWidget(btn_refresh)
        hdr.addWidget(btn_export_gudang)
        root.addLayout(hdr)

        # ── Stat Cards ──
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)

        card1, self.lbl_total_item = _make_stat_card("📦", "0", "Total Jenis Barang")
        card2, self.lbl_total_stok = _make_stat_card("🔢", "0", "Total Unit Stok", "#89dceb")
        card3, self.lbl_stok_menipis = _make_stat_card("⚠️", "0", "Stok Menipis", "#f9e2af")
        card4, self.lbl_stok_habis = _make_stat_card("🚫", "0", "Stok Habis", "#f38ba8")
        card5, self.lbl_total_log = _make_stat_card("📋", "0", "Total Log Perubahan", "#cba6f7")

        for card in [card1, card2, card3, card4, card5]:
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            stats_row.addWidget(card)

        root.addLayout(stats_row)

        # ── Tab ──
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabBar::tab { padding: 8px 20px; }")

        tabs.addTab(self._tab_stok(), "📦  Manajemen Stok")
        tabs.addTab(self._tab_log(), "📋  Log Stok")
        tabs.addTab(self._tab_backup(), "💾  Backup Stok")
        tabs.addTab(self._tab_alert(), "⚠️  Stok Alert")

        root.addWidget(tabs)

    # ══════════════════════════════════════════════
    # TAB: MANAJEMEN STOK
    # ══════════════════════════════════════════════

    def _tab_stok(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # ── Form tambah / update stok ──
        form_group = QGroupBox("Tambah / Update Stok")
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.combo_warna_stok = QComboBox()
        self.combo_kategori_stok = QComboBox()
        self.combo_ukuran_stok = QComboBox()
        self.spin_jumlah = QSpinBox()
        self.spin_jumlah.setRange(0, 99999)
        self.spin_minimum = QSpinBox()
        self.spin_minimum.setRange(0, 9999)
        self.spin_minimum.setValue(10)
        self.input_keterangan = QLineEdit()
        self.input_keterangan.setPlaceholderText("Keterangan perubahan stok")

        form_layout.addRow("Warna:", self.combo_warna_stok)
        form_layout.addRow("Kategori:", self.combo_kategori_stok)
        form_layout.addRow("Ukuran:", self.combo_ukuran_stok)
        form_layout.addRow("Jumlah Stok:", self.spin_jumlah)
        form_layout.addRow("Stok Minimum Alert:", self.spin_minimum)
        form_layout.addRow("Keterangan:", self.input_keterangan)
        form_group.setLayout(form_layout)

        btn_row = QHBoxLayout()
        btn_save = QPushButton("💾  Simpan Stok")
        btn_save.clicked.connect(self._save_stok)
        btn_restock = QPushButton("➕  Restock")
        btn_restock.setProperty("class", "success")
        btn_restock.clicked.connect(self._restock_from_table)
        btn_del = QPushButton("🗑  Hapus")
        btn_del.setProperty("class", "danger")
        btn_del.clicked.connect(self._delete_stok)

        btn_row.addWidget(btn_save)
        btn_row.addWidget(btn_restock)
        btn_row.addWidget(btn_del)
        btn_row.addStretch()

        # ── Tabel Stok ──
        self.tbl_stok = QTableWidget()
        self.tbl_stok.setColumnCount(8)
        self.tbl_stok.setHorizontalHeaderLabels([
            "ID", "Kategori", "Warna", "Ukuran",
            "Jumlah", "Min Alert", "Update Terakhir", "Status"
        ])
        self.tbl_stok.setAlternatingRowColors(True)
        self.tbl_stok.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_stok.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_stok.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl_stok.itemSelectionChanged.connect(self._on_stok_selected)

        layout.addWidget(form_group)
        layout.addLayout(btn_row)
        layout.addWidget(self.tbl_stok)
        return w

    # ══════════════════════════════════════════════
    # TAB: LOG STOK
    # ══════════════════════════════════════════════

    def _tab_log(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 12, 12, 12)

        ctrl = QHBoxLayout()
        btn_refresh_log = QPushButton("🔄  Refresh Log")
        btn_refresh_log.setProperty("class", "secondary")
        btn_refresh_log.clicked.connect(self._load_log)
        ctrl.addWidget(btn_refresh_log)
        ctrl.addStretch()
        layout.addLayout(ctrl)

        self.tbl_log = QTableWidget()
        self.tbl_log.setColumnCount(9)
        self.tbl_log.setHorizontalHeaderLabels([
            "ID", "Warna", "Kategori", "Ukuran",
            "Stok Lama", "Stok Baru", "Perubahan", "Aksi", "Tanggal"
        ])
        self.tbl_log.setAlternatingRowColors(True)
        self.tbl_log.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_log.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tbl_log)
        return w

    # ══════════════════════════════════════════════
    # TAB: BACKUP STOK
    # ══════════════════════════════════════════════

    def _tab_backup(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 12, 12, 12)

        ctrl = QHBoxLayout()
        btn_refresh_backup = QPushButton("🔄  Refresh Backup")
        btn_refresh_backup.setProperty("class", "secondary")
        btn_refresh_backup.clicked.connect(self._load_backup)
        ctrl.addWidget(btn_refresh_backup)
        ctrl.addStretch()

        info = QLabel("💡 Backup dibuat otomatis setiap ada perubahan stok.")
        info.setStyleSheet("color: #6c7086; font-size: 10px;")
        ctrl.addWidget(info)
        layout.addLayout(ctrl)

        self.tbl_backup = QTableWidget()
        self.tbl_backup.setColumnCount(7)
        self.tbl_backup.setHorizontalHeaderLabels([
            "ID", "Warna", "Kategori", "Ukuran",
            "Jumlah", "Keterangan", "Tanggal Backup"
        ])
        self.tbl_backup.setAlternatingRowColors(True)
        self.tbl_backup.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_backup.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tbl_backup)
        return w

    # ══════════════════════════════════════════════
    # TAB: STOK ALERT
    # ══════════════════════════════════════════════

    def _tab_alert(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        # Stok habis
        grp_habis = QGroupBox("🚫  Stok Habis (0 unit)")
        lyt_habis = QVBoxLayout(grp_habis)
        self.tbl_habis = QTableWidget()
        self.tbl_habis.setColumnCount(4)
        self.tbl_habis.setHorizontalHeaderLabels(["ID", "Warna", "Kategori", "Ukuran"])
        self.tbl_habis.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        lyt_habis.addWidget(self.tbl_habis)

        # Stok menipis
        grp_menipis = QGroupBox("⚠️  Stok Menipis (≤ Batas Minimum)")
        lyt_menipis = QVBoxLayout(grp_menipis)
        self.tbl_menipis = QTableWidget()
        self.tbl_menipis.setColumnCount(6)
        self.tbl_menipis.setHorizontalHeaderLabels([
            "ID", "Warna", "Kategori", "Ukuran", "Jumlah", "Min Alert"
        ])
        self.tbl_menipis.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        lyt_menipis.addWidget(self.tbl_menipis)

        layout.addWidget(grp_habis)
        layout.addWidget(grp_menipis)
        return w

    # ══════════════════════════════════════════════
    # LOAD DATA
    # ══════════════════════════════════════════════

    def _export_gudang(self):
        """Export semua data gudang ke Excel."""
        if not self.excel_exporter_gudang:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Warning", "Export tidak tersedia.")
            return
        try:
            success, message = self.excel_exporter_gudang.export_gudang()
            from PyQt6.QtWidgets import QMessageBox
            if success:
                QMessageBox.information(self, "Sukses", message)
            else:
                QMessageBox.warning(self, "Gagal", message)
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", str(e))

    def refresh_all(self):
        """Refresh semua data di semua tab."""
        self._load_combo_data()
        self._load_stok_table()
        self._load_log()
        self._load_backup()
        self._load_alerts()
        self._update_stats()

    def _load_combo_data(self):
        try:
            for combo in [self.combo_warna_stok]:
                combo.blockSignals(True)
                combo.clear()
                for row in self.db_utama.get_all_warna():
                    combo.addItem(row[1], row[0])
                combo.blockSignals(False)

            for combo in [self.combo_kategori_stok]:
                combo.blockSignals(True)
                combo.clear()
                for row in self.db_utama.get_all_kategori():
                    combo.addItem(row[1], row[0])
                combo.blockSignals(False)

            for combo in [self.combo_ukuran_stok]:
                combo.blockSignals(True)
                combo.clear()
                for row in self.db_utama.get_all_ukuran():
                    combo.addItem(row[1], row[0])
                combo.blockSignals(False)
        except Exception as e:
            logger.error(f"Gagal load combo: {e}")

    def _load_stok_table(self):
        try:
            data = self.db_gudang.get_all_stok()
            self.tbl_stok.setRowCount(len(data))
            for row_idx, item in enumerate(data):
                jumlah = item['jumlah']
                minimum = item['stok_minimum']

                if jumlah == 0:
                    status, badge_style = "HABIS", BADGE_HABIS
                elif jumlah <= minimum:
                    status, badge_style = "MENIPIS", BADGE_MENIPIS
                else:
                    status, badge_style = "OK", BADGE_OK

                cols = [
                    str(item['id']), item['kategori'], item['warna'],
                    item['ukuran'], str(jumlah), str(minimum),
                    item['tanggal_update']
                ]
                for col_idx, val in enumerate(cols):
                    cell = QTableWidgetItem(val)
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.tbl_stok.setItem(row_idx, col_idx, cell)

                status_lbl = QLabel(status)
                status_lbl.setStyleSheet(badge_style)
                status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tbl_stok.setCellWidget(row_idx, 7, status_lbl)

            self.tbl_stok.resizeRowsToContents()
        except Exception as e:
            logger.error(f"Gagal load stok: {e}")

    def _load_log(self):
        try:
            data = self.db_gudang.get_log_stok(limit=200)
            self.tbl_log.setRowCount(len(data))
            for row_idx, item in enumerate(data):
                perubahan = item['perubahan']
                perubahan_str = f"+{perubahan}" if perubahan > 0 else str(perubahan)
                perubahan_color = "#a6e3a1" if perubahan > 0 else "#f38ba8"

                cols = [
                    str(item['id']), item['warna'], item['kategori'], item['ukuran'],
                    str(item['stok_lama']), str(item['stok_baru']),
                    perubahan_str, item['aksi'], item['tanggal']
                ]
                for col_idx, val in enumerate(cols):
                    cell = QTableWidgetItem(val)
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if col_idx == 6:
                        cell.setForeground(
                            __import__('PyQt6.QtGui', fromlist=['QColor']).QColor(perubahan_color)
                        )
                    self.tbl_log.setItem(row_idx, col_idx, cell)
        except Exception as e:
            logger.error(f"Gagal load log: {e}")

    def _load_backup(self):
        try:
            data = self.db_gudang.get_backup_stok(limit=200)
            self.tbl_backup.setRowCount(len(data))
            for row_idx, item in enumerate(data):
                cols = [
                    str(item['id']), item['warna'], item['kategori'], item['ukuran'],
                    str(item['jumlah']), item.get('keterangan', ''), item['tanggal_backup']
                ]
                for col_idx, val in enumerate(cols):
                    cell = QTableWidgetItem(val)
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.tbl_backup.setItem(row_idx, col_idx, cell)
        except Exception as e:
            logger.error(f"Gagal load backup: {e}")

    def _load_alerts(self):
        try:
            habis = self.db_gudang.get_stok_habis()
            self.tbl_habis.setRowCount(len(habis))
            for i, item in enumerate(habis):
                for j, val in enumerate([str(item['id']), item['warna'], item['kategori'], item['ukuran']]):
                    cell = QTableWidgetItem(val)
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.tbl_habis.setItem(i, j, cell)

            menipis = self.db_gudang.get_stok_menipis()
            self.tbl_menipis.setRowCount(len(menipis))
            for i, item in enumerate(menipis):
                for j, val in enumerate([
                    str(item['id']), item['warna'], item['kategori'],
                    item['ukuran'], str(item['jumlah']), str(item['stok_minimum'])
                ]):
                    cell = QTableWidgetItem(val)
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.tbl_menipis.setItem(i, j, cell)
        except Exception as e:
            logger.error(f"Gagal load alert: {e}")

    def _update_stats(self):
        try:
            stats = self.db_gudang.get_statistik_gudang()
            self.lbl_total_item.setText(str(stats['total_item']))
            self.lbl_total_stok.setText(str(stats['total_stok']))
            self.lbl_stok_menipis.setText(str(stats['stok_menipis']))
            self.lbl_stok_habis.setText(str(stats['stok_habis']))
            self.lbl_total_log.setText(str(stats['total_log']))
        except Exception as e:
            logger.error(f"Gagal update stats: {e}")

    # ══════════════════════════════════════════════
    # ACTIONS
    # ══════════════════════════════════════════════

    def _on_stok_selected(self):
        """Isi form dari baris terpilih di tabel stok."""
        row = self.tbl_stok.currentRow()
        if row < 0:
            return
        try:
            jumlah_item = self.tbl_stok.item(row, 4)
            minimum_item = self.tbl_stok.item(row, 5)
            if jumlah_item:
                self.spin_jumlah.setValue(int(jumlah_item.text()))
            if minimum_item:
                self.spin_minimum.setValue(int(minimum_item.text()))
        except Exception:
            pass

    def _get_selected_stok_id(self):
        row = self.tbl_stok.currentRow()
        if row < 0:
            return None
        item = self.tbl_stok.item(row, 0)
        return int(item.text()) if item else None

    def _save_stok(self):
        try:
            warna_id = self.combo_warna_stok.currentData()
            kategori_id = self.combo_kategori_stok.currentData()
            ukuran_id = self.combo_ukuran_stok.currentData()

            if not all([warna_id, kategori_id, ukuran_id]):
                QMessageBox.warning(self, "Warning", "Pilih warna, kategori, dan ukuran!")
                return

            jumlah = self.spin_jumlah.value()
            minimum = self.spin_minimum.value()
            keterangan = self.input_keterangan.text().strip() or "Update manual"

            self.db_gudang.add_or_update_stok(
                warna_id, kategori_id, ukuran_id, jumlah, minimum, keterangan
            )
            QMessageBox.information(self, "Sukses", "Stok berhasil disimpan!")
            self.input_keterangan.clear()
            self.refresh_all()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal simpan stok: {e}")

    def _restock_from_table(self):
        stok_id = self._get_selected_stok_id()
        if not stok_id:
            QMessageBox.warning(self, "Warning", "Pilih baris stok di tabel terlebih dahulu!")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Restock Barang")
        dialog.setMinimumWidth(320)
        layout = QFormLayout(dialog)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        spin = QSpinBox()
        spin.setRange(1, 99999)
        spin.setValue(10)
        ket_edit = QLineEdit()
        ket_edit.setPlaceholderText("Keterangan restock")

        layout.addRow("Tambah Qty:", spin)
        layout.addRow("Keterangan:", ket_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                keterangan = ket_edit.text().strip() or "Restock manual"
                self.db_gudang.restock(stok_id, spin.value(), keterangan)
                QMessageBox.information(self, "Sukses", f"Restock +{spin.value()} berhasil!")
                self.refresh_all()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Gagal restock: {e}")

    def _delete_stok(self):
        stok_id = self._get_selected_stok_id()
        if not stok_id:
            QMessageBox.warning(self, "Warning", "Pilih baris stok di tabel terlebih dahulu!")
            return
        reply = QMessageBox.question(
            self, "Konfirmasi", f"Hapus stok ID {stok_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db_gudang.delete_stok(stok_id)
            QMessageBox.information(self, "Sukses", "Stok berhasil dihapus.")
            self.refresh_all()
